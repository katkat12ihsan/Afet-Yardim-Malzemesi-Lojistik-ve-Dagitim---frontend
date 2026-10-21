@echo off
rem Backend deposunda yeni hafta gonderildiginde calistirin:
rem backend paketini GitHub'daki en son surume gunceller ve veritabani semasini yukseltir.
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Sanal ortam yok. Once baslat.bat dosyasini calistirin.
    pause
    exit /b 1
)
echo Backend GitHub'dan guncelleniyor...
".venv\Scripts\python.exe" -m pip install -q --force-reinstall --no-deps -r requirements.txt || goto hata
".venv\Scripts\python.exe" -m backend.data.kurulum || goto hata
".venv\Scripts\python.exe" -m pip show afet-lojistik-backend | findstr /b "Version"
echo Guncelleme tamam.
pause
exit /b 0

:hata
echo Guncelleme basarisiz. Internet baglantisini kontrol edip tekrar deneyin.
pause
exit /b 1
