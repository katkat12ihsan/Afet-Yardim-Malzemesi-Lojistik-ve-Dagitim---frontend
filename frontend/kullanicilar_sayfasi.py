"""Sunum katmanı - Kullanıcılar sayfası (yalnızca Yönetici).

Hafta 5: kullanıcı listesi.
Rol düzenleme: seçili kullanıcının rolünü (Depo rolünde bağlı deposunu da)
değiştirme penceresi ve son rol değişiklikleri tablosu.

Kurallar (kendi rolünü değiştirememe, Depo için depo zorunluluğu, açık
oturumların kapanması, geçmiş kaydı) backend'deki KimlikServisi.rol_degistir
içindedir; bu sayfa yalnızca servisi çağırır ve hatayı gösterir.
"""

import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk
from typing import Callable, Optional

from backend.models import Kullanici, Rol
from backend.services.hatalar import IsKuraliHatasi, OturumGecersiz
from backend.services.kimlik_servisi import KimlikServisi


class KullanicilarSayfasi(tk.Frame):
    def __init__(self, ust: tk.Widget, kimlik: KimlikServisi, token: str, kullanici: Kullanici,
                 oturum_bitti: Callable[[str], None], durum_yaz: Callable[[str], None]) -> None:
        super().__init__(ust, bg="white")
        self._kimlik = kimlik
        self._token = token
        self._kullanici = kullanici
        self._oturum_bitti = oturum_bitti
        self._durum_yaz = durum_yaz
        self._kayitlar: dict[str, Kullanici] = {}
        self._depolar = dict(kimlik.depo_secenekleri())          # id -> ad

        tk.Label(self, text="Kullanıcılar", bg="white",
                 font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=24, pady=(18, 2))
        tk.Label(self, bg="white", fg="#555", font=("Segoe UI", 10), justify=tk.LEFT, wraplength=720,
                 text="Sistemdeki hesaplar ve rolleri. Parolalar hash'li saklanır, burada gösterilmez. "
                      "Rolü değiştirmek için bir kullanıcı seçip \"Rolü Düzenle\"ye basın "
                      "(ya da satıra çift tıklayın).").pack(anchor="w", padx=24)

        self.t_kullanici = self._tablo((
            ("kadi", "Kullanıcı adı", 120), ("ad", "Ad soyad", 190), ("rol", "Rol", 85),
            ("depo", "Depo", 200), ("son", "Son giriş", 125), ("durum", "Durum", 70)), yukseklik=8)
        self.t_kullanici.tag_configure("ben", foreground="#1565c0")
        self.t_kullanici.bind("<Double-1>", lambda _: self._rol_penceresi())

        dugmeler = tk.Frame(self, bg="white")
        dugmeler.pack(fill=tk.X, padx=24, pady=(6, 0))
        ttk.Button(dugmeler, text="Rolü Düzenle", command=self._rol_penceresi).pack(side=tk.LEFT)
        tk.Label(dugmeler, bg="white", fg="#607d8b", font=("Segoe UI", 9),
                 text="Mavi satır: sizin hesabınız (kendi rolünüzü başka bir Yönetici değiştirebilir)."
                 ).pack(side=tk.LEFT, padx=12)

        tk.Label(self, text="Son rol değişiklikleri", bg="white",
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=24, pady=(14, 4))
        self.t_gecmis = self._tablo((
            ("tarih", "Tarih", 120), ("kadi", "Kullanıcı", 110), ("eski", "Eski rol", 150),
            ("yeni", "Yeni rol", 150), ("degistiren", "Değiştiren", 110)), yukseklik=5)
        self.yenile()

    # ------------------------------------------------------------ yardımcı
    def _tablo(self, kolonlar, yukseklik: int) -> ttk.Treeview:
        cerceve = tk.Frame(self, bg="white")
        cerceve.pack(fill=tk.BOTH, expand=True, padx=24, pady=(8, 0))
        tablo = ttk.Treeview(cerceve, columns=[k[0] for k in kolonlar], show="headings",
                             height=yukseklik, selectmode="browse")
        for anahtar, baslik, genislik in kolonlar:
            tablo.heading(anahtar, text=baslik)
            tablo.column(anahtar, width=genislik)
        kaydirma = ttk.Scrollbar(cerceve, orient=tk.VERTICAL, command=tablo.yview)
        tablo.configure(yscrollcommand=kaydirma.set)
        tablo.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        kaydirma.pack(side=tk.RIGHT, fill=tk.Y)
        return tablo

    def _rol_metni(self, rol: str, depo: Optional[str]) -> str:
        return f"{rol} ({depo})" if depo else rol

    def _calistir(self, islev: Callable, *arg):
        try:
            return islev(self._token, *arg)
        except OturumGecersiz as hata:
            self._oturum_bitti(str(hata))
        except IsKuraliHatasi as hata:
            messagebox.showerror("İşlem yapılamadı", str(hata), parent=self)
        return None

    # -------------------------------------------------------------- liste
    def yenile(self) -> None:
        kullanicilar = self._calistir(self._kimlik.kullanicilari_listele)
        if kullanicilar is None:
            return
        self.t_kullanici.delete(*self.t_kullanici.get_children())
        self._kayitlar = {}
        for k in kullanicilar:
            kilitli = k.kilitli_bitis is not None and k.kilitli_bitis > datetime.now()
            durum = "kilitli" if kilitli else ("aktif" if k.aktif else "pasif")
            iid = self.t_kullanici.insert("", tk.END, tags=("ben",) if k.id == self._kullanici.id else (), values=(
                k.kullanici_adi, k.ad_soyad, k.rol.value, self._depolar.get(k.depo_id, "-"),
                k.son_giris.strftime("%d.%m.%Y %H:%M") if k.son_giris else "-", durum))
            self._kayitlar[iid] = k

        self.t_gecmis.delete(*self.t_gecmis.get_children())
        for g in self._calistir(self._kimlik.rol_gecmisi, 20) or []:
            self.t_gecmis.insert("", tk.END, values=(
                g["tarih"].replace("T", " ")[:16], g["kullanici_adi"],
                self._rol_metni(g["eski_rol"], g["eski_depo"]),
                self._rol_metni(g["yeni_rol"], g["yeni_depo"]), g["degistiren"]))

    # ----------------------------------------------------- rol penceresi
    def _rol_penceresi(self) -> None:
        secim = self.t_kullanici.selection()
        if not secim:
            messagebox.showinfo("Kullanıcı seçin", "Önce listeden bir kullanıcı seçin.", parent=self)
            return
        hedef = self._kayitlar[secim[0]]
        if hedef.id == self._kullanici.id:
            messagebox.showinfo("Kendi hesabınız",
                                "Kendi rolünüzü değiştiremezsiniz; bunu başka bir Yönetici yapmalı.",
                                parent=self)
            return

        p = tk.Toplevel(self)
        p.title("Rolü Düzenle")
        p.resizable(False, False)
        p.transient(self.winfo_toplevel())
        p.configure(bg="white", padx=20, pady=16)
        p.geometry(f"+{self.winfo_rootx() + 220}+{self.winfo_rooty() + 90}")
        tk.Label(p, text=f"{hedef.ad_soyad}", bg="white", font=("Segoe UI", 13, "bold")).pack(anchor="w")
        tk.Label(p, bg="white", fg="#546e7a",
                 text=f"{hedef.kullanici_adi}  ·  şu anki rol: "
                      f"{self._rol_metni(hedef.rol.value, self._depolar.get(hedef.depo_id))}"
                 ).pack(anchor="w", pady=(0, 10))

        roller = {r.value: r for r in Rol}
        tk.Label(p, text="Yeni rol", bg="white").pack(anchor="w")
        c_rol = ttk.Combobox(p, values=list(roller), state="readonly", width=30)
        c_rol.set(hedef.rol.value)
        c_rol.pack(anchor="w", pady=(2, 8))
        depo_adlari = {ad: depo_id for depo_id, ad in self._depolar.items()}
        tk.Label(p, text="Depo (yalnızca Depo rolü için)", bg="white").pack(anchor="w")
        c_depo = ttk.Combobox(p, values=list(depo_adlari), state="readonly", width=30)
        c_depo.set(self._depolar.get(hedef.depo_id, ""))
        c_depo.pack(anchor="w", pady=(2, 8))

        def depo_kutusu(_=None) -> None:
            c_depo.configure(state="readonly" if c_rol.get() == Rol.DEPO.value else "disabled")
        c_rol.bind("<<ComboboxSelected>>", depo_kutusu)
        depo_kutusu()

        tk.Label(p, bg="white", fg="#607d8b", font=("Segoe UI", 9), wraplength=290, justify=tk.LEFT,
                 text="Kaydettiğinizde kullanıcının açık oturumları kapanır; yeni rol bir sonraki "
                      "girişinde geçerli olur. Değişiklik geçmişe kaydedilir.").pack(anchor="w")
        l_hata = tk.Label(p, bg="white", fg="#c62828", wraplength=290, justify=tk.LEFT)
        l_hata.pack(anchor="w", pady=(6, 0))

        def kaydet() -> None:
            yeni_rol = roller[c_rol.get()]
            depo_id = depo_adlari.get(c_depo.get()) if yeni_rol is Rol.DEPO else None
            try:
                k = self._kimlik.rol_degistir(self._token, hedef.id, yeni_rol, depo_id)
            except OturumGecersiz as hata:
                p.destroy()
                self._oturum_bitti(str(hata))
                return
            except IsKuraliHatasi as hata:          # pencere açık kalır, kullanıcı düzeltir
                l_hata.configure(text=str(hata))
                return
            p.destroy()
            self._durum_yaz(f"Rol değişti: {k.kullanici_adi} → "
                            f"{self._rol_metni(k.rol.value, self._depolar.get(k.depo_id))}")
            self.yenile()

        satir = tk.Frame(p, bg="white")
        satir.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(satir, text="Kaydet", command=kaydet).pack(side=tk.RIGHT)
        ttk.Button(satir, text="Vazgeç", command=p.destroy).pack(side=tk.RIGHT, padx=8)
        p.bind("<Return>", lambda _: kaydet())
        p.grab_set()
