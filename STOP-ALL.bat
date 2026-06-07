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

echo [1/3] Cerrando Backend de Socio AI...
powershell -NoProfile -Command ^
  "$targets = Get-Process | Where-Object { $_.MainWindowTitle -like 'SocioAI Backend*' }; " ^
  "if ($targets) { $targets | Stop-Process -Force }"

echo [2/3] Cerrando Frontend de Socio AI...
powershell -NoProfile -Command ^
  "$targets = Get-Process | Where-Object { $_.MainWindowTitle -like 'SocioAI Frontend*' }; " ^
  "if ($targets) { $targets | Stop-Process -Force }"

echo [3/3] Cerrando otras ventanas opcionales de Socio AI...
powershell -NoProfile -Command ^
  "$targets = Get-Process | Where-Object { $_.MainWindowTitle -like 'SocioAI*' }; " ^
  "if ($targets) { $targets | Stop-Process -Force }"

echo.
echo ============================================
echo  Servicios locales de Socio AI cerrados
echo ============================================
echo.
timeout /t 2 /nobreak >nul

endlocal
