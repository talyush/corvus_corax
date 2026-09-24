@echo off
rem ============================================================
rem  Corvus Corax - Ollama kalici baslatma scripti (Windows)
rem  ------------------------------------------------------------
rem  Yapisi:
rem    - 11434 portu zaten LISTENING ise hicbir sey yapmaz (cikar).
rem    - Degilse ollama serve'i ayri/minimize pencere olarak baslatir.
rem  Manuel:  cift tikla veya cmd'den  scripts\ollama_start.bat
rem ============================================================
setlocal

where ollama >nul 2>nul
if errorlevel 1 goto NO_OLLAMA

rem --- Port zaten acik mi? (LISTENING kontrolu) ---
netstat -ano -p tcp 2>nul | findstr /c "11434" >nul 2>nul
if not errorlevel 1 goto ALREADY

rem --- Port kapali: serve baslat (minimize, log dosyasiyla) ---
echo [..] Ollama serve baslatiliyor  port=11434
start "CorvusOllamaServe" /min cmd /c "ollama serve > %TEMP%\ollama_serve.log 2>&1"

rem --- Bekleyip acildigini dogrula (max ~20sn) ---
set /a tries=0
:CHECK
set /a tries+=1
timeout /t 2 /nobreak >nul
netstat -ano -p tcp 2>nul | findstr /c "11434" >nul 2>nul
if not errorlevel 1 goto UP
if %tries% lss 10 goto CHECK

echo [UYARI] 20sn icinde port acilmadi. Log: %TEMP%\ollama_serve.log
exit /b 2

:ALREADY
echo [OK] Ollama zaten calisiyor  port=11434
exit /b 0

:UP
echo [OK] Ollama ayakta  http://127.0.0.1:11434
exit /b 0

:NO_OLLAMA
echo [HATA] ollama PATH'te bulunamadi. Kur: https://ollama.com/download
exit /b 1