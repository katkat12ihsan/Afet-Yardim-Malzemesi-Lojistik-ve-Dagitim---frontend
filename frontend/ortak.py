"""Sayfaların ortak kullandığı küçük arayüz yardımcıları (Hafta 7)."""

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Optional

from backend.services.hatalar import IsKuraliHatasi, OturumGecersiz

ONCELIK_ADI = {1: "Düşük", 2: "Orta", 3: "Yüksek", 4: "Kritik"}


def sayi_yaz(deger: Optional[float]) -> str:
    """1200.0 -> '1200', 12.5 -> '12,5' (Türkçe ondalık virgül); None -> '-'."""
    if deger is None:
        return "-"
    if deger == int(deger):
        return str(int(deger))
    return f"{deger:.3f}".rstrip("0").rstrip(".").replace(".", ",")


def tarih_yaz(iso: Optional[str], saat: bool = True, kisa: bool = False) -> str:
    """'2026-10-09T14:30:00' -> '09.10.2026 14:30' (kisa=True: '09.10 14:30')."""
    if not iso:
        return "-"
    gun = f"{iso[8:10]}.{iso[5:7]}" + ("" if kisa else f".{iso[0:4]}")
    return f"{gun} {iso[11:16]}" if saat and len(iso) > 10 else gun


def tablo(ust: tk.Widget, kolonlar, yukseklik: int = 10, sec: str = "browse") -> ttk.Treeview:
    """Kaydırma çubuklu tablo. kolonlar: (anahtar, başlık, genişlik[, hiza])"""
    cerceve = tk.Frame(ust, bg="white")
    cerceve.pack(fill=tk.BOTH, expand=True)
    t = ttk.Treeview(cerceve, columns=[k[0] for k in kolonlar], show="headings",
                     height=yukseklik, selectmode=sec)
    for k in kolonlar:
        anahtar, baslik, genislik = k[:3]
        t.heading(anahtar, text=baslik)
        t.column(anahtar, width=genislik, anchor=k[3] if len(k) > 3 else "w")
    kaydirma = ttk.Scrollbar(cerceve, orient=tk.VERTICAL, command=t.yview)
    t.configure(yscrollcommand=kaydirma.set)
    t.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    kaydirma.pack(side=tk.RIGHT, fill=tk.Y)
    return t


def bilgi(ust: tk.Widget, metin: str, renk: str = "#546e7a") -> tk.Label:
    etiket = tk.Label(ust, text=metin, bg="white", fg=renk, font=("Segoe UI", 9),
                      justify=tk.LEFT, wraplength=760)
    etiket.pack(anchor="w", pady=(0, 6))
    return etiket


class ServisCagirici:
    """Servis çağrısı: iş kuralı hatasını kullanıcıya gösterir, oturum bittiyse çıkışa yönlendirir."""

    def __init__(self, ust: tk.Widget, token: str, oturum_bitti: Callable[[str], None]) -> None:
        self._ust, self._token, self._oturum_bitti = ust, token, oturum_bitti

    def __call__(self, islev: Callable, *arg, baslik: str = "İşlem yapılamadı", **kw):
        try:
            return islev(self._token, *arg, **kw)
        except OturumGecersiz as hata:
            self._oturum_bitti(str(hata))
        except IsKuraliHatasi as hata:
            messagebox.showerror(baslik, str(hata), parent=self._ust)
        return None
