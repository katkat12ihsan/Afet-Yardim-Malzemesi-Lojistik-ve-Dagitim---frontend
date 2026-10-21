@echo off
rem Uygulamayi baslatir. Cift tiklamak yeterli.
rem Ilk calistirmada sanal ortami (.venv) kurar, backend paketini GitHub'dan yukler
rem ve ornek veritabanini olusturur. Sonraki calistirmalarda dogrudan acar.
chcp 65001 >nul
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" goto calistir

echo Ilk calistirma: sanal ortam kuruluyor (internet ve Git gerekir)...
py -3 -m venv .venv 2>nul || python -m venv .venv || goto hata
".venv\Scripts\python.exe" -m pip install -q --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt || goto hata
".venv\Scripts\python.exe" -m backend.data.kurulum --ornek-veri || goto hata

:calistir
start "" ".venv\Scripts\pythonw.exe" main.py
exit /b 0

:hata
echo.
echo Kurulum basarisiz. Internet baglantisini, Python ve Git kurulumunu kontrol edin.
pause
exit /b 1
