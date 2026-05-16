# Guía de Integración n8n + SocioAI

**Objetivo:** Automatizar tareas de auditoría (agendar reuniones, enviar alertas, documentación, reportes)

---

## 1. ARQUITECTURA GENERAL

```
┌─────────────┐        ┌────────┐        ┌─────────────────┐
│  SocioAI    │──────→ │  n8n   │──────→ │ Google Calendar │
│  Backend    │        │Workflow│        │ Slack           │
└─────────────┘        │        │        │ Google Drive    │
                       │        │        │ Power BI        │
                       └────────┘        │ Email           │
                                         └─────────────────┘
```

---

## 2. SETUP INICIAL

### 2.1 Instalar n8n

**Opción A: Cloud (Recomendado para inicio)**
```bash
# Ir a https://n8n.cloud
# Crear cuenta gratuita
# Crear workspace
```

**Opción B: Self-hosted (Cuando escales)**
```bash
npm install -g n8n
n8n start
# Accede a http://localhost:5678
```

### 2.2 Crear Credenciales en n8n

n8n necesita autenticarse con:

| Servicio | Credencial | Dónde obtenerla |
|----------|-----------|-----------------|
| **Google Calendar** | OAuth2 | Google Cloud Console |
| **Google Drive** | OAuth2 | Google Cloud Console |
| **Google Sheets** | OAuth2 | Google Cloud Console |
| **Slack** | Webhook URL | Slack App Settings |
| **Power BI** | OAuth2 + Dataset ID | Power BI Admin Portal |
| **SendGrid** | API Key | SendGrid Dashboard |
| **Claude API** | API Key | Anthropic Console |

**Pasos:**
1. En n8n, ve a Credentials (parte superior izquierda)
2. Click "+ New"
3. Selecciona el servicio
4. Sigue el wizard de autenticación
5. Test connection

---

## 3. WEBHOOKS DESDE SOCIOAI

Para que SocioAI pueda **disparar** los flujos de n8n, necesitas:

### 3.1 Crear Endpoints en Backend

En `backend/routes/automations.py`:

```python
from fastapi import APIRouter, HTTPException
from backend.auth import verify_token

router = APIRouter(prefix="/api/automations", tags=["Automations"])

@router.post("/trigger/schedule-meeting")
async def trigger_schedule_meeting(data: dict):
    """
    Dispara flujo n8n: Auto Schedule Meetings
    
    Body expected:
    {
        "auditor_email": "auditor@firma.com",
        "auditor_name": "Juan Pérez",
        "message": "Necesito reunión con el CFO para revisar cartera"
    }
    """
    import httpx
    
    # Webhook URL de n8n (obtenido al crear workflow)
    webhook_url = os.getenv("N8N_SCHEDULE_MEETING_WEBHOOK")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(webhook_url, json=data)
        
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to schedule meeting")
    
    return {"status": "scheduled", "webhook": webhook_url}


@router.post("/trigger/smart-alerts")
async def trigger_smart_alerts(data: dict):
    """
    Dispara flujo n8n: Smart Alerts
    
    Body expected:
    {
        "audit_id": "123",
        "cliente_nombre": "ABC Corp",
        "balance": {...}
    }
    """
    webhook_url = os.getenv("N8N_SMART_ALERTS_WEBHOOK")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(webhook_url, json=data)
        
    return {"status": "alert_sent"}


@router.post("/trigger/auto-documentation")
async def trigger_auto_documentation(data: dict):
    """
    Dispara flujo n8n: Auto Documentation Generator
    
    Body expected:
    {
        "audit_action": "Revisé cartera, 95% cubierto",
        "client_name": "ABC Corp",
        "area": "Cuentas por Cobrar",
        "result": "SIN HALLAZGOS",
        "auditor_email": "auditor@firma.com",
        "drive_folder_id": "xyz123"
    }
    """
    webhook_url = os.getenv("N8N_AUTO_DOCUMENTATION_WEBHOOK")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(webhook_url, json=data)
    
    return {"status": "documentation_generating"}


@router.post("/trigger/powerbi-reports")
async def trigger_powerbi_reports(data: dict):
    """
    Dispara flujo n8n: Auto Power BI Reports
    
    Body expected:
    {
        "client_name": "ABC Corp",
        "client_email": "cfo@abc.com",
        "materialidad_global": 50000,
        "ingresos": 1000000,
        "ganancias": 100000,
        "activos": 5000000,
        "patrimonio": 2000000,
        "umbral_trivial": 5000,
        "riesgos": [
            {"area": "Cartera", "nivel": "ALTO", "descripcion": "..."}
        ]
    }
    """
    webhook_url = os.getenv("N8N_POWERBI_REPORTS_WEBHOOK")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(webhook_url, json=data)
    
    return {"status": "report_generating"}
```

Luego agrega en `backend/main.py`:

```python
from backend.routes import automations

app.include_router(automations.router)
```

### 3.2 Configurar Variables de Entorno

En `.env`:

```env
# n8n Webhooks
N8N_SCHEDULE_MEETING_WEBHOOK=https://YOUR_N8N_INSTANCE.n8n.cloud/webhook/...
N8N_SMART_ALERTS_WEBHOOK=https://YOUR_N8N_INSTANCE.n8n.cloud/webhook/...
N8N_AUTO_DOCUMENTATION_WEBHOOK=https://YOUR_N8N_INSTANCE.n8n.cloud/webhook/...
N8N_POWERBI_REPORTS_WEBHOOK=https://YOUR_N8N_INSTANCE.n8n.cloud/webhook/...

# Credenciales
POWERBI_DATASET_ID=xxx
POWERBI_RISKS_DATASET_ID=yyy
POWERBI_REPORT_ID=zzz
```

