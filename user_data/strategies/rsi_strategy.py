# --- Freqtrade Libraries ---
from freqtrade.strategy import IStrategy
from pandas import DataFrame
import talib.abstract as ta


class RsiStrategy(IStrategy):
    """
    This is our first custom strategy.
    LOGIC:
    - BUY SIGNAL: When RSI drops below 30 (oversold).
    - SELL SIGNAL: When RSI rises above 70 (overbought).
    """

    # Strategy interface version.
    INTERFACE_VERSION = 3

    # Recommended timeframe for the strategy.
    timeframe = "5m"

    # Take profit settings:
    # Sell if in profit of 3% after 60 minutes.
    # Sell if in profit of 2% after 120 minutes.
    minimal_roi = {
        "60": 0.03,
        "120": 0.02,
        "0": 0.05,  # Sell if in profit of 5% if time is not up.
    }

    # Stoploss setting: close position if in 10% loss.
    stoploss = -0.10

    # These settings determine the general behavior of the strategy.
    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    startup_trend_req = 14  # At least 14 candles of data are required for RSI.

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Calculates the indicators required for the strategy.
        In our case, this is only RSI.
        """
        # Calculate RSI (Relative Strength Index) with a 14-period lookback.
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Determines the buy signal conditions.
        """
        dataframe.loc[
            (
                # If RSI value drops below 30...
                (dataframe["rsi"] < 30)
                & (dataframe["volume"] > 0)  # Ensure volume is not zero.
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
                # If RSI value rises above 70...
                (dataframe["rsi"] > 70)
                & (dataframe["volume"] > 0)  # Ensure volume is not zero.
            ),
            "exit_long",
        ] = 1
        return dataframe