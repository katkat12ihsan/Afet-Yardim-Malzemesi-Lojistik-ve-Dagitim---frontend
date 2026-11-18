"""Sunum katmanı - Rota / Dağıtım Planı sayfası (Hafta 9: harita/rota API).

Üstte dağıtımlar (mesafe/süre önbellekten; liste açılırken servise istek gitmez).
Bir dağıtım seçilince RotaServisi.dagitim_rotasi çağrılır:
  * harita servisinden (ya da önbellekten) karayolu mesafesi, süresi ve rota çizgisi,
  * servis yoksa / hata verirse kuş uçuşu tahmin ve NEDEN tahmin gösterildiği (turuncu).
Rota, harita karosu indirmeden Canvas üzerine çizilir: enlem/boylam -> piksel.

Durum düğmeleri (Yola Çıkar / Teslim Edildi / İptal) EslestirmeServisi'ni çağırır;
kurallar (E7 geçişleri, stok düşümü) backend'dedir.
"""

import math
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Optional

from backend.models import DagitimDurumu, Kullanici
from backend.services.eslestirme_servisi import EslestirmeServisi
from backend.services.rota_servisi import RotaBilgisi, RotaServisi, sure_yaz

from frontend.ihtiyac_sayfasi import DURUM_RENGI
from frontend.ortak import ServisCagirici, bilgi, sayi_yaz, tablo, tarih_yaz

TUVAL_G, TUVAL_Y, KENAR = 430, 200, 30
RENK_ROTA, RENK_TAHMIN = "#1565c0", "#ef6c00"


def km_yaz(km: Optional[float]) -> str:
    return "-" if km is None else f"{sayi_yaz(km)} km"


def piksele_cevir(noktalar, genislik: int, yukseklik: int, kenar: int):
    """(enlem, boylam) listesi -> (x, y) piksel listesi; oran korunur, kuzey yukarıda.

    Küçük bir bölgede (bir il) eşdikdörtgen izdüşüm yeterli: boylam farkı cos(enlem)
    ile kısaltılır, yoksa doğu-batı yönü olduğundan geniş görünür.
    """
    enlemler = [e for e, _ in noktalar]
    orta = math.cos(math.radians(sum(enlemler) / len(enlemler)))
    xs = [b * orta for _, b in noktalar]
    ys = enlemler
    gx, gy = (max(xs) - min(xs)) or 1e-9, (max(ys) - min(ys)) or 1e-9
    olcek = min((genislik - 2 * kenar) / gx, (yukseklik - 2 * kenar) / gy)
    ox = (genislik - gx * olcek) / 2
    oy = (yukseklik - gy * olcek) / 2
    return [(ox + (x - min(xs)) * olcek, yukseklik - (oy + (y - min(ys)) * olcek)) for x, y in zip(xs, ys)]


