# GRU Predictor Strategy (for PyTorch)
from typing import Any

import talib.abstract as ta
from pandas import DataFrame

from freqtrade.strategy import IStrategy


class GRUPredictorStrategy(IStrategy):
    timeframe = "5m"
    INTERFACE_VERSION = 3

    def feature_engineering_standard(
        self, dataframe: DataFrame, metadata: dict, **kwargs: Any
    ) -> DataFrame:
        """
        Features for the GRU model.
        """
        dataframe["%-rsi"] = ta.RSI(dataframe)
        return dataframe

    def set_freqai_targets(self, dataframe: DataFrame, metadata: dict, **kwargs: Any) -> DataFrame:
        """
        Target for the GRU model. We'll predict a simple up/down classification.
        """
        dataframe["&-s_label_classification"] = (
            dataframe["close"].shift(-10) > dataframe["close"]
        ).astype(int)
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe = self.freqai.start(dataframe, metadata, self)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe
