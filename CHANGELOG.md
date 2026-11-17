# Değişiklik Günlüğü — Frontend

Sürüm numaraları [anlamsal sürümleme](https://semver.org/lang/tr/) kuralına uyar ve backend ile aynı numarayı kullanır: frontend `v0.6.0`, backend `v0.6.0` ile çalışır (`requirements.txt` bu etiketi kurar).

## [0.6.1] — 17.11.2026 · Parola sıfırlama (etiket: `v0.6.1`, backend `v0.6.1`)

### Eklenenler
- **Kullanıcılar → Parolayı Sıfırla** (yalnızca Yönetici): onaydan sonra tek kullanımlık geçici parola üretilir ve yalnızca bir kez, ayrı bir pencerede gösterilir (Panoya Kopyala). Durum sütununda "parola sıfırlandı". Rol değişiklikleri ve parola sıfırlamaları alt kısımda iki sekmede.
- **Giriş → Parolamı unuttum**: parolanın Yönetici tarafından sıfırlandığını anlatan bilgi (uygulama internetsiz çalıştığı için e-posta/SMS ile sıfırlama yok).
- **Yeni Parola Belirle** formu: geçici parolayla girince oturum açılmaz, kullanıcı kendi parolasını belirler ve doğrudan giriş yapar.
- Arayüz testi: sıfırla → geçici parola → ilk girişte yeni parola (toplam 6 test).

### Değişenler
- `requirements.txt` backend'i `@v0.6.1`'e sabitler.

## [0.6.0] — 04.11.2026 · Hafta 8 · VİZE ara sürümü (etiket: `v0.6.0`)

### Değişenler
- Ana panelde modül tablosuna **Durum** sütunu (Hazır / Kısmen / Planlandı), modüller haftaya göre sıralı ve renkli.
- **Rota / Dağıtım Planı** menüsü artık yer tutucu sayfa yerine İhtiyaç Eşleştirme'nin **Dağıtımlar** sekmesini açar (harita/rota Hafta 9'da eklenecek).
- Envanter stok tablosuna **Rezerve** sütunu; Stok Çıkışı penceresi "rezerve X, serbest Y" bilgisini gösterir ve rezerve stoğa dokunan çıkışta backend'in mesajını gösterir.
- `requirements.txt` backend'i `@main` yerine etiketli `@v0.6.0` sürümüne sabitler: sınavda kurulan kod etiketli sürümün aynısıdır.

### Eklenenler
- `demo.bat`: gerçek veritabanına dokunmadan, her açılışta temiz örnek veriyle (`%USERPROFILE%\AfetLojistik\demo.db`) vize demosu.
- `tests/test_arayuz.py`: arayüz duman testi. Her rol × her menü sayfası × her sekme hatasız açılıyor; yetkisiz sayfada "Erişim engellendi"; Depo rolünde doğru menüler kilitli; panelde durumlar görünüyor (5 test).

## [0.5.0] — 29.10.2026 · Hafta 7
- Bağış Girişi sayfası (yeni bağış, bağış geçmişi), İhtiyaç Eşleştirme sayfası (talepler ve öneri, dağıtımlar, stok–talep dengesi), `ortak.py`.

## [0.4.3] — 23.10.2026
- Kullanıcılar sayfası ayrı dosyada; Rolü Düzenle penceresi ve son rol değişiklikleri.
- `main.py`, backend'i bulamazsa kendini `.venv` Python'u ile yeniden başlatır; `baslat.bat`, `guncelle.bat`.

## [0.4.0] — 21.10.2026 · Hafta 6
- Envanter sayfası: stok durumu, giriş/çıkış/sayım/kritik seviye pencereleri, hareket geçmişi, malzeme tanımları.

## [0.3.0] — 09.10.2026 · Hafta 5
- Giriş/kayıt penceresi, kullanıcı-rol bilgisi, çıkış, rol bazlı menü. 16.10.2026: ayrı depo; backend GitHub'dan kurulur.

## [0.2.0] — 09.10.2026 · Hafta 4
- Ana panelde veritabanı özet kartları; açılışta migration.

## [0.1.0] — 09.10.2026 · Hafta 3
- Tkinter ana pencere iskeleti ve başlangıç noktası.
