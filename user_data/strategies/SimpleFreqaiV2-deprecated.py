# --- Do not remove these libs ---
import talib.abstract as ta
from pandas import DataFrame

import freqtrade.vendor.qtpylib.indicators as qtpylib
from freqtrade.strategy import IStrategy


# --------------------------------


class SimpleFreqaiV2(IStrategy):
    """
    A simple FreqAI strategy based on a few indicators.
    This is a standard IStrategy that FreqAI enhances.
    """

    # Set to false if you don't want to use the model for selling
    use_exit_signal: bool = False

    # Minimal ROI designed for the strategy tool
    minimal_roi = {"60": 0.05, "30": 0.07, "0": 0.1}

    # Optimal stoploss designed for the strategy tool
    stoploss = -0.15

    # Optimal timeframe for the strategy
    timeframe = "5m"

    # FreqAI will call these methods if it's enabled in the config.

    def define_features(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Defines the features that the model will be trained on.
        """
        dataframe["rsi"] = ta.RSI(dataframe)
        dataframe["ema_20"] = ta.EMA(dataframe, timeperiod=20)
        dataframe["ema_50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["ema_diff"] = (dataframe["ema_20"] - dataframe["ema_50"]) / dataframe["ema_50"]

        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe["bb_lowerband"] = bollinger["lower"]
        dataframe["bb_middleband"] = bollinger["mid"]
        dataframe["bb_upperband"] = bollinger["upper"]
        dataframe["bb_width"] = (dataframe["bb_upperband"] - dataframe["bb_lowerband"]) / dataframe[
            "bb_middleband"
        ]

        dataframe["%rsi"] = dataframe["rsi"]
        dataframe["%ema_diff"] = dataframe["ema_diff"]
        dataframe["%bb_width"] = dataframe["bb_width"]

        return dataframe

    def define_labels(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Defines the labels that the model will be trained to predict.
        """
        dataframe["&s-future_mean_returns_10"] = 0
        return dataframe

    # Standard IStrategy methods are below.

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        This method is NOT called by FreqAI. FreqAI calls define_features().
        We populate the FreqAI features here for non-FreqAI runs or analysis.
        """
        # The indicators are defined in define_features().
        # For non-freqai runs, we call it here to have the indicators populated.
        if not self.config.get("freqai", {}).get("enabled", False):
            dataframe = self.define_features(dataframe, metadata)

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on the predictions of the model, decide when to enter a trade.
        """
        # The prediction column is added by FreqAI automatically.
        # Check if the column exists to ensure we are in FreqAI mode.
        if self.config.get("freqai", {}).get("enabled", False):
            label_period = self.freqai_info["feature_parameters"]["label_period_candles"]
            pred_col = f"&s-future_mean_returns_10_pred_{label_period}"
            if pred_col in dataframe.columns:
                dataframe.loc[
                    ((dataframe[pred_col] > 0.0001) & (dataframe["volume"] > 0)), "enter_long"
                ] = 1
        else:
            # This is a sample entry signal for non-FreqAI runs
            dataframe.loc[((dataframe["rsi"] < 30) & (dataframe["volume"] > 0)), "enter_long"] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        This is not used as use_exit_signal is False.
        """
        dataframe["exit_long"] = 0
        return dataframe
