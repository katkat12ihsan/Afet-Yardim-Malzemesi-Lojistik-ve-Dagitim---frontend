"""Sunum (arayüz) katmanı - ana pencere.

Hafta 3: sol menü + içerik alanından oluşan boş iskelet. Her modül,
geliştirileceği haftayı gösteren bir yer tutucu sayfa açar.
Hafta 4: ana panelde veritabanı özet kartları (OzetServisi üzerinden).
Hafta 5: giriş yapan kullanıcı ve rolü, çıkış, rol bazlı menü, Kullanıcılar sayfası.

Frontend veritabanını tanımaz; yalnızca backend servislerini kullanır.
Servis nesneleri ve oturum token'ı dışarıdan (main.py) verilir.

Yetki: Menüde yetkisiz modüller soluk gösterilir (kullanım kolaylığı), ama
asıl karar her sayfa açılışında backend'deki `modul_erisimi` ile verilir.
"""

import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from backend import config
from backend.services import modul_servisi
from backend.services.hatalar import OturumGecersiz, YetkisizErisim
from backend.services.kimlik_servisi import KimlikServisi
from backend.services.ozet_servisi import OzetServisi
from backend.services.yetki import erisebilir_mi

RENK_UST = "#b71c1c"
RENK_MENU = "#263238"
RENK_MENU_SECILI = "#37474f"
RENK_MENU_KILITLI = "#78909c"


