# Setup n8n - Guía Paso a Paso (1 hora)

**Objetivo:** Tener n8n corriendo con 4 workflows automáticos  
**Tiempo:** ~60 minutos  
**Costo:** $0 (free tier de n8n)

---

## PASO 1: Crear Cuenta n8n Cloud (5 minutos)

### 1.1 Acceso
```
1. Abre https://n8n.cloud en navegador
2. Click en "Sign up" (esquina superior derecha)
```

**Que verás:**
```
┌──────────────────────────────────────────┐
│  n8n Cloud - Sign Up                     │
│                                          │
│  Email: [____________________________]    │
│  Password: [____________________________] │
│  Name: [____________________________]     │
│                                          │
│  [Sign up with Google]                   │
│  [Sign up]                               │
└──────────────────────────────────────────┘
```

### 1.2 Llenar datos
- Email: tu@email.com
- Password: contraseña fuerte (mín 12 caracteres)
- Name: "Joao Salas" o nombre empresa

### 1.3 Verificar email
- Revisa email
- Click en enlace de verificación
- Listo, estás dentro

---

## PASO 2: Crear Workspace (2 minutos)

### 2.1 Dashboard inicial
Después de login, verás:

```
┌──────────────────────────────────────┐
│ My Workspace                         │
│                                      │
│ [+ New]  [Import]  [Open Recent]     │
│                                      │
│ No workflows yet                     │
│                                      │
│ Create your first workflow →         │
└──────────────────────────────────────┘
```

### 2.2 Crear workspace
- Click en nombre arriba a la izquierda
- "Create new workspace"
- Nombre: "SocioAI Production"
- Click "Create"

---

## PASO 3: Importar 4 Workflows (10 minutos)

### 3.1 Importar primer workflow
```
1. En dashboard, click [+ New]
2. Click "Import from URL or File"
3. Click "Select a file"
4. Selecciona: /n8n/workflows/auto_schedule_meetings.json
5. Click "Import"
6. Espera 5 segundos mientras carga
```

**Que verás:**
```
┌──────────────────────────────────────────┐
│ Workflow: Auto Schedule Meetings         │
│                                          │
│ ┌────────────────────────────────────┐   │
│ │ [Webhook] → [Claude] → [IF] → ...  │   │
│ └────────────────────────────────────┘   │
│                                          │
│ Status: Draft (not active)               │
└──────────────────────────────────────────┘
```

### 3.2 Repetir para otros 3 workflows
Haz lo mismo para:
- `auto_smart_alerts.json`
- `auto_documentation.json`
- `auto_powerbi_reports.json`

**Resultado:**
```
Workflows listados:
├─ Auto Schedule Meetings ✓
├─ Smart Alerts System ✓
├─ Auto Documentation ✓
└─ Auto Power BI Reports ✓
```

---

## PASO 4: Configurar Credenciales (20 minutos)

### 4.1 Acceso a Credenciales
```
1. Click ícono de engranaje (arriba a la izquierda)
2. Click "Credentials"
3. Deberías ver: "No credentials yet"
```

### 4.2 Agregar Google Calendar OAuth2

**¿Por qué Google Calendar?** Para que n8n pueda acceder y crear eventos.

```
1. Click "+ Add new"
2. Buscar "Google Calendar"
3. Click "Google Calendar"
```

**Popup que aparece:**
```
┌──────────────────────────────────────────┐
│ Google Calendar - Authenticate           │
│                                          │
│ [Sign in with Google] ← Click aquí      │
└──────────────────────────────────────────┘
```

**Qué pasa:**
1. Se abre Google login
2. Selecciona tu cuenta Google
3. Autoriza n8n a acceder a Calendar
4. Se cierra automáticamente
5. Credencial guardada ✓

### 4.3 Agregar Google Drive OAuth2

Mismo proceso que Calendar:
```
1. Click "+ Add new"
2. Buscar "Google Drive"
3. Click "Google Drive"
4. [Sign in with Google]
5. Autoriza
```

### 4.4 Agregar Slack (Webhook)

Este es diferente - es más simple:

```
1. Click "+ Add new"
2. Buscar "Slack"
3. Seleccionar "Slack (Webhook)"
4. Te dice: "Paste your Slack Webhook URL"
```

**¿Cómo obtener webhook de Slack?**

Si no tienes Slack:
```
a) Crea espacio gratuito en https://slack.com
b) Workspace name: "SocioAI"
c) Crea canal: #auditorias
```

Si ya tienes Slack:
```
1. Ve a tu Slack workspace
2. Click "Settings & administration"
3. Click "Manage apps"
4. Search "Incoming Webhooks"
5. Click "Incoming Webhooks" → "Install"
6. Selecciona canal: #auditorias
7. Click "Add New Webhook to Workspace"
8. Copia URL (tipo: https://hooks.slack.com/services/...)
9. Pega en n8n
10. Click "Save"
```

