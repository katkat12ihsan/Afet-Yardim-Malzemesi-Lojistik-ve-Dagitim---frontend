"""Uygulamanın başlangıç noktası:  python main.py

Backend'i hazırlar (bağlantı + migration), servisleri oluşturup frontend'e verir.
Akış: Giriş penceresi -> (başarılı giriş) -> Ana pencere -> (Çıkış) -> Giriş penceresi ...
"""

from backend.data.database import baglanti_ac, migrasyonlari_uygula
from backend.services.kimlik_servisi import KimlikServisi
from backend.services.ozet_servisi import OzetServisi
from frontend.giris_penceresi import GirisPenceresi
from frontend.main_window import AnaPencere


def main() -> None:
    baglanti = baglanti_ac()
    try:
        migrasyonlari_uygula(baglanti)  # şema güncel değilse günceller
        kimlik = KimlikServisi(baglanti)
        ozet = OzetServisi(baglanti, kimlik)

        bilgi = ""
        if kimlik.ilk_kurulum_mu():
            bilgi = ("Sistemde hiç kullanıcı yok. Kayıt ol ekranından ilk Yönetici hesabını "
                     "açın ya da örnek kullanıcılar için: python -m backend.data.kurulum --ornek-veri")
        while True:
            token = GirisPenceresi(kimlik, bilgi).calistir()
            if token is None:            # giriş penceresi kapatıldı
                break
            pencere = AnaPencere(kimlik, ozet, token)
            pencere.mainloop()
            if not pencere.cikis_yapildi:  # ana pencere X ile kapatıldı
                kimlik.cikis_yap(token)
                break
            bilgi = "Çıkış yapıldı."
    finally:
        baglanti.close()


if __name__ == "__main__":
    main()
