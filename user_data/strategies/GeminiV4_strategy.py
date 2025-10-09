# --- Do not remove these imports ---
from functools import reduce

import talib.abstract as ta
from pandas import DataFrame

from freqtrade.strategy import IStrategy


class GeminiV4_strategy(IStrategy):
    """
    GeminiV4 - Volatility Trading Strategy

    Objective: Identify periods of low volatility (a "squeeze") and use an AI model
    to predict the subsequent high-volatility breakout.
    """

    INTERFACE_VERSION = 3
    timeframe = "5m"

    # Minimal ROI and stoploss are fallbacks
    minimal_roi = {"0": 0.05}
    stoploss = -0.15
    use_exit_signal = True
    startup_trend_req = 300

    def feature_engineering_standard(
        self, dataframe: DataFrame, metadata: dict, **kwargs
    ) -> DataFrame:
        """
        Create the core features for the volatility squeeze analysis.
        """
        # -- Bollinger Bands --
        bollinger = ta.BBANDS(dataframe, timeperiod=20, nbdevup=2.0, nbdevdn=2.0, matype=0)
        dataframe["bb_lowerband"] = bollinger["lowerband"]
        dataframe["bb_middleband"] = bollinger["middleband"]
        dataframe["bb_upperband"] = bollinger["upperband"]

        # -- Keltner Channels --
        keltner_period = 20
        atr_period = 10
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=atr_period)
        keltner_middle = ta.EMA(dataframe, timeperiod=keltner_period)
        keltner_upper = keltner_middle + dataframe["atr"] * 1.5
        keltner_lower = keltner_middle - dataframe["atr"] * 1.5

        # --- Volatility Squeeze Feature ---
        # A "squeeze" is on when the Bollinger Bands are inside the Keltner Channels
        squeeze_on = (dataframe["bb_lowerband"] > keltner_lower) & (
            dataframe["bb_upperband"] < keltner_upper
        )
        dataframe["%-squeeze_on"] = squeeze_on.astype(int)

        # Other volatility and momentum features
        dataframe["%-bb_width"] = (
            dataframe["bb_upperband"] - dataframe["bb_lowerband"]
        ) / dataframe["bb_middleband"]
        dataframe["%-rsi"] = ta.RSI(dataframe)

        return dataframe

    def set_freqai_targets(self, dataframe: DataFrame, metadata: dict, **kwargs) -> DataFrame:
        """
        Define the training target.

        The goal is to predict a profitable breakout after a volatility squeeze.
        A "buy" signal (1) is generated if:
        1. A squeeze has just ended (the `%-squeeze_on` feature goes from 1 to 0).
        2. The price increases by at least 2 * ATR in the next N candles.
        """
        label_period = self.freqai_info["feature_parameters"]["label_period_candles"]

        # Identify where the squeeze ends
        squeeze_ends = (dataframe["%-squeeze_on"].shift(1) == 1) & (dataframe["%-squeeze_on"] == 0)

        # Calculate the maximum future price increase over the label period
        future_max_price = dataframe["high"].rolling(label_period).max().shift(-label_period)
        future_price_increase = future_max_price - dataframe["close"]

        # Define a profitable breakout as an increase of 2x ATR
        profitable_breakout = future_price_increase > (dataframe["atr"] * 2.0)

        # Set the target class
        dataframe["&-s_class"] = (squeeze_ends & profitable_breakout).astype(str)

        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Main entry point for FreqAI.
        """
        dataframe = self.freqai.start(dataframe, metadata, self)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        AI-driven entry logic.
        """
        enter_long_conditions = [
            dataframe["do_predict"] == 1,
            dataframe["&-s_class"] == "1",
        ]

        if enter_long_conditions:
            dataframe.loc[
                reduce(lambda x, y: x & y, enter_long_conditions),
                ["enter_long", "enter_tag"],
            ] = (1, "ai_squeeze_breakout")

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        AI-driven exit logic.
        """
        exit_long_conditions = [
            dataframe["do_predict"] == 1,
            dataframe["&-s_class"] == "0",
        ]

        if exit_long_conditions:
            dataframe.loc[
                reduce(lambda x, y: x & y, exit_long_conditions),
                "exit_long",
            ] = 1

        return dataframe
