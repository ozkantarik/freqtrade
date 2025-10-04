# --- Do not remove these imports ---
from freqtrade.strategy import IStrategy
from pandas import DataFrame

# --------------------------------
# Add your lib to import here
import talib.abstract as ta
from technical import qtpylib


class freqai_strategy_ok(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "5m"

    can_short = False
    # Alım/satım komutları olmadığı için bu ayarların bir önemi yok ama kalabilirler
    use_exit_signal = True
    startup_trend_req = 200

    def feature_engineering_expand_lookahead(
        self, dataframe: DataFrame, period: int, **kwargs
    ) -> DataFrame:
        dataframe[f"future_max_{period}"] = dataframe["high"].rolling(period).max().shift(-period)
        return dataframe

    def feature_engineering_expand_basic(
        self, dataframe: DataFrame, metadata: dict, **kwargs
    ) -> DataFrame:
        dataframe["rsi"] = ta.RSI(dataframe)
        dataframe["sma_200"] = ta.SMA(dataframe, timeperiod=200)
        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe["bb_lowerband"] = bollinger["lower"]
        dataframe["bb_middleband"] = bollinger["mid"]
        dataframe["bb_upperband"] = bollinger["upper"]
        return dataframe

    def set_freqai_targets(self, dataframe: DataFrame, **kwargs):
        dataframe["target_profit"] = (
            dataframe["future_max_20"] > dataframe["close"] * 1.03
        ).astype(int)
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # The indicators are defined in feature_engineering_expand_basic
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
        # FreqAI populates the exit signal automatically based on the config triggers
        return dataframe
