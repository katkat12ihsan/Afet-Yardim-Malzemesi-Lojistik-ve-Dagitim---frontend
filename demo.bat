@echo off
rem Vize/sinif demosu: GERCEK veritabanina dokunmadan, her seferinde temiz ornek veriyle acar.
rem Demo veritabani: %%USERPROFILE%%\AfetLojistik\demo.db  (gercek veri: afet_lojistik.db, degismez)
rem Test hesaplari: yonetici, kurum1, depo1 (parolalar backend deposunda backend/data/ornek_veri.py)
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Sanal ortam yok. Once baslat.bat dosyasini calistirin.
    pause
    exit /b 1
)
set "AFET_DB_YOLU=%USERPROFILE%\AfetLojistik\demo.db"
echo Demo veritabani sifirlaniyor: %AFET_DB_YOLU%
".venv\Scripts\python.exe" -m backend.data.kurulum --sifirla --ornek-veri || goto hata
start "" ".venv\Scripts\pythonw.exe" main.py
exit /b 0

:hata
echo Demo veritabani hazirlanamadi.
pause
exit /b 1
