"""Sunum katmanı - İhtiyaç Eşleştirme sayfası (Hafta 7).

Üç sekme:
  1) Talepler ve Eşleştirme : öncelik sıralı talepler; seçilen talep için en yakın
                              depodan başlayan öneri, eksik miktar uyarısı, dağıtımı planla
  2) Dağıtımlar             : durum güncelleme (Yola çıkar / Teslim edildi / İptal)
  3) Stok–Talep Dengesi     : malzeme bazında fazla / eksik görünümü

Kurallar (E1-E9: fazla gönderim yok, rezerve düşülmüş uygun stok, durum geçişleri ...)
EslestirmeServisi'ndedir; sayfa yalnızca servisi çağırır ve hatayı gösterir.
"""

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from typing import Callable, Optional

from backend.models import DagitimDurumu, Kullanici
from backend.services.eslestirme_servisi import EslestirmeOnerisi, EslestirmeServisi, OneriSatiri, TalepBilgisi
from backend.services.hatalar import IsKuraliHatasi, OturumGecersiz

from frontend.ortak import ONCELIK_ADI, ServisCagirici, bilgi, sayi_yaz, tablo, tarih_yaz

DURUM_RENGI = {"Bekliyor": "#c62828", "Kısmen karşılandı": "#ef6c00", "Karşılandı": "#2e7d32", "İptal": "#90a4ae",
               "Planlandı": "#1565c0", "Yolda": "#ef6c00", "Teslim edildi": "#2e7d32",
               "Eksik": "#c62828", "Fazla": "#1565c0", "Talep yok": "#607d8b", "Dengede": "#2e7d32"}


