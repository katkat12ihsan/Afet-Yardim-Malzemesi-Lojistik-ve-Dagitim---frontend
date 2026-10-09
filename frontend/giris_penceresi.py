"""Sunum katmanı - giriş ve kayıt penceresi (Hafta 5).

Parola alanları '•' ile maskelenir. Parola frontend'de hiçbir yere
kaydedilmez; doğrudan KimlikServisi'ne verilir ve orada hash'lenir.
Başarılı girişte servis bir oturum token'ı döndürür; pencere kapanınca
token main.py'ye iletilir.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional

from backend import config
from backend.models import Rol
from backend.services.hatalar import IsKuraliHatasi
from backend.services.kimlik_servisi import KimlikServisi

RENK_UST = "#b71c1c"


class GirisPenceresi(tk.Tk):
    def __init__(self, kimlik: KimlikServisi, bilgi: str = "") -> None:
        super().__init__()
        self._kimlik = kimlik
        self.token: Optional[str] = None
        self.title(f"Giriş - {config.UYGULAMA_ADI}")
        self.geometry("440x560")
        self.resizable(False, False)
        self.configure(bg="white")

        bant = tk.Frame(self, bg=RENK_UST)
        bant.pack(fill=tk.X)
        tk.Label(bant, text="Afet Yardım Lojistik", bg=RENK_UST, fg="white",
                 font=("Segoe UI", 16, "bold")).pack(pady=(16, 0))
        tk.Label(bant, text="Malzeme envanteri ve dağıtım sistemi", bg=RENK_UST, fg="#ffcdd2",
                 font=("Segoe UI", 9)).pack(pady=(0, 14))

        self.govde = tk.Frame(self, bg="white")
        self.govde.pack(fill=tk.BOTH, expand=True, padx=36, pady=20)
        self.mesaj = tk.Label(self, text=bilgi, bg="white", fg="#2e7d32", wraplength=370,
                              justify=tk.LEFT, font=("Segoe UI", 9))
        self.mesaj.pack(side=tk.BOTTOM, pady=(0, 16))
        self._giris_formu()

    # -------------------------------------------------------------- yardımcı
    def _temizle(self) -> None:
        for cocuk in self.govde.winfo_children():
            cocuk.destroy()

    def _alan(self, etiket: str, gizli: bool = False) -> ttk.Entry:
        tk.Label(self.govde, text=etiket, bg="white", fg="#37474f",
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(8, 2))
        giris = ttk.Entry(self.govde, show="•" if gizli else "", font=("Segoe UI", 11))
        giris.pack(fill=tk.X, ipady=3)
        return giris

    def _mesaj_goster(self, metin: str, hata: bool = True) -> None:
        self.mesaj.configure(text=metin, fg="#c62828" if hata else "#2e7d32")

    # ----------------------------------------------------------------- GİRİŞ
    def _giris_formu(self) -> None:
        self._temizle()
        tk.Label(self.govde, text="Giriş Yap", bg="white",
                 font=("Segoe UI", 15, "bold")).pack(anchor="w")
        self.e_kadi = self._alan("Kullanıcı adı")
        self.e_parola = self._alan("Parola", gizli=True)
        ttk.Button(self.govde, text="Giriş", command=self._giris).pack(fill=tk.X, pady=(18, 6), ipady=4)
        tk.Button(self.govde, text="Hesabın yok mu? Kayıt ol", relief=tk.FLAT, bd=0, bg="white",
                  fg="#1565c0", cursor="hand2", command=self._kayit_formu).pack()
        self.bind("<Return>", lambda _: self._giris())
        self.e_kadi.focus_set()

    def _giris(self) -> None:
        try:
            self.token = self._kimlik.giris_yap(self.e_kadi.get(), self.e_parola.get())
        except IsKuraliHatasi as hata:
            self.e_parola.delete(0, tk.END)
            self._mesaj_goster(str(hata))
            return
        self.destroy()

    # ----------------------------------------------------------------- KAYIT
    def _kayit_formu(self) -> None:
        self._temizle()
        self.unbind("<Return>")
        self._mesaj_goster("")
        tk.Label(self.govde, text="Kayıt Ol", bg="white",
                 font=("Segoe UI", 15, "bold")).pack(anchor="w")
        self.k_ad = self._alan("Ad soyad")
        self.k_kadi = self._alan("Kullanıcı adı")
        self.k_parola = self._alan(f"Parola (en az {config.PAROLA_MIN_UZUNLUK} karakter, harf ve rakam)", gizli=True)
        self.k_tekrar = self._alan("Parola tekrar", gizli=True)

        roller = [Rol.KURUM, Rol.DEPO]
        if self._kimlik.ilk_kurulum_mu():          # sistemde hiç kullanıcı yoksa
            roller.insert(0, Rol.YONETICI)
        self._rol_haritasi = {r.value: r for r in roller}
        satir = tk.Frame(self.govde, bg="white")
        satir.pack(fill=tk.X, pady=(10, 0))
        tk.Label(satir, text="Rol", bg="white", fg="#37474f", font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w")
        tk.Label(satir, text="Depo (Depo rolü için)", bg="white", fg="#37474f",
                 font=("Segoe UI", 9)).grid(row=0, column=1, sticky="w", padx=(10, 0))
        self.k_rol = ttk.Combobox(satir, values=list(self._rol_haritasi), state="readonly", width=12)
        self.k_rol.current(0)
        self.k_rol.grid(row=1, column=0, sticky="w")
        self._depolar = {ad: depo_id for depo_id, ad in self._kimlik.depo_secenekleri()}
        self.k_depo = ttk.Combobox(satir, values=list(self._depolar), state="readonly", width=26)
        self.k_depo.grid(row=1, column=1, sticky="w", padx=(10, 0))

        ttk.Button(self.govde, text="Kaydı Tamamla", command=self._kayit).pack(fill=tk.X, pady=(16, 6), ipady=4)
        tk.Button(self.govde, text="Girişe dön", relief=tk.FLAT, bd=0, bg="white",
                  fg="#1565c0", cursor="hand2", command=self._giris_formu).pack()

    def _kayit(self) -> None:
        try:
            kullanici = self._kimlik.kayit_ol(
                self.k_kadi.get(), self.k_ad.get(), self.k_parola.get(), self.k_tekrar.get(),
                self._rol_haritasi[self.k_rol.get()], self._depolar.get(self.k_depo.get()),
            )
        except IsKuraliHatasi as hata:
            self._mesaj_goster(str(hata))
            return
        self._giris_formu()
        self.e_kadi.insert(0, kullanici.kullanici_adi)
        self.e_parola.focus_set()
        self._mesaj_goster(f"Kayıt başarılı ({kullanici.rol.value}). Şimdi giriş yapabilirsiniz.", hata=False)

    # ------------------------------------------------------------------ akış
    def calistir(self) -> Optional[str]:
        """Pencereyi gösterir; giriş başarılıysa token, kapatılırsa None döner."""
        self.mainloop()
        return self.token
