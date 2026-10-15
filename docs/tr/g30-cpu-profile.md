# G30 sınırlı CPU profili

Bu kayıt, sabitlenmiş Qwen3-0.6B adayı için ayrı bir revision-2 metaveri profilidir. Özgün G27 manifestini, kaynak commit'ini, operator kimliklerini, tokenizer/config/template kimliklerini ve yayımlayıcı tarafından bildirilen ağırlık kimliğini korur. Yeni rol bileşeni, adayı değişmemiş G27 üst manifestine tam EYL SHA256 değeriyle bağlar.

Profil dört isteğe bağlı öneri arayüzünü kaydeder: reasoning, planning, specialist ve critic. Critic sınırlı bir aday/kanıt çiftini alır ve `evaluation.proposal.v1` altında doğrulanmamış metin döndürür; sayısal puan, hüküm veya eylem üretmez. Varsayılan atamalar boş kalır. Rol niyeti yürütme izni veya kalite iddiası vermez.

İlk sahipli CPU sınırı batch bir, kabul edilen iş başına en fazla 64 context konumu ve sekiz yeni tokendır; manifestteki daha geniş bildirim sınırları korunur. Desteklenmeyen mimari, precision, tokenizer kimliği, rol veya kapasite güvenli biçimde reddedilmelidir. Üst tokenizer ve byte'ları ayrı kimliklerle sabitlenmiştir. Bu katalog kaydı tek başına yerel yürütmeyi etkinleştirmez.

Ağırlıklar bu katalog deposunda tutulmaz. Sabitlenmiş tam dosya SHA256 ve boyut, gerçek byte'lar ayrı ve sınırlı yerel kabulde doğrulanıncaya kadar yalnız yayımlayıcının bildirimidir. Model yürütümü, upstream ile nümerik eşdeğerlik, gecikme, kapasite, rol kalitesi, GPU ve eğitim burada `not_run` durumundadır. Serileştirilmiş profil ve EYL kaydı yalnız niyet/köken metaverisidir.
