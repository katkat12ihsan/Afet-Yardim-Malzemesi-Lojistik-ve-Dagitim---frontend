# P16 · Afet Yardım Malzemesi Lojistik ve Dağıtım — **Frontend**

Bağış malzemelerinin envanterini yönetip ihtiyaç noktalarına dağıtımı planlayan **Python masaüstü uygulaması**nın arayüzü (Tkinter).

| Depo | İçerik |
|---|---|
| [Backend](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend) | Varlık, iş ve veri erişim katmanları, veritabanı şeması, testler, **proje dokümantasyonu** |
| **Frontend (bu depo)** | Tkinter arayüzü (`frontend/`) ve başlangıç noktası (`main.py`) |

> Bilgisayar Uygulamaları I — Proje Tabanlı Öğrenme dersi projesi · İhsan Katkat (251161036)
> Durum: **Hafta 6 — Envanter Yönetimi**

## Kurulum ve çalıştırma

Gereksinim: Python 3.10+ ve Git (backend paketi GitHub'dan kurulur).

```bash
git clone https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---frontend.git
cd Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---frontend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m backend.data.kurulum --ornek-veri
python main.py
```

`python -m backend.data.kurulum --ornek-veri` veritabanını oluşturur ve her rolden bir test kullanıcısı ekler: `yonetici`, `kurum1`, `depo1`. Parolalar backend deposunda, `backend/data/ornek_veri.py` → `KULLANICILAR` içindedir (yalnızca yerel demo içindir). Hiç kullanıcı yoksa kayıt ekranından ilk Yönetici hesabı açılabilir.

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
| Kullanıcılar | Yalnızca Yönetici |
| Envanter Yönetimi (Hafta 6) | Stok durumu (Normal/Kritik/Tükendi), giriş/çıkış/sayım/kritik seviye pencereleri, hareket geçmişi, malzeme tanımları (Yönetici). Depo görevlisi yalnızca kendi deposunu görür. |

| Rol | Erişebildiği modüller |
|---|---|
| Yönetici | Tümü + Kullanıcılar |
| Kurum | Panel, İhtiyaç, Dağıtım, YZ Önerisi, Takip, Rapor |
| Depo | Panel, Envanter, Bağış, Takip |

![Envanter - stok durumu](https://raw.githubusercontent.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/main/docs/ekran-goruntuleri/hafta-06-envanter-stok-durumu.png)

![Envanter - yetersiz stok uyarısı](https://raw.githubusercontent.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/main/docs/ekran-goruntuleri/hafta-06-yetersiz-stok-uyarisi.png)

## Klasör yapısı

```
main.py                  başlangıç noktası: giriş -> ana pencere -> çıkış -> giriş
frontend/
  giris_penceresi.py     giriş / kayıt penceresi
  main_window.py         ana pencere, rol bazlı menü, sayfalar
  envanter_sayfasi.py    envanter: stok durumu, hareket geçmişi, malzeme tanımları
requirements.txt         backend paketi (GitHub)
```

**Kural:** Frontend veritabanına doğrudan erişmez; yalnızca `backend.services` (KimlikServisi, OzetServisi, EnvanterServisi, modül planı) ve `backend.models` kullanır. Yetki kontrolü arayüzde değil backend'de yapılır; menüdeki kilit yalnızca kullanım kolaylığıdır.

## Dokümantasyon

Tüm proje dokümantasyonu backend deposundadır:
[ER diyagramı](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/blob/main/docs/ER-Diyagrami.md) ·
[Mimari](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/blob/main/docs/Mimari.md) ·
[Güvenlik notu](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/blob/main/docs/Guvenlik-Notu.md) ·
[Envanter](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/blob/main/docs/Envanter.md) ·
[Haftalık raporlar](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/tree/main/docs/haftalik-raporlar) ·
[Formlar](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/tree/main/docs/formlar) ·
[AI kullanım günlüğü](https://github.com/katkat12ihsan/Afet-Yardim-Malzemesi-Lojistik-ve-Dagitim---backend/blob/main/docs/ai-kullanim-gunlugu.md)