### 4.5 Agregar SendGrid API Key

Para enviar emails:

```
1. Si no tienes: Crea cuenta gratis en https://sendgrid.com
2. Ve a "Settings" → "API Keys"
3. Click "Create API Key"
4. Name: "n8n"
5. Copia la key
6. En n8n:
   - Click "+ Add new"
   - Buscar "SendGrid"
   - Pega API Key
   - Click "Save"
```

### 4.6 Agregar Claude API Key

Para análisis con IA:

```
1. Ve a https://console.anthropic.com
2. Click "API Keys"
3. Click "Create Key"
4. Copia
5. En n8n:
   - Click "+ Add new"
   - Buscar "HTTP Request"
   - Seleccionar "API Key" auth
   - Name: "Anthropic"
   - Key: "x-api-key"
   - Value: [Tu API Key]
   - Click "Save"
```

**Resultado esperado:**
```
Credentials (5 agregadas):
├─ Google Calendar ✓
├─ Google Drive ✓
├─ Slack Webhook ✓
├─ SendGrid ✓
└─ Anthropic ✓
```

---

## PASO 5: Configurar Cada Workflow (20 minutos)

### 5.1 Auto Schedule Meetings

```
1. Click en workflow "Auto Schedule Meetings"
2. Verás diagrama:
   [Webhook] → [Claude] → [IF] → [Google Calendar] → [Email] → [Sheets]
```

**Configurar nodos:**

**Nodo 1: Webhook**
```
- Status: Ya debe estar listo
- Escribe URL que aparece (copiar para luego)
- Click "Save"
```

**Nodo 2: Claude - Detect Meeting Need**
```
- Click en el nodo
- En panel derecha:
  - API Key: seleccionar "Anthropic" (ya agregada)
  - Click "Save"
```

**Nodo 3: Google Calendar**
```
- Click en nodo
- Authentication: seleccionar "Google Calendar" (ya agregada)
- Click "Save"
```

**Nodo 4: SendGrid Email**
```
- Click en nodo
- API Key: seleccionar "SendGrid" (ya agregada)
- Click "Save"
```

### 5.2 Smart Alerts System

Mismo proceso:
```
1. Click en workflow
2. Pasar por cada nodo (azules con círculos)
3. Seleccionar credenciales ya configuradas
4. Click "Save" en cada uno
```

### 5.3 Auto Documentation

Similar a Schedule Meetings

### 5.4 Auto Power BI Reports

Similar a Schedule Meetings

---

## PASO 6: Activar Workflows (5 minutos)

### 6.1 Activar cada uno
```
Para cada workflow:
1. Abre el workflow
2. Arriba a la derecha, botón grande [Off]
3. Click para cambiar a [On]
4. Se torna verde ✓
```

**Resultado:**
```
Auto Schedule Meetings        [On] ✓
Smart Alerts System           [On] ✓
Auto Documentation            [On] ✓
Auto Power BI Reports         [On] ✓
```

---

## PASO 7: Obtener Webhook URLs (5 minutos)

**Importante:** Necesitas estas URLs para que SocioAI dispare los workflows.

### 7.1 Copiar URL de cada workflow

Para cada workflow:
```
1. Abre el workflow
2. Click en nodo "Start - Webhook..." (el primero)
3. Panel derecha mostará URL
4. Click icono copiar
5. Pega en documento de texto
```

**Documento que necesitas crear:**

`n8n_webhooks.txt`:
```
# n8n Webhook URLs - Guardadas el 16 mayo 2026

AUTO_SCHEDULE_MEETINGS_WEBHOOK=
https://YOUR_INSTANCE.n8n.cloud/webhook/xxxxxxxxxxxxx

AUTO_SMART_ALERTS_WEBHOOK=
https://YOUR_INSTANCE.n8n.cloud/webhook/yyyyyyyyyyyyy

AUTO_DOCUMENTATION_WEBHOOK=
https://YOUR_INSTANCE.n8n.cloud/webhook/zzzzzzzzzzzzz

AUTO_POWERBI_REPORTS_WEBHOOK=
https://YOUR_INSTANCE.n8n.cloud/webhook/wwwwwwwwwwwww
```

---

## PASO 8: Configurar .env en Backend (3 minutos)

En tu `.env` del proyecto:

