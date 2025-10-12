# --- Do not remove these imports ---
from functools import reduce

import numpy as np
import talib.abstract as ta
from pandas import DataFrame

import freqtrade.vendor.qtpylib.indicators as qtpylib
from freqtrade.strategy import IStrategy


class GeminiV8_strategy(IStrategy):
    """
    GeminiV8 - Dynamic Target Strategy (Production)

    Objective: Evolve the V7 architecture by implementing a dynamic training
    target based on market volatility (ATR), making the AI's predictions
    more context-aware. This version contains the hardcoded, optimized
    parameters for production use.
    """

    INTERFACE_VERSION = 3
    timeframe = "5m"

    # --- Optimal parameters ---
    buy_adx_threshold = 53
    fast_ema_period = 50
    slow_ema_period = 358
    slope_period = 7
    target_atr_multiplier = 0.49

    # Minimal ROI and stoploss are fallbacks
    minimal_roi = {"0": 0.1}
    stoploss = -0.10
    use_exit_signal = True
    startup_trend_req = 200

    @staticmethod
    def rolling_slope(ser, window):
        """Helper function to calculate the slope of a series"""
        return ser.rolling(window=window).apply(
            lambda x: np.polyfit(range(window), x, 1)[0], raw=True
        )

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Calculate all indicators for both the AI model and the strategy logic.
        """
        # --- Base indicators ---
        dataframe["adx"] = ta.ADX(dataframe)
        dataframe["plus_di"] = ta.PLUS_DI(dataframe)
        dataframe["minus_di"] = ta.MINUS_DI(dataframe)
        dataframe["ema_fast"] = ta.EMA(dataframe, timeperiod=self.fast_ema_period)
        dataframe["ema_slow"] = ta.EMA(dataframe, timeperiod=self.slow_ema_period)

        # --- Indicator for dynamic target ---
        dataframe["atr"] = ta.ATR(dataframe)

        # --- New slope indicators ---
        dataframe["adx_slope"] = self.rolling_slope(dataframe["adx"], self.slope_period)
        dataframe["fast_ema_slope"] = self.rolling_slope(dataframe["ema_fast"], self.slope_period)

        # --- FreqAI Run ---
        dataframe = self.freqai.start(dataframe, metadata, self)

        return dataframe

    def feature_engineering_standard(
        self, dataframe: DataFrame, metadata: dict, **kwargs
    ) -> DataFrame:
        """
        Create and select the features for the AI model.
        """
        # --- Feature Engineering ---
        # Spread between fast and slow EMA, normalized
        dataframe["ema_spread"] = (dataframe["ema_fast"] - dataframe["ema_slow"]) / dataframe[
            "ema_slow"
        ]

        # --- Feature Selection ---
        # We select the new, more informative features for the model
        dataframe["%-ema_spread"] = dataframe["ema_spread"]
        dataframe["%-adx_slope"] = dataframe["adx_slope"]
        dataframe["%-fast_ema_slope"] = dataframe["fast_ema_slope"]
        # Keep ADX value as well
        dataframe["%-adx"] = dataframe["adx"]

        return dataframe

    def set_freqai_targets(self, dataframe: DataFrame, metadata: dict, **kwargs) -> DataFrame:
        """
        Define the training target for the AI.

        The AI's goal is to predict if the price will rise by an amount
        proportional to the current market volatility (ATR).
        """
        label_period = self.freqai_info["feature_parameters"]["label_period_candles"]

        # Dynamic target using ATR
        future_price = dataframe["close"].shift(-label_period)
        target_price = dataframe["close"] + (dataframe["atr"] * self.target_atr_multiplier)

        trend_continued = future_price > target_price

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
            ] = (1, "ai_v8_buy")

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
