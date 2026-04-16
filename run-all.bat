@echo off
echo Iniciando Nuevo Socio AI - Papeles Trabajo v2...
echo.

REM Abrir las 3 terminales
echo ✓ Abriendo Backend (puerto 8000)...
start cmd /k "python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000"

timeout /t 2

echo ✓ Abriendo Frontend (puerto 3001)...
start cmd /k "cd frontend && npm run dev"

timeout /t 2

echo ✓ Abriendo Desktop App (Electron)...
start cmd /k "cd desktop-sync-manager && npm run dev"

echo.
echo ✓ Todos los servicios se están iniciando...
echo   - Backend: http://127.0.0.1:8000
echo   - Frontend: http://localhost:3001
echo   - Desktop App: Ventana Electron
pause