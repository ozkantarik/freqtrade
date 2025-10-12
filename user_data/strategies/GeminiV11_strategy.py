# --- Do not remove these imports ---
from functools import reduce

import numpy as np
import talib.abstract as ta
from pandas import DataFrame

import freqtrade.vendor.qtpylib.indicators as qtpylib
from freqtrade.strategy import IStrategy


class GeminiV11_strategy(IStrategy):
    """
    GeminiV11 - The All-Weather Hunter

    This strategy is a true all-weather hunter, capable of going long in
    trending markets and short in ranging markets.
    """

    INTERFACE_VERSION = 3
    timeframe = "5m"
    can_short = True

    # --- Optimal Trend-Following Parameters (from V8) ---
    buy_adx_threshold = 53
    fast_ema_period = 50
    slow_ema_period = 358
    slope_period = 7
    target_atr_multiplier = 0.49

    # --- Market Regime Filter Parameters ---
    regime_adx_threshold = 25

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
        Calculate all indicators.
        """
        dataframe["adx"] = ta.ADX(dataframe)
        dataframe["plus_di"] = ta.PLUS_DI(dataframe)
        dataframe["minus_di"] = ta.MINUS_DI(dataframe)
        dataframe["ema_fast"] = ta.EMA(dataframe, timeperiod=self.fast_ema_period)
        dataframe["ema_slow"] = ta.EMA(dataframe, timeperiod=self.slow_ema_period)
        dataframe["atr"] = ta.ATR(dataframe)
        dataframe["adx_slope"] = self.rolling_slope(dataframe["adx"], self.slope_period)
        dataframe["fast_ema_slope"] = self.rolling_slope(
            dataframe["ema_fast"], self.slope_period
        )
        dataframe = self.freqai.start(dataframe, metadata, self)
        return dataframe

    def feature_engineering_standard(
        self, dataframe: DataFrame, metadata: dict, **kwargs
    ) -> DataFrame:
        """
        Features for the primary AI model.
        """
        dataframe["ema_spread"] = (
            dataframe["ema_fast"] - dataframe["ema_slow"]
        ) / dataframe["ema_slow"]
        dataframe["%-ema_spread"] = dataframe["ema_spread"]
        dataframe["%-adx_slope"] = dataframe["adx_slope"]
        dataframe["%-fast_ema_slope"] = dataframe["fast_ema_slope"]
        dataframe["%-adx"] = dataframe["adx"]
        return dataframe

    def set_freqai_targets(self, dataframe: DataFrame, metadata: dict, **kwargs) -> DataFrame:
        """
        Target for the primary AI model.
        """
        label_period = self.freqai_info["feature_parameters"]["label_period_candles"]
        future_price = dataframe["close"].shift(-label_period)
        target_price = (
            dataframe["close"] + (dataframe["atr"] * self.target_atr_multiplier)
        )
        trend_continued = future_price > target_price
        dataframe["&-s_class"] = trend_continued.astype(int).astype(str)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Boilerplate to satisfy Freqtrade framework"""
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Boilerplate to satisfy Freqtrade framework"""
        return dataframe

    def populate_entry_long_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Long entry logic.
        """
        is_trending = dataframe["adx"] > self.regime_adx_threshold
        trending_conditions = [
            (dataframe["adx"] > self.buy_adx_threshold),
            (dataframe["plus_di"] > dataframe["minus_di"]),
            (dataframe["ema_fast"] > dataframe["ema_slow"]),
            (dataframe["do_predict"] == 1),
            (dataframe["&-s_class"] == "1"),
        ]
        dataframe.loc[
            is_trending & reduce(lambda x, y: x & y, trending_conditions),
            ["enter_long", "enter_tag"],
        ] = (1, "trending_long")
        return dataframe

    def populate_exit_long_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Long exit logic.
        """
        dataframe.loc[
            (qtpylib.crossed_below(dataframe["ema_fast"], dataframe["ema_slow"])),
            "exit_long",
        ] = 1
        return dataframe

    def populate_entry_short_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Short entry logic.
        """
        is_ranging = dataframe["adx"] <= self.regime_adx_threshold
        ranging_conditions = [
            (dataframe["do_predict"] == 1),
            (dataframe["&-s_class"] == "0"),
        ]
        dataframe.loc[
            is_ranging & reduce(lambda x, y: x & y, ranging_conditions),
            ["enter_short", "enter_tag"],
        ] = (1, "ranging_short")
        return dataframe

    def populate_exit_short_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Short exit logic.
        """
        dataframe.loc[
            (qtpylib.crossed_above(dataframe["ema_fast"], dataframe["ema_slow"])),
            "exit_short",
        ] = 1
        return dataframe
