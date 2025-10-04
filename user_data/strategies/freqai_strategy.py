# --- Do not remove these imports ---
from functools import reduce

import talib.abstract as ta
from pandas import DataFrame
from technical import qtpylib

from freqtrade.strategy import IStrategy


# --------------------------------


class freqai_strategy(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "5m"

    can_short = False
    use_exit_signal = True
    startup_trend_req = 200

    def feature_engineering_expand_basic(
        self, dataframe: DataFrame, metadata: dict, **kwargs
    ) -> DataFrame:
        """
        This function is called by FreqAI to add features for training.
        """
        dataframe["%-pct-change"] = dataframe["close"].pct_change()
        dataframe["%-raw_volume"] = dataframe["volume"]
        dataframe["%-raw_price"] = dataframe["close"]
        return dataframe

    def feature_engineering_standard(
        self, dataframe: DataFrame, metadata: dict, **kwargs
    ) -> DataFrame:
        """
        Adds technical indicators and advanced features to the dataframe.
        """
        # --- Base Indicators ---
        dataframe["rsi"] = ta.RSI(dataframe)
        dataframe["mfi"] = ta.MFI(dataframe)
        dataframe["adx"] = ta.ADX(dataframe)
        macd = ta.MACD(dataframe)
        dataframe["macd"] = macd["macd"]
        dataframe["macdsignal"] = macd["macdsignal"]
        dataframe["macdhist"] = macd["macdhist"]
        dataframe["ema_20"] = ta.EMA(dataframe, timeperiod=20)
        dataframe["ema_50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["ema_100"] = ta.EMA(dataframe, timeperiod=100)
        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe["bb_lowerband"] = bollinger["lower"]
        dataframe["bb_middleband"] = bollinger["mid"]
        dataframe["bb_upperband"] = bollinger["upper"]
        dataframe["atr"] = ta.ATR(dataframe)
        dataframe["obv"] = ta.OBV(dataframe)

        # --- Advanced Features ---
        dataframe["%-rsi_roc_10"] = ta.ROC(dataframe["rsi"], timeperiod=10)
        dataframe["%-dist_from_ema_50_norm"] = (
            dataframe["close"] - dataframe["ema_50"]
        ) / dataframe["atr"]

        rsi_rolling = dataframe["rsi"].rolling(20)
        dataframe["%-rsi_norm"] = (dataframe["rsi"] - rsi_rolling.mean()) / rsi_rolling.std()

        mfi_rolling = dataframe["mfi"].rolling(20)
        dataframe["%-mfi_norm"] = (dataframe["mfi"] - mfi_rolling.mean()) / mfi_rolling.std()

        adx_rolling = dataframe["adx"].rolling(20)
        dataframe["%-adx_norm"] = (dataframe["adx"] - adx_rolling.mean()) / adx_rolling.std()

        macd_rolling = dataframe["macd"].rolling(20)
        dataframe["%-macd_norm"] = (dataframe["macd"] - macd_rolling.mean()) / macd_rolling.std()

        dataframe["%-ai_score"] = (
            dataframe["%-rsi_norm"]
            + dataframe["%-mfi_norm"]
            + dataframe["%-adx_norm"]
            + dataframe["%-macd_norm"]
            + dataframe["%-dist_from_ema_50_norm"]
        )
        return dataframe

    def set_freqai_targets(self, dataframe: DataFrame, metadata: dict, **kwargs):
        """
        Adds the training target to the dataframe.
        """
        period = self.config["freqai"]["feature_parameters"]["label_period_candles"]

        # The lookahead data is created here, right before it's used for the target.
        dataframe[f"future_max_{period}"] = dataframe["high"].rolling(period).max().shift(-period)

        dataframe["&-s-future_return"] = (
            dataframe[f"future_max_{period}"] - dataframe["close"]
        ) / dataframe["close"]
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        This is the main entry point for FreqAI.
        """
        dataframe = self.freqai.start(dataframe, metadata, self)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Users can add any custom logic to populate entry signals here.
        """
        # Using the prediction (`&-s-future_return`) to generate signals.
        enter_long_conditions = [
            dataframe["do_predict"] == 1,
            dataframe["&-s-future_return"] > 0.01,
        ]

        if enter_long_conditions:
            dataframe.loc[
                reduce(lambda x, y: x & y, enter_long_conditions),
                ["enter_long", "enter_tag"],
            ] = (1, "ai_buy")

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Users can add any custom logic to populate exit signals here.
        """
        exit_long_conditions = [
            dataframe["do_predict"] == 1,
            dataframe["&-s-future_return"] < -0.01,
        ]

        if exit_long_conditions:
            dataframe.loc[
                reduce(lambda x, y: x & y, exit_long_conditions),
                "exit_long",
            ] = 1

        return dataframe
