"""Hafta 8 - Arayüz entegrasyon (duman) testi.

Gerçek pencereleri açar: her rol için her menü sayfası ve her sekme açılır, hata
olmamalı ve rol kuralları ekranda da doğru görünmeli. Geçici bir veritabanı kullanır;
kullanıcının gerçek veritabanına dokunmaz.

    .venv\\Scripts\\python.exe -m unittest      (frontend klasöründe)
"""

import os
import tempfile
import unittest
from unittest import mock

# Backend ayarları içe aktarılırken okunur: geçici veritabanını ÖNCE tanımla
_KLASOR = tempfile.TemporaryDirectory()
os.environ["AFET_DB_YOLU"] = os.path.join(_KLASOR.name, "arayuz_testi.db")

from tkinter import TclError, ttk  # noqa: E402

from backend import config  # noqa: E402
from backend.data.database import baglanti_ac, islem, migrasyonlari_uygula  # noqa: E402
from backend.data.ornek_veri import KULLANICILAR, ornek_kullanicilari_yukle, ornek_veri_yukle  # noqa: E402
from backend.models import Rol  # noqa: E402
from backend.services import modul_servisi  # noqa: E402
from backend.services.bagis_servisi import BagisServisi  # noqa: E402
from backend.services.envanter_servisi import EnvanterServisi  # noqa: E402
from backend.services.eslestirme_servisi import EslestirmeServisi  # noqa: E402
from backend.services.kimlik_servisi import KimlikServisi  # noqa: E402
from backend.services.ozet_servisi import OzetServisi  # noqa: E402
from backend.entegrasyon.harita_api import OrsIstemcisi  # noqa: E402
from backend.services.rota_servisi import KAYNAK_TAHMIN, RotaServisi  # noqa: E402
from backend.services.yetki import erisebilir_mi  # noqa: E402
from frontend.giris_penceresi import GirisPenceresi  # noqa: E402
from frontend.main_window import AnaPencere  # noqa: E402


def tearDownModule():
    _KLASOR.cleanup()


