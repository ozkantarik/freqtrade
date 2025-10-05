# --- Do not remove these imports ---
import logging
from functools import reduce

import talib.abstract as ta
from pandas import DataFrame
from technical import qtpylib

from freqtrade.strategy import IStrategy


logger = logging.getLogger(__name__)


class FreqAIV3_strategy(IStrategy):
    """
    FreqAI V3 Hybrid Strategy

    Designed by Gemini, this strategy combines the best of FreqAI's capabilities
    to create a powerful, reliable, and adaptable trading model.

    Core Concepts:
    1.  Automated Multi-Timeframe Analysis: Generates features across multiple
        timeframes (e.g., 5m, 15m, 1h) for a broad market view.
    2.  Intelligent Feature Engineering: Creates custom-normalized indicators and a
        composite 'ai_score' for a deeper analytical edge.
    3.  Risk-Adjusted Target: The model is trained to predict future returns
        penalized by volatility, encouraging safer, more stable trades.
    4.  AI-Controlled Entries & Exits: The model dynamically decides when to enter
        and exit based on its evolving predictions.
    """

    INTERFACE_VERSION = 3
    timeframe = "5m"

    # ROI table and stoploss are not strictly necessary for an AI-driven strategy
    # but are kept as a fallback and for legacy analysis.
    minimal_roi = {"0": 0.05}
    stoploss = -0.15

    # Let the AI decide when to exit.
    use_exit_signal = True

    # More startup candles are needed for multi-timeframe analysis.
    startup_trend_req = 300

    can_short = False

    def feature_engineering_expand_all(
        self, dataframe: DataFrame, period: int, metadata: dict, **kwargs
    ) -> DataFrame:
        """
        Automated Feature Expansion (from FreqaiExampleStrategy)

        This function generates a broad set of indicators across all timeframes
        and periods defined in the configuration file.
        """
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
        """
        Automated Basic Feature Expansion

        This function generates simple features that are expanded across
        timeframes but not periods.
        """
        dataframe["%-pct-change"] = dataframe["close"].pct_change()
        dataframe["%-raw_volume"] = dataframe["volume"]
        dataframe["%-raw_price"] = dataframe["close"]
        return dataframe

    def feature_engineering_standard(
        self, dataframe: DataFrame, metadata: dict, **kwargs
    ) -> DataFrame:
        """
        Intelligent & Custom Feature Engineering (from freqai_strategy)

        This function is called last and is used to create advanced,
        normalized, and composite features.
        """
        # Base indicators for normalization
        dataframe["rsi"] = ta.RSI(dataframe)
        dataframe["mfi"] = ta.MFI(dataframe)
        dataframe["adx"] = ta.ADX(dataframe)
        dataframe["atr"] = ta.ATR(dataframe)

        # Normalize indicators by their recent rolling history
        for indicator in ["rsi", "mfi", "adx"]:
            rolling_mean = dataframe[indicator].rolling(20).mean()
            rolling_std = dataframe[indicator].rolling(20).std()
            dataframe[f"%-{indicator}_norm"] = (dataframe[indicator] - rolling_mean) / rolling_std

        # Create a composite AI score
        dataframe["%-ai_score"] = (
            dataframe["%-rsi_norm"] + dataframe["%-mfi_norm"] + dataframe["%-adx_norm"]
        )

        # Add time-based features
        dataframe["%-day_of_week"] = dataframe["date"].dt.dayofweek
        dataframe["%-hour_of_day"] = dataframe["date"].dt.hour

        return dataframe

    def set_freqai_targets(self, dataframe: DataFrame, metadata: dict, **kwargs) -> DataFrame:
        """
        Define the training target: a risk-adjusted future return.

        We aim to predict the mean return over a future period, penalized by the
        standard deviation (volatility) of that same period. This encourages the
        model to find profitable but also stable opportunities.
        """
        label_period = self.freqai_info["feature_parameters"]["label_period_candles"]

        future_returns = dataframe["close"].shift(-label_period) / dataframe["close"] - 1
        future_volatility = future_returns.rolling(label_period).std()

        # Target is the future return divided by future volatility (a simplified Sharpe Ratio)
        # We use a small epsilon to avoid division by zero
        dataframe["&-s-risk_adjusted_return"] = future_returns / (future_volatility + 1e-6)

        # Fill NaNs that can result from the calculation
        dataframe.fillna({"&-s-risk_adjusted_return": 0}, inplace=True)

        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Main entry point for FreqAI.
        """
        # FreqAI will orchestrate the feature engineering and prediction generation
        dataframe = self.freqai.start(dataframe, metadata, self)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        AI-driven entry logic.

        Enter a trade if the model predicts a favorable risk-adjusted return.
        """
        enter_long_conditions = [
            dataframe["do_predict"] == 1,
            dataframe["&-s-risk_adjusted_return"] > 0.04,  # Threshold for entry
        ]

        if enter_long_conditions:
            dataframe.loc[
                reduce(lambda x, y: x & y, enter_long_conditions),
                ["enter_long", "enter_tag"],
            ] = (1, "ai_buy_v3")

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        AI-driven exit logic.

        Exit a trade if the model's prediction turns unfavorable.
        """
        exit_long_conditions = [
            dataframe["do_predict"] == 1,
            dataframe["&-s-risk_adjusted_return"] < -0.01,  # Threshold for exit
        ]

        if exit_long_conditions:
            dataframe.loc[
                reduce(lambda x, y: x & y, exit_long_conditions),
                "exit_long",
            ] = 1

        return dataframe
