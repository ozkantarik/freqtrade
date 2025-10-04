# --- Freqtrade Kütüphaneleri ---
from freqtrade.strategy import IStrategy, IntParameter
from pandas import DataFrame
import talib.abstract as ta
from technical import qtpylib


class rsi_sma_bb_strategy(IStrategy):
    """
    Bu bizim Hyperopt için optimize edilecek üçüncü ve en gelişmiş stratejimiz (v3.0).
    """

    INTERFACE_VERSION = 3
    timeframe = "5m"

    # Kâr alma ve zarar durdurma ayarları
    minimal_roi = {"0": 0.05}
    stoploss = -0.10

    # Stratejinin genel davranışını belirleyen ayarlar
    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = False
    startup_trend_req = 200

    # --- Hyperopt Parametreleri ---
    # ALIM AYARLARI
    buy_rsi = IntParameter(10, 40, default=22, space="buy")
    buy_bb_window = IntParameter(15, 30, default=15, space="buy")
    buy_bb_std = IntParameter(1, 4, default=2, space="buy")

    # SATIM AYARLARI
    sell_rsi = IntParameter(60, 90, default=61, space="sell")

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Strateji için gerekli olan 3 indikatörü de Hyperopt'tan gelen değerlerle hesaplar.
        """
        # Bollinger Bands - Artık sabit sayılar yerine Hyperopt'un deneyeceği değerleri kullanıyor.
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
        Alım sinyali için 3 koşulu birden kontrol eder.
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
        Satım sinyalini belirler.
        """
        dataframe.loc[
            ((dataframe["rsi"] > self.sell_rsi.value) & (dataframe["volume"] > 0)), "exit_long"
        ] = 1
        return dataframe
