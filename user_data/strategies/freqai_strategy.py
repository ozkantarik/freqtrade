# --- Do not remove these imports ---
import talib.abstract as ta
from pandas import DataFrame

from freqtrade.strategy import IStrategy
from freqtrade.strategy.parameters import RealParameter
from technical import qtpylib


class freqai_strategy(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "5m"

    # Hyperoptable parameters
    buy_pred_threshold = RealParameter(0.5, 1.0, default=0.7, space="buy")

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
        dataframe['rsi'] = ta.RSI(dataframe)
        dataframe['mfi'] = ta.MFI(dataframe)
        dataframe['adx'] = ta.ADX(dataframe)
        macd = ta.MACD(dataframe)
        dataframe['macd'] = macd['macd']
        dataframe['macdsignal'] = macd['macdsignal']
        dataframe['macdhist'] = macd['macdhist']

        # Trend Indicators
        dataframe['ema_20'] = ta.EMA(dataframe, timeperiod=20)
        dataframe['ema_50'] = ta.EMA(dataframe, timeperiod=50)
        dataframe['ema_100'] = ta.EMA(dataframe, timeperiod=100)

        # Volatility Indicators
        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe['bb_lowerband'] = bollinger['lower']
        dataframe['bb_middleband'] = bollinger['mid']
        dataframe['bb_upperband'] = bollinger['upper']
        dataframe['atr'] = ta.ATR(dataframe)

        # Volume Indicators
        dataframe['obv'] = ta.OBV(dataframe)

        return dataframe

    def feature_engineering_expand_basic(
        self, dataframe: DataFrame, metadata: dict, **kwargs
    ) -> DataFrame:
        """
        Adds technical indicators to the dataframe.
        This function is called by FreqAI to add features for training.
        """
        dataframe = self.populate_indicators(dataframe, metadata)

        return dataframe

    def set_freqai_targets(self, dataframe: DataFrame, metadata: dict, **kwargs):
        """
        Adds the training target to the dataframe.
        This function is called by FreqAI to set the target for training.
        """
        # For this baseline, we're predicting if the price will simply
        # increase in the next 10 candles.
        dataframe["target_profit"] = (
            dataframe["future_max_10"] > dataframe["close"]
        ).astype(int)
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
