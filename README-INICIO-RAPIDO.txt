╔════════════════════════════════════════════════════════════════════════════╗
║                 PAPELES-TRABAJO v2 - INICIO RÁPIDO                          ║
╚════════════════════════════════════════════════════════════════════════════╝

📋 ARCHIVOS INCLUIDOS:
══════════════════════════════════════════════════════════════════════════════

1. RUN-PAPELES-TRABAJO-V2.bat  ← EJECUTA ESTO PARA INICIAR TODO
2. STOP-ALL.bat                ← Ejecuta esto para detener todo
3. .env                        ← Variables de entorno (JWT_SECRET_KEY, etc)


🚀 PARA EMPEZAR:
══════════════════════════════════════════════════════════════════════════════

OPCIÓN 1 - La más fácil (RECOMENDADA):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Haz DOBLE CLICK en: RUN-PAPELES-TRABAJO-V2.bat

   Se abrirán automáticamente 3 ventanas:
   • Ventana 1: Backend (Uvicorn en puerto 8000)
   • Ventana 2: Frontend (Next.js en puerto 3000)
   • Ventana 3: Desktop App (Electron)

2. Espera a que aparezcan los mensajes de éxito en cada ventana:
   ✓ Backend: "Uvicorn running on http://127.0.0.1:8000"
   ✓ Frontend: "Ready in XXXms"
   ✓ Desktop: Ventana Electron se abre


OPCIÓN 2 - Manual (si prefieres):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Abre 3 terminales (cmd o PowerShell) en esta carpeta:

Terminal 1 - BACKEND:
  python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

Terminal 2 - FRONTEND:
  cd frontend
  npm run dev

Terminal 3 - DESKTOP APP:
  cd desktop-sync-manager
  npm run dev


✅ VERIFICAR QUE FUNCIONA:
══════════════════════════════════════════════════════════════════════════════

1. Backend:
   Abre navegador → http://127.0.0.1:8000/docs
   Deberías ver: Swagger UI con todos los endpoints

2. Frontend:
   Abre navegador → http://localhost:3000
   Deberías ver: Página de login de Socio AI

3. Desktop App:
   Una ventana Electron debe abrirse automáticamente
   Deberías ver: Formulario de conexión (URL, Cliente ID, Token)


🧪 FLUJO DE PRUEBA:
══════════════════════════════════════════════════════════════════════════════

1. En Desktop App:
   • URL: http://localhost:8000 (o http://127.0.0.1:8000)
   • Cliente ID: test-cliente-123
   • Token: (obtener del login en Frontend)
   • Click "Conectar"

2. En Desktop App → "Descargar Plantilla"
   Guarda el Excel en Downloads/

3. Llena el Excel con datos de prueba

4. En Desktop App → "Subir Archivo"
   Selecciona el Excel, ingresa:
   • Código del Área: SFI-001
   • Nombre del Área: Sistemas Financieros
   • Click "Subir archivo"

5. En Frontend → http://localhost:3000/papeles-trabajo/test-cliente-123
   Tab "Papeles Excel (v2)"
   Deberías ver el archivo subido


⛔ PARA DETENER TODO:
══════════════════════════════════════════════════════════════════════════════

Opción 1: Haz DOBLE CLICK en STOP-ALL.bat

Opción 2: Cierra manualmente cada ventana terminal con Ctrl+C


🔑 VARIABLES DE ENTORNO (.env):
══════════════════════════════════════════════════════════════════════════════

El archivo .env contiene:
  JWT_SECRET_KEY = Ikjfi3BhNEL7ZzUAx20oMOluGR6awCYQe9qmcdTsH1r5SngyFKDWJXvp8b4VtP
  ENVIRONMENT = development

No lo borres, el backend lo necesita para autenticación JWT.


⚠️ ERRORES COMUNES:
══════════════════════════════════════════════════════════════════════════════

"ModuleNotFoundError: No module named 'backend'"
  → Asegúrate de correr desde la RAÍZ: C:\Users\echoe\Desktop\Nuevo Socio AI

"JWT_SECRET_KEY no esta configurado"
  → El .env no se cargó. Verifica que exista en la raíz del proyecto.

"Port 3000 is already in use"
  → Ejecuta STOP-ALL.bat para cerrar procesos anteriores

"Unable to find Electron app"
  → Ejecuta: npm run build:main (en desktop-sync-manager)


📱 URLS IMPORTANTES:
══════════════════════════════════════════════════════════════════════════════

Backend (API):
  • URL base: http://127.0.0.1:8000
  • Docs: http://127.0.0.1:8000/docs
  • ReDoc: http://127.0.0.1:8000/redoc

Frontend (Web):
  • URL: http://localhost:3000
  • Papeles Trabajo: http://localhost:3000/papeles-trabajo/test-cliente-123

Desktop App:
  • Se abre automáticamente como ventana Electron


📚 DOCUMENTACIÓN COMPLETA:
══════════════════════════════════════════════════════════════════════════════

Ver estos archivos para documentación detallada:
  • PAPELES_TRABAJO_V2_GUIDE.md - Guía técnica completa
  • desktop-sync-manager/README.md - Documentación del Sync Manager
  • IMPLEMENTATION_SUMMARY.md - Resumen de implementación


═════════════════════════════════════════════════════════════════════════════

¿Necesitas ayuda? Revisa los mensajes en las terminales para errores específicos.

¡Listo! Ejecuta RUN-PAPELES-TRABAJO-V2.bat para empezar. 🚀

═════════════════════════════════════════════════════════════════════════════
