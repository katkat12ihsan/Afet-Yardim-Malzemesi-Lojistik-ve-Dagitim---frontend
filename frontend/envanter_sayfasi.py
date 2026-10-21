"""Sunum katmanı - Envanter Yönetimi sayfası (Hafta 6).

Üç sekme:
  1) Stok Durumu      : depo seçimi, filtre, stok tablosu; giriş/çıkış/sayım/kritik seviye
  2) Hareket Geçmişi  : seçili deponun son stok hareketleri (kim, ne zaman, neden)
  3) Malzeme Tanımları: malzeme/kategori ekle-güncelle-sil (yalnızca Yönetici)

Bu dosyada iş kuralı yoktur. Tüm doğrulama (miktar, yetersiz stok, birim,
sahiplik, yetki) EnvanterServisi'ndedir; sayfa yalnızca servisi çağırır ve
servisin fırlattığı hatayı kullanıcıya gösterir.
"""

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Optional

from backend.models import Kullanici, Rol
from backend.services.envanter_servisi import GECERLI_BIRIMLER, EnvanterServisi, StokSatiri
from backend.services.hatalar import IsKuraliHatasi, OturumGecersiz

TUMU = "Tümü"


def sayi_yaz(deger: float) -> str:
    """1200.0 -> '1200', 12.5 -> '12,5' (Türkçe ondalık virgül)."""
    if deger == int(deger):
        return str(int(deger))
    return f"{deger:.3f}".rstrip("0").rstrip(".").replace(".", ",")