```bash
# Copias y pegas las URLs del paso anterior

# n8n Webhooks
N8N_SCHEDULE_MEETING_WEBHOOK=https://YOUR_INSTANCE.n8n.cloud/webhook/xxxxxxxxxxxxx
N8N_SMART_ALERTS_WEBHOOK=https://YOUR_INSTANCE.n8n.cloud/webhook/yyyyyyyyyyyyy
N8N_AUTO_DOCUMENTATION_WEBHOOK=https://YOUR_INSTANCE.n8n.cloud/webhook/zzzzzzzzzzzzz
N8N_POWERBI_REPORTS_WEBHOOK=https://YOUR_INSTANCE.n8n.cloud/webhook/wwwwwwwwwwwww

# Power BI (si planeas integrar)
POWERBI_DATASET_ID=xxxxx (obtener de Power BI admin)
POWERBI_REPORT_ID=xxxxx
```

---

## PASO 9: Test Local (5 minutos)

### 9.1 Test Schedule Meetings

En terminal, ejecuta:

```bash
curl -X POST https://YOUR_INSTANCE.n8n.cloud/webhook/xxxxxxxxxxxxx \
  -H "Content-Type: application/json" \
  -d '{
    "auditor_email": "test@test.com",
    "auditor_name": "Test User",
    "message": "Necesito reunión con el CFO para revisar cartera"
  }'
```

**Deberías ver:**
```
En n8n: "Execution successful"
En tu Google Calendar: Nuevo evento creado
En tu email: Confirmación de reunión agendada
```

### 9.2 Test Smart Alerts

```bash
curl -X POST https://YOUR_INSTANCE.n8n.cloud/webhook/yyyyyyyyyyyyy \
  -H "Content-Type: application/json" \
  -d '{
    "audit_id": "123",
    "cliente_nombre": "ABC Corp",
    "balance": {
      "cartera_dias": 120,
      "cartera_monto": 250000
    }
  }'
```

**Deberías ver:**
```
En n8n: "Execution successful"
En Slack #auditorias: Alerta roja con la cartera vencida
```

---

## PASO 10: Conectar con SocioAI Backend (5 minutos)

### 10.1 Crear archivo automations.py

Ya lo tenemos en `backend/routes/automations.py` (creado hace poco)

### 10.2 Asegurar endpoints estén registrados

En `backend/main.py`:

```python
from backend.routes import automations

# Agregar esta línea con los otros routers
app.include_router(automations.router)
```

### 10.3 Test desde backend

```bash
# Lanza backend
python -m uvicorn backend.main:app --reload

# En otro terminal, test
curl -X POST http://localhost:8000/api/automations/trigger/schedule-meeting \
  -H "Content-Type: application/json" \
  -d '{
    "auditor_email": "joao@socioai.ec",
    "auditor_name": "Joao",
    "message": "Necesito reunión"
  }'
```

**Deberías ver:**
```json
{
  "status": "scheduled",
  "webhook": "https://YOUR_INSTANCE.n8n.cloud/webhook/..."
}
```

---

## ✅ CHECKLIST FINAL

```
CUENTA Y WORKSPACE
☑ Cuenta n8n creada
☑ Email verificado
☑ Workspace "SocioAI Production" creado

WORKFLOWS IMPORTADOS
☑ Auto Schedule Meetings
☑ Smart Alerts System
☑ Auto Documentation
☑ Auto Power BI Reports

CREDENCIALES CONFIGURADAS
☑ Google Calendar OAuth2
☑ Google Drive OAuth2
☑ Slack Webhook
☑ SendGrid API Key
☑ Anthropic API Key

WORKFLOWS CONFIGURADOS
☑ Todos los nodos tienen credenciales
☑ Todos activados [On]
☑ URLs copiadas a n8n_webhooks.txt

BACKEND CONECTADO
☑ automations.py existe
☑ Importado en main.py
☑ .env variables configuradas
☑ Tests funcionan (curl)

RESULTADO ESPERADO
☑ Puedes agendar reuniones desde SocioAI
☑ Recibes alertas en Slack
☑ Documentos se generan en Google Drive
☑ Reportes se envían a Power BI
```

---

## 🚨 TROUBLESHOOTING

| Problema | Solución |
|----------|----------|
| "Credencial no aparece" | Refrescar página n8n (Ctrl+F5) |
| "Google Calendar auth falla" | Ir a Google Cloud Console → Activa "Google Calendar API" |
| "Webhook URL no funciona" | Asegúrate que workflow esté [On], no [Off] |
| "Email no se envía" | SendGrid key tiene límite free (100/día) |
| "Power BI no recibe datos" | Verificar que Dataset ID sea correcto |
| "Slack no muestra mensaje" | Webhook URL tiene que ser de "Incoming Webhooks" |

---

## 📞 SOPORTE

- n8n Docs: https://docs.n8n.io
- n8n Community: https://community.n8n.io
- Soporte SocioAI: legal@socioai.ec

**Tiempo total esperado: ~60 minutos**
