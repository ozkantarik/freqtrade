# --- Freqtrade Kütüphaneleri ---
from freqtrade.strategy import IStrategy, IntParameter
from pandas import DataFrame
import talib.abstract as ta


class rsi_sma_strategy(IStrategy):
    """
    Bu, Hyperopt için optimize edilecek olan RSI + SMA stratejimizdir.
    """

    INTERFACE_VERSION = 3
    timeframe = "5m"

    # Kâr alma ayarları
    minimal_roi = {"0": 0.05}

    # Zarar durdurma ayarı
    stoploss = -0.10

    # Stratejinin genel davranışını belirleyen ayarlar
    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    startup_trend_req = 200

    # --- Hyperopt Ayarları ---
    # Freqtrade'e hangi parametreleri test edeceğini bu bölümde söyleriz.

    # ALIM AYARLARI
    buy_rsi = IntParameter(10, 40, default=22, space="buy")

    # SATIM AYARLARI
    sell_rsi = IntParameter(60, 90, default=61, space="sell")

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Strateji için gerekli olan indikatörleri hesaplar.
        """
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["sma_200"] = ta.SMA(dataframe, timeperiod=200)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Alım sinyali koşullarını belirler.
        """
        dataframe.loc[
            (
                # Artık sabit "30" yerine, Hyperopt'un deneyeceği "buy_rsi" değerini kullanıyoruz.
                (dataframe["rsi"] < self.buy_rsi.value)
                & (dataframe["close"] > dataframe["sma_200"])
                & (dataframe["volume"] > 0)
            ),
            "enter_long",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Satım sinyali koşullarını belirler.
        """
        dataframe.loc[
            (
                # Artık sabit "70" yerine, Hyperopt'un deneyeceği "sell_rsi" değerini kullanıyoruz.
                (dataframe["rsi"] > self.sell_rsi.value) & (dataframe["volume"] > 0)
            ),
            "exit_long",
        ] = 1
        return dataframe
