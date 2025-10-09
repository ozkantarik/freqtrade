# CemV1 Strategy - Single-Stage Advanced Model
from functools import reduce

import talib.abstract as ta
from pandas import DataFrame
from technical import qtpylib

from freqtrade.strategy import DecimalParameter, IStrategy


class CemV1Strategy(IStrategy):
    timeframe = "5m"
    INTERFACE_VERSION = 3

    # --- Hyperopt Spaces ---
    buy_future_max_return = DecimalParameter(0.01, 0.10, default=0.03, space="buy")
    sell_future_max_return = DecimalParameter(0.00, 0.02, default=0.01, space="sell")

    # --- Fallback settings ---
    minimal_roi = {"0": 0.05}
    stoploss = -0.15
    use_exit_signal = True
    startup_trend_req = 300

    def feature_engineering_expand_all(
        self, dataframe: DataFrame, period: int, metadata: dict, **kwargs
    ) -> DataFrame:
        dataframe[f"%-rsi-{period}"] = ta.RSI(dataframe, timeperiod=period)
        dataframe[f"%-mfi-{period}"] = ta.MFI(dataframe, timeperiod=period)
        dataframe[f"%-adx-{period}"] = ta.ADX(dataframe, timeperiod=period)
        dataframe[f"%-sma-{period}"] = ta.SMA(dataframe, timeperiod=period)
        bollinger = qtpylib.bollinger_bands(
            qtpylib.typical_price(dataframe), window=period, stds=2.2
        )
        dataframe[f"%-bb_width-{period}"] = (bollinger["upper"] - bollinger["lower"]) / bollinger[
            "mid"
        ]
        dataframe[f"%-close-bb_lower-{period}"] = dataframe["close"] / bollinger["lower"]
        return dataframe

    def feature_engineering_expand_basic(
        self, dataframe: DataFrame, metadata: dict, **kwargs
    ) -> DataFrame:
        dataframe["%-pct-change"] = dataframe["close"].pct_change()
        dataframe["%-raw_volume"] = dataframe["volume"]
        dataframe["%-raw_price"] = dataframe["close"]
        return dataframe

    def feature_engineering_standard(
        self, dataframe: DataFrame, metadata: dict, **kwargs
    ) -> DataFrame:
        dataframe["rsi"] = ta.RSI(dataframe)
        dataframe["mfi"] = ta.MFI(dataframe)
        dataframe["adx"] = ta.ADX(dataframe)
        for indicator in ["rsi", "mfi", "adx"]:
            rolling_mean = dataframe[indicator].rolling(20).mean()
            rolling_std = dataframe[indicator].rolling(20).std()
            dataframe[f"%-{indicator}_norm"] = (dataframe[indicator] - rolling_mean) / rolling_std
        dataframe["%-ai_score"] = (
            dataframe["%-rsi_norm"] + dataframe["%-mfi_norm"] + dataframe["%-adx_norm"]
        )
        dataframe["%-day_of_week"] = dataframe["date"].dt.dayofweek
        dataframe["%-hour_of_day"] = dataframe["date"].dt.hour
        return dataframe

    def set_freqai_targets(self, dataframe: DataFrame, metadata: dict, **kwargs) -> DataFrame:
        label_period = self.freqai_info["feature_parameters"]["label_period_candles"]
        future_max_price = dataframe["high"].rolling(label_period).max().shift(-label_period)
        dataframe["&-s_future_max_return"] = (future_max_price - dataframe["close"]) / dataframe[
            "close"
        ]
        dataframe.fillna({"&-s_future_max_return": 0}, inplace=True)
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe = self.freqai.start(dataframe, metadata, self)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        enter_long_conditions = [
            dataframe["do_predict"] == 1,
            dataframe["&-s_future_max_return"] > self.buy_future_max_return.value,
        ]
        if enter_long_conditions:
            dataframe.loc[
                reduce(lambda x, y: x & y, enter_long_conditions),
                ["enter_long", "enter_tag"],
            ] = (1, "ai_buy_cem_v1")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        exit_long_conditions = [
            dataframe["do_predict"] == 1,
            dataframe["&-s_future_max_return"] < self.sell_future_max_return.value,
        ]
        if exit_long_conditions:
            dataframe.loc[
                reduce(lambda x, y: x & y, exit_long_conditions),
                "exit_long",
            ] = 1
        return dataframe
