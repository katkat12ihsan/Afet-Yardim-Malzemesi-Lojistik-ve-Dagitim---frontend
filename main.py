"""Uygulamanın başlangıç noktası.

Çalıştırma: baslat.bat dosyasına çift tıklayın (ya da: .venv/Scripts/python.exe main.py).

Backend'i hazırlar (bağlantı + migration), servisleri oluşturup frontend'e verir.
Akış: Giriş penceresi -> (başarılı giriş) -> Ana pencere -> (Çıkış) -> Giriş penceresi ...
"""

import sys


def _backend_bulunamadi() -> None:
    """Backend paketi ayrı depodadır ve yalnızca .venv'e kuruludur. main.py başka bir
    Python ile açılırsa (çift tıklama, VS Code'da yanlış yorumlayıcı) anlaşılır uyarı ver."""
    mesaj = ("Backend paketi bulunamadı.\n\n"
             f"Bu Python ile açıldı:\n{sys.executable}\n\n"
             "Uygulamayı proje klasöründeki 'baslat.bat' dosyasına çift tıklayarak açın.\n"
             "VS Code kullanıyorsanız yorumlayıcı olarak .venv\\Scripts\\python.exe seçin.")
    print(mesaj, file=sys.stderr)
    try:
        import tkinter as tk
        from tkinter import messagebox
        kok = tk.Tk()
        kok.withdraw()
        messagebox.showerror("Afet Yardım Lojistik - başlatılamadı", mesaj)
        kok.destroy()
    except Exception:
        pass
    sys.exit(1)


try:
    from backend.data.database import baglanti_ac, migrasyonlari_uygula
    from backend.services.envanter_servisi import EnvanterServisi
    from backend.services.kimlik_servisi import KimlikServisi
    from backend.services.ozet_servisi import OzetServisi
except ModuleNotFoundError as hata:
    if not (hata.name or "").startswith("backend"):
        raise
    _backend_bulunamadi()

from frontend.giris_penceresi import GirisPenceresi
from frontend.main_window import AnaPencere


def main() -> None:
    baglanti = baglanti_ac()
    try:
        migrasyonlari_uygula(baglanti)  # şema güncel değilse günceller
        kimlik = KimlikServisi(baglanti)
        ozet = OzetServisi(baglanti, kimlik)
        envanter = EnvanterServisi(baglanti, kimlik)

        bilgi = ""
        if kimlik.ilk_kurulum_mu():
            bilgi = ("Sistemde hiç kullanıcı yok. Kayıt ol ekranından ilk Yönetici hesabını "
                     "açın ya da örnek kullanıcılar için: python -m backend.data.kurulum --ornek-veri")
        while True:
            token = GirisPenceresi(kimlik, bilgi).calistir()
            if token is None:            # giriş penceresi kapatıldı
                break
            pencere = AnaPencere(kimlik, ozet, envanter, token)
            pencere.mainloop()
            if not pencere.cikis_yapildi:  # ana pencere X ile kapatıldı
                kimlik.cikis_yap(token)
                break
            bilgi = "Çıkış yapıldı."
    finally:
        baglanti.close()


if __name__ == "__main__":
    main()
