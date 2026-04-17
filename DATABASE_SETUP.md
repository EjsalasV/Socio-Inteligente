# 🗄️ Setup de Base de Datos - Persistencia de Clientes

## 🎯 Objetivo
Pasar de almacenamiento en archivos a **Base de Datos PostgreSQL** en Railway, para que los clientes y su trabajo NO se pierdan en redeploys.

## 📋 Lo que hemos hecho

### 1. **Nuevas Migraciones SQL** (en `backend/migrations/`)
- `001_create_clients_and_audits.sql` - Crear tablas de clientes y auditorías
- `005_link_observations_to_audits.sql` - Vincular observaciones de papeles a auditorías

### 2. **Nuevos Modelos SQLAlchemy** (en `backend/models/`)
- `client.py` - Modelo Client (memoria de clientes)
- `audit.py` - Modelo Audit (auditorías por período)

### 3. **Nuevo Router API** (en `backend/routes/`)
- `clientes.py` - Endpoints para crear/listar clientes y auditorías
  - `GET /api/clientes` - Listar clientes
  - `POST /api/clientes` - Crear cliente
  - `GET /api/clientes/{cliente_id}` - Obtener cliente
  - `GET /api/clientes/{cliente_id}/auditorias` - Listar auditorías de cliente
  - `POST /api/clientes/{cliente_id}/auditorias` - Crear auditoría

### 4. **Actualización de Database Utils** (`backend/utils/database.py`)
- Cambió de sesión dummy (None) a **sesión SQLAlchemy real**
- Conecta a `DATABASE_URL` (variable de entorno)
- Inicializa tablas automáticamente con `init_db()`

### 5. **Actualización de Main.py**
- Agrega evento `@app.on_event("startup")` para inicializar BD

---

## 🚀 Pasos para Activar

### Paso 1: Verificar DATABASE_URL en Vercel
En Vercel, ve a tu proyecto → Settings → Environment Variables

Verifica que exista:
```
DATABASE_URL = postgresql://usuario:password@host:puerto/railway
```

Si NO existe, cópiala desde Railway:
1. Ve a tu proyecto en Railway
2. En PostgreSQL, click en "Connect"
3. Copia la URL de conexión (PostgreSQL URI)
4. Pégala en Vercel como `DATABASE_URL`

---

### Paso 2: Ejecutar Migraciones Localmente (OPCIONAL, para testing)

Si quieres probar localmente primero:

```bash
cd "C:\Users\echoe\Desktop\Nuevo Socio AI\backend"
python run_migrations.py
```

Esto ejecutará todos los archivos `.sql` en `migrations/` en orden.

---

### Paso 3: Redeploy en Vercel

Cuando haces redeploy, el evento `startup` ejecutará automáticamente:
1. Se conecta a Railway PostgreSQL
2. Crea las tablas (si no existen)
3. Las observaciones se vinculan a auditorías

**Las migraciones SQL no se ejecutan automáticamente**, pero las tablas se crean con `Base.metadata.create_all()` en Python.

---

### Paso 4: Crear Cliente vía API

Una vez que el app esté deployed, puedes crear clientes vía API:

**cURL:**
```bash
curl -X POST https://socio-ai-backend.vercel.app/api/clientes \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "bustamante_fabara_ip_cl",
    "nombre": "Bustamante Fábara IP",
    "sector": "Manufactura",
    "periodo_actual": "2025"
  }'
```

**O desde el Frontend** (cuando lo actualicemos):
```typescript
const response = await fetch('/api/clientes', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` },
  body: JSON.stringify({
    client_id: 'bustamante_fabara_ip_cl',
    nombre: 'Bustamante Fábara IP'
  })
});
```

---

## 💾 Estructura de Persistencia

### Tabla: `clients` (clientes)
```sql
id              INTEGER PK
client_id       VARCHAR(50) UNIQUE  -- bustamante_fabara_ip_cl
nombre          VARCHAR(255)
ruc             VARCHAR(20)
sector          VARCHAR(100)
tipo_entidad    VARCHAR(50)
materialidad_general DECIMAL(15,2)
periodo_actual  VARCHAR(10)         -- "2025"
estado          VARCHAR(20)         -- ACTIVO, EN_AUDITORÍA, FINALIZADO
created_at      TIMESTAMP
updated_at      TIMESTAMP
created_by      VARCHAR(100)
```

### Tabla: `audits` (auditorías)
```sql
id              INTEGER PK
client_id       INTEGER FK → clients
codigo_auditoria VARCHAR(50) UNIQUE -- BUSTAMANTE_2025
periodo         VARCHAR(10)        -- "2025"
estado          VARCHAR(20)        -- PLANEACIÓN, EJECUCIÓN, REPORTE, FINALIZADO
socio_asignado  VARCHAR(100)
senior_asignado VARCHAR(100)
hallazgos_total INTEGER
created_at      TIMESTAMP
updated_at      TIMESTAMP
```

### Tabla: `workpapers_observations` (actualizada)
```sql
...existing columns...
audit_id        INTEGER FK → audits  -- NUEVA: vincula a auditoría
```

---

## 🔍 Verificar que Funciona

### 1. En Vercel Deployment Logs
```
✅ Database initialized at startup
✅ Conexión a base de datos verificada
```

### 2. Listar Clientes
```bash
curl https://socio-ai-backend.vercel.app/api/clientes \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Respuesta esperada:
```json
{
  "status": "success",
  "data": {
    "total": 1,
    "clientes": [
      {
        "id": 1,
        "client_id": "bustamante_fabara_ip_cl",
        "nombre": "Bustamante Fábara IP",
        "estado": "ACTIVO",
        "created_at": "2026-04-17T..."
      }
    ]
  }
}
```

### 3. Verificar en Railway (Opcional)
```bash
# Conectar a PostgreSQL
PGPASSWORD=YOUR_PASSWORD psql -h nozomi.proxy.rlwy.net -U postgres -p 28971 -d railway

# En psql:
\dt              -- Listar tablas
SELECT * FROM clients;  -- Ver clientes
SELECT * FROM audits;   -- Ver auditorías
```

---

## ✨ Resultado Final

✅ Clientes se crean y almacenan en **PostgreSQL Railway**  
✅ Auditorías se crean por cliente y período  
✅ Observaciones se vinculan a auditorías  
✅ **NO se pierden en redeploy** (datos en BD, no en archivos)  
✅ Frontend puede cargar clientes persistentes  

---

## 📝 Próximos Pasos

1. **Frontend:** Actualizar componente para listar clientes desde `/api/clientes`
2. **Frontend:** Crear formulario para crear clientes
3. **V2 Upload:** Vincular subida de Excel a `audit_id` específico
4. **Auditoría:** Registrar cambios en `audit_history` cuando se crean/modifican observaciones

---

## ❓ Si Hay Problemas

**Problema:** `DATABASE_URL not configured`
- **Solución:** Verificar que está en Vercel env vars

**Problema:** `Connection refused` en Railway
- **Solución:** Verificar que Railway está activo y URL es correcta

**Problema:** `Table already exists`
- **Solución:** Es normal en redeploys. Las migraciones usan `IF NOT EXISTS`

**Problema:** Observaciones no se guardan
- **Solución:** Asegúrate de tener `audit_id` al insertar observaciones
