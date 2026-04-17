# ☑️ CHECKLIST: Activar Persistencia de BD

**Tiempo estimado:** 15-20 minutos

---

## 📋 PRE-CHECKLIST (Verificar sin hacer cambios)

- [ ] Vercel project abierto y accesible
- [ ] Railway PostgreSQL activo
- [ ] Git repo actualizado (git status limpio)
- [ ] Terminal PowerShell o cmd abierta en la carpeta del proyecto

---

## 🔧 CHECKLIST TÉCNICO

### 1. Archivos Creados/Modificados (Verificar)

En `backend/migrations/`:
- [ ] `001_create_clients_and_audits.sql` (NUEVO)
- [ ] `005_link_observations_to_audits.sql` (NUEVO)
- [ ] `002_create_papeles_templates.sql` (existente)
- [ ] `003_create_papeles_observations.sql` (existente)
- [ ] `004_seed_workpapers_templates.sql` (existente)

En `backend/models/`:
- [ ] `client.py` (NUEVO)
- [ ] `audit.py` (NUEVO)
- [ ] `workpapers_observation.py` (MODIFICADO - ahora con audit_id)

En `backend/routes/`:
- [ ] `clientes.py` (REEMPLAZADO - ahora usa BD en lugar de archivos)
- [ ] `clientes_old_filebase.py` (backup del anterior)

En `backend/`:
- [ ] `utils/database.py` (ACTUALIZADO - usa SQLAlchemy real)
- [ ] `main.py` (ACTUALIZADO - agrega startup event)
- [ ] `run_migrations.py` (NUEVO - script para ejecutar migraciones)

En raíz:
- [ ] `verify_database.py` (NUEVO - script de verificación)
- [ ] `DATABASE_SETUP.md` (NUEVO - documentación)
- [ ] `SETUP_PERSISTENCIA.md` (NUEVO - guía de pasos)

---

### 2. Configuración Vercel

```bash
# Paso A: Abre Vercel → Tu Proyecto → Settings
# 
# Paso B: Environment Variables
#         Busca: DATABASE_URL
#
# ✅ Si existe:
#    Ve al Paso 3
#
# ❌ Si NO existe:
#    1. Abre Railway → Proyecto → Postgres → Connect
#    2. Copia la URL PostgreSQL completa
#    3. En Vercel, crea NEW:
#       Name:  DATABASE_URL
#       Value: <pega la URL>
#    4. Save
```

- [ ] DATABASE_URL configurada en Vercel

---

### 3. Commit a GitHub

```bash
# En PowerShell/CMD, dentro del proyecto:

git add -A
git status  # Verifica que ves los archivos nuevos
git commit -m "feat: DB persistence for clients (Phase 0)

Migrate from file-based storage to PostgreSQL for client data
- Create clients and audits tables
- Update database.py to use real SQLAlchemy
- Add BD initialization on startup
- Link workpapers_observations with audits
- Replace file-based client routes with database routes

Data now persists across redeploys."
```

- [ ] Commit creado localmente

---

### 4. Push a GitHub

```bash
git push origin main
```

- [ ] Push a GitHub exitoso
- [ ] Vercel detecta el push y comienza redeploy automático

---

### 5. Esperar Redeploy

En Vercel, ve a **Deployments** → **Actividades Recientes**

```
Esperado:
- 🟡 Building... (2-3 min)
- 🟢 Ready (con URL y logs)
```

En los **logs** (últimas líneas):
```
✅ Database initialized at startup
✅ Conexión a base de datos verificada
✅ 5 migration files detected
```

- [ ] Redeploy completado (verde)
- [ ] Logs muestran "Database initialized"

---

## ✅ TESTING (Verificar que Funciona)

### Test 1: Listar Clientes (vacío)

```bash
# Necesitas un JWT token válido
# Si no tienes, primero haz login en la app

$TOKEN = "tu_jwt_token_aqui"

curl -X GET https://socio-ai-backend.vercel.app/api/clientes `
  -H "Authorization: Bearer $TOKEN" `
  -H "Content-Type: application/json"
```

Respuesta esperada:
```json
{
  "status": "success",
  "data": {
    "total": 0,
    "clientes": []
  }
}
```

- [ ] Request exitoso (200 OK)
- [ ] Respuesta muestra "total: 0"

---

### Test 2: Crear Cliente

```bash
$TOKEN = "tu_jwt_token"

$body = @{
    client_id = "test_cliente_$(Get-Date -Format 'yyyyMMddHHmmss')"
    nombre = "Test Cliente BD"
    sector = "Manufactura"
    periodo_actual = "2025"
    materialidad_general = 500000
} | ConvertTo-Json

curl -X POST https://socio-ai-backend.vercel.app/api/clientes `
  -H "Authorization: Bearer $TOKEN" `
  -H "Content-Type: application/json" `
  -Body $body
