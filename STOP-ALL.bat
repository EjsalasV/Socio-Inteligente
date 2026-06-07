@echo off
setlocal

REM ==========================================
REM Cierra solo los servicios locales de Socio AI
REM ==========================================

title Socio AI - Detener Servicios

echo.
echo ============================================
echo  Cerrando servicios de Socio AI...
echo ============================================
echo.

REM start-local.bat abre ventanas con estos titulos.
REM /T mata tambien los procesos hijos de cada ventana.
echo [1/3] Cerrando Backend de Socio AI...
taskkill /FI "WINDOWTITLE eq SocioAI Backend*" /T /F 2>nul

echo [2/3] Cerrando Frontend de Socio AI...
taskkill /FI "WINDOWTITLE eq SocioAI Frontend*" /T /F 2>nul

echo [3/3] Cerrando utilidades opcionales de Socio AI...
taskkill /FI "WINDOWTITLE eq SocioAI*" /T /F 2>nul

echo.
echo ============================================
echo  Servicios locales de Socio AI cerrados
echo ============================================
echo.
timeout /t 2 /nobreak >nul

endlocal
