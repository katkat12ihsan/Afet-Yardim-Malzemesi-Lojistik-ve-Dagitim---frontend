"""Uygulamanın başlangıç noktası:  python main.py

Backend'i hazırlar (bağlantı + migration), servisleri oluşturup frontend'e verir.
"""

from backend.data.database import baglanti_ac, migrasyonlari_uygula
from backend.services.ozet_servisi import OzetServisi
from frontend.main_window import AnaPencere


def main() -> None:
    baglanti = baglanti_ac()
    try:
        migrasyonlari_uygula(baglanti)  # şema güncel değilse günceller
        pencere = AnaPencere(OzetServisi(baglanti))
        pencere.mainloop()
    finally:
        baglanti.close()


if __name__ == "__main__":
    main()
