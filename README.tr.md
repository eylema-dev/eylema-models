# Eyleme model kataloğu

**Ad güncellemesi — 14 Ekim 2026:** Ürünün adı **Eyleme** (önceki adı Eylema), tamamlayıcı ürünün adı **Derleme** (önceki adı Derlema) oldu; **Onama** aynı kaldı. GitHub organizasyonunun adı artık `eyleme-dev` (önceki adı `eylema-dev`). Ana deponun adı artık `eyleme-dev/eyleme`. 15 Ekim 2026 tarihinde altı `eylema-*` alt deposu `eyleme-*` olarak değişti. Alan adları, komutlar, crate/paket adları, ortam değişkenleri, veri yolları ve protokol/şema tanımlayıcıları uyumluluk için mevcut yazımlarını korur. Tarihsel kanıtlar özgün ad ve bağlantıları korur.

Model üstverisi ve kabul edilmiş model kümesi manifestleri. [English](README.md).

**Durum: offline geliştirme denetimiyle sabit G27 aday kataloğu ve dokuz isteğe bağlı rol arayüzü kaydı.** Gerçek üretim Rust manifest kontrolleri core içindedir; ağırlık, tokenizer/model yürütmesi, kıyaslama veya eğitilmiş model sunulmaz.

[Katalog/sözleşme notları](docs/tr/model-catalog.md) · [Qwen adayı](catalog/qwen3-0.6b.v1.json) · [Rol arayüzleri](contracts/role-interfaces.v1.json). `python tools/model_catalog.py --check`, bildirilen JSON/EYL/kaynak/rol/operator tutarlılığını denetler; inference değil geliştirme aracıdır.

## Kapsam

Kaynak revizyonları, özetler, lisanslar, işleç gereksinimleri ve değerlendirme referansları kataloglanır. Ayrı sürümlenen sözleşme gerekene kadar kanonik model kümesi şeması Eyleme çekirdek deposunda kalır. Üstveri kaydı çalıştırma veya kabul anlamına gelmez.

Üretim Rust kodu, ortak tipler, çalışma zamanı/model yürütmesi ve CLI [Eyleme](https://github.com/eyleme-dev/eyleme) içinde; ürün sözleşmeleri [İngilizce](https://github.com/eyleme-dev/eyleme-docs-en) ve [Türkçe](https://github.com/eyleme-dev/eyleme-docs-tr) belge depolarındadır. [Depo haritası](https://github.com/eyleme-dev/devguide/blob/main/docs/tr/repository-map.md) sınırları tanımlar.

## İlk kabul kapısı

Uygulamadan önce girdi/çıktı sözleşmeleri, kesin çekirdek revizyonu, anlamlı hata durumları, bağımlılık envanteri ve yürütme hedefleri içeren sınırlı bir görev açın. Uygulama ekleyen PR'da belge aşaması kaynak korumasını uygun testlerle değiştirin. Belge CI'ı çalışma zamanı veya donanım kanıtı değildir.

[Katkı rehberini](CONTRIBUTING.tr.md) ve [AGENTS](AGENTS.md) sözleşmesini kullanın. Özel veriler, kimlik bilgileri, operasyon kayıtları ve model ağırlıkları Git dışında kalır. Açık varlıklar için ayrıca onaylanmış depolama, köken ve lisans kararı gerekir; burada depolama veya hizmet kurulmaz. Kendi kaynak kodumuz ve belgelerimiz [Apache-2.0](LICENSE) lisanslıdır. Ayrı belirtilen üçüncü taraf içerikleri, model ağırlıkları ve veri kümeleri kendi koşullarını korur.

G56 [bildirilen karar/skor adayı ve sentetik referansı](docs/tr/decision-score-profile.md) ekler; kendi Rust metaveriyi çözer, yerel skor/model kalitesi desteklenmeyen/not_run kalır.

G67, [ilan edilen embedding profili](docs/tr/embedding-profile.md), bağımsız sentetik pooling/L2/erişim referansları ve gerçek core EYL fixture testleri ekler. Native model/Türkçe kalite yürütmesi G68 altında not_run kalır.
