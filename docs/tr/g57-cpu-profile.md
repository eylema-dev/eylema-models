# G57 kendi CPU karar profili

Durum: yalnız CPU manifest yazımı ve sentetik geliştirme kontrolleri; gerçek model/referans kabulü not_run. [İngilizce](../en/g57-cpu-profile.md).

Ayrı qwen3-reranker-0.6b.cpu kimliği G56 kaynak/artifact/tokenizer ve DecisionRoleInterface sözleşmesini korur; kendi F32 backbone ve F64 skaler normalizasyonumuzu kullanır. Özgün düz çift şablonu, son konum yes9693/no2152, yarım-çifte micros,750000eşik/100000fark ve çift başına reset kullanılır. Üretim, kalibrasyon veya eylem yetkisi yoktur. Özgün G56 metaverisi değişmez.

CPU JSON/EYL aynı core fixture ile koordinelidir; yeni CPU operatör bileşeni sınırlı gerçek kabulü tanımlar. Duyurulan ağırlık1191588280bayt/SHA25627cd75a405b9c1b46b59abfd88aaa209e6fed2a1972cde9b70e7659537c5e65b; G57 için indirilmedi. Önerilen310tensor düzeni, tam bayt/head kalitesi, kapasite ve native kanıt doğrulanmadı. Genel metaveri ataması desteklenmez. Kaynak/profil/haklar e61197ed45024b0ed8a2d74b80b4d909f1255473 ve yayıncı README beyanına sabittir; proje/veri/aktarımı izni doğmaz.
