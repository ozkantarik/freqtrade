# --- Do not remove these imports ---
from functools import reduce

import numpy as np
import talib.abstract as ta
from pandas import DataFrame

import freqtrade.vendor.qtpylib.indicators as qtpylib
from freqtrade.strategy import IStrategy, DecimalParameter


class GeminiV12_strategy(IStrategy):
    """
    GeminiV12 - The Confidence Engine

    This strategy uses a regression model to predict future returns and trades
    based on the confidence of that prediction.
    """

    INTERFACE_VERSION = 3
    timeframe = "5m"
    can_short = True

    # --- Hyperparameters ---
    entry_threshold = 0.01 # Custom entry threshold

    # --- Optimal Trend-Following Parameters (from V8) ---
    buy_adx_threshold = 26
    fast_ema_period = 50
    slow_ema_period = 358
    slope_period = 7

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

        # New indicators for V11
        dataframe["rsi"] = ta.RSI(dataframe)
        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe["bb_lowerband"] = bollinger["lower"]
        dataframe["bb_middleband"] = bollinger["mid"]
        dataframe["bb_upperband"] = bollinger["upper"]

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

        # New features for V11
        dataframe["%-rsi"] = dataframe["rsi"]
        dataframe["%-bb_width"] = (dataframe["bb_upperband"] - dataframe["bb_lowerband"]) / dataframe["bb_middleband"]

        return dataframe

    def set_freqai_targets(self, dataframe: DataFrame, metadata: dict, **kwargs) -> DataFrame:
        """
        Target for the new regression model.
        """
        label_period = self.freqai_info["feature_parameters"]["label_period_candles"]
        dataframe["&s-future_return"] = (
            dataframe["close"].shift(-label_period) / dataframe["close"] - 1
        )
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Boilerplate to satisfy Freqtrade framework"""
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Boilerplate to satisfy Freqtrade framework"""
        return dataframe

    def populate_entry_long_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Long entry logic - REGRESSION MODEL
        """
        enter_long_conditions = [
            (dataframe["do_predict"] == 1),
            (dataframe["&-s_prediction"] > self.entry_threshold),
        ]

        dataframe.loc[
            reduce(lambda x, y: x & y, enter_long_conditions),
            ["enter_long", "enter_tag"],
        ] = (1, "regression_long")
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
        Short entry logic - REGRESSION MODEL
        """
        enter_short_conditions = [
            (dataframe["do_predict"] == 1),
            (dataframe["&-s_prediction"] < -self.entry_threshold),
        ]

        dataframe.loc[
            reduce(lambda x, y: x & y, enter_short_conditions),
            ["enter_short", "enter_tag"],
        ] = (1, "regression_short")

    def populate_exit_short_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Short exit logic.
        """
        dataframe.loc[
            (qtpylib.crossed_above(dataframe["ema_fast"], dataframe["ema_slow"])),
            "exit_short",
        ] = 1
        return dataframe
