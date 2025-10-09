# --- Do not remove these imports ---
from functools import reduce

import numpy as np
import talib.abstract as ta
from pandas import DataFrame

from freqtrade.strategy import DecimalParameter, IStrategy


class GeminiV4_strategy(IStrategy):
    """
    GeminiV4 - Volatility Trading Strategy

    Objective: Identify periods of low volatility (a "squeeze") and use an AI model
    to predict the subsequent high-volatility breakout.
    """

    INTERFACE_VERSION = 3
    timeframe = "5m"

    # Define optimizable parameter for the profit target
    buy_profit_target_atr_multiplier = DecimalParameter(0.5, 3.0, default=2.0, space="buy")

    # Minimal ROI and stoploss are fallbacks
    minimal_roi = {"0": 0.05}
    stoploss = -0.15
    use_exit_signal = True
    startup_trend_req = 300

    def feature_engineering_standard(
        self, dataframe: DataFrame, metadata: dict, **kwargs
    ) -> DataFrame:
        """
        Select and prefix the features for the AI model.
        """
        dataframe["%-squeeze_on"] = dataframe["squeeze_on"]
        dataframe["%-bb_width"] = dataframe["bb_width"]
        dataframe["%-rsi"] = dataframe["rsi"]

        return dataframe

    def set_freqai_targets(self, dataframe: DataFrame, metadata: dict, **kwargs) -> DataFrame:
        """
        Define the training target.

        The goal is to predict a profitable breakout *during* a squeeze.
        A "buy" signal (1) is generated if:
        1. The candle is currently in a squeeze (`%-squeeze_on` == 1).
        2. The price increases by at least (ATR * multiplier) in the next N candles.
        """
        label_period = self.freqai_info["feature_parameters"]["label_period_candles"]

        # Calculate the maximum future price increase over the label period
        future_max_price = dataframe["high"].rolling(label_period).max().shift(-label_period)
        future_price_increase = future_max_price - dataframe["close"]

        # Define a profitable breakout
        profitable_breakout = future_price_increase > (
            dataframe["atr"] * self.buy_profit_target_atr_multiplier.value
        )

        # Set the target class only for candles that are in a squeeze
        dataframe["&-s_class"] = np.where(
            dataframe["%-squeeze_on"] == 1, profitable_breakout, 0
        ).astype(str)

        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Calculate all indicators for both the AI model and the strategy logic.
        """
        # -- Bollinger Bands --
        bollinger = ta.BBANDS(dataframe, timeperiod=20, nbdevup=2.0, nbdevdn=2.0, matype=0)
        dataframe["bb_lowerband"] = bollinger["lowerband"]
        dataframe["bb_middleband"] = bollinger["middleband"]
        dataframe["bb_upperband"] = bollinger["upperband"]
        dataframe["bb_width"] = (dataframe["bb_upperband"] - dataframe["bb_lowerband"]) / dataframe[
            "bb_middleband"
        ]

        # -- Keltner Channels --
        keltner_period = 20
        atr_period = 10
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=atr_period)
        keltner_middle = ta.EMA(dataframe, timeperiod=keltner_period)
        keltner_upper = keltner_middle + dataframe["atr"] * 1.5
        keltner_lower = keltner_middle - dataframe["atr"] * 1.5

        # --- Volatility Squeeze ---
        dataframe["squeeze_on"] = (
            (dataframe["bb_lowerband"] > keltner_lower)
            & (dataframe["bb_upperband"] < keltner_upper)
        ).astype(int)

        # -- Other features --
        dataframe["rsi"] = ta.RSI(dataframe)

        # --- FreqAI Run ---
        dataframe = self.freqai.start(dataframe, metadata, self)

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        AI-driven entry logic.
        """
        squeeze_ends = (dataframe["squeeze_on"].shift(1) == 1) & (dataframe["squeeze_on"] == 0)
        enter_long_conditions = [
            dataframe["do_predict"] == 1,
            dataframe["&-s_class"] == "1",
            squeeze_ends,
        ]

        if enter_long_conditions:
            dataframe.loc[
                reduce(lambda x, y: x & y, enter_long_conditions),
                ["enter_long", "enter_tag"],
            ] = (1, "ai_squeeze_breakout")

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        AI exit signal is disabled for this version.
        Exits will be handled by stoploss or ROI.
        """
        dataframe["exit_long"] = 0
        return dataframe
