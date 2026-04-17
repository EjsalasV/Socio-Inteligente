# 🔧 FIX: Configurar DATABASE_URL en Vercel

## ❌ El Problema

```
ValueError: ❌ DATABASE_URL no está configurada
```

El app necesita saber dónde está la BD PostgreSQL en Railway.

---

## ✅ La Solución (5 minutos)

### PASO 1: Obtener la URL de Railway

1. Abre **Railway** → Tu Proyecto
2. Click en **Postgres** (la base de datos)
3. Click en **Connect**
4. Busca **PostgreSQL URI** y **cópiala completa**

Debería verse así:
```
postgresql://postgres:PASSWORD@nozomi.proxy.rlwy.net:28971/railway
```

---

### PASO 2: Agregar en Vercel

1. Abre **Vercel** → Tu Proyecto → **Settings**
2. Click en **Environment Variables** (tab)
3. Click en **Add New** (botón)
4. **Name:** `DATABASE_URL`
5. **Value:** Pega la URL de Railway (completa, sin espacios)
6. Click **Add**
7. Click **Save**

**Importante:** Si hay un botón de "Deploy", clickealo para redeploy automático.

---

### PASO 3: Verifica en Vercel

Ve a **Deployments** → Última versión

Debería estar en estado **Ready** (verde).

En los logs, busca:
```
✅ Database initialized at startup
✅ Conexión a base de datos verificada
```

Si ves eso: **¡ÉXITO!** 🎉

---

## 📋 Checklist

- [ ] DATABASE_URL copiada de Railway
- [ ] DATABASE_URL agregada en Vercel (Name + Value)
- [ ] Vercel en estado Ready (verde)
- [ ] Logs muestran "Database initialized"

---

## 🧪 Prueba que Funciona

```bash
# Con tu JWT token válido:
TOKEN="your_jwt_token"

# 1. Crear cliente
curl -X POST https://socio-ai-backend.vercel.app/api/clientes \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"client_id": "test", "nombre": "Test"}'

# Respuesta esperada:
# {"status": "success", "id": 1, ...}

# 2. Listar clientes
curl -X GET https://socio-ai-backend.vercel.app/api/clientes \
  -H "Authorization: Bearer $TOKEN"

# Respuesta esperada:
# {"status": "success", "data": {"total": 1, "clientes": [...]}}
```

---

## ❓ Si Algo Falla

**Problema:** Redeploy aún no completa
- **Solución:** Espera 2-3 minutos más

**Problema:** Logs aún muestran "DATABASE_URL no configurada"
- **Solución:** 
  1. Verifica que el NAME es exactamente `DATABASE_URL` (mayúsculas)
  2. Verifica que el VALUE es la URL completa sin espacios
  3. Click "Save"
  4. Espera redeploy

**Problema:** "Connection refused" en los logs
- **Solución:**
  1. Railway → Postgres → Status (debe estar **Ready**)
  2. Verifica que la URL es correcta (no hay errores de tipeo)

**Problema:** App inicia pero "Error descargando plantilla" sigue apareciendo
- **Solución:** La BD está configurada pero los papeles templates no están cargados
  - Esto se soluciona con la próxima sesión
  - Por ahora, la persistencia de clientes ya funciona

---

## 🎯 Resultado

Una vez agregada DATABASE_URL:

✅ App inicia sin errores
✅ Clientes se guardan en PostgreSQL
✅ Clientes persisten en redeploys
✅ Próximas sesiones: Cargar datos de papeles modelo

---

## 📞 Soporte

Si tienes dudas:
- Railway Docs: https://docs.railway.app/
- Vercel Docs: https://vercel.com/docs
- Mi documentación: SETUP_PERSISTENCIA.md

**¡Hazme saber cuando esté configurado y podremos probar!**
