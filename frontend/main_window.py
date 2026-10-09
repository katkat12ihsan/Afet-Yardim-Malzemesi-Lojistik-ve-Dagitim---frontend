"""Sunum (arayüz) katmanı - ana pencere.

Hafta 3: sol menü + içerik alanından oluşan boş iskelet. Her modül,
geliştirileceği haftayı gösteren bir yer tutucu sayfa açar.
"""

import tkinter as tk
from tkinter import ttk

from backend import config
from backend.services import modul_servisi

RENK_UST = "#b71c1c"
RENK_MENU = "#263238"
RENK_MENU_SECILI = "#37474f"


class AnaPencere(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
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

        tablo = ttk.Treeview(self.icerik, columns=("hafta", "aciklama"), height=9)
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

    def _yer_tutucu_sayfa(self, modul: modul_servisi.ModulBilgisi) -> None:
        tk.Label(self.icerik, text=modul.ad, bg="white",
                 font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=24, pady=(24, 4))
        tk.Label(self.icerik, text=modul.aciklama, bg="white", fg="#555",
                 font=("Segoe UI", 10)).pack(anchor="w", padx=24)
        tk.Label(self.icerik, text=f"Bu modül {modul.hafta}. haftada geliştirilecek.",
                 bg="#fff3e0", fg="#e65100", font=("Segoe UI", 11),
                 padx=12, pady=8).pack(anchor="w", padx=24, pady=20)
        self.durum.configure(text=f"Sürüm {config.SURUM}  |  {modul.ad}: yer tutucu")
