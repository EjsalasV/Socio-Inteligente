@echo off
setlocal EnableDelayedExpansion

title Socio AI - Logs en Tiempo Real

cd /d "%~dp0"

if not exist logs (
    echo.
    echo No se encontro la carpeta "logs".
    echo El backend aun no ha generado logs.
    echo.
    pause
    exit /b 1
)

for /f "delims=" %%A in ('dir /b /od logs\socio_ai_*.log 2^>nul') do (
    set "LATEST_LOG=%%A"
)

if not defined LATEST_LOG (
    echo.
    echo No se encontro ningun archivo de log.
    echo.
    pause
    exit /b 1
)

set "LOG_FILE=logs\!LATEST_LOG!"

cls
echo.
echo ================================================
echo  Socio AI - Logs en Tiempo Real
echo ================================================
echo.
echo Archivo: !LOG_FILE!
echo.
echo Presiona Ctrl+C para salir
echo.
echo ================================================
echo.

powershell -Command "Get-Content '!LOG_FILE!' -Tail 100 -Wait"