---

## 4. IMPORTAR WORKFLOWS EN N8N

### 4.1 Opción A: Importar JSON

1. En n8n, click "+ New"
2. Click "Import from URL/File"
3. Sube el archivo JSON desde `/n8n/workflows/`
4. Click "Import"

### 4.2 Opción B: Crear Manualmente

Si prefieres crear desde cero:

1. Click "+ New" → "Blank workflow"
2. Agrega nodos según los diagramas en los JSONs
3. Configura credenciales
4. **Importante:** Al crear webhook trigger, copia la URL
5. Pega la URL en las variables de entorno (`N8N_*_WEBHOOK`)

---

## 5. DISPARAR WORKFLOWS DESDE FRONTEND

Cuando el auditor hace algo en SocioAI, dispara el workflow:

### 5.1 Ejemplo: Agendar Reunión

En `frontend/app/auditorias/[id]/page.tsx`:

```typescript
// Cuando auditor escribe "Necesito reunión con CFO"
async function handleScheduleMeeting(message: string) {
  const response = await fetch(
    '/api/automations/trigger/schedule-meeting',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        auditor_email: user.email,
        auditor_name: user.name,
        message: message
      })
    }
  )
  
  if (response.ok) {
    showNotification('✓ Reunión agendada automáticamente')
  }
}
```

### 5.2 Ejemplo: Enviar Alerta Diaria

Crear un **cron job** en el backend:

```python
# En backend/services/automation_service.py

from apscheduler.schedulers.background import BackgroundScheduler
import httpx

scheduler = BackgroundScheduler()

@scheduler.scheduled_job('cron', hour=9, minute=0)  # 9 AM todos los días
async def trigger_daily_smart_alerts():
    """Dispara alertas cada mañana"""
    
    # Obtener auditorías pendientes
    pending_audits = db.query(Audit).filter(
        Audit.estado == 'EN_PROGRESO'
    ).all()
    
    for audit in pending_audits:
        await fetch(
            os.getenv('N8N_SMART_ALERTS_WEBHOOK'),
            json={
                'audit_id': audit.id,
                'cliente_nombre': audit.cliente.nombre,
                'balance': audit.trial_balance
            }
        )

scheduler.start()
```

---

## 6. PRUEBAS

### 6.1 Test Webhook

En n8n, cada workflow tiene un botón "Test":

```
┌─────────────────────────────────────┐
│ Start - Webhook from SocioAI        │
│                                     │
│ [Test] [Listen for webhook]         │
└─────────────────────────────────────┘
```

1. Click "Listen for webhook"
2. Copia la URL de test
3. En terminal:
```bash
curl -X POST https://webhook.url \
  -H "Content-Type: application/json" \
  -d '{
    "auditor_email": "test@test.com",
    "message": "Necesito reunión"
  }'
```
4. Deberías ver los datos en n8n

### 6.2 Monitoreo en Producción

En n8n, cada ejecución se registra:

1. Click en el workflow
2. Tab "Executions"
3. Ver historial de ejecuciones
4. Hacer drill-down en errores

---

## 7. COSTOS

| Componente | Costo | Nota |
|-----------|-------|------|
| **n8n Cloud** | Gratis hasta 5 workflows | Upgrade $10-25/mes |
| **Google Workspace** | ~$5-10/usuario | (probablemente ya tienes) |
| **Slack** | Gratis básico | $8/usuario si pagas |
| **Power BI** | ~$10/mes | Starter license |
| **SendGrid** | Gratis hasta 100 emails/día | Luego $0.0001/email |
| **Claude API** | $0.003 per 1K input tokens | Usa para análisis |

**Total inicial:** ~$20-30/mes (muy barato vs. Caseware)

---

## 8. ROADMAP

### Mes 1
- [ ] Setup n8n cloud
- [ ] Integrar Google Calendar
- [ ] Integrar Slack

### Mes 2
- [ ] Integrar Google Drive
- [ ] Automatizar documentación
- [ ] Integrar Power BI

### Mes 3
- [ ] Optimizar alertas
- [ ] Agregar más workflows
- [ ] Self-host n8n (si escala)

---

## 9. TROUBLESHOOTING

### Problema: "Webhook no recibe datos"
**Solución:**
1. Verifica que el endpoint en backend existe
2. Verifica que .env tiene la URL correcta
3. Usa `console.log()` en frontend para confirmar que se envía

### Problema: "Google Calendar no autoriza"
**Solución:**
1. Ve a Google Cloud Console
2. Activa "Google Calendar API"
3. Crea OAuth2 credentials (tipo: Web application)
4. En n8n, reautentica con las nuevas credenciales

### Problema: "Power BI no recibe datos"
**Solución:**
1. Verifica que el dataset existe y es el ID correcto
2. Power BI requiere "Service Principal" para API
3. En Power BI Admin Portal, activa "Service Principal can use Power BI APIs"

---

## 10. CONTACTO Y SOPORTE

- **n8n Docs:** https://docs.n8n.io
- **n8n Community:** https://community.n8n.io
- **Soporte SocioAI:** legal@socioai.ec