class EnvanterSayfasi(tk.Frame):
    def __init__(self, ust: tk.Widget, servis: EnvanterServisi, token: str, kullanici: Kullanici,
                 oturum_bitti: Callable[[str], None], durum_yaz: Callable[[str], None]) -> None:
        super().__init__(ust, bg="white")
        self._servis = servis
        self._token = token
        self._kullanici = kullanici
        self._oturum_bitti = oturum_bitti
        self._durum_yaz = durum_yaz
        self._yonetici = kullanici.rol is Rol.YONETICI
        self._satirlar: dict[str, StokSatiri] = {}

        tk.Label(self, text="Envanter Yönetimi", bg="white",
                 font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=24, pady=(18, 0))
        self._filtre_cubugu()
        defter = ttk.Notebook(self)
        defter.pack(fill=tk.BOTH, expand=True, padx=24, pady=(6, 12))
        self._stok_sekmesi(defter)
        self._hareket_sekmesi(defter)
        self._tanim_sekmesi(defter)
        defter.bind("<<NotebookTabChanged>>", lambda _: self.yenile())
        self.yenile()

    # ------------------------------------------------------------ yardımcı
    def _calistir(self, islev: Callable, *arg, **kw):
        """Servis çağrısı: iş kuralı hatasını kullanıcıya gösterir, oturum bittiyse çıkar."""
        try:
            return islev(self._token, *arg, **kw)
        except OturumGecersiz as hata:
            self._oturum_bitti(str(hata))
        except IsKuraliHatasi as hata:
            messagebox.showerror("İşlem yapılamadı", str(hata), parent=self)
        return None

    @staticmethod
    def _tablo(ust: tk.Widget, kolonlar: tuple[tuple[str, str, int, str], ...],
               yukseklik: int = 12) -> ttk.Treeview:
        cerceve = tk.Frame(ust, bg="white")
        cerceve.pack(fill=tk.BOTH, expand=True)
        tablo = ttk.Treeview(cerceve, columns=[k[0] for k in kolonlar], show="headings",
                             height=yukseklik, selectmode="browse")
        for anahtar, baslik, genislik, hiza in kolonlar:
            tablo.heading(anahtar, text=baslik)
            tablo.column(anahtar, width=genislik, anchor=hiza)
        kaydirma = ttk.Scrollbar(cerceve, orient=tk.VERTICAL, command=tablo.yview)
        tablo.configure(yscrollcommand=kaydirma.set)
        tablo.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        kaydirma.pack(side=tk.RIGHT, fill=tk.Y)
        return tablo

    # -------------------------------------------------------- filtre çubuğu
    def _filtre_cubugu(self) -> None:
        cubuk = tk.Frame(self, bg="white")
        cubuk.pack(fill=tk.X, padx=24, pady=(8, 0))
        depolar = self._calistir(self._servis.erisilebilir_depolar) or []
        self._depo_id = {d.ad: d.id for d in depolar}
        kategoriler = self._calistir(self._servis.kategoriler) or []
        self._kategori_id = {k.ad: k.id for k in kategoriler}

        tk.Label(cubuk, text="Depo", bg="white").pack(side=tk.LEFT)
        self.c_depo = ttk.Combobox(cubuk, values=list(self._depo_id), state="readonly", width=30)
        if depolar:
            self.c_depo.current(0)
        if len(depolar) == 1:                       # Depo görevlisi: yalnızca kendi deposu
            self.c_depo.configure(state="disabled")
        self.c_depo.pack(side=tk.LEFT, padx=(4, 14))
        tk.Label(cubuk, text="Kategori", bg="white").pack(side=tk.LEFT)
        self.c_kategori = ttk.Combobox(cubuk, values=[TUMU, *self._kategori_id], state="readonly", width=12)
        self.c_kategori.current(0)
        self.c_kategori.pack(side=tk.LEFT, padx=(4, 14))
        tk.Label(cubuk, text="Ara", bg="white").pack(side=tk.LEFT)
        self.e_ara = ttk.Entry(cubuk, width=16)
        self.e_ara.pack(side=tk.LEFT, padx=(4, 14))
        self.v_kritik = tk.BooleanVar(value=False)
        ttk.Checkbutton(cubuk, text="Yalnızca kritik/tükenen", variable=self.v_kritik,
                        command=self.yenile).pack(side=tk.LEFT)
        for w in (self.c_depo, self.c_kategori):
            w.bind("<<ComboboxSelected>>", lambda _: self.yenile())
        self.e_ara.bind("<KeyRelease>", lambda _: self.yenile())

    def _secili_depo(self) -> Optional[int]:
        return self._depo_id.get(self.c_depo.get())

    # --------------------------------------------------------- stok sekmesi
    def _stok_sekmesi(self, defter: ttk.Notebook) -> None:
        sekme = tk.Frame(defter, bg="white", padx=8, pady=8)
        defter.add(sekme, text="Stok Durumu")
        self.t_stok = self._tablo(sekme, (
            ("malzeme", "Malzeme", 210, "w"), ("kategori", "Kategori", 100, "w"),
            ("miktar", "Miktar", 80, "e"), ("birim", "Birim", 60, "w"),
            ("kritik", "Kritik seviye", 90, "e"), ("durum", "Durum", 80, "center")))
        self.t_stok.tag_configure("Kritik", background="#ffebee", foreground="#c62828")
        self.t_stok.tag_configure("Tükendi", background="#eceff1", foreground="#607d8b")
        self.t_stok.bind("<Double-1>", lambda _: self._hareket_penceresi("giris"))

        dugmeler = tk.Frame(sekme, bg="white")
        dugmeler.pack(fill=tk.X, pady=(8, 0))
        for metin, tur in (("+ Stok Girişi", "giris"), ("− Stok Çıkışı", "cikis"),
                           ("Sayım Düzeltmesi", "sayim"), ("Kritik Seviye", "kritik")):
            ttk.Button(dugmeler, text=metin, command=lambda t=tur: self._hareket_penceresi(t)
                       ).pack(side=tk.LEFT, padx=(0, 8))
        self.l_ozet = tk.Label(dugmeler, bg="white", fg="#455a64", font=("Segoe UI", 9))
        self.l_ozet.pack(side=tk.RIGHT)

    def _stoklari_doldur(self) -> None:
        depo_id = self._secili_depo()
        if depo_id is None:
            return
        satirlar = self._calistir(
            self._servis.stok_listesi, depo_id, self._kategori_id.get(self.c_kategori.get()),
            self.e_ara.get(), self.v_kritik.get()) or []
        self.t_stok.delete(*self.t_stok.get_children())
        self._satirlar = {}
        for s in satirlar:
            iid = self.t_stok.insert("", tk.END, tags=(s.durum,), values=(
                s.malzeme, s.kategori, sayi_yaz(s.miktar), s.birim,
                sayi_yaz(s.kritik_seviye) if s.kritik_seviye else "-", s.durum))
            self._satirlar[iid] = s
        kritik = sum(1 for s in satirlar if s.durum == "Kritik")
        tukenen = sum(1 for s in satirlar if s.durum == "Tükendi")
        self.l_ozet.configure(text=f"{len(satirlar)} malzeme · {kritik} kritik · {tukenen} tükendi")

    def _secili_stok(self) -> Optional[StokSatiri]:
        secim = self.t_stok.selection()
        if not secim:
            messagebox.showinfo("Malzeme seçin", "Önce tablodan bir malzeme seçin.", parent=self)
            return None
        return self._satirlar[secim[0]]

    def _hareket_penceresi(self, tur: str) -> None:
        satir = self._secili_stok()
        if satir is None:
            return
        depo_id = self._secili_depo()
        basliklar = {
            "giris": ("Stok Girişi", f"Giriş miktarı ({satir.birim})", self._servis.stok_girisi),
            "cikis": ("Stok Çıkışı", f"Çıkış miktarı ({satir.birim})", self._servis.stok_cikisi),
            "sayim": ("Sayım Düzeltmesi", f"Sayılan miktar ({satir.birim})", self._servis.sayim_duzeltmesi),
            "kritik": ("Kritik Seviye", f"Kritik seviye ({satir.birim})", self._servis.kritik_seviye_ayarla),
        }
        baslik, etiket, islev = basliklar[tur]

        p = tk.Toplevel(self)
        p.title(baslik)
        p.resizable(False, False)
        p.transient(self.winfo_toplevel())
        p.configure(bg="white", padx=20, pady=16)
        p.geometry(f"+{self.winfo_rootx() + 220}+{self.winfo_rooty() + 90}")   # sayfanın üzerinde aç
        tk.Label(p, text=satir.malzeme, bg="white", font=("Segoe UI", 13, "bold")).pack(anchor="w")
        tk.Label(p, text=f"{self.c_depo.get()}  ·  mevcut: {sayi_yaz(satir.miktar)} {satir.birim}",
                 bg="white", fg="#546e7a").pack(anchor="w", pady=(0, 10))
        tk.Label(p, text=etiket, bg="white").pack(anchor="w")
        e_miktar = ttk.Entry(p, width=32)
        e_miktar.pack(anchor="w", pady=(2, 8))
        e_aciklama = None
        if tur != "kritik":
            tk.Label(p, text="Açıklama" + (" (zorunlu: farkın nedeni)" if tur == "sayim" else ""),
                     bg="white").pack(anchor="w")
            e_aciklama = ttk.Entry(p, width=32)
            e_aciklama.pack(anchor="w", pady=(2, 8))
        l_hata = tk.Label(p, bg="white", fg="#c62828", wraplength=280, justify=tk.LEFT)
        l_hata.pack(anchor="w")

        def kaydet() -> None:
            arg = (depo_id, satir.malzeme_id, e_miktar.get())
            if e_aciklama is not None:
                arg += (e_aciklama.get(),)
            try:
                sonuc = islev(self._token, *arg)
            except OturumGecersiz as hata:
                p.destroy()
                self._oturum_bitti(str(hata))
                return
            except IsKuraliHatasi as hata:      # pencere açık kalır, kullanıcı düzeltir
                l_hata.configure(text=str(hata))
                return
            p.destroy()
            if sonuc is not None:
                self._durum_yaz(f"{baslik}: {satir.malzeme} {sayi_yaz(sonuc.onceki_miktar)} → "
                                f"{sayi_yaz(sonuc.sonraki_miktar)} {satir.birim}")
            else:
                self._durum_yaz(f"{baslik}: {satir.malzeme} güncellendi")
            self.yenile()

        dugmeler = tk.Frame(p, bg="white")
        dugmeler.pack(fill=tk.X, pady=(8, 0))
        ttk.Button(dugmeler, text="Kaydet", command=kaydet).pack(side=tk.RIGHT)
        ttk.Button(dugmeler, text="Vazgeç", command=p.destroy).pack(side=tk.RIGHT, padx=8)
        p.bind("<Return>", lambda _: kaydet())
        e_miktar.focus_set()
        p.grab_set()

    # ------------------------------------------------------ hareket sekmesi
    def _hareket_sekmesi(self, defter: ttk.Notebook) -> None:
        sekme = tk.Frame(defter, bg="white", padx=8, pady=8)
        defter.add(sekme, text="Hareket Geçmişi")
        tk.Label(sekme, bg="white", fg="#546e7a", font=("Segoe UI", 9),
                 text="Her giriş, çıkış ve sayım silinmeyen bir kayıt olarak tutulur. "
                      "Stok miktarı = bu hareketlerin toplamı.").pack(anchor="w", pady=(0, 6))
        self.t_hareket = self._tablo(sekme, (
            ("tarih", "Tarih", 110, "w"), ("malzeme", "Malzeme", 140, "w"), ("tur", "Tür", 60, "center"),
            ("degisim", "Değişim", 65, "e"), ("onceki", "Önceki", 60, "e"), ("sonraki", "Sonraki", 60, "e"),
            ("kullanici", "Kullanıcı", 75, "w"), ("aciklama", "Açıklama", 240, "w")), yukseklik=14)
        self.t_hareket.tag_configure("arti", foreground="#2e7d32")
        self.t_hareket.tag_configure("eksi", foreground="#c62828")

    def _hareketleri_doldur(self) -> None:
        depo_id = self._secili_depo()
        if depo_id is None:
            return
        self.t_hareket.delete(*self.t_hareket.get_children())
        for h in self._calistir(self._servis.hareket_gecmisi, depo_id) or []:
            tarih = h["tarih"].replace("T", " ")[:16]
            degisim = ("+" if h["degisim"] > 0 else "−") + sayi_yaz(abs(h["degisim"]))
            self.t_hareket.insert("", tk.END, tags=("arti" if h["degisim"] > 0 else "eksi",), values=(
                tarih, h["malzeme"], h["tur"], degisim, sayi_yaz(h["onceki_miktar"]),
                sayi_yaz(h["sonraki_miktar"]), h["kullanici"], h["aciklama"]))

    # -------------------------------------------------------- tanım sekmesi
    def _tanim_sekmesi(self, defter: ttk.Notebook) -> None:
        sekme = tk.Frame(defter, bg="white", padx=8, pady=8)
        defter.add(sekme, text="Malzeme Tanımları")
        sag = tk.Frame(sekme, bg="white")
        if self._yonetici:
            self._tanim_formu(sekme)
        else:
            tk.Label(sekme, bg="#fff3e0", fg="#e65100", padx=8, pady=4,
                     text="Malzeme ve kategori tanımlarını yalnızca Yönetici değiştirebilir.").pack(anchor="w", pady=(0, 6))
        sag.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.t_malzeme = self._tablo(sag, (
            ("ad", "Malzeme", 200, "w"), ("kategori", "Kategori", 110, "w"),
            ("birim", "Birim", 60, "w"), ("aciklama", "Açıklama", 200, "w")), yukseklik=14)
        self.t_malzeme.bind("<<TreeviewSelect>>", lambda _: self._formu_doldur())
        self._malzeme_kayitlari: dict[str, object] = {}

    def _tanim_formu(self, sekme: tk.Frame) -> None:
        form = tk.Frame(sekme, bg="white", padx=4)
        form.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 14))
        tk.Label(form, text="Malzeme", bg="white", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.f_ad = self._form_alani(form, "Ad")
        tk.Label(form, text="Kategori", bg="white").pack(anchor="w")
        self.f_kategori = ttk.Combobox(form, values=list(self._kategori_id), state="readonly", width=24)
        self.f_kategori.pack(anchor="w", pady=(0, 6))
        tk.Label(form, text="Birim", bg="white").pack(anchor="w")
        self.f_birim = ttk.Combobox(form, values=GECERLI_BIRIMLER, state="readonly", width=24)
        self.f_birim.current(0)
        self.f_birim.pack(anchor="w", pady=(0, 6))
        self.f_aciklama = self._form_alani(form, "Açıklama")
        satir = tk.Frame(form, bg="white")
        satir.pack(anchor="w", pady=(4, 14))
        ttk.Button(satir, text="Ekle", command=self._malzeme_ekle).pack(side=tk.LEFT)
        ttk.Button(satir, text="Güncelle", command=self._malzeme_guncelle).pack(side=tk.LEFT, padx=4)
        ttk.Button(satir, text="Sil", command=self._malzeme_sil).pack(side=tk.LEFT)

        tk.Label(form, text="Kategori", bg="white", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.f_yeni_kategori = self._form_alani(form, "Yeni kategori adı")
        satir = tk.Frame(form, bg="white")
        satir.pack(anchor="w")
        ttk.Button(satir, text="Kategori Ekle", command=self._kategori_ekle).pack(side=tk.LEFT)
        ttk.Button(satir, text="Seçili Kategoriyi Sil", command=self._kategori_sil).pack(side=tk.LEFT, padx=4)

    @staticmethod
    def _form_alani(form: tk.Frame, etiket: str) -> ttk.Entry:
        tk.Label(form, text=etiket, bg="white").pack(anchor="w")
        alan = ttk.Entry(form, width=27)
        alan.pack(anchor="w", pady=(0, 6))
        return alan

    def _malzemeleri_doldur(self) -> None:
        kategori_adi = {v: k for k, v in self._kategori_id.items()}
        self.t_malzeme.delete(*self.t_malzeme.get_children())
        self._malzeme_kayitlari = {}
        for m in self._calistir(self._servis.malzemeler) or []:
            iid = self.t_malzeme.insert("", tk.END, values=(
                m.ad, kategori_adi.get(m.kategori_id, "?"), m.birim, m.aciklama))
            self._malzeme_kayitlari[iid] = m

    def _formu_doldur(self) -> None:
        secim = self.t_malzeme.selection()
        if not self._yonetici or not secim:
            return
        m = self._malzeme_kayitlari[secim[0]]
        kategori_adi = {v: k for k, v in self._kategori_id.items()}
        for alan, deger in ((self.f_ad, m.ad), (self.f_aciklama, m.aciklama)):
            alan.delete(0, tk.END)
            alan.insert(0, deger)
        self.f_kategori.set(kategori_adi.get(m.kategori_id, ""))
        self.f_birim.set(m.birim)

    def _form_degerleri(self) -> tuple:
        return (self._kategori_id.get(self.f_kategori.get(), -1), self.f_ad.get(),
                self.f_birim.get(), self.f_aciklama.get())

    def _secili_malzeme(self):
        secim = self.t_malzeme.selection()
        if not secim:
            messagebox.showinfo("Malzeme seçin", "Önce listeden bir malzeme seçin.", parent=self)
            return None
        return self._malzeme_kayitlari[secim[0]]

    def _malzeme_ekle(self) -> None:
        m = self._calistir(self._servis.malzeme_ekle, *self._form_degerleri())
        if m:
            self._durum_yaz(f"Malzeme eklendi: {m.ad}")
            self.yenile()

    def _malzeme_guncelle(self) -> None:
        secili = self._secili_malzeme()
        if secili and self._calistir(self._servis.malzeme_guncelle, secili.id, *self._form_degerleri()):
            self._durum_yaz(f"Malzeme güncellendi: {self.f_ad.get()}")
            self.yenile()

    def _malzeme_sil(self) -> None:
        secili = self._secili_malzeme()
        if not secili or not messagebox.askyesno("Malzemeyi sil", f"'{secili.ad}' silinsin mi?", parent=self):
            return
        try:
            self._servis.malzeme_sil(self._token, secili.id)
        except OturumGecersiz as hata:
            self._oturum_bitti(str(hata))
            return
        except IsKuraliHatasi as hata:
            messagebox.showerror("Silinemedi", str(hata), parent=self)
            return
        self._durum_yaz(f"Malzeme silindi: {secili.ad}")
        self.yenile()

    def _kategorileri_yenile(self) -> None:
        self._kategori_id = {k.ad: k.id for k in self._calistir(self._servis.kategoriler) or []}
        self.c_kategori.configure(values=[TUMU, *self._kategori_id])
        if self._yonetici:
            self.f_kategori.configure(values=list(self._kategori_id))

    def _kategori_ekle(self) -> None:
        k = self._calistir(self._servis.kategori_ekle, self.f_yeni_kategori.get())
        if k:
            self.f_yeni_kategori.delete(0, tk.END)
            self._kategorileri_yenile()
            self._durum_yaz(f"Kategori eklendi: {k.ad}")

    def _kategori_sil(self) -> None:
        ad = self.f_kategori.get()
        if not ad:
            messagebox.showinfo("Kategori seçin", "Formdaki Kategori kutusundan silinecek kategoriyi seçin.",
                                parent=self)
            return
        if not messagebox.askyesno("Kategoriyi sil", f"'{ad}' kategorisi silinsin mi?", parent=self):
            return
        try:
            self._servis.kategori_sil(self._token, self._kategori_id[ad])
        except OturumGecersiz as hata:
            self._oturum_bitti(str(hata))
            return
        except IsKuraliHatasi as hata:
            messagebox.showerror("Silinemedi", str(hata), parent=self)
            return
        self.f_kategori.set("")
        self._kategorileri_yenile()
        self._durum_yaz(f"Kategori silindi: {ad}")

    # ------------------------------------------------------------------ genel
    def yenile(self) -> None:
        if not self.winfo_exists():
            return
        self._stoklari_doldur()
        self._hareketleri_doldur()
        self._malzemeleri_doldur()
