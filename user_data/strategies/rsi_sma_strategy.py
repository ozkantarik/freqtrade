# --- Freqtrade Libraries ---
from freqtrade.strategy import IStrategy, IntParameter
from pandas import DataFrame
import talib.abstract as ta


class rsi_sma_strategy(IStrategy):
    """
    This is our RSI + SMA strategy, which will be optimized by Hyperopt.
    """

    INTERFACE_VERSION = 3
    timeframe = "5m"

    # Take profit settings
    minimal_roi = {"0": 0.05}

    # Stoploss setting
    stoploss = -0.10

    # General strategy behavior settings
    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    startup_trend_req = 200

    # --- Hyperopt Settings ---
    # In this section, we tell Freqtrade which parameters to test.

    # BUY SETTINGS
    buy_rsi = IntParameter(10, 40, default=22, space="buy")

    # SELL SETTINGS
    sell_rsi = IntParameter(60, 90, default=61, space="sell")

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Calculates the indicators required for the strategy.
        """
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["sma_200"] = ta.SMA(dataframe, timeperiod=200)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Determines the buy signal conditions.
        """
        dataframe.loc[
            (
                # We now use the "buy_rsi" value that Hyperopt will test, instead of a fixed "30".
                (dataframe["rsi"] < self.buy_rsi.value)
                & (dataframe["close"] > dataframe["sma_200"])
                & (dataframe["volume"] > 0)
            ),
            "enter_long",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Determines the sell signal conditions.
        """
        dataframe.loc[
            (
                # We now use the "sell_rsi" value that Hyperopt will test, instead of a fixed "70".
                (dataframe["rsi"] > self.sell_rsi.value) & (dataframe["volume"] > 0)
            ),
            "exit_long",
        ] = 1
        return dataframe
