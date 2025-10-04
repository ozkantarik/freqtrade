# --- Freqtrade Kütüphaneleri ---
from freqtrade.strategy import IStrategy
from pandas import DataFrame
import talib.abstract as ta


class RsiStrategy(IStrategy):
    """
    Bu bizim ilk özel stratejimiz.
    MANTIĞI:
    - ALIM SİNYALİ: RSI 30'un altına düştüğünde (aşırı satım).
    - SATIM SİNYALİ: RSI 70'in üzerine çıktığında (aşırı alım).
    """

    # Strateji arayüz versiyonu.
    INTERFACE_VERSION = 3

    # Strateji için önerilen zaman aralığı.
    timeframe = "5m"

    # Kâr alma ayarları:
    # 60 dakika sonra %3 kârda ise sat.
    # 120 dakika sonra %2 kârda ise sat.
    minimal_roi = {
        "60": 0.03,
        "120": 0.02,
        "0": 0.05,  # Eğer süre dolmazsa %5 kârda sat.
    }

    # Zarar durdurma ayarı: %10 zararda ise pozisyonu kapat.
    stoploss = -0.10

    # Bu ayarlar, stratejinin genel davranışını belirler.
    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    startup_trend_req = 14  # RSI için en az 14 mumluk veri gerekir.

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Strateji için gerekli olan indikatörleri hesaplar.
        Bizim durumumuzda bu sadece RSI.
        """
        # RSI (Relative Strength Index) indikatörünü 14 periyotluk hesapla.
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Alım sinyali koşullarını belirler.
        """
        dataframe.loc[
            (
                # RSI değeri 30'un altına düşerse...
                (dataframe["rsi"] < 30)
                & (dataframe["volume"] > 0)  # Hacmin sıfır olmadığından emin ol.
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
                # RSI değeri 70'in üzerine çıkarsa...
                (dataframe["rsi"] > 70)
                & (dataframe["volume"] > 0)  # Hacmin sıfır olmadığından emin ol.
            ),
            "exit_long",
        ] = 1
        return dataframe