```

Respuesta esperada:
```json
{
  "status": "success",
  "message": "Cliente ... creado exitosamente",
  "data": {
    "id": 1,
    "client_id": "test_cliente_...",
    "nombre": "Test Cliente BD",
    "estado": "ACTIVO",
    "created_at": "2026-04-17T..."
  }
}
```

- [ ] Request exitoso (200 OK)
- [ ] Respuesta muestra cliente con id
- [ ] Campo "estado" = "ACTIVO"

---

### Test 3: Listar Clientes (con datos)

```bash
$TOKEN = "tu_jwt_token"

curl -X GET https://socio-ai-backend.vercel.app/api/clientes `
  -H "Authorization: Bearer $TOKEN"
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
        "client_id": "test_cliente_...",
        "nombre": "Test Cliente BD",
        "estado": "ACTIVO"
      }
    ]
  }
}
```

- [ ] total ahora = 1
- [ ] Cliente aparece en lista

---

### Test 4: Verificar en Railway (Opcional)

```bash
# En terminal (requiere psql instalado)

$env:PGPASSWORD = "gaYntTmchGXngJnyAtaCKETbVKhDfUvk"

psql -h nozomi.proxy.rlwy.net -U postgres -p 28971 -d railway -c `
"SELECT id, client_id, nombre, estado FROM clients;"
```

Deberías ver el cliente que creaste:
```
 id |  client_id   |   nombre   | estado
----+--------------+------------+--------
  1 | test_cliente | Test BD    | ACTIVO
```

- [ ] Cliente visible en PostgreSQL
- [ ] Datos coinciden con API

---

### Test 5: Persistencia (El Gran Test) 🎯

**¿Es esto lo que querías?** Cliente que NO desaparece en redeploy

```bash
# 1. Verificar cliente existe (Test 3)
# 2. Hacer cambio dummy y redeploy:
git commit --allow-empty -m "test: trigger redeploy"
git push origin main

# 3. Esperar redeploy (2-3 min)
# 4. Llamar API cliente nuevamente (Test 3)
# 5. ¿Cliente sigue ahí? ✅ = ÉXITO
```

- [ ] Cliente sigue existiendo después de redeploy
- [ ] **PERSISTENCIA CONFIRMADA** 🎉

---

## 🚨 Si Algo Falla

### Error: `DATABASE_URL not configured`
```
✅ Solución:
1. Vercel → Settings → Environment Variables
2. Agregar DATABASE_URL (copiar de Railway)
3. Redeploy
```
- [ ] DATABASE_URL agregada

### Error: `Connection refused` (Railway)
```
✅ Solución:
1. Railway → Proyecto → Postgres → Status
2. ¿Está en "Ready"?
3. Si no, esperar o reiniciar
4. Verificar URL en Vercel
```
- [ ] Railway está en estado Ready

### Error: `401 Unauthorized` en curl
```
✅ Solución:
1. Token JWT inválido o expirado
2. Loguéate en app para obtener token fresco
3. Copia en DevTools → Network → cualquier request → headers
4. Usa ese token
```
- [ ] Token JWT válido

### Error: `Table already exists`
```
✅ Solución:
Normal en redeploys. Las migraciones usan IF NOT EXISTS.
Simplemente continúa.
```
- [ ] Entendido

---

## 🎯 Confirmación Final

Una vez hayas completado TODO, verifica:

- [ ] Git push completado
- [ ] Vercel redeploy verde (Ready)
- [ ] Test 1-5 pasados
- [ ] Cliente persiste después de redeploy
- [ ] BD visible en Railway psql

Si TODO está marcado ✅:

## **🎉 ¡PERSISTENCIA DE BD ACTIVADA!**

Tu sistema **tiene memoria**. Los clientes no se pierden en redeploys.

---

## 📝 Notas

- No borres `clientes_old_filebase.py` todavía (backup)
- Las migraciones SQL están en `migrations/`, no se ejecutan automáticamente pero las tablas se crean con `create_all()`
- El `verify_database.py` necesita `DATABASE_URL` local para conectar (no necesario para Vercel)
- Cada cliente puede tener múltiples auditorías (una por período)

---

## ⏭️ Próximo: Papeles Trabajo V1 Actualizado

Una vez confirm persistencia, podemos:
1. Actualizar V1 para crear observaciones con `audit_id`
2. Agregar frontend para seleccionar cliente desde BD
3. Implementar historial de cambios (audit_history)

**¿Necesitas que avance?** Confirma este checklist primero.
