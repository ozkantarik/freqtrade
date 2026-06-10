# [PROJE] FreqAI - Gemini Serisi Strateji Geliştirme
## Devir ve Durum Raporu - 13 Ekim 2025

---

### [GÖREV] Genel Amaç:
- FreqAI kullanarak, hem long hem de short pozisyon açabilen, değişken piyasa koşullarında ("all-weather") kârlı bir alım satım stratejisi geliştirmek.
- Bu amaçla, başarısız olan `GeminiV11` (Sınıflandırma Modeli) tecrübesinden ders çıkararak `GeminiV12` (Regresyon Modeli) mimarisine geçiş yapmak.

---

### [AŞAMA 1] GeminiV11 - Sınıflandırma Deneyi ve Başarısızlık Analizi

- **[STRATEJİ] Yaklaşım:**
    - `LightGBMClassifier` kullanarak bir sınıflandırma modeli oluşturuldu.
    - Model, piyasanın gelecekteki yönünü üç sınıftan biri olarak tahmin etmeye çalıştı: `UP` (Yukarı), `DOWN` (Aşağı), `SIDEWAYS` (Yatay).
    - Hedef, modelin `UP` veya `DOWN` sinyali vermesi durumunda pozisyona girmekti.

- **[PROBLEM] Sıfır İşlem Sorunu:**
    - Yapılan tüm backtestler, modelin hiçbir zaman `UP` veya `DOWN` tahmini yapmadığını gösterdi.
    - **Temel Neden:** Piyasa verisindeki aşırı sınıf dengesizliği (`class imbalance`). Fiyatların yatay hareket ettiği durumlar, belirgin bir yükseliş veya düşüş gösterdiği durumlardan kat kat fazlaydı. Bu nedenle, model en güvenli ve istatistiksel olarak en olası sonucu, yani `SIDEWAYS` sınıfını tahmin etmeyi "öğrendi".

- **[BAŞARISIZ ÇÖZÜM GİRİŞİMLERİ]:**
    - **Hedef Tanımını Değiştirmek:** `UP` ve `DOWN` sınıflarını tanımlayan ATR (Average True Range) çarpanı değiştirildi, ancak sonuç alınamadı.
    - **Sınıf Ağırlıklandırma:** Modelin azınlık sınıflara (`UP`, `DOWN`) daha fazla önem vermesi için ağırlıklandırma denendi, fakat model yine de `SIDEWAYS` tahmininde ısrar etti.
    - **Özellik Zenginleştirme (`Feature Engineering`):** Modele `RSI` ve `Bollinger Bands` gibi yeni göstergeler eklenerek daha fazla bilgi verilmeye çalışıldı, ancak bu da sınıf dengesizliği sorununu aşamadı.

- **[ÖĞRENİLEN DERS] Kritik Sonuç:**
    - Bu tür dengesiz bir veri setinde, sınıflandırma yaklaşımı doğası gereği başarısızlığa mahkumdur. Model, ceza (kayıp) riskini en aza indirmek için her zaman en yaygın sınıfı tahmin etme eğilimindedir. Bu nedenle, bu mimari terk edildi.

---

### [AŞAMA 2] GeminiV12 - Regresyon Modeline Stratejik Geçiş

- **[STRATEJİ] Yeni Yaklaşım:**
    - Sınıflandırma yerine, gelecekteki fiyat getirisini sürekli bir değer olarak tahmin eden bir regresyon modeline (`LightGBMRegressor`) geçildi.
    - **Hedef:** Modelin, örneğin, "gelecek 24 mum içinde fiyat %X artacak/azalacak" şeklinde bir sayısal tahmin yapması.
    - **Giriş Mantığı:** Bu sayısal tahmin, bir "güven skoru" olarak kullanılacaktı. Eğer modelin tahmini belirli bir eşik değerin (`entry_threshold`) üzerindeyse (örneğin, > %0.5 artış), long pozisyon aç; altındaysa (örneğin, < -%0.5 düşüş), short pozisyon aç.

- **[PROBLEM] Sıfır İşlem Sorununun Devam Etmesi:**
    - Regresyon modeline geçilmesine rağmen, backtestler yine sıfır işlemle sonuçlandı. Bu durum, problemin artık modelin kendisinden daha derinlerde, FreqAI framework'ünün işleyişinde olduğunu gösterdi.

---

### [AŞAMA 3] Derinlemesine Hata Ayıklama ve Framework Keşifleri

Bu aşama, projenin en kritik ve en öğretici bölümüdür.

- **[KEŞİF 1] Tahmin Sütunu Kayıp:**
    - Strateji içine `print()` komutları eklenerek yapılan ilk incelemede, FreqAI'nin tahminleri yazdığı varsayılan `&-s_prediction` sütununun dataframe içinde hiç var olmadığı tespit edildi.

- **[KEŞİF 2] Regresyon Modelinin Farklı Çıktısı (`BaseRegressionModel.py` Analizi):**
    - FreqAI kaynak kodu (`BaseRegressionModel.py`) incelendiğinde, regresyon modellerinin tahminlerini `&-s_prediction` sütununa **yazmadığı** anlaşıldı.
    - **SMOKING GUN:** Regresyon modelleri, tahminlerini doğrudan hedef etiketinin (label) adını taşıyan bir sütuna yazar. Bizim durumumuzda bu sütun `&s-future_return` olmalıydı.

