"""Sunum (arayüz) katmanı - ana pencere.

Hafta 3: sol menü + içerik alanından oluşan boş iskelet. Her modül,
geliştirileceği haftayı gösteren bir yer tutucu sayfa açar.
Hafta 4: ana panelde veritabanı özet kartları (OzetServisi üzerinden).

Frontend veritabanını tanımaz; yalnızca backend servislerini kullanır.
Servis nesnesi dışarıdan (main.py) verilir.
"""

import tkinter as tk
from tkinter import ttk

from backend import config
from backend.services import modul_servisi
from backend.services.ozet_servisi import OzetServisi

RENK_UST = "#b71c1c"
RENK_MENU = "#263238"
RENK_MENU_SECILI = "#37474f"


class AnaPencere(tk.Tk):
    def __init__(self, ozet_servisi: OzetServisi) -> None:
        super().__init__()
        self._ozet_servisi = ozet_servisi
        self.title(config.UYGULAMA_ADI)
        self.geometry("1000x620")
        self.minsize(820, 520)

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
        buton = tk.Button(menu, text=metin, anchor="w", relief=tk.FLAT,
                          bg=RENK_MENU, fg="white", activebackground=RENK_MENU_SECILI,
                          activeforeground="white", font=("Segoe UI", 10), bd=0,
                          padx=16, pady=10, command=lambda: self.sayfa_goster(anahtar))
        buton.pack(fill=tk.X)
        self._menu_butonlari[anahtar] = buton

    def _durum_cubugu_olustur(self) -> None:
        self.durum = ttk.Label(self, text=f"Sürüm {config.SURUM}", anchor="w",
                               padding=(10, 4))
        self.durum.pack(side=tk.BOTTOM, fill=tk.X)

    # ------------------------------------------------------------ sayfalar
    def sayfa_goster(self, anahtar: str) -> None:
        for anahtar_, buton in self._menu_butonlari.items():
            buton.configure(bg=RENK_MENU_SECILI if anahtar_ == anahtar else RENK_MENU)
        for cocuk in self.icerik.winfo_children():
            cocuk.destroy()

        if anahtar == "panel":
            self._panel_sayfasi()
        else:
            self._yer_tutucu_sayfa(modul_servisi.modul_bul(anahtar))

    def _panel_sayfasi(self) -> None:
        tk.Label(self.icerik, text="Ana Panel", bg="white",
                 font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=24, pady=(24, 4))
        tk.Label(self.icerik, bg="white", fg="#555", justify=tk.LEFT,
                 text="Bağış malzemelerinin envanterini yönetip ihtiyaç noktalarına "
                      "dağıtımı planlayan masaüstü uygulaması.\n"
                      "Aşağıdaki tablo modüllerin geliştirme takvimini gösterir.",
                 font=("Segoe UI", 10)).pack(anchor="w", padx=24)
        self._ozet_kartlari()

        tablo = ttk.Treeview(self.icerik, columns=("hafta", "aciklama"), height=7)
        tablo.heading("#0", text="Modül")
        tablo.heading("hafta", text="Hafta")
        tablo.heading("aciklama", text="Kapsam")
        tablo.column("#0", width=190)
        tablo.column("hafta", width=60, anchor="center")
        tablo.column("aciklama", width=480)
        for modul in modul_servisi.modulleri_getir():
            tablo.insert("", tk.END, text=modul.ad, values=(modul.hafta, modul.aciklama))
        tablo.pack(fill=tk.BOTH, expand=True, padx=24, pady=16)
        self.durum.configure(text=f"Sürüm {config.SURUM}")

    def _ozet_kartlari(self) -> None:
        ozet = self._ozet_servisi.panel_ozeti()
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

    def _yer_tutucu_sayfa(self, modul: modul_servisi.ModulBilgisi) -> None:
        tk.Label(self.icerik, text=modul.ad, bg="white",
                 font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=24, pady=(24, 4))
        tk.Label(self.icerik, text=modul.aciklama, bg="white", fg="#555",
                 font=("Segoe UI", 10)).pack(anchor="w", padx=24)
        tk.Label(self.icerik, text=f"Bu modül {modul.hafta}. haftada geliştirilecek.",
                 bg="#fff3e0", fg="#e65100", font=("Segoe UI", 11),
                 padx=12, pady=8).pack(anchor="w", padx=24, pady=20)
        self.durum.configure(text=f"Sürüm {config.SURUM}  |  {modul.ad}: yer tutucu")