class RotaSayfasi(tk.Frame):
    def __init__(self, ust: tk.Widget, rota_servisi: RotaServisi, eslestirme_servisi: EslestirmeServisi,
                 token: str, kullanici: Kullanici, oturum_bitti: Callable[[str], None],
                 durum_yaz: Callable[[str], None]) -> None:
        super().__init__(ust, bg="white")
        self._rota = rota_servisi
        self._eslestirme = eslestirme_servisi
        self._durum_yaz = durum_yaz
        self._cagir = ServisCagirici(self, token, oturum_bitti)
        self.son_rota: Optional[RotaBilgisi] = None

        tk.Label(self, text="Rota / Dağıtım Planı", bg="white",
                 font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=24, pady=(18, 2))
        durum = rota_servisi.servis_durumu()
        self.l_servis = tk.Label(self, text=durum, bg="white", font=("Segoe UI", 9), justify=tk.LEFT,
                                 wraplength=760, fg="#2e7d32" if "tanımlı değil" not in durum else RENK_TAHMIN)
        self.l_servis.pack(anchor="w", padx=24)

        govde = tk.Frame(self, bg="white")
        govde.pack(fill=tk.BOTH, expand=True, padx=24, pady=(4, 6))
        bilgi(govde, "Bir dağıtım seçin: karayolu mesafesi, süresi ve rotası gösterilir. "
                     "Planlandı → Yola Çıkar (stok bu anda düşer) → Teslim Edildi.")
        self.t_dagitim = tablo(govde, (
            ("no", "No", 35, "center"), ("durum", "Durum", 90), ("depo", "Depo", 145),
            ("nokta", "İhtiyaç noktası", 150), ("kalemler", "Kalemler", 120),
            ("plan", "Planlanan", 85, "center"), ("mesafe", "Mesafe", 70, "e"), ("sure", "Süre", 75, "e")),
            yukseklik=4)
        for d, renk in DURUM_RENGI.items():
            self.t_dagitim.tag_configure(d, foreground=renk)
        self.t_dagitim.bind("<<TreeviewSelect>>", lambda _: self.rotayi_goster())

        dugmeler = tk.Frame(govde, bg="white")
        dugmeler.pack(fill=tk.X, pady=(6, 4))
        ttk.Button(dugmeler, text="Yeniden Hesapla", command=lambda: self.rotayi_goster(yeniden=True)
                   ).pack(side=tk.LEFT)
        for metin, yeni in (("İptal Et", DagitimDurumu.IPTAL), ("Teslim Edildi", DagitimDurumu.TESLIM_EDILDI),
                            ("Yola Çıkar", DagitimDurumu.YOLDA)):
            ttk.Button(dugmeler, text=metin, command=lambda y=yeni: self._durum_degistir(y)
                       ).pack(side=tk.RIGHT, padx=(6, 0))

        alt = tk.Frame(govde, bg="white")
        alt.pack(fill=tk.BOTH, expand=True)
        self.tuval = tk.Canvas(alt, width=TUVAL_G, height=TUVAL_Y, bg="#f5f7f8",
                               highlightthickness=1, highlightbackground="#cfd8dc")
        self.tuval.pack(side=tk.LEFT, anchor="n")
        ayrinti = tk.Frame(alt, bg="white", padx=14)
        ayrinti.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, anchor="n")
        self.l_baslik = tk.Label(ayrinti, bg="white", font=("Segoe UI", 11, "bold"), justify=tk.LEFT,
                                 wraplength=300, anchor="w")
        self.l_baslik.pack(anchor="w")
        self.l_olcu = tk.Label(ayrinti, bg="white", font=("Segoe UI", 20, "bold"), fg=RENK_ROTA)
        self.l_olcu.pack(anchor="w", pady=(6, 0))
        self.l_kaynak = tk.Label(ayrinti, bg="white", fg="#546e7a", font=("Segoe UI", 9))
        self.l_kaynak.pack(anchor="w")
        self.l_uyari = tk.Label(ayrinti, bg="white", fg=RENK_TAHMIN, font=("Segoe UI", 9),
                                justify=tk.LEFT, wraplength=300)
        self.l_uyari.pack(anchor="w", pady=(8, 0))
        self._bos_tuval("Rotayı görmek için yukarıdan bir dağıtım seçin.")
        self.yenile()

    # -------------------------------------------------------------- liste
    def yenile(self) -> None:
        secili = self.t_dagitim.selection()
        self.t_dagitim.delete(*self.t_dagitim.get_children())
        for r in self._cagir(self._rota.rota_listesi) or []:
            self.t_dagitim.insert("", tk.END, iid=str(r.dagitim_id), tags=(r.durum,), values=(
                r.dagitim_id, r.durum, r.depo, r.nokta, r.kalemler, tarih_yaz(r.planlanan_tarih, kisa=True),
                km_yaz(r.mesafe_km), sure_yaz(r.sure_dk)))
        if secili and self.t_dagitim.exists(secili[0]):
            self.t_dagitim.selection_set(secili[0])

    def _secili(self) -> Optional[int]:
        secim = self.t_dagitim.selection()
        return int(secim[0]) if secim else None

    # --------------------------------------------------------------- rota
    def rotayi_goster(self, yeniden: bool = False) -> None:
        dagitim_id = self._secili()
        if dagitim_id is None:
            if yeniden:
                messagebox.showinfo("Dağıtım seçin", "Önce bir dağıtım seçin.", parent=self)
            return
        self.configure(cursor="watch")                     # servis birkaç saniye sürebilir
        self.update_idletasks()
        try:
            rota = self._cagir(self._rota.dagitim_rotasi, dagitim_id, yeniden_sor=yeniden,
                               baslik="Rota hesaplanamadı")
        finally:
            self.configure(cursor="")
        if rota is None:
            return
        self.son_rota = rota
        renk = RENK_TAHMIN if rota.tahmini else RENK_ROTA
        self.l_baslik.configure(text=f"#{rota.dagitim_id}  {rota.depo}\n→ {rota.nokta}")
        self.l_olcu.configure(text=f"{km_yaz(rota.mesafe_km)}  ·  {sure_yaz(rota.sure_dk)}", fg=renk)
        self.l_kaynak.configure(text=f"Kaynak: {rota.kaynak}")
        self.l_uyari.configure(text=rota.uyari)
        self._ciz(rota)
        if not rota.tahmini:                                # tablodaki mesafe/süre güncellensin
            self.t_dagitim.set(str(dagitim_id), "mesafe", km_yaz(rota.mesafe_km))
            self.t_dagitim.set(str(dagitim_id), "sure", sure_yaz(rota.sure_dk))
        self._durum_yaz(f"Rota #{rota.dagitim_id}: {km_yaz(rota.mesafe_km)}, {sure_yaz(rota.sure_dk)} ({rota.kaynak})")

    def _bos_tuval(self, metin: str) -> None:
        self.tuval.delete("all")
        self.tuval.create_text(TUVAL_G / 2, TUVAL_Y / 2, text=metin, fill="#90a4ae", font=("Segoe UI", 9))

    def _ciz(self, rota: RotaBilgisi) -> None:
        t = self.tuval
        t.delete("all")
        noktalar = list(rota.geometri) or [rota.baslangic, rota.bitis]
        pikseller = piksele_cevir(noktalar + [rota.baslangic, rota.bitis], TUVAL_G, TUVAL_Y, KENAR)
        cizgi, (bx, by), (sx, sy) = pikseller[:-2], pikseller[-2], pikseller[-1]
        renk = RENK_TAHMIN if rota.tahmini else RENK_ROTA
        duz = [k for p in cizgi for k in p]
        if len(duz) >= 4:
            t.create_line(*duz, fill=renk, width=3, dash=(6, 4) if rota.tahmini else None,
                          capstyle=tk.ROUND, joinstyle=tk.ROUND)
        t.create_rectangle(bx - 6, by - 6, bx + 6, by + 6, fill="#2e7d32", outline="white", width=2)
        t.create_oval(sx - 7, sy - 7, sx + 7, sy + 7, fill="#c62828", outline="white", width=2)
        for x, y, ad in ((bx, by, rota.depo), (sx, sy, rota.nokta)):
            t.create_text(min(max(x, 80), TUVAL_G - 80), y + (14 if y < TUVAL_Y - 40 else -15), text=ad,
                          font=("Segoe UI", 8, "bold"), fill="#37474f")
        t.create_text(TUVAL_G - 14, 14, text="K ↑", font=("Segoe UI", 8), fill="#78909c")
        t.create_text(8, 12, anchor="w", font=("Segoe UI", 8), fill="#78909c",
                      text="■ depo   ● ihtiyaç noktası   " + ("- - - kuş uçuşu (tahmini)" if rota.tahmini
                                                             else "— karayolu rotası"))

    # -------------------------------------------------------------- durum
    def _durum_degistir(self, yeni: DagitimDurumu) -> None:
        dagitim_id = self._secili()
        if dagitim_id is None:
            messagebox.showinfo("Dağıtım seçin", "Önce bir dağıtım seçin.", parent=self)
            return
        if yeni is DagitimDurumu.IPTAL and not messagebox.askyesno(
                "Dağıtımı iptal et", f"Dağıtım #{dagitim_id} iptal edilsin mi?", parent=self):
            return
        d = self._cagir(self._eslestirme.dagitim_durumu_degistir, dagitim_id, yeni, baslik="Durum değiştirilemedi")
        if d:
            self._durum_yaz(f"Dağıtım #{d.id}: {d.durum.value}")
            self.yenile()
