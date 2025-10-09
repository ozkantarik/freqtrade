# --- Do not remove these imports ---
from functools import reduce

import talib.abstract as ta
from pandas import DataFrame

import freqtrade.vendor.qtpylib.indicators as qtpylib
from freqtrade.strategy import IStrategy


class GeminiV5_strategy(IStrategy):
    """
    GeminiV5 - Pure Trend Following Strategy

    Objective: Identify a strong, established trend and use an AI model to confirm
    the trend is likely to continue before entering a trade.
    """

    INTERFACE_VERSION = 3
    timeframe = "5m"

    # Minimal ROI and stoploss are fallbacks
    minimal_roi = {"0": 0.10}
    stoploss = -0.10
    use_exit_signal = True
    startup_trend_req = 200

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Calculate all indicators for both the AI model and the strategy logic.
        """
        # --- Trend-defining indicators ---
        dataframe["adx"] = ta.ADX(dataframe)
        dataframe["plus_di"] = ta.PLUS_DI(dataframe)
        dataframe["minus_di"] = ta.MINUS_DI(dataframe)

        dataframe["ema_fast"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["ema_slow"] = ta.EMA(dataframe, timeperiod=200)

        # --- FreqAI Run ---
        dataframe = self.freqai.start(dataframe, metadata, self)

        return dataframe

    def feature_engineering_standard(
        self, dataframe: DataFrame, metadata: dict, **kwargs
    ) -> DataFrame:
        """
        Select and prefix the features for the AI model.
        """
        dataframe["%-adx"] = dataframe["adx"]
        dataframe["%-plus_di"] = dataframe["plus_di"]
        dataframe["%-minus_di"] = dataframe["minus_di"]
        dataframe["%-ema_fast"] = dataframe["ema_fast"]
        dataframe["%-ema_slow"] = dataframe["ema_slow"]
        return dataframe

    def set_freqai_targets(self, dataframe: DataFrame, metadata: dict, **kwargs) -> DataFrame:
        """
        Define the training target.

        The goal is to predict if a strong trend will continue.
        A "buy" signal (1) is generated if:
        1. The current candle is in a strong uptrend (ADX > 25, DI+ > DI-).
        2. The price is higher N candles in the future.
        """
        label_period = self.freqai_info["feature_parameters"]["label_period_candles"]

        # Define what a strong uptrend is
        strong_uptrend = (
            (dataframe["adx"] > 25)
            & (dataframe["plus_di"] > dataframe["minus_di"])
            & (dataframe["ema_fast"] > dataframe["ema_slow"])
        )

        # Define if the trend continued
        trend_continued = dataframe["close"].shift(-label_period) > dataframe["close"]

        # Set the target class
        dataframe["&-s_class"] = (strong_uptrend & trend_continued).astype(str)

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
            ] = (1, "ai_trend_buy")

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Exit when the trend is no longer considered active.
        """
        # A simple trend-following exit: exit when fast EMA crosses below slow EMA
        dataframe.loc[
            (qtpylib.crossed_below(dataframe["ema_fast"], dataframe["ema_slow"])),
            "exit_long",
        ] = 1

        return dataframe