class AnaPencere(tk.Tk):
    def __init__(self, kimlik: KimlikServisi, ozet_servisi: OzetServisi, token: str) -> None:
        super().__init__()
        self._kimlik = kimlik
        self._ozet_servisi = ozet_servisi
        self._token = token
        self.cikis_yapildi = False           # main.py: True ise giriş ekranına döner
        self.kullanici = kimlik.oturum_dogrula(token)

        self.title(config.UYGULAMA_ADI)
        self.geometry("1040x640")
        self.minsize(860, 540)

        self._menu_butonlari: dict[str, tk.Button] = {}
        self._ust_bant_olustur()
        self._govde_olustur()
        self._durum_cubugu_olustur()
        self.sayfa_goster("panel")

    # ------------------------------------------------------------- yerleşim
    def _ust_bant_olustur(self) -> None:
        bant = tk.Frame(self, bg=RENK_UST, height=56)
        bant.pack(side=tk.TOP, fill=tk.X)
        tk.Label(bant, text=config.UYGULAMA_ADI, bg=RENK_UST, fg="white",
                 font=("Segoe UI", 15, "bold")).pack(side=tk.LEFT, padx=16, pady=12)
        tk.Button(bant, text="Çıkış Yap", command=self._cikis, relief=tk.FLAT, bd=0,
                  bg="#8e0000", fg="white", activebackground="#5f0000", activeforeground="white",
                  font=("Segoe UI", 9, "bold"), padx=12, pady=4).pack(side=tk.RIGHT, padx=16)
        tk.Label(bant, text=f"{self.kullanici.ad_soyad}  ·  {self.kullanici.rol.value}",
                 bg=RENK_UST, fg="#ffcdd2", font=("Segoe UI", 10)).pack(side=tk.RIGHT)

    def _govde_olustur(self) -> None:
        govde = tk.Frame(self)
        govde.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        menu = tk.Frame(govde, bg=RENK_MENU, width=210)
        menu.pack(side=tk.LEFT, fill=tk.Y)
        menu.pack_propagate(False)

        self._menu_ogesi_ekle(menu, "panel", "Ana Panel")
        for modul in modul_servisi.modulleri_getir():
            self._menu_ogesi_ekle(menu, modul.anahtar, modul.ad)

        self.icerik = tk.Frame(govde, bg="white")
        self.icerik.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _menu_ogesi_ekle(self, menu: tk.Frame, anahtar: str, metin: str) -> None:
        yetkili = erisebilir_mi(self.kullanici, anahtar)
        buton = tk.Button(menu, text=metin if yetkili else f"{metin}  (kilitli)", anchor="w",
                          relief=tk.FLAT, bg=RENK_MENU, fg="white" if yetkili else RENK_MENU_KILITLI,
                          activebackground=RENK_MENU_SECILI, activeforeground="white",
                          font=("Segoe UI", 10), bd=0, padx=16, pady=10,
                          command=lambda: self.sayfa_goster(anahtar))
        buton.pack(fill=tk.X)
        self._menu_butonlari[anahtar] = buton

    def _durum_cubugu_olustur(self) -> None:
        self.durum = ttk.Label(self, anchor="w", padding=(10, 4))
        self.durum.pack(side=tk.BOTTOM, fill=tk.X)

    def _durum_yaz(self, ek: str = "") -> None:
        metin = f"Sürüm {config.SURUM}  |  Kullanıcı: {self.kullanici.kullanici_adi}"
        self.durum.configure(text=f"{metin}  |  {ek}" if ek else metin)

    # ------------------------------------------------------------ oturum
    def _cikis(self) -> None:
        self._kimlik.cikis_yap(self._token)
        self.cikis_yapildi = True
        self.destroy()

    def _oturum_bitti(self, mesaj: str) -> None:
        messagebox.showwarning("Oturum", mesaj, parent=self)
        self.cikis_yapildi = True            # giriş ekranına dön
        self.destroy()

    # ------------------------------------------------------------ sayfalar
    def sayfa_goster(self, anahtar: str) -> None:
        try:
            # Asıl yetki kontrolü backend'de: oturum geçerli mi + rol yetkili mi?
            self._kimlik.modul_erisimi(self._token, anahtar)
        except OturumGecersiz as hata:
            self._oturum_bitti(str(hata))
            return
        except YetkisizErisim as hata:
            self._sayfayi_temizle(anahtar)
            self._erisim_engellendi(str(hata))
            return

        self._sayfayi_temizle(anahtar)
        if anahtar == "panel":
            self._panel_sayfasi()
        elif anahtar == "kullanicilar":
            self._kullanicilar_sayfasi()
        else:
            self._yer_tutucu_sayfa(modul_servisi.modul_bul(anahtar))

    def _sayfayi_temizle(self, anahtar: str) -> None:
        for anahtar_, buton in self._menu_butonlari.items():
            buton.configure(bg=RENK_MENU_SECILI if anahtar_ == anahtar else RENK_MENU)
        for cocuk in self.icerik.winfo_children():
            cocuk.destroy()

    def _baslik(self, metin: str, aciklama: str = "") -> None:
        tk.Label(self.icerik, text=metin, bg="white",
                 font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=24, pady=(24, 4))
        if aciklama:
            tk.Label(self.icerik, text=aciklama, bg="white", fg="#555", justify=tk.LEFT,
                     font=("Segoe UI", 10)).pack(anchor="w", padx=24)

    def _erisim_engellendi(self, mesaj: str) -> None:
        self._baslik("Erişim engellendi")
        tk.Label(self.icerik, text=mesaj, bg="#ffebee", fg="#c62828", font=("Segoe UI", 11),
                 padx=12, pady=8).pack(anchor="w", padx=24, pady=20)
        self._durum_yaz("yetkisiz erişim denemesi")

    def _panel_sayfasi(self) -> None:
        self._baslik("Ana Panel",
                     f"Hoş geldiniz, {self.kullanici.ad_soyad}. Bağış malzemelerinin envanterini "
                     "yönetip ihtiyaç noktalarına dağıtımı planlayan masaüstü uygulaması.")
        self._ozet_kartlari()

        tablo = ttk.Treeview(self.icerik, columns=("hafta", "erisim", "aciklama"), height=8)
        tablo.heading("#0", text="Modül")
        tablo.heading("hafta", text="Hafta")
        tablo.heading("erisim", text="Erişim")
        tablo.heading("aciklama", text="Kapsam")
        tablo.column("#0", width=180)
        tablo.column("hafta", width=55, anchor="center")
        tablo.column("erisim", width=70, anchor="center")
        tablo.column("aciklama", width=430)
        for modul in modul_servisi.modulleri_getir():
            erisim = "var" if erisebilir_mi(self.kullanici, modul.anahtar) else "yok"
            tablo.insert("", tk.END, text=modul.ad, values=(modul.hafta, erisim, modul.aciklama))
        tablo.pack(fill=tk.BOTH, expand=True, padx=24, pady=16)
        self._durum_yaz()

    def _ozet_kartlari(self) -> None:
        ozet = self._ozet_servisi.panel_ozeti(self._token)
        satir = tk.Frame(self.icerik, bg="white")
        satir.pack(fill=tk.X, padx=24, pady=(16, 0))
        kartlar = (
            ("Malzeme çeşidi", ozet.malzeme_cesidi, "#1565c0"),
            ("Depo", ozet.depo, "#ef6c00"),
            ("İhtiyaç noktası", ozet.ihtiyac_noktasi, "#2e7d32"),
            ("Bekleyen talep", ozet.bekleyen_talep, "#c62828"),
            ("Kritik stok", ozet.kritik_stok, "#6a1b9a"),
        )
        for baslik, deger, renk in kartlar:
            kart = tk.Frame(satir, bg="#f5f5f5", highlightbackground=renk, highlightthickness=2)
            kart.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 10))
            tk.Label(kart, text=str(deger), bg="#f5f5f5", fg=renk,
                     font=("Segoe UI", 20, "bold")).pack(pady=(8, 0))
            tk.Label(kart, text=baslik, bg="#f5f5f5", fg="#455a64",
                     font=("Segoe UI", 9)).pack(pady=(0, 8))
        if ozet.bos_mu:
            tk.Label(self.icerik, bg="white", fg="#e65100", font=("Segoe UI", 9),
                     text="Veritabanı boş. Örnek veri için: "
                          "python -m backend.data.kurulum --ornek-veri").pack(anchor="w", padx=24, pady=(6, 0))

    def _kullanicilar_sayfasi(self) -> None:
        self._baslik("Kullanıcılar", "Sistemdeki hesaplar ve rolleri. Parolalar hash'li saklanır, "
                                     "burada gösterilmez.")
        tablo = ttk.Treeview(self.icerik, show="headings", height=12,
                             columns=("kadi", "ad", "rol", "depo", "son", "durum"))
        for kolon, baslik, genislik in (("kadi", "Kullanıcı adı", 120), ("ad", "Ad soyad", 200),
                                        ("rol", "Rol", 90), ("depo", "Depo", 200),
                                        ("son", "Son giriş", 140), ("durum", "Durum", 80)):
            tablo.heading(kolon, text=baslik)
            tablo.column(kolon, width=genislik)
        depolar = dict(self._kimlik.depo_secenekleri())
        for k in self._kimlik.kullanicilari_listele(self._token):
            kilitli = k.kilitli_bitis is not None and k.kilitli_bitis > datetime.now()
            durum = "kilitli" if kilitli else ("aktif" if k.aktif else "pasif")
            tablo.insert("", tk.END, values=(
                k.kullanici_adi, k.ad_soyad, k.rol.value, depolar.get(k.depo_id, "-"),
                k.son_giris.strftime("%d.%m.%Y %H:%M") if k.son_giris else "-", durum))
        tablo.pack(fill=tk.BOTH, expand=True, padx=24, pady=16)
        self._durum_yaz("Kullanıcılar")

    def _yer_tutucu_sayfa(self, modul: modul_servisi.ModulBilgisi) -> None:
        self._baslik(modul.ad, modul.aciklama)
        tk.Label(self.icerik, text=f"Bu modül {modul.hafta}. haftada geliştirilecek.",
                 bg="#fff3e0", fg="#e65100", font=("Segoe UI", 11),
                 padx=12, pady=8).pack(anchor="w", padx=24, pady=20)
        self._durum_yaz(f"{modul.ad}: yer tutucu")
