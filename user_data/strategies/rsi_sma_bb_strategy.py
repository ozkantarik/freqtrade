# --- Freqtrade Libraries ---
from freqtrade.strategy import IStrategy, IntParameter
from pandas import DataFrame
import talib.abstract as ta
from technical import qtpylib


class rsi_sma_bb_strategy(IStrategy):
    """
    This is our third and most advanced strategy to be optimized by Hyperopt (v3.0).
    """

    INTERFACE_VERSION = 3
    timeframe = "5m"

    # Take profit and stoploss settings
    minimal_roi = {"0": 0.05}
    stoploss = -0.10

    # General strategy behavior settings
    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = False
    startup_trend_req = 200

    # --- Hyperopt Parameters ---
    # BUY SETTINGS
    buy_rsi = IntParameter(10, 40, default=22, space="buy")
    buy_bb_window = IntParameter(15, 30, default=15, space="buy")
    buy_bb_std = IntParameter(1, 4, default=2, space="buy")

    # SELL SETTINGS
    sell_rsi = IntParameter(60, 90, default=61, space="sell")

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Calculates the 3 indicators required for the strategy using values from Hyperopt.
        """
        # Bollinger Bands - Now uses values that Hyperopt will test, instead of fixed numbers.
        bollinger = qtpylib.bollinger_bands(
            qtpylib.typical_price(dataframe),
            window=self.buy_bb_window.value,
            stds=self.buy_bb_std.value,
        )
        dataframe["bb_lowerband"] = bollinger["lower"]

        # RSI
        dataframe["rsi"] = ta.RSI(dataframe)

        # SMA - 200
        dataframe["sma_200"] = ta.SMA(dataframe, timeperiod=200)

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Checks all 3 conditions for a buy signal.
        """
        dataframe.loc[
            (
                (dataframe["rsi"] < self.buy_rsi.value)
                & (dataframe["close"] > dataframe["sma_200"])
                & (dataframe["close"] <= dataframe["bb_lowerband"])
                & (dataframe["volume"] > 0)
            ),
            "enter_long",
        ] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Determines the sell signal.
        """
        dataframe.loc[
            ((dataframe["rsi"] > self.sell_rsi.value) & (dataframe["volume"] > 0)), "exit_long"
        ] = 1
        return dataframe