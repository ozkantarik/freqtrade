# --- Do not remove these imports ---
import talib.abstract as ta
from pandas import DataFrame
from technical import qtpylib

from freqtrade.strategy import IStrategy


class freqai_strategy(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "5m"

    can_short = False
    use_exit_signal = True
    startup_trend_req = 200

    def feature_engineering_expand_lookahead(
        self, dataframe: DataFrame, period: int, **kwargs
    ) -> DataFrame:
        """
        Adds future-looking data to the dataframe.
        This function is called by FreqAI to add lookahead data for training.
        """
        dataframe[f"future_max_{period}"] = dataframe["high"].rolling(period).max().shift(-period)
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Adds technical indicators to the dataframe.
        This function is called by FreqAI to add features for training.
        """
        # Momentum Indicators
        dataframe["rsi"] = ta.RSI(dataframe)
        dataframe["mfi"] = ta.MFI(dataframe)
        dataframe["adx"] = ta.ADX(dataframe)
        macd = ta.MACD(dataframe)
        dataframe["macd"] = macd["macd"]
        dataframe["macdsignal"] = macd["macdsignal"]
        dataframe["macdhist"] = macd["macdhist"]

        # Trend Indicators
        dataframe["ema_20"] = ta.EMA(dataframe, timeperiod=20)
        dataframe["ema_50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["ema_100"] = ta.EMA(dataframe, timeperiod=100)

        # Volatility Indicators
        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe["bb_lowerband"] = bollinger["lower"]
        dataframe["bb_middleband"] = bollinger["mid"]
        dataframe["bb_upperband"] = bollinger["upper"]
        dataframe["atr"] = ta.ATR(dataframe)

        # Volume Indicators
        dataframe["obv"] = ta.OBV(dataframe)

        # Advanced Feature: Rate of Change of RSI
        dataframe["rsi_roc_10"] = ta.ROC(dataframe["rsi"], timeperiod=10)

        # Advanced Feature: Distance from EMA50, normalized by ATR
        dataframe["dist_from_ema_50_norm"] = (dataframe["close"] - dataframe["ema_50"]) / dataframe[
            "atr"
        ]

        return dataframe

    def feature_engineering_expand_basic(
        self, dataframe: DataFrame, metadata: dict, **kwargs
    ) -> DataFrame:
        """
        This function is called by FreqAI to add features for training.
        """
        dataframe = self.populate_indicators(dataframe, metadata)

        return dataframe

    def set_freqai_targets(self, dataframe: DataFrame, metadata: dict, **kwargs):
        """
        Adds the training target to the dataframe.
        This function is called by FreqAI to set the target for training.
        """
        period = self.config["freqai"]["feature_parameters"]["label_period_candles"]

        dataframe["&s-future_return"] = (
            dataframe[f"future_max_{period}"] - dataframe["close"]
        ) / dataframe["close"]
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the entry signal for the given dataframe
        :param dataframe: DataFrame
        :param metadata: Additional information, like the current pair
        :return: DataFrame with entry columns populated
        """
        # FreqAI populates the entry signal automatically based on the config triggers
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the exit signal for the given dataframe
        :param dataframe: DataFrame
        :param metadata: Additional information, like the current pair
        :return: DataFrame with exit columns populated
        """
        # FreqAI populates the entry signal automatically based on the config triggers
        return dataframe
