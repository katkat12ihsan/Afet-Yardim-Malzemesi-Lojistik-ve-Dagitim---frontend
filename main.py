"""Uygulamanın başlangıç noktası.

Çalıştırma: python main.py, VS Code'da Run (▶) ya da baslat.bat - hepsi aynı sonucu verir.

Backend'i hazırlar (bağlantı + migration), servisleri oluşturup frontend'e verir.
Akış: Giriş penceresi -> (başarılı giriş) -> Ana pencere -> (Çıkış) -> Giriş penceresi ...

Neden aşağıdaki başlatma kontrolü var?
Backend ayrı bir depodadır ve bu projenin .venv sanal ortamına paket olarak kuruludur.
main.py başka bir Python ile açılırsa (genel Python, VS Code'da farklı yorumlayıcı)
backend bulunamaz. Bu durumda main.py kendini .venv'deki Python ile yeniden başlatır.
"""

import os
import subprocess
import sys
from pathlib import Path

PROJE_KLASORU = Path(__file__).resolve().parent
VENV_PYTHON = PROJE_KLASORU / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def _venv_ile_yeniden_baslat() -> None:
    """Backend yalnızca .venv'de kurulu: .venv varsa ve şu an onunla çalışmıyorsak, onunla aç."""
    if VENV_PYTHON.exists() and Path(sys.executable).resolve() != VENV_PYTHON.resolve():
        sys.exit(subprocess.call([str(VENV_PYTHON), str(PROJE_KLASORU / "main.py"), *sys.argv[1:]],
                                 cwd=PROJE_KLASORU))


def _backend_bulunamadi() -> None:
    """.venv hiç kurulmamışsa (yeni bilgisayar, ilk klonlama) ne yapılacağını söyle."""
    mesaj = ("Backend paketi bulunamadı; projenin sanal ortamı (.venv) henüz kurulmamış.\n\n"
             "İlk kurulum için proje klasöründeki 'baslat.bat' dosyasına bir kez çift tıklayın.\n"
             "Sonrasında main.py'yi istediğiniz yoldan (VS Code, python main.py) açabilirsiniz.")
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
    from backend.services.bagis_servisi import BagisServisi
    from backend.services.envanter_servisi import EnvanterServisi
    from backend.services.eslestirme_servisi import EslestirmeServisi
    from backend.services.kimlik_servisi import KimlikServisi
    from backend.services.ozet_servisi import OzetServisi
except ModuleNotFoundError as hata:
    if not (hata.name or "").startswith("backend"):
        raise
    _venv_ile_yeniden_baslat()   # .venv varsa buradan geri dönmez
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
        bagis = BagisServisi(baglanti, kimlik, envanter)
        eslestirme = EslestirmeServisi(baglanti, kimlik, envanter)

        bilgi = ""
        if kimlik.ilk_kurulum_mu():
            bilgi = ("Sistemde hiç kullanıcı yok. Kayıt ol ekranından ilk Yönetici hesabını "
                     "açın ya da örnek kullanıcılar için: python -m backend.data.kurulum --ornek-veri")
        while True:
            token = GirisPenceresi(kimlik, bilgi).calistir()
            if token is None:            # giriş penceresi kapatıldı
                break
            pencere = AnaPencere(kimlik, ozet, envanter, token, bagis, eslestirme)
            pencere.mainloop()
            if not pencere.cikis_yapildi:  # ana pencere X ile kapatıldı
                kimlik.cikis_yap(token)
                break
            bilgi = "Çıkış yapıldı."
    finally:
        baglanti.close()


if __name__ == "__main__":
    main()