class IhtiyacSayfasi(tk.Frame):
    def __init__(self, ust: tk.Widget, servis: EslestirmeServisi, token: str, kullanici: Kullanici,
                 oturum_bitti: Callable[[str], None], durum_yaz: Callable[[str], None]) -> None:
        super().__init__(ust, bg="white")
        self._servis = servis
        self._token = token
        self._oturum_bitti = oturum_bitti
        self._durum_yaz = durum_yaz
        self._cagir = ServisCagirici(self, token, oturum_bitti)
        self._talepler: dict[str, TalepBilgisi] = {}
        self._oneri: Optional[EslestirmeOnerisi] = None
        self._atamalar: dict[int, float] = {}            # depo_id -> miktar (kullanıcı değiştirebilir)

        tk.Label(self, text="İhtiyaç Eşleştirme", bg="white",
                 font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=24, pady=(18, 4))
        self.defter = ttk.Notebook(self)
        self.defter.pack(fill=tk.BOTH, expand=True, padx=24, pady=(4, 12))
        self._talep_sekmesi()
        self._dagitim_sekmesi()
        self._denge_sekmesi()
        self.defter.bind("<<NotebookTabChanged>>", lambda _: self.yenile())
        self.yenile()

    @staticmethod
    def _renkler(t: ttk.Treeview) -> None:
        for durum, renk in DURUM_RENGI.items():
            t.tag_configure(durum, foreground=renk)

    # ------------------------------------------------------- talepler
    def _talep_sekmesi(self) -> None:
        s = tk.Frame(self.defter, bg="white", padx=10, pady=8)
        self.defter.add(s, text="Talepler ve Eşleştirme")
        ust = tk.Frame(s, bg="white")
        ust.pack(fill=tk.X)
        bilgi(ust, "Talepler ihtiyaç noktasının önceliğine (Kritik önce), sonra talep tarihine göre sıralıdır. "
                   "Bir talep seçin: kalan miktar için uygun stoğu olan depolar en yakından başlayarak önerilir.")
        self.v_kapali = tk.BooleanVar(value=False)
        satir = tk.Frame(s, bg="white")
        satir.pack(fill=tk.X)
        ttk.Checkbutton(satir, text="Karşılanan ve iptal edilen talepleri de göster", variable=self.v_kapali,
                        command=self._talepleri_doldur).pack(side=tk.LEFT)
        ttk.Button(satir, text="Talebi İptal Et", command=self._talep_iptal).pack(side=tk.RIGHT)
        ttk.Button(satir, text="+ Yeni Talep", command=self._yeni_talep).pack(side=tk.RIGHT, padx=6)

        self.t_talep = tablo(s, (("no", "#", 35, "center"), ("oncelik", "Öncelik", 60, "center"),
                                 ("nokta", "İhtiyaç noktası", 150), ("malzeme", "Malzeme", 125),
                                 ("talep", "Talep", 55, "e"), ("karsilanan", "Karşılanan", 70, "e"),
                                 ("kalan", "Kalan", 55, "e"), ("birim", "Birim", 50), ("durum", "Durum", 105)),
                             yukseklik=7)
        self._renkler(self.t_talep)
        self.t_talep.bind("<<TreeviewSelect>>", lambda _: self._oneriyi_goster())

        self.f_oneri = tk.LabelFrame(s, text="Eşleştirme önerisi", bg="white", fg="#546e7a", padx=8, pady=6)
        self.f_oneri.pack(fill=tk.BOTH, expand=True, pady=(8, 0))
        self.l_oneri = tk.Label(self.f_oneri, text="Bir talep seçin.", bg="white", anchor="w", justify=tk.LEFT)
        self.l_oneri.pack(fill=tk.X)
        self.t_oneri = tablo(self.f_oneri, (("depo", "Depo", 230), ("km", "Mesafe (km)", 90, "e"),
                                            ("uygun", "Uygun stok", 90, "e"), ("miktar", "Gönderilecek", 100, "e")),
                             yukseklik=3)
        self.t_oneri.bind("<Double-1>", lambda _: self._miktar_degistir())
        self.l_eksik = tk.Label(self.f_oneri, text="", bg="white", fg="#c62828", anchor="w", justify=tk.LEFT)
        self.l_eksik.pack(fill=tk.X, pady=(4, 0))
        alt = tk.Frame(self.f_oneri, bg="white")
        alt.pack(fill=tk.X, pady=(4, 0))
        ttk.Button(alt, text="Miktarı Değiştir", command=self._miktar_degistir).pack(side=tk.LEFT)
        tk.Label(alt, text="Araç plakası (isteğe bağlı)", bg="white").pack(side=tk.LEFT, padx=(16, 4))
        self.e_plaka = ttk.Entry(alt, width=14)
        self.e_plaka.pack(side=tk.LEFT)
        ttk.Button(alt, text="Dağıtımı Planla", command=self._planla).pack(side=tk.RIGHT)

    def _talepleri_doldur(self) -> None:
        secili = self.t_talep.selection()
        self.t_talep.delete(*self.t_talep.get_children())
        self._talepler = {}
        for t in self._cagir(self._servis.talepler, sadece_acik=not self.v_kapali.get()) or []:
            iid = str(t.id)
            self.t_talep.insert("", tk.END, iid=iid, tags=(t.durum,), values=(
                t.id, ONCELIK_ADI.get(t.oncelik, t.oncelik), t.nokta, t.malzeme, sayi_yaz(t.miktar),
                sayi_yaz(t.karsilanan), sayi_yaz(t.kalan), t.birim, t.durum))
            self._talepler[iid] = t
        if secili and secili[0] in self._talepler:
            self.t_talep.selection_set(secili[0])
        else:
            self._oneri = None
            self._oneri_tablosu()

    def _oneriyi_goster(self) -> None:
        secim = self.t_talep.selection()
        if not secim:
            return
        self._oneri = self._cagir(self._servis.oneri, int(secim[0]))
        self._atamalar = {s.depo_id: s.miktar for s in self._oneri.satirlar} if self._oneri else {}
        self._oneri_tablosu()

    def _oneri_tablosu(self) -> None:
        self.t_oneri.delete(*self.t_oneri.get_children())
        o = self._oneri
        if o is None:
            self.l_oneri.configure(text="Bir talep seçin.")
            self.l_eksik.configure(text="")
            return
        t = o.talep
        self.l_oneri.configure(text=f"#{t.id}  {t.nokta} — {t.malzeme}:  talep {sayi_yaz(t.miktar)}, "
                                    f"karşılanan {sayi_yaz(t.karsilanan)}, kalan {sayi_yaz(t.kalan)} {t.birim}")
        for a in o.adaylar:
            self.t_oneri.insert("", tk.END, iid=str(a.depo_id), values=(
                a.depo, sayi_yaz(a.mesafe_km), sayi_yaz(a.uygun_stok), sayi_yaz(self._atamalar.get(a.depo_id, 0))))
        toplam = sum(self._atamalar.values())
        eksik = max(round(t.kalan - toplam, 3), 0)
        if t.kalan == 0:
            self.l_eksik.configure(text="Bu talep kapalı; eşleştirilecek kalan miktar yok.", fg="#2e7d32")
        elif not o.adaylar:
            self.l_eksik.configure(text=f"Eksik: hiçbir depoda uygun stok yok; {sayi_yaz(t.kalan)} {t.birim} "
                                        "karşılanamıyor.", fg="#c62828")
        elif eksik:
            self.l_eksik.configure(text=f"Eksik: depolardaki uygun stok yetmiyor; {sayi_yaz(eksik)} {t.birim} "
                                        "açıkta kalacak (talep 'Kısmen karşılandı' olur).", fg="#c62828")
        else:
            self.l_eksik.configure(text="Kalan miktarın tamamı karşılanabiliyor.", fg="#2e7d32")

    def _miktar_degistir(self) -> None:
        secim = self.t_oneri.selection()
        if not self._oneri or not secim:
            messagebox.showinfo("Depo seçin", "Öneri tablosundan bir depo seçin.", parent=self)
            return
        depo_id = int(secim[0])
        aday: OneriSatiri = next(a for a in self._oneri.adaylar if a.depo_id == depo_id)
        deger = simpledialog.askstring("Gönderilecek miktar",
                                       f"{aday.depo}\nUygun stok: {sayi_yaz(aday.uygun_stok)} {self._oneri.talep.birim}\n"
                                       "Gönderilecek miktar (0 = bu depodan gönderme):",
                                       initialvalue=sayi_yaz(self._atamalar.get(depo_id, 0)), parent=self)
        if deger is None:
            return
        try:
            self._atamalar[depo_id] = float(deger.strip().replace(",", ".") or 0)
        except ValueError:
            messagebox.showerror("Miktar", "Sayı girin.", parent=self)
            return
        self._oneri_tablosu()

    def _planla(self) -> None:
        if not self._oneri:
            messagebox.showinfo("Talep seçin", "Önce bir talep seçin.", parent=self)
            return
        atamalar = [(d, m) for d, m in self._atamalar.items() if m > 0]
        olusan = self._cagir(self._servis.eslestir, self._oneri.talep.id, atamalar, self.e_plaka.get(),
                             baslik="Dağıtım planlanamadı")
        if olusan:
            self.e_plaka.delete(0, tk.END)
            self._durum_yaz(f"Talep #{self._oneri.talep.id}: {len(olusan)} dağıtım planlandı "
                            f"(#{', #'.join(str(d.id) for d in olusan)})")
            self._talepleri_doldur()
            self._oneriyi_goster()

    def _yeni_talep(self) -> None:
        noktalar = {n.ad: n.id for n in self._cagir(self._servis.ihtiyac_noktalari) or []}
        malzemeler = {m.ad: m for m in self._cagir(self._servis.malzemeler) or []}
        p = tk.Toplevel(self)
        p.title("Yeni Talep")
        p.resizable(False, False)
        p.transient(self.winfo_toplevel())
        p.configure(bg="white", padx=20, pady=16)
        p.geometry(f"+{self.winfo_rootx() + 220}+{self.winfo_rooty() + 90}")
        tk.Label(p, text="İhtiyaç noktası", bg="white").pack(anchor="w")
        c_nokta = ttk.Combobox(p, values=list(noktalar), state="readonly", width=34)
        c_nokta.pack(anchor="w", pady=(2, 8))
        tk.Label(p, text="Malzeme", bg="white").pack(anchor="w")
        c_malzeme = ttk.Combobox(p, values=list(malzemeler), state="readonly", width=34)
        c_malzeme.pack(anchor="w", pady=(2, 8))
        tk.Label(p, text="Miktar", bg="white").pack(anchor="w")
        e_miktar = ttk.Entry(p, width=16)
        e_miktar.pack(anchor="w", pady=(2, 8))
        l_hata = tk.Label(p, bg="white", fg="#c62828", wraplength=300, justify=tk.LEFT)
        l_hata.pack(anchor="w")

        def kaydet() -> None:
            if not c_nokta.get() or not c_malzeme.get():
                l_hata.configure(text="İhtiyaç noktası ve malzeme seçin.")
                return
            try:
                t = self._servis.talep_ekle(self._token, noktalar[c_nokta.get()],
                                            malzemeler[c_malzeme.get()].id, e_miktar.get())
            except OturumGecersiz as hata:
                p.destroy()
                self._oturum_bitti(str(hata))
                return
            except IsKuraliHatasi as hata:      # pencere açık kalır, kullanıcı düzeltir
                l_hata.configure(text=str(hata))
                return
            p.destroy()
            self._durum_yaz(f"Talep #{t.id} eklendi")
            self._talepleri_doldur()

        satir = tk.Frame(p, bg="white")
        satir.pack(fill=tk.X, pady=(8, 0))
        ttk.Button(satir, text="Kaydet", command=kaydet).pack(side=tk.RIGHT)
        ttk.Button(satir, text="Vazgeç", command=p.destroy).pack(side=tk.RIGHT, padx=8)
        p.grab_set()

    def _talep_iptal(self) -> None:
        secim = self.t_talep.selection()
        if not secim:
            messagebox.showinfo("Talep seçin", "Önce bir talep seçin.", parent=self)
            return
        t = self._talepler[secim[0]]
        if not messagebox.askyesno("Talebi iptal et", f"#{t.id} {t.nokta} — {t.malzeme} talebi iptal edilsin mi?",
                                   parent=self):
            return
        try:
            self._servis.talep_iptal(self._token, t.id)
        except OturumGecersiz as hata:
            self._oturum_bitti(str(hata))
            return
        except IsKuraliHatasi as hata:
            messagebox.showerror("Talep iptal edilemedi", str(hata), parent=self)
            return
        self._durum_yaz(f"Talep #{t.id} iptal edildi")
        self._talepleri_doldur()

    # ------------------------------------------------------- dağıtımlar
    def _dagitim_sekmesi(self) -> None:
        s = tk.Frame(self.defter, bg="white", padx=10, pady=8)
        self.defter.add(s, text="Dağıtımlar")
        bilgi(s, "Planlandı → Yola Çıkar (stok depodan bu anda düşer) → Teslim Edildi. Planlanmış ya da yoldaki "
                 "dağıtım iptal edilebilir; yoldan dönen malzeme depoya iade girer. Talep durumu otomatik güncellenir.")
        self.t_dagitim = tablo(s, (("no", "No", 35, "center"), ("durum", "Durum", 80), ("depo", "Depo", 125),
                                   ("nokta", "İhtiyaç noktası", 125), ("kalemler", "Kalemler", 140),
                                   ("plan", "Planlanan", 80, "center"), ("teslim", "Teslim", 80, "center"),
                                   ("plaka", "Plaka", 70)),
                               yukseklik=14)
        self._renkler(self.t_dagitim)
        alt = tk.Frame(s, bg="white")
        alt.pack(fill=tk.X, pady=(8, 0))
        for metin, durum in (("Yola Çıkar", DagitimDurumu.YOLDA), ("Teslim Edildi", DagitimDurumu.TESLIM_EDILDI),
                             ("İptal Et", DagitimDurumu.IPTAL)):
            ttk.Button(alt, text=metin, command=lambda d=durum: self._dagitim_durumu(d)).pack(side=tk.LEFT, padx=(0, 6))

    def _dagitimlari_doldur(self) -> None:
        self.t_dagitim.delete(*self.t_dagitim.get_children())
        for d in self._cagir(self._servis.dagitim_listesi) or []:
            kalemler = (d["kalemler"] or "").replace(".0 ", " ")
            self.t_dagitim.insert("", tk.END, iid=str(d["id"]), tags=(d["durum"],), values=(
                d["id"], d["durum"], d["depo"], d["nokta"], kalemler, tarih_yaz(d["planlanan_tarih"], kisa=True),
                tarih_yaz(d["teslim_tarihi"], kisa=True), d["arac_plaka"] or "-"))

    def _dagitim_durumu(self, yeni: DagitimDurumu) -> None:
        secim = self.t_dagitim.selection()
        if not secim:
            messagebox.showinfo("Dağıtım seçin", "Önce bir dağıtım seçin.", parent=self)
            return
        if yeni is DagitimDurumu.IPTAL and not messagebox.askyesno(
                "Dağıtımı iptal et", f"Dağıtım #{secim[0]} iptal edilsin mi?", parent=self):
            return
        d = self._cagir(self._servis.dagitim_durumu_degistir, int(secim[0]), yeni, baslik="Durum değiştirilemedi")
        if d:
            self._durum_yaz(f"Dağıtım #{d.id}: {d.durum.value}")
            self._dagitimlari_doldur()

    # ------------------------------------------------------- denge
    def _denge_sekmesi(self) -> None:
        s = tk.Frame(self.defter, bg="white", padx=10, pady=8)
        self.defter.add(s, text="Stok–Talep Dengesi")
        bilgi(s, "Fazla/eksik görünümü: tüm depolardaki uygun stok (planlanmış dağıtımlar düşülmüş) ile açık "
                 "taleplerin kalanı karşılaştırılır. Eksik olanlar önce listelenir; bağış toplarken bu listeye bakın.")
        self.t_denge = tablo(s, (("malzeme", "Malzeme", 220), ("birim", "Birim", 70), ("uygun", "Uygun stok", 100, "e"),
                                 ("talep", "Açık talep", 100, "e"), ("fark", "Fark", 90, "e"), ("durum", "Durum", 100)),
                             yukseklik=14)
        self._renkler(self.t_denge)

    def _dengeyi_doldur(self) -> None:
        self.t_denge.delete(*self.t_denge.get_children())
        for d in self._cagir(self._servis.stok_talep_dengesi) or []:
            fark = ("+" if d.fark > 0 else "") + sayi_yaz(d.fark)
            self.t_denge.insert("", tk.END, tags=(d.durum,), values=(
                d.malzeme, d.birim, sayi_yaz(d.uygun_stok), sayi_yaz(d.acik_talep), fark, d.durum))

    # ------------------------------------------------------------- genel
    def yenile(self) -> None:
        if not self.winfo_exists():
            return
        sekme = self.defter.index("current")
        (self._talepleri_doldur, self._dagitimlari_doldur, self._dengeyi_doldur)[sekme]()