class ArayuzTesti(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config.PAROLA_ITERASYON = 1_000
        cls.db = baglanti_ac()
        migrasyonlari_uygula(cls.db)
        with islem(cls.db):
            ornek_veri_yukle(cls.db)
            ornek_kullanicilari_yukle(cls.db)
        cls.kimlik = KimlikServisi(cls.db)
        env = EnvanterServisi(cls.db, cls.kimlik)
        # Rota: anahtarsız istemci -> testler gerçek harita servisine gitmez (kuş uçuşu tahmin)
        cls.servisler = (OzetServisi(cls.db, cls.kimlik), env, BagisServisi(cls.db, cls.kimlik, env),
                         EslestirmeServisi(cls.db, cls.kimlik, env),
                         RotaServisi(cls.db, cls.kimlik, OrsIstemcisi("")))
        cls.parola = {k: p for k, _, p, _, _ in KULLANICILAR}

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def pencere(self, kadi):
        ozet, env, bagis, esl, rota = self.servisler
        token = self.kimlik.giris_yap(kadi, self.parola[kadi])
        w = AnaPencere(self.kimlik, ozet, env, token, bagis, esl, rota)
        def kapat():
            try:
                w.destroy()
            except TclError:          # test içinde zaten kapandıysa (ör. Çıkış Yap)
                pass
        self.addCleanup(kapat)
        return w

    def test_giris_penceresi_acilir(self):
        g = GirisPenceresi(self.kimlik)
        g.update()
        self.assertIn("Giriş", g.title())
        g.destroy()

    def test_her_rolde_her_sayfa_ve_sekme_hatasiz_acilir(self):
        for kadi, _, _, rol, _ in KULLANICILAR:
            w = self.pencere(kadi)
            for anahtar in ["panel"] + [m.anahtar for m in modul_servisi.modulleri_getir()]:
                with self.subTest(kullanici=kadi, sayfa=anahtar):
                    w.sayfa_goster(anahtar)
                    w.update()
                    icerik = w.icerik.winfo_children()
                    self.assertTrue(icerik, "sayfa boş")
                    for defter in (c for c in icerik[0].winfo_children() if isinstance(c, ttk.Notebook)):
                        for i in range(len(defter.tabs())):
                            defter.select(i)
                            w.update()
                    yetkili = anahtar == "panel" or erisebilir_mi(w.kullanici, anahtar)
                    engellendi = any(getattr(c, "cget", None) and c.winfo_class() == "Label"
                                     and c.cget("text") == "Erişim engellendi" for c in icerik)
                    self.assertEqual(engellendi, not yetkili)
            w._cikis()

    def test_menude_yetkisiz_moduller_kilitli(self):
        w = self.pencere("depo1")
        kilitli = {a for a, b in w._menu_butonlari.items() if "(kilitli)" in b.cget("text")}
        self.assertEqual(kilitli, {"ihtiyac", "dagitim", "oneri", "rapor", "kullanicilar"})

    def test_rota_sayfasi_secilen_dagitimin_rotasini_cizer(self):
        w = self.pencere("kurum1")
        w.sayfa_goster("dagitim")
        w.update()
        sayfa = w.icerik.winfo_children()[0]
        satirlar = sayfa.t_dagitim.get_children()
        self.assertGreater(len(satirlar), 0)
        self.assertIn("tanımlı değil", sayfa.l_servis.cget("text"))      # anahtarsız: uyarı görünür
        sayfa.t_dagitim.selection_set(satirlar[0])
        w.update()                                                        # <<TreeviewSelect>> -> rota
        self.assertEqual(sayfa.son_rota.dagitim_id, int(satirlar[0]))
        self.assertEqual(sayfa.son_rota.kaynak, KAYNAK_TAHMIN)
        self.assertIn("km", sayfa.l_olcu.cget("text"))
        self.assertIn("Kuş uçuşu tahmin", sayfa.l_uyari.cget("text"))
        self.assertTrue(sayfa.tuval.find_all())                           # rota çizildi

    def test_panelde_modul_durumlari_gorunur(self):
        w = self.pencere("yonetici")
        w.update()
        tablo = next(c for c in w.icerik.winfo_children() if isinstance(c, ttk.Treeview))
        durumlar = {tablo.item(i, "text"): tablo.set(i, "durum") for i in tablo.get_children()}
        self.assertEqual(durumlar["Envanter Yönetimi"], modul_servisi.HAZIR)
        self.assertEqual(durumlar["Rota / Dağıtım Planı"], modul_servisi.HAZIR)       # Hafta 9


    def test_parola_sifirlama_ve_ilk_giriste_yeni_parola(self):
        """Yönetici sıfırlar -> geçici parola bir kez görünür -> kullanıcı girişte kendi parolasını belirler."""
        self.kimlik.kayit_ol("unutkan", "Unutkan Kişi", "Eski12345", "Eski12345", Rol.KURUM)
        w = self.pencere("yonetici")
        w.sayfa_goster("kullanicilar")
        w.update()
        sayfa = w.icerik.winfo_children()[0]
        satir = next(i for i in sayfa.t_kullanici.get_children() if sayfa.t_kullanici.set(i, "kadi") == "unutkan")
        sayfa.t_kullanici.selection_set(satir)
        with mock.patch("frontend.kullanicilar_sayfasi.messagebox.askyesno", return_value=True):
            sayfa._parola_sifirla()
        gecici = sayfa.e_gecici.get()
        sayfa.e_gecici.winfo_toplevel().destroy()
        satir = next(i for i in sayfa.t_kullanici.get_children() if sayfa.t_kullanici.set(i, "kadi") == "unutkan")
        self.assertEqual(sayfa.t_kullanici.set(satir, "durum"), "parola sıfırlandı")
        self.assertEqual(sayfa.t_sifirlama.set(sayfa.t_sifirlama.get_children()[0], "kadi"), "unutkan")

        g = GirisPenceresi(self.kimlik)

        def kapat():
            try:
                g.destroy()
            except TclError:          # başarılı girişte pencere kendini kapatır
                pass
        self.addCleanup(kapat)
        g.e_kadi.insert(0, "unutkan")
        g.e_parola.insert(0, gecici)
        g._giris()                                   # oturum açılmaz, yeni parola formu gelir
        self.assertIsNone(g.token)
        g.y_parola.insert(0, "Yeni12345")
        g.y_tekrar.insert(0, "Yeni12345")
        kaydet = next(c for c in g.govde.winfo_children()
                      if c.winfo_class() == "TButton" and "Kaydet" in c.cget("text"))
        kaydet.invoke()
        self.assertEqual(self.kimlik.oturum_dogrula(g.token).kullanici_adi, "unutkan")


if __name__ == "__main__":
    unittest.main()
