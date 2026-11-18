# P16 · Afet Yardım Malzemesi Lojistik ve Dağıtım — **Frontend**

Bağış malzemelerinin envanterini yönetip ihtiyaç noktalarına dağıtımı planlayan **Python masaüstü uygulaması**nın arayüzü (Tkinter).

| Depo | İçerik |
|---|---|
| [Backend](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend) | Varlık, iş ve veri erişim katmanları, veritabanı şeması, testler, **proje dokümantasyonu** |
| **Frontend (bu depo)** | Tkinter arayüzü (`frontend/`) ve başlangıç noktası (`main.py`) |

> Bilgisayar Uygulamaları I — Proje Tabanlı Öğrenme dersi projesi · İhsan Katkat (251161036)
> Durum: **Hafta 9 — Harita / Rota API [`v0.7.0`](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---frontend/tree/v0.7.0)** (backend de `v0.7.0`) · vize sürümü [`v0.6.0`](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---frontend/tree/v0.6.0) · [Değişiklik günlüğü](CHANGELOG.md)

## Kurulum ve çalıştırma

Gereksinim: Python 3.10+ ve Git (backend paketi GitHub'dan kurulur).

**İlk kurulum (bir kez):** depoyu klonlayın ve **`baslat.bat`** dosyasına çift tıklayın. Sanal ortamı (`.venv`) kurar, backend'i GitHub'dan yükler ve örnek veritabanını oluşturur.

**Sonrasında:** uygulamayı istediğiniz yoldan açın: VS Code'da `main.py` → Run (▶), `python main.py` ya da `baslat.bat`. `main.py` genel Python ile açılırsa backend'i bulamaz ve kendini otomatik olarak `.venv` Python'u ile yeniden başlatır.

| Dosya | Ne zaman |
|---|---|
| `baslat.bat` | İlk kurulum; istenirse her açışta da kullanılabilir |
| `guncelle.bat` | Backend deposuna yeni hafta gönderildiğinde: backend'i `requirements.txt`'teki sürüme günceller, şemayı yükseltir |
| `demo.bat` | **Vize/sınıf demosu:** ayrı bir demo veritabanını (`%USERPROFILE%\AfetLojistik\demo.db`) her açılışta temiz örnek veriyle kurar. Gerçek veritabanına dokunmaz. Adımlar: [Demo senaryosu](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/blob/main/docs/Demo-Senaryosu.md) |

> **Sürüm sabitleme:** `requirements.txt` backend'i etiketli sürümden kurar (`...backend.git@v0.7.0`). Böylece etiketli sürümün kodu her kurulumda aynıdır; yeni hafta etiketlenince bu satır da güncellenir.

> **Neden `.venv`?** Backend ayrı bir depodadır ve bu projenin `.venv` sanal ortamına paket olarak kuruludur; genel Python onu görmez. `main.py` bu yüzden açılışta backend'i bulamazsa `.venv` ile yeniden başlar. **"Backend paketi bulunamadı"** uyarısı yalnızca `.venv` hiç kurulmamışsa çıkar; çözüm `baslat.bat`'ı bir kez çalıştırmaktır.

Elle kurulum (komut satırı):

```bash
git clone https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---frontend.git
cd Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---frontend
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m backend.data.kurulum --ornek-veri
.venv\Scripts\python.exe main.py
```

Kurulum komutu (`backend.data.kurulum --ornek-veri`) veritabanını oluşturur ve her rolden bir test kullanıcısı ekler: `yonetici`, `kurum1`, `depo1`. Parolalar backend deposunda, `backend/data/ornek_veri.py` → `KULLANICILAR` içindedir (yalnızca yerel demo içindir). Hiç kullanıcı yoksa kayıt ekranından ilk Yönetici hesabı açılabilir.

**İki depoyu birlikte geliştirirken:** depoları yan yana klonlayın ve backend'i düzenlenebilir kurun; backend'de yapılan değişiklik arayüze hemen yansır:

```bash
pip install -e ../Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend
```

## Ekranlar

| Ekran | Açıklama |
|---|---|
| Giriş / kayıt | Parola alanı maskeli; hatalı girişte "Kullanıcı adı veya parola hatalı." |
| Ana panel | Veritabanından gelen özet kartları; modüllerin haftası, **durumu (Hazır / Kısmen / Planlandı)** ve kullanıcının erişimi |
| Rol bazlı menü | Yetkisiz modüller "(kilitli)"; tıklanınca "Erişim engellendi" (karar backend'de verilir) |
| Kullanıcılar | Yalnızca Yönetici. Hesap listesi, **Rolü Düzenle** penceresi (Depo rolünde depo seçimi) ve son rol değişiklikleri. Kişi kendi rolünü değiştiremez. |
| Envanter Yönetimi (Hafta 6) | Stok durumu (Normal/Kritik/Tükendi), **Rezerve** sütunu (planlanmış dağıtımlara ayrılan; Envanter'den çıkarılamaz, Hafta 8), giriş/çıkış/sayım/kritik seviye pencereleri, hareket geçmişi, malzeme tanımları (Yönetici). Depo görevlisi yalnızca kendi deposunu görür. |
| Bağış Girişi (Hafta 7) | Yeni bağış formu (bağışçı, depo, kalemler, son kullanma), bağış geçmişi ve kalemleri. Depo görevlisi yalnızca kendi deposuna girer. |
| İhtiyaç Eşleştirme (Hafta 7) | Öncelik sıralı talepler, en yakın depodan öneri ve eksik uyarısı, dağıtımı planla; Dağıtımlar (Yola Çıkar / Teslim Edildi / İptal); Stok–Talep Dengesi. |
| Rota / Dağıtım Planı (Hafta 9) | Dağıtımlar; seçilen dağıtımın karayolu mesafesi, süresi ve rotası (OpenRouteService), Canvas'ta çizim. API anahtarı yoksa ya da servis hata verirse kuş uçuşu tahmin ve nedeni (turuncu). Yola Çıkar / Teslim Edildi / İptal. Anahtar: `HARITA_API_ANAHTARI` ortam değişkeni ya da `C:\Users\<kullanıcı>\AfetLojistik\.env` (ayrıntı: backend `docs/Rota-API.md`). |

| Rol | Erişebildiği modüller |
|---|---|
| Yönetici | Tümü + Kullanıcılar |
| Kurum | Panel, İhtiyaç, Dağıtım, YZ Önerisi, Takip, Rapor |
| Depo | Panel, Envanter, Bağış, Takip |

![Ana panel - modül durumu](https://raw.githubusercontent.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/main/docs/ekran-goruntuleri/hafta-08-ana-panel-modul-durumu.png)

![Envanter - rezerve stok çıkarılamaz](https://raw.githubusercontent.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/main/docs/ekran-goruntuleri/hafta-08-rezerve-cikis-engeli.png)

![Envanter - stok durumu](https://raw.githubusercontent.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/main/docs/ekran-goruntuleri/hafta-06-envanter-stok-durumu.png)

![Envanter - yetersiz stok uyarısı](https://raw.githubusercontent.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/main/docs/ekran-goruntuleri/hafta-06-yetersiz-stok-uyarisi.png)

## Klasör yapısı

```
baslat.bat               çift tıkla aç (ilk seferde kurulum)
guncelle.bat             backend'i requirements.txt'teki sürüme güncelle
demo.bat                 vize demosu: ayrı demo veritabanı, temiz örnek veri
CHANGELOG.md             sürümler ve değişiklikler
tests/test_arayuz.py     arayüz testi: her rol/sayfa/sekme, parola sıfırlama, rota sayfası (6 test; harita servisine gitmez)
main.py                  başlangıç noktası: giriş -> ana pencere -> çıkış -> giriş
frontend/
  giris_penceresi.py     giriş / kayıt penceresi
  main_window.py         ana pencere, rol bazlı menü, sayfalar
  envanter_sayfasi.py    envanter: stok durumu, hareket geçmişi, malzeme tanımları
  kullanicilar_sayfasi.py  kullanıcılar: liste, rolü düzenle, rol değişikliği geçmişi
  bagis_sayfasi.py       bağış girişi: yeni bağış, bağış geçmişi
  ihtiyac_sayfasi.py     ihtiyaç eşleştirme: talepler/öneri, dağıtımlar, stok–talep dengesi
  rota_sayfasi.py        rota / dağıtım planı: mesafe, süre, rota çizimi, durum düğmeleri
  ortak.py               sayfaların ortak tablo/biçim yardımcıları
requirements.txt         backend paketi (GitHub, etiketli sürüm @v0.7.0)
```

**Kural:** Frontend veritabanına doğrudan erişmez; yalnızca `backend.services` (KimlikServisi, OzetServisi, EnvanterServisi, BagisServisi, EslestirmeServisi, modül planı) ve `backend.models` kullanır. Yetki kontrolü arayüzde değil backend'de yapılır; menüdeki kilit yalnızca kullanım kolaylığıdır.

## Testler

Arayüz testi gerçek pencereleri açar ama geçici bir veritabanı kullanır (gerçek veriye dokunmaz):

```bash
.venv\Scripts\python.exe -m unittest
```

## Dokümantasyon

Tüm proje dokümantasyonu backend deposundadır:
[ER diyagramı](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/blob/main/docs/ER-Diyagrami.md) ·
[Mimari](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/blob/main/docs/Mimari.md) ·
[Güvenlik notu](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/blob/main/docs/Guvenlik-Notu.md) ·
[Envanter](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/blob/main/docs/Envanter.md) ·
[Bağış ve Eşleştirme](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/blob/main/docs/Bagis-ve-Eslestirme.md) ·
[Demo senaryosu](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/blob/main/docs/Demo-Senaryosu.md) ·
[Haftalık raporlar](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/tree/main/docs/haftalik-raporlar) ·
[Formlar](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/tree/main/docs/formlar) ·
[AI kullanım günlüğü](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/blob/main/docs/ai-kullanim-gunlugu.md)
