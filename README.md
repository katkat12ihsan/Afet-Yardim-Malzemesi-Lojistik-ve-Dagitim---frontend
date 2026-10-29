# P16 · Afet Yardım Malzemesi Lojistik ve Dağıtım — **Frontend**

Bağış malzemelerinin envanterini yönetip ihtiyaç noktalarına dağıtımı planlayan **Python masaüstü uygulaması**nın arayüzü (Tkinter).

| Depo | İçerik |
|---|---|
| [Backend](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend) | Varlık, iş ve veri erişim katmanları, veritabanı şeması, testler, **proje dokümantasyonu** |
| **Frontend (bu depo)** | Tkinter arayüzü (`frontend/`) ve başlangıç noktası (`main.py`) |

> Bilgisayar Uygulamaları I — Proje Tabanlı Öğrenme dersi projesi · İhsan Katkat (251161036)
> Durum: **Hafta 7 — Bağış Girişi ve İhtiyaç Eşleştirme**

## Kurulum ve çalıştırma

Gereksinim: Python 3.10+ ve Git (backend paketi GitHub'dan kurulur).

**İlk kurulum (bir kez):** depoyu klonlayın ve **`baslat.bat`** dosyasına çift tıklayın. Sanal ortamı (`.venv`) kurar, backend'i GitHub'dan yükler ve örnek veritabanını oluşturur.

**Sonrasında:** uygulamayı istediğiniz yoldan açın: VS Code'da `main.py` → Run (▶), `python main.py` ya da `baslat.bat`. `main.py` genel Python ile açılırsa backend'i bulamaz ve kendini otomatik olarak `.venv` Python'u ile yeniden başlatır.

| Dosya | Ne zaman |
|---|---|
| `baslat.bat` | İlk kurulum; istenirse her açışta da kullanılabilir |
| `guncelle.bat` | Backend deposuna yeni hafta gönderildiğinde: backend'i son sürüme günceller, şemayı yükseltir |

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
| Ana panel | Veritabanından gelen özet kartları, modüllerin hafta planı ve kullanıcının erişimi |
| Rol bazlı menü | Yetkisiz modüller "(kilitli)"; tıklanınca "Erişim engellendi" (karar backend'de verilir) |
| Kullanıcılar | Yalnızca Yönetici. Hesap listesi, **Rolü Düzenle** penceresi (Depo rolünde depo seçimi) ve son rol değişiklikleri. Kişi kendi rolünü değiştiremez. |
| Envanter Yönetimi (Hafta 6) | Stok durumu (Normal/Kritik/Tükendi), giriş/çıkış/sayım/kritik seviye pencereleri, hareket geçmişi, malzeme tanımları (Yönetici). Depo görevlisi yalnızca kendi deposunu görür. |
| Bağış Girişi (Hafta 7) | Yeni bağış formu (bağışçı, depo, kalemler, son kullanma), bağış geçmişi ve kalemleri. Depo görevlisi yalnızca kendi deposuna girer. |
| İhtiyaç Eşleştirme (Hafta 7) | Öncelik sıralı talepler, en yakın depodan öneri ve eksik uyarısı, dağıtımı planla; Dağıtımlar (Yola Çıkar / Teslim Edildi / İptal); Stok–Talep Dengesi. |

| Rol | Erişebildiği modüller |
|---|---|
| Yönetici | Tümü + Kullanıcılar |
| Kurum | Panel, İhtiyaç, Dağıtım, YZ Önerisi, Takip, Rapor |
| Depo | Panel, Envanter, Bağış, Takip |

![Envanter - stok durumu](https://raw.githubusercontent.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/main/docs/ekran-goruntuleri/hafta-06-envanter-stok-durumu.png)

![Envanter - yetersiz stok uyarısı](https://raw.githubusercontent.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/main/docs/ekran-goruntuleri/hafta-06-yetersiz-stok-uyarisi.png)

## Klasör yapısı

```
baslat.bat               çift tıkla aç (ilk seferde kurulum)
guncelle.bat             backend'i GitHub'daki son sürüme güncelle
main.py                  başlangıç noktası: giriş -> ana pencere -> çıkış -> giriş
frontend/
  giris_penceresi.py     giriş / kayıt penceresi
  main_window.py         ana pencere, rol bazlı menü, sayfalar
  envanter_sayfasi.py    envanter: stok durumu, hareket geçmişi, malzeme tanımları
  kullanicilar_sayfasi.py  kullanıcılar: liste, rolü düzenle, rol değişikliği geçmişi
  bagis_sayfasi.py       bağış girişi: yeni bağış, bağış geçmişi
  ihtiyac_sayfasi.py     ihtiyaç eşleştirme: talepler/öneri, dağıtımlar, stok–talep dengesi
  ortak.py               sayfaların ortak tablo/biçim yardımcıları
requirements.txt         backend paketi (GitHub)
```

**Kural:** Frontend veritabanına doğrudan erişmez; yalnızca `backend.services` (KimlikServisi, OzetServisi, EnvanterServisi, BagisServisi, EslestirmeServisi, modül planı) ve `backend.models` kullanır. Yetki kontrolü arayüzde değil backend'de yapılır; menüdeki kilit yalnızca kullanım kolaylığıdır.

## Dokümantasyon

Tüm proje dokümantasyonu backend deposundadır:
[ER diyagramı](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/blob/main/docs/ER-Diyagrami.md) ·
[Mimari](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/blob/main/docs/Mimari.md) ·
[Güvenlik notu](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/blob/main/docs/Guvenlik-Notu.md) ·
[Envanter](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/blob/main/docs/Envanter.md) ·
[Bağış ve Eşleştirme](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/blob/main/docs/Bagis-ve-Eslestirme.md) ·
[Haftalık raporlar](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/tree/main/docs/haftalik-raporlar) ·
[Formlar](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/tree/main/docs/formlar) ·
[AI kullanım günlüğü](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/blob/main/docs/ai-kullanim-gunlugu.md)
