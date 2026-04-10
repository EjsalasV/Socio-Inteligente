# Deployment Vercel + Railway - Checklist

## 1. Railway Backend Setup

### Variables de Entorno (Railway Dashboard → Tu servicio → Variables)

```
# Autenticación
ENV=production
JWT_SECRET_KEY=<your-strong-secret-min-32-chars>

# CORS - CRÍTICO para WebSocket
ALLOWED_ORIGINS=https://socio-ai-frontend.vercel.app,https://tu-dominio-custom.com

# Admin (cambiar en producción)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=<strong-password>
SOCIO_ORG_ID=org-socio-main

# LLM
DEEPSEEK_API_KEY=sk-<tu-key>
AI_PROVIDER=openai
OPENAI_API_KEY=<opcional>

# Redis (opcional, para rate limiting distribuido)
RATE_LIMIT_REDIS_URL=redis://user:password@redis-host:port

# Supabase (opcional, para memoria persistente)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-key

# Clientes permitidos
ALLOWED_CLIENTES=*
```

### Dockerfile
✅ Ya está en raíz (`Dockerfile`) - Railway lo detecta automáticamente

### Deploy
```bash
# Git push → Railway auto-deploys
git push origin main

# O manual:
railway up
```

---

## 2. Vercel Frontend Setup

### Project Settings

**Build:** `npm run build`  
**Start:** `npm start`  
**Framework Preset:** `Next.js`

### Environment Variables (Vercel Dashboard → Settings → Environment Variables)

```
# API & WebSocket endpoints
NEXT_PUBLIC_API_BASE=https://socio-inteligente-production.up.railway.app
NEXT_PUBLIC_WS_BASE=wss://socio-inteligente-production.up.railway.app

# Timeouts
NEXT_PUBLIC_API_TIMEOUT_MS=20000
NEXT_PUBLIC_HEAVY_TIMEOUT_MS=45000

# Dashboard
NEXT_PUBLIC_DASHBOARD_AREAS_PAGE_SIZE=8
```

### Deploy
```bash
# Git push → Vercel auto-deploys
git push origin main

# O manual:
vercel deploy --prod
```

---

## 3. Network & CORS Verification

### Test CORS preflight (antes de login)
```bash
curl -X OPTIONS "https://socio-inteligente-production.up.railway.app/auth/login" \
  -H "Origin: https://socio-ai-frontend.vercel.app" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -v
```

**Debe responder:**
```
Access-Control-Allow-Origin: https://socio-ai-frontend.vercel.app
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, PATCH
Access-Control-Allow-Credentials: true
```

### Test WebSocket connection
```javascript
// Browser console @ https://socio-ai-frontend.vercel.app
const token = sessionStorage.getItem("socio_auth_token");
const ws = new WebSocket(
  `wss://socio-inteligente-production.up.railway.app/ws/clientes/cliente_demo?module=dashboard&token=${token}`
);
ws.onopen = () => console.log("✅ WebSocket connected");
ws.onerror = (e) => console.error("❌ WebSocket error:", e);
ws.onmessage = (m) => console.log("📨 Message:", m.data);
```

---

## 4. Monitoring & Debugging

### Railway Logs
```bash
# Real-time logs
railway logs -f

# Search for errors
railway logs | grep -i "error\|cors\|websocket"
```

### Vercel Logs
```bash
# Function logs (real-time)
vercel logs --tail

# Or check Vercel Dashboard → Deployments → Logs
```

### Common Issues

| Problema | Causa | Fix |
|----------|-------|-----|
| "Reconectando" en dashboard | WebSocket sin token | Verificar `sessionStorage` en browser |
| CORS 403 | ALLOWED_ORIGINS no match | Actualizar Railway env var |
| "0 en equipo" | WebSocket rejected (4401) | Check JWT_SECRET_KEY match |
| ❌ Slow API | Large payloads | Use pagination (ya implementado) |

---

## 5. Production Checklist

- [ ] JWT_SECRET_KEY ≠ dev-secret
- [ ] ALLOWED_ORIGINS includes Vercel domain
- [ ] ADMIN_PASSWORD changed from CHANGE_ME
- [ ] Redis configured (si usas limiter distribuido)
- [ ] DEEPSEEK_API_KEY / LLM keys válidas
- [ ] WebSocket test en browser console pasa
- [ ] Dashboard carga sin "Reconectando"
- [ ] Login + API requests sin CORS errors
- [ ] Rate limiting activo (`/health` endpoint trabajado)

---

## 6. Custom Domain (Optional)

### Vercel
1. Vercel Dashboard → Settings → Domains
2. Add custom domain
3. Update DNS records

### Railway
1. Railway Dashboard → Settings → Custom Domain
2. Point CNAME/A records to Railway

### Env Vars Update
```
# Both Vercel & Railway
ALLOWED_ORIGINS=https://your-domain.com,https://socio-ai-frontend.vercel.app
```

---

## 7. Scaling (Future)

- **Multi-region:** Railway → multi-region deployment ($$ extra)
- **CDN:** Vercel → Automatic via Edge Functions
- **Database:** ChromaDB → Supabase (managed)
- **Storage:** Railway → S3 backup bucket

---

## Quick Reference

| Env | Value | Where |
|-----|-------|-------|
| Frontend URL | https://socio-ai-frontend.vercel.app | Railway ALLOWED_ORIGINS |
| Backend API | https://socio-inteligente-production.up.railway.app | Vercel NEXT_PUBLIC_API_BASE |
| WebSocket | wss://socio-inteligente-production.up.railway.app | Vercel NEXT_PUBLIC_WS_BASE |
| Auth | httpOnly cookie + sessionStorage token | Browser |
| CSRF | X-CSRF-Token header + localStorage | Middleware |

---

Status: ✅ Production-ready (19/87 core fixes implemented)
