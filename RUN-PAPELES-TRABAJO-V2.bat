@echo off
REM ==========================================
REM Papeles-Trabajo v2 - Launcher
REM ==========================================
REM Este script abre las 3 aplicaciones en paralelo:
REM 1. Backend (FastAPI) en puerto 8000
REM 2. Frontend (Next.js) en puerto 3000
REM 3. Desktop App (Electron)
REM ==========================================

chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║  Socio AI - Papeles-Trabajo v2                         ║
echo ║  Iniciando Backend + Frontend + Desktop App            ║
echo ╚════════════════════════════════════════════════════════╝
echo.

REM Verifica que estamos en la carpeta correcta
if not exist "backend\main.py" (
    echo ❌ Error: No estás en la carpeta correcta
    echo Ejecuta este .bat desde: C:\Users\echoe\Desktop\Nuevo Socio AI
    pause
    exit /b 1
)

if not exist ".env" (
    echo ⚠️  .env no encontrado. Créalo manualmente.
    pause
    exit /b 1
)

echo ✓ Configuración encontrada
echo ✓ .env cargado
echo.

REM Abre las 3 terminales
echo ╔─ INICIANDO SERVICIOS ─────────────────────────────────╗
echo.

echo [1/3] Abriendo Backend (FastAPI)...
start "Backend - Uvicorn" cmd /k "title Backend - Uvicorn 8000 & python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000"

timeout /t 2 /nobreak

echo [2/3] Abriendo Frontend (Next.js)...
start "Frontend - Next.js" cmd /k "title Frontend - Next.js 3000 & cd frontend && npm run dev"

timeout /t 2 /nobreak

echo [3/3] Abriendo Desktop App (Electron)...
start "Desktop App - Electron" cmd /k "title Desktop App - Electron & cd desktop-sync-manager && npm run dev"

echo.
echo ╚────────────────────────────────────────────────────────╝
echo.
echo ✓ Todos los servicios en inicio...
echo.
echo 📍 URLs:
echo   • Backend:     http://127.0.0.1:8000
echo   • Frontend:    http://localhost:3000
echo   • Desktop App: Electron (ventana independiente)
echo.
echo 💡 Cierra cualquier ventana terminal para detener ese servicio
echo.
pause
