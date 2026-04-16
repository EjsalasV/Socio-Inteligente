@echo off
REM ==========================================
REM Cierra todos los servicios
REM ==========================================

echo.
echo Cerrando servicios...
echo.

REM Mata los procesos
taskkill /FI "WINDOWTITLE eq Backend*" /T /F 2>nul
taskkill /FI "WINDOWTITLE eq Frontend*" /T /F 2>nul
taskkill /FI "WINDOWTITLE eq Desktop*" /T /F 2>nul

REM También mata los procesos específicos
taskkill /IM python.exe /F 2>nul
taskkill /IM node.exe /F 2>nul
taskkill /IM electron.exe /F 2>nul

echo ✓ Servicios detenidos
timeout /t 2 /nobreak
