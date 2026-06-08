@echo off
setlocal

REM ==========================================
REM Cierra solo las ventanas locales de Socio AI
REM ==========================================

title Socio AI - Detener Servicios

echo.
echo ============================================
echo  Cerrando servicios de Socio AI...
echo ============================================
echo.

echo [1/3] Cerrando Backend de Socio AI...
taskkill /F /FI "IMAGENAME eq cmd.exe" /FI "WINDOWTITLE eq SocioAI Backend" >nul 2>nul
taskkill /F /FI "IMAGENAME eq cmd.exe" /FI "WINDOWTITLE eq SocioAI - Backend" >nul 2>nul
taskkill /F /FI "IMAGENAME eq cmd.exe" /FI "WINDOWTITLE eq Backend - Uvicorn 8000" >nul 2>nul
taskkill /F /FI "IMAGENAME eq cmd.exe" /FI "WINDOWTITLE eq Backend - FastAPI 8000" >nul 2>nul

echo [2/3] Cerrando Frontend de Socio AI...
taskkill /F /FI "IMAGENAME eq cmd.exe" /FI "WINDOWTITLE eq SocioAI Frontend" >nul 2>nul
taskkill /F /FI "IMAGENAME eq cmd.exe" /FI "WINDOWTITLE eq SocioAI - Frontend" >nul 2>nul
taskkill /F /FI "IMAGENAME eq cmd.exe" /FI "WINDOWTITLE eq Frontend - Next.js 3000" >nul 2>nul
taskkill /F /FI "IMAGENAME eq cmd.exe" /FI "WINDOWTITLE eq Frontend - Next 3000" >nul 2>nul

echo [3/3] Cerrando otras ventanas opcionales de Socio AI...
taskkill /F /FI "IMAGENAME eq cmd.exe" /FI "WINDOWTITLE eq Desktop App - Electron" >nul 2>nul
taskkill /F /FI "IMAGENAME eq cmd.exe" /FI "WINDOWTITLE eq SocioAI Desktop" >nul 2>nul

echo [4/4] Cerrando procesos por comando asociado al proyecto...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$patterns = @('Nuevo Socio AI','backend.main:app','uvicorn backend.main:app','npm run dev','desktop-sync-manager'); " ^
  "$procs = Get-CimInstance Win32_Process | Where-Object { $cmd = [string]$_.CommandLine; $patterns | Where-Object { $cmd -like ('*' + $_ + '*') } }; " ^
  "if ($procs) { $procs | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue } }"

echo.
echo ============================================
echo  Servicios locales de Socio AI cerrados
echo ============================================
echo.
timeout /t 2 /nobreak >nul

endlocal
