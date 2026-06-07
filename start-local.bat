@echo off
setlocal EnableDelayedExpansion

title Socio AI - Local Starter

echo ============================================
echo  Socio AI - Inicio local (Backend + Frontend)
echo ============================================
echo.

REM Asegurar que se ejecuta desde la raiz del proyecto
cd /d "%~dp0"

if not exist "backend\main.py" (
  echo [ERROR] No se encontro backend\main.py
  echo Ejecuta este .bat desde la raiz del proyecto.
  pause
  exit /b 1
)

if not exist "frontend\package.json" (
  echo [ERROR] No se encontro frontend\package.json
  echo Ejecuta este .bat desde la raiz del proyecto.
  pause
  exit /b 1
)

where py >nul 2>nul
if %errorlevel%==0 (
  set "PY_CMD=py"
) else (
  set "PY_CMD=python"
)

echo [1/2] Iniciando Backend en http://127.0.0.1:8000 ...
start "SocioAI Backend" cmd /k "cd /d %~dp0 && set KNOWLEDGE_CORE_ENABLED=1 && %PY_CMD% -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 2 /nobreak >nul

echo Verificando backend...
set "BACK_OK=0"
for /l %%i in (1,1,20) do (
  powershell -NoProfile -Command "try { $r=Invoke-WebRequest -Uri 'http://127.0.0.1:8000/health' -UseBasicParsing -TimeoutSec 2; if($r.StatusCode -eq 200){exit 0}else{exit 1} } catch { exit 1 }" >nul 2>nul
  if !errorlevel! equ 0 (
    set "BACK_OK=1"
    goto :backend_up
  )
  timeout /t 1 /nobreak >nul
)

:backend_up
if "%BACK_OK%"=="1" (
  echo Backend OK en 8000.
) else (
  echo [WARN] Backend aun no responde en /health. Revisa la ventana "SocioAI Backend".
)

echo [2/2] Iniciando Frontend en http://localhost:3000 ...
start "SocioAI Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo OK. Servicios lanzados:
echo - Backend:  http://127.0.0.1:8000
echo - Frontend: http://localhost:3000
echo.
echo Puedes cerrar esta ventana; los servicios siguen en sus consolas.
pause

endlocal
