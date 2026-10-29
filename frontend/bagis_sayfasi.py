"""Sunum katmanı - Bağış Girişi sayfası (Hafta 7).

İki sekme:
  1) Yeni Bağış     : bağışçı (mevcut ya da yeni), depo, kalemler (malzeme, miktar, son kullanma)
  2) Bağış Geçmişi  : kaydedilen bağışlar ve seçilen bağışın kalemleri

Doğrulamanın tamamı BagisServisi'ndedir (B1-B8). Sayfa kalemleri yalnızca listeler;
"Bağışı Kaydet"e basıldığında servis hepsini kontrol eder, hata varsa hangi kalemde
olduğunu söyler ve hiçbir şey kaydedilmez.
"""

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable

from backend.models import Kullanici
from backend.services.bagis_servisi import BAGISCI_TURLERI, BagisServisi, KalemGirdisi

from frontend.ortak import ServisCagirici, bilgi, sayi_yaz, tablo, tarih_yaz

YENI_BAGISCI = "— Yeni bağışçı ekle —"


class BagisSayfasi(tk.Frame):
    def __init__(self, ust: tk.Widget, servis: BagisServisi, token: str, kullanici: Kullanici,
                 oturum_bitti: Callable[[str], None], durum_yaz: Callable[[str], None]) -> None:
        super().__init__(ust, bg="white")
        self._servis = servis
        self._token = token
        self._durum_yaz = durum_yaz
        self._cagir = ServisCagirici(self, token, oturum_bitti)
        self._kalemler: list[tuple[int, str, str, str, str]] = []   # (malzeme_id, ad, miktar, birim, skt)

        tk.Label(self, text="Bağış Girişi", bg="white",
                 font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=24, pady=(18, 4))
        self.defter = ttk.Notebook(self)
        self.defter.pack(fill=tk.BOTH, expand=True, padx=24, pady=(4, 12))
        self._yeni_bagis_sekmesi()
        self._gecmis_sekmesi()
        self.defter.bind("<<NotebookTabChanged>>", lambda _: self._gecmisi_doldur())

    # ------------------------------------------------------------ yeni bağış
    def _yeni_bagis_sekmesi(self) -> None:
        s = tk.Frame(self.defter, bg="white", padx=10, pady=8)
        self.defter.add(s, text="Yeni Bağış")
        bilgi(s, "Bağış kaydedilince her kalem seçilen depoya stok girişi olarak eklenir ve hareket "
                 "geçmişine \"Bağış #no\" açıklamasıyla düşer. Gıda ürünlerinde son kullanma tarihi zorunludur.")

        ust = tk.Frame(s, bg="white")
        ust.pack(fill=tk.X)
        depolar = self._cagir(self._servis.depolar) or []
        self._depo_id = {d.ad: d.id for d in depolar}
        tk.Label(ust, text="Depo", bg="white").grid(row=0, column=0, sticky="w")
        self.c_depo = ttk.Combobox(ust, values=list(self._depo_id), state="readonly", width=32)
        if depolar:
            self.c_depo.current(0)
        if len(depolar) == 1:
            self.c_depo.configure(state="disabled")
        self.c_depo.grid(row=1, column=0, sticky="w", padx=(0, 16))
        tk.Label(ust, text="Bağışçı", bg="white").grid(row=0, column=1, sticky="w")
        self.c_bagisci = ttk.Combobox(ust, state="readonly", width=34)
        self.c_bagisci.grid(row=1, column=1, sticky="w", padx=(0, 16))
        self.c_bagisci.bind("<<ComboboxSelected>>", lambda _: self._yeni_bagisci_alanlari())
        tk.Label(ust, text="Açıklama (isteğe bağlı)", bg="white").grid(row=0, column=2, sticky="w")
        self.e_aciklama = ttk.Entry(ust, width=30)
        self.e_aciklama.grid(row=1, column=2, sticky="w")

        self.f_yeni = tk.LabelFrame(s, text="Yeni bağışçı (KVKK: yalnızca gerekli bilgi)", bg="white",
                                    fg="#546e7a", padx=8, pady=6)
        alanlar = (("Ad / kurum adı", 28), ("Tür", 12), ("Telefon (isteğe bağlı)", 18), ("E-posta (isteğe bağlı)", 24))
        self.y_alan = []
        for sutun, (etiket, genislik) in enumerate(alanlar):
            tk.Label(self.f_yeni, text=etiket, bg="white").grid(row=0, column=sutun, sticky="w")
            if etiket == "Tür":
                w = ttk.Combobox(self.f_yeni, values=BAGISCI_TURLERI, state="readonly", width=genislik)
                w.current(0)
            else:
                w = ttk.Entry(self.f_yeni, width=genislik)
            w.grid(row=1, column=sutun, sticky="w", padx=(0, 10))
            self.y_alan.append(w)
        self._bagiscilari_doldur()

        kalem = tk.LabelFrame(s, text="Kalem ekle", bg="white", fg="#546e7a", padx=8, pady=6)
        kalem.pack(fill=tk.X, pady=(10, 6))
        malzemeler = self._cagir(self._servis.malzemeler) or []
        self._malzeme = {m.ad: m for m in malzemeler}
        tk.Label(kalem, text="Malzeme", bg="white").grid(row=0, column=0, sticky="w")
        self.c_malzeme = ttk.Combobox(kalem, values=list(self._malzeme), state="readonly", width=28)
        self.c_malzeme.grid(row=1, column=0, padx=(0, 10))
        self.c_malzeme.bind("<<ComboboxSelected>>", lambda _: self.l_birim.configure(
            text=self._malzeme[self.c_malzeme.get()].birim))
        tk.Label(kalem, text="Miktar", bg="white").grid(row=0, column=1, sticky="w")
        self.e_miktar = ttk.Entry(kalem, width=10)
        self.e_miktar.grid(row=1, column=1)
        self.l_birim = tk.Label(kalem, text="", bg="white", fg="#546e7a", width=6, anchor="w")
        self.l_birim.grid(row=1, column=2, padx=(4, 10))
        tk.Label(kalem, text="Son kullanma (GG.AA.YYYY)", bg="white").grid(row=0, column=3, sticky="w")
        self.e_skt = ttk.Entry(kalem, width=14)
        self.e_skt.grid(row=1, column=3, padx=(0, 10))
        ttk.Button(kalem, text="+ Kalem Ekle", command=self._kalem_ekle).grid(row=1, column=4)
        self.e_skt.bind("<Return>", lambda _: self._kalem_ekle())

        self.t_kalem = tablo(s, (("no", "#", 40, "center"), ("malzeme", "Malzeme", 240), ("miktar", "Miktar", 90, "e"),
                                 ("birim", "Birim", 70), ("skt", "Son kullanma", 120, "center")), yukseklik=6)
        alt = tk.Frame(s, bg="white")
        alt.pack(fill=tk.X, pady=(8, 0))
        ttk.Button(alt, text="Seçili Kalemi Çıkar", command=self._kalem_cikar).pack(side=tk.LEFT)
        ttk.Button(alt, text="Formu Temizle", command=self._temizle).pack(side=tk.LEFT, padx=8)
        ttk.Button(alt, text="Bağışı Kaydet", command=self._kaydet).pack(side=tk.RIGHT)

    def _bagiscilari_doldur(self) -> None:
        self._bagisci_id = {b.ad: b.id for b in self._cagir(self._servis.bagiscilar) or []}
        self.c_bagisci.configure(values=[YENI_BAGISCI, *self._bagisci_id])
        self.c_bagisci.set(next(iter(self._bagisci_id), YENI_BAGISCI))
        self._yeni_bagisci_alanlari()

    def _yeni_bagisci_alanlari(self) -> None:
        if self.c_bagisci.get() == YENI_BAGISCI:
            self.f_yeni.pack(fill=tk.X, pady=(10, 0), after=self.c_bagisci.master)
        else:
            self.f_yeni.pack_forget()

    def _kalem_ekle(self) -> None:
        ad = self.c_malzeme.get()
        if not ad or not self.e_miktar.get().strip():
            messagebox.showinfo("Kalem", "Malzeme seçin ve miktar yazın.", parent=self)
            return
        m = self._malzeme[ad]
        self._kalemler.append((m.id, m.ad, self.e_miktar.get().strip(), m.birim, self.e_skt.get().strip()))
        for alan in (self.e_miktar, self.e_skt):
            alan.delete(0, tk.END)
        self._kalemleri_goster()
        self.c_malzeme.focus_set()

    def _kalem_cikar(self) -> None:
        secim = self.t_kalem.selection()
        if secim:
            del self._kalemler[self.t_kalem.index(secim[0])]
            self._kalemleri_goster()

    def _kalemleri_goster(self) -> None:
        self.t_kalem.delete(*self.t_kalem.get_children())
        for i, (_, ad, miktar, birim, skt) in enumerate(self._kalemler, start=1):
            self.t_kalem.insert("", tk.END, values=(i, ad, miktar, birim, skt or "-"))

    def _temizle(self) -> None:
        self._kalemler.clear()
        self._kalemleri_goster()
        for alan in (self.e_aciklama, self.e_miktar, self.e_skt, *[a for a in self.y_alan if isinstance(a, ttk.Entry)
                                                                    and not isinstance(a, ttk.Combobox)]):
            alan.delete(0, tk.END)

    def _kaydet(self) -> None:
        kalemler = [KalemGirdisi(mid, miktar, skt or None) for mid, _, miktar, _, skt in self._kalemler]
        secili = self.c_bagisci.get()
        ek = {"bagisci_id": self._bagisci_id[secili]} if secili in self._bagisci_id else {
            "yeni_bagisci": {"ad": self.y_alan[0].get(), "tur": self.y_alan[1].get(),
                             "telefon": self.y_alan[2].get(), "eposta": self.y_alan[3].get()}}
        bagis = self._cagir(self._servis.bagis_kaydet, self._depo_id.get(self.c_depo.get(), -1), kalemler,
                            aciklama=self.e_aciklama.get(), baslik="Bağış kaydedilemedi", **ek)
        if bagis is None:
            return
        adet = len(kalemler)
        self._temizle()
        self._bagiscilari_doldur()
        self._durum_yaz(f"Bağış #{bagis.id} kaydedildi: {adet} kalem {self.c_depo.get()} stoğuna eklendi")
        messagebox.showinfo("Bağış kaydedildi", f"Bağış #{bagis.id} kaydedildi.\n{adet} kalem stoğa eklendi.",
                            parent=self)

    # ----------------------------------------------------------- geçmiş
    def _gecmis_sekmesi(self) -> None:
        s = tk.Frame(self.defter, bg="white", padx=10, pady=8)
        self.defter.add(s, text="Bağış Geçmişi")
        self.t_bagis = tablo(s, (("no", "No", 40, "center"), ("tarih", "Tarih", 115), ("bagisci", "Bağışçı", 160),
                                 ("tur", "Tür", 70), ("depo", "Depo", 170), ("kalem", "Kalem", 50, "center"),
                                 ("aciklama", "Açıklama", 130)), yukseklik=9)
        self.t_bagis.bind("<<TreeviewSelect>>", lambda _: self._detayi_doldur())
        tk.Label(s, text="Seçili bağışın kalemleri", bg="white", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(8, 4))
        self.t_detay = tablo(s, (("malzeme", "Malzeme", 220), ("kategori", "Kategori", 110), ("miktar", "Miktar", 80, "e"),
                                 ("birim", "Birim", 70), ("skt", "Son kullanma", 120, "center")), yukseklik=5)

    def _gecmisi_doldur(self) -> None:
        if self.defter.index("current") != 1:
            return
        self.t_bagis.delete(*self.t_bagis.get_children())
        for b in self._cagir(self._servis.bagis_listesi) or []:
            self.t_bagis.insert("", tk.END, iid=str(b["id"]), values=(
                b["id"], tarih_yaz(b["tarih"]), b["bagisci"], b["tur"], b["depo"], b["kalem_sayisi"], b["aciklama"]))
        self.t_detay.delete(*self.t_detay.get_children())

    def _detayi_doldur(self) -> None:
        secim = self.t_bagis.selection()
        self.t_detay.delete(*self.t_detay.get_children())
        if secim:
            for k in self._cagir(self._servis.bagis_detayi, int(secim[0])) or []:
                self.t_detay.insert("", tk.END, values=(k["malzeme"], k["kategori"], sayi_yaz(k["miktar"]),
                                                        k["birim"], tarih_yaz(k["son_kullanma_tarihi"], saat=False)))