- **[KEŞİF 3] Framework Hata #1 - "&" Sütunlarının Silinmesi (`data_kitchen.py` Analizi):**
    - Strateji, `&s-future_return` sütununu kullanacak şekilde düzeltildiğinde dahi sorun devam etti.
    - Daha derin bir kaynak kodu analizi (`data_kitchen.py`), FreqAI'nin `fill_predictions` adlı bir fonksiyonunda, stratejiye veri göndermeden hemen önce, **adı `&` ile başlayan tüm sütunları sildiğini** ortaya çıkardı.
    - **Sonuç:** Bu, bir "Catch-22" durumu yaratan bir framework hatasıydı. Framework, tahminleri `&` ile başlayan bir sütuna yazıyor, ama sonra aynı sütunu stratejinin görmesine izin vermeden siliyordu.

- **[ÇÖZÜM 1] "&" Ön Ekini Kaldırma:**
    - Bu hatayı aşmak için, hedef sütununun adı `future_return_pct` olarak değiştirildi (başında `&` olmadan).
    - **Yan Etki:** `&s-` ön eki, veriyi otomatik olarak kaydırarak geleceğe bakma hatasını (lookahead bias) önlüyordu. Bu ön ek kaldırıldığı için, bu kaydırma işlemi `set_freqai_targets` fonksiyonu içinde manuel olarak yapıldı.

- **[KEŞİF 4] Framework Hata #2 - "&" Sütunlarının Aranması (`data_kitchen.py` Analizi):**
    - Önceki çözüm uygulandıktan sonra, bu kez `ValueError: Found array with 0 feature(s)` hatası alındı.
    - Tekrar kaynak koduna dönüldüğünde, `find_labels` fonksiyonunun bir sütunu "hedef etiket" olarak tanıması için **içinde `&` karakteri aradığı** tespit edildi.
    - **Sonuç:** Bu, ilk hatayla çelişen ikinci bir framework hatasıydı. Sistem, hem `&` karakterini zorunlu kılıyor hem de onu siliyordu.

- **[ÇÖZÜM 2] Framework'ü Yamamak:**
    - Bu kilitlenmeyi aşmak için, `data_kitchen.py` dosyası manuel olarak değiştirildi. `find_labels` fonksiyonu, `&` içeren VEYA adı `future_return_pct` olan sütunları etiket olarak kabul edecek şekilde yamandı.

- **[ÖĞRENİLEN DERS] Hyperopt ve Geliştirme Sürümü Uyumsuzlukları:**
    - Yukarıdaki sorunlar çözüldükten sonra, `hyperopt` ile optimizasyon denenirken bir dizi `TypeError` hatası alındı.
    - Araştırmalar ve denemeler, kullanılan Freqtrade geliştirme sürümünün (`2025.10-dev`) `hyperopt` parametre tanımlama (`Real`, `IntParameter` vb.) konusunda resmi dokümantasyondan ayrıştığını ve hatalı olduğunu gösterdi. `space`, `default`, `name` gibi argümanlar beklenmedik hatalara yol açtı.
    - **Çözüm:** `hyperopt` denemeleri durduruldu ve sorunu izole etmek için `entry_threshold` değeri strateji içinde manuel olarak sabitlendi.

---

### [AŞAMA 4] Mevcut Durum ve Sonraki Adımlar

- **[DURUM] Stabil ve Çalışan Bir Sistem:**
    - Tüm framework hataları ve strateji bug'ları giderildi.
    - `GeminiV12_strategy` artık `backtesting` modunda **hatasız** bir şekilde çalışıyor.
    - En son yapılan testte, `entry_threshold` değeri `0.0001` gibi çok düşük bir seviyeye çekilmesine rağmen sıfır işlem gerçekleşti. Bu, modelin tahminlerinin bu düşük eşiği bile geçemediğini gösteriyor.

- **[SONUÇ] Model Performansı Yetersiz:**
    - Mevcut özellik seti (`feature set`) ile `LightGBMRegressor` modeli, anlamlı ve ticarete girilebilecek kadar güçlü tahminler üretemiyor.

- **[GELECEK İÇİN ÖNERİLEN ADIMLAR] Proje Devam Ederse:**
    1.  **Özellik Mühendisliğini Geliştir (`Feature Engineering`):** Mevcut 6 özellik, piyasanın geleceğini tahmin etmek için yetersizdir. Modele daha fazla ve daha çeşitli bilgiler sunulmalıdır (örn: farklı periyotlarda volatilite, momentum, hacim göstergeleri).
    2.  **Model Parametrelerini Ayarla:** `config.json` içindeki `model_training_parameters` bölümü kullanılarak `LightGBMRegressor` modelinin kendi iç parametreleri (örn: `n_estimators`, `learning_rate`) optimize edilebilir.
    3.  **`Hyperopt` Sorununu Çöz:** Freqtrade'in stabil bir sürümüne geçerek veya `hyperopt` parametrelerinin doğru kullanımını daha derinlemesine araştırarak `entry_threshold` gibi kritik eşik değerlerini otomatik olarak optimize etme yeteneği geri kazanılmalıdır.
    4.  **Alternatif Modelleri Dene:** `LightGBM` yerine `XGBoost`, `CatBoost` veya basit bir `LinearRegression` gibi farklı regresyon modelleri denenerek performansları karşılaştırılabilir.

Bu rapor, projenin yeniden başlatılması için gerekli tüm tarihsel bağlamı ve teknik detayları sağlamaktadır.

Saygılarımla,
Gemini.
