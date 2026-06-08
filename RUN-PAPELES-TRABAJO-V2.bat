@echo off
REM Papeles-Trabajo v2 - Launcher Script
REM Abre Backend, Frontend y Desktop App

chcp 65001 >/dev/null
setlocal enabledelayedexpansion

echo.
echo ====================================================
echo  Socio AI - Papeles-Trabajo v2
echo  Iniciando Backend + Frontend + Desktop App
echo ====================================================
echo.

REM Verifica que estamos en la carpeta correcta
if not exist "backend\main.py" (
    echo ERROR: No estás en la carpeta correcta
    echo Ejecuta este .bat desde: C:\Users\echoe\Desktop\Nuevo Socio AI
    pause
    exit /b 1
)

if not exist ".env" (
    echo WARNING: .env no encontrado. Creándolo...
    pause
    exit /b 1
)

echo OK: Configuracion encontrada
echo OK: .env cargado
echo.

REM Abre las 3 terminales
echo Iniciando servicios...
echo.

echo [1/3] Abriendo Backend (FastAPI en puerto 8000)...
start "SocioAI Backend" cmd /k "title SocioAI Backend && python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000"

timeout /t 2 /nobreak

echo [2/3] Abriendo Frontend (Next.js en puerto 3000)...
start "SocioAI Frontend" cmd /k "title SocioAI Frontend && cd frontend && npm run dev"

timeout /t 2 /nobreak

echo [3/3] Abriendo Desktop App (Electron)...
start "SocioAI Desktop" cmd /k "title SocioAI Desktop && cd desktop-sync-manager && npm run dev"

echo.
echo ====================================================
echo.
echo OK: Todos los servicios en inicio...
echo.
echo URLs:
echo   - Backend:     http://127.0.0.1:8000
echo   - Frontend:    http://localhost:3000
echo   - Desktop:     Electron window
echo.
echo Para detener todo, ejecuta: STOP-ALL.bat
echo.
pause
