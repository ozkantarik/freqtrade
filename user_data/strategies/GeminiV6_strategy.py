# --- Do not remove these imports ---
from functools import reduce

import talib.abstract as ta
from pandas import DataFrame

import freqtrade.vendor.qtpylib.indicators as qtpylib
from freqtrade.strategy import IStrategy


class GeminiV6_strategy(IStrategy):
    """
    GeminiV6 - Decoupled Trend-Following Strategy

    Objective: Use a general-purpose AI model to predict price increases,
    and then use traditional trend-defining indicators as a filter to decide
    when to act on the AI's predictions.
    """

    INTERFACE_VERSION = 3
    timeframe = "5m"

    # --- Optimal parameters found via hyperopt ---
    buy_adx_threshold = 39
    fast_ema_period = 35
    slow_ema_period = 237

    # Minimal ROI and stoploss are fallbacks
    minimal_roi = {"0": 0.1}
    stoploss = -0.10
    use_exit_signal = True
    startup_trend_req = 200

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Calculate all indicators for both the AI model and the strategy logic.
        """
        # --- Trend-defining indicators for the strategy filter ---
        dataframe["adx"] = ta.ADX(dataframe)
        dataframe["plus_di"] = ta.PLUS_DI(dataframe)
        dataframe["minus_di"] = ta.MINUS_DI(dataframe)

        dataframe["ema_fast"] = ta.EMA(dataframe, timeperiod=self.fast_ema_period)
        dataframe["ema_slow"] = ta.EMA(dataframe, timeperiod=self.slow_ema_period)

        # --- FreqAI Run ---
        dataframe = self.freqai.start(dataframe, metadata, self)

        return dataframe

    def feature_engineering_standard(
        self, dataframe: DataFrame, metadata: dict, **kwargs
    ) -> DataFrame:
        """
        Select and prefix the features for the AI model.
        The model will be trained on the same indicators our strategy uses for its filter.
        """
        dataframe["%-adx"] = dataframe["adx"]
        dataframe["%-plus_di"] = dataframe["plus_di"]
        dataframe["%-minus_di"] = dataframe["minus_di"]
        dataframe["%-ema_fast"] = dataframe["ema_fast"]
        dataframe["%-ema_slow"] = dataframe["ema_slow"]
        return dataframe

    def set_freqai_targets(self, dataframe: DataFrame, metadata: dict, **kwargs) -> DataFrame:
        """
        Define the training target for the AI.

        The AI's goal is simplified: predict if the price will be higher
        N candles in the future, regardless of any other condition.
        """
        label_period = self.freqai_info["feature_parameters"]["label_period_candles"]

        # The target is simply whether the price rose or not.
        trend_continued = dataframe["close"].shift(-label_period) > dataframe["close"]

        # Set the target class
        dataframe["&-s_class"] = trend_continued.astype(int).astype(str)

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        AI-driven entry logic with an indicator filter.

        A trade is entered if:
        1. The strategy's indicators confirm a "strong uptrend".
        2. The AI, trained on all data, predicts the price will rise.
        """
        # Define what a strong uptrend is (our strategy's filter)
        strong_uptrend = (
            (dataframe["adx"] > self.buy_adx_threshold)
            & (dataframe["plus_di"] > dataframe["minus_di"])
            & (dataframe["ema_fast"] > dataframe["ema_slow"])
        )

        enter_long_conditions = [
            strong_uptrend,
            dataframe["do_predict"] == 1,
            dataframe["&-s_class"] == "1",
        ]

        if enter_long_conditions:
            dataframe.loc[
                reduce(lambda x, y: x & y, enter_long_conditions),
                ["enter_long", "enter_tag"],
            ] = (1, "ai_decoupled_buy")

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
