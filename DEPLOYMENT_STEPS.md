# 🚀 Deployment Guide - Railway + Vercel - April 2026

**Estado Actual:**
- ✅ Backend: 181/181 tests pasando
- ✅ Frontend: Next.js 16.2.1 compilado sin errores
- ✅ Latest Commit: 380ab23 (Holdings Cascade Analysis)

---

## PASO 1: Railway Backend Deploy

### 1.1 Prerequisites
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login to Railway
railway login

# Link project (si aún no está linked)
railway link
```

### 1.2 Set Production Environment Variables

En Railway Dashboard → Tu Servicio → Variables:

```
# AUTH
ENV=production
JWT_SECRET_KEY=your-secure-32-char-key-here-!!!!!
ADMIN_USERNAME=socio_admin_prod_2026
ADMIN_PASSWORD=your-strong-password-here

# CORS & Networking
ALLOWED_ORIGINS=https://socio-ai-frontend.vercel.app,https://yourdomain.com
SOCIO_ORG_ID=org-socio-main

# LLM Integration
AI_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
DEEPSEEK_API_KEY=sk-your-key-here

# Redis (optional, for distributed rate limiting)
RATE_LIMIT_REDIS_URL=redis://xxx

# Supabase (optional, for persistent memory)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=xxx
```

### 1.3 Deploy Backend

```bash
# Option A: Auto-deploy via git push
git push origin main
# Railway webhook triggers auto-deploy

# Option B: Manual deploy
railway up
```

**Verificar deployment:**
```bash
# Real-time logs
railway logs -f

# Check if API is responding
curl https://socio-inteligente-production.up.railway.app/health
# Should return: {"status": "ok"}
```

---

## PASO 2: Vercel Frontend Deploy

### 2.1 Prerequisites

```bash
# Install Vercel CLI
npm i -g vercel

# Login to Vercel
vercel login
```

### 2.2 Link Vercel Project

```bash
cd frontend
vercel link
```

When prompted:
- **Project Name:** `socio-ai-frontend` (or your choice)
- **Project Path:** `frontend/`
- **Framework Preset:** Next.js
- **Build Command:** `npm run build` (default, press Enter)
- **Output Directory:** `.next` (default, press Enter)

### 2.3 Set Production Environment Variables

En Vercel Dashboard → Settings → Environment Variables:

```
NEXT_PUBLIC_API_BASE=https://socio-inteligente-production.up.railway.app
NEXT_PUBLIC_WS_BASE=wss://socio-inteligente-production.up.railway.app
NEXT_PUBLIC_API_TIMEOUT_MS=20000
NEXT_PUBLIC_HEAVY_TIMEOUT_MS=45000
NEXT_PUBLIC_DASHBOARD_AREAS_PAGE_SIZE=8
```

### 2.4 Deploy Frontend

```bash
cd frontend

# Option A: Auto-deploy via git push
git push origin main
# Vercel webhook triggers auto-deploy

# Option B: Manual deploy
vercel deploy --prod
```

**Verificar deployment:**
```bash
# Check Vercel Dashboard → Deployments
# Or open: https://socio-ai-frontend.vercel.app

# Check build logs
vercel logs --tail
```

---

## PASO 3: Integration Testing

### 3.1 CORS Preflight Verification

```bash
# From any terminal, test CORS
curl -X OPTIONS "https://socio-inteligente-production.up.railway.app/auth/login" \
  -H "Origin: https://socio-ai-frontend.vercel.app" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -v
```

**Expected Response Headers:**
```
Access-Control-Allow-Origin: https://socio-ai-frontend.vercel.app
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, PATCH, OPTIONS
Access-Control-Allow-Credentials: true
```

### 3.2 Manual API Test

```bash
# Test login endpoint
curl -X POST "https://socio-inteligente-production.up.railway.app/auth/login" \
  -H "Content-Type: application/json" \
  -H "Origin: https://socio-ai-frontend.vercel.app" \
  -d '{"username": "admin", "password": "your-admin-password"}'
```

**Expected Response:**
```json
{
  "status": "success",
  "data": {
    "access_token": "eyJhbG...",
    "token_type": "bearer"
  }
}
```

### 3.3 WebSocket Connection Test (Browser Console)

1. Open https://socio-ai-frontend.vercel.app
2. Open Browser DevTools (F12)
3. Go to Console tab
4. Run:

```javascript
// Get your auth token
const token = sessionStorage.getItem("socio_auth_token");

// Connect to WebSocket
const ws = new WebSocket(
  `wss://socio-inteligente-production.up.railway.app/ws/clientes/cliente_demo?module=dashboard&token=${token}`
);

ws.onopen = () => console.log("✅ WebSocket connected!");
ws.onerror = (e) => console.error("❌ Error:", e);
ws.onmessage = (m) => console.log("📨 Message:", JSON.parse(m.data));
```

**If it works:** ✅ You'll see "WebSocket connected!" in console

---

## PASO 4: Production Validation Checklist

### Backend
- [ ] API responds to `/health` endpoint
- [ ] Login endpoint accepts valid credentials
- [ ] JWT tokens are being issued (> 300 chars)
- [ ] CORS headers are correct for Vercel origin
- [ ] Database connections working (Supabase, if used)
- [ ] LLM integration responding (if configured)
- [ ] Redis cache working (if configured)
- [ ] All audit program endpoints responding
- [ ] Rate limiting is active (test with 10 rapid requests)

### Frontend
- [ ] Page loads without "Cannot GET /" errors
- [ ] Login form displays
- [ ] Authentication works (valid credentials → dashboard)
- [ ] Dashboard loads client list
- [ ] WebSocket connection established (no "Reconectando" message)
- [ ] Pagination works on papeles-trabajo
- [ ] Error pages render correctly (test with random URL)
- [ ] Performance is acceptable (<3s load time)

### Integration
- [ ] Frontend tokens accepted by backend
- [ ] Real-time updates work (WebSocket messages)
- [ ] Role-based access control working
- [ ] Audit validators return correct results
- [ ] No CORS errors in browser console
- [ ] No unauthorized 401/403 errors

---

## PASO 5: Monitoring & Alerts Setup

### Railway
```bash
# Set up email alerts
railway env:export > .env.local

# Monitor logs continuously
railway logs -f --follow --until="1 hour ago"
```

### Vercel
- Go to Vercel Dashboard → Settings → Alerts
- Enable: Bad Gateway (5xx), High Error Rate

### Recommended: Add Uptime Monitoring
```bash
# Use free service like UptimeRobot
# Configure: https://socio-inteligente-production.up.railway.app/health
# Check interval: 5 minutes
# Alert email: your-ops-email@company.com
```

---

## PASO 6: Rollback Plan (if needed)

### Quick Rollback to Previous Version

**Railway:**
```bash
# Check deployment history
railway logs --deployment-history

# Redeploy previous commit
git revert HEAD
git push origin main
# Railway auto-deploys
```

**Vercel:**
```bash
# Check Deployments tab in Vercel Dashboard
# Click "Promote" on any previous deployment to make it production
```

---

## Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| "Cannot GET /" on frontend | Build failed silently | Check `vercel logs --tail` |
| CORS 403 on login | ALLOWED_ORIGINS mismatch | Update Railway env var |
| WebSocket "Reconectando" | JWT_SECRET_KEY mismatch | Regenerate tokens |
| "0 en equipo" | WebSocket rejected | Check browser console for 401 |
| API Timeout (>30s) | Large payload or slow DB | Check database connection |
| Rate limit blocking | Legitimate traffic > limits | Adjust RATE_LIMIT_* env vars |

---

## Final Checklist

- [ ] Backend deployed to Railway (git push triggered auto-deploy)
- [ ] Frontend deployed to Vercel (git push triggered auto-deploy)
- [ ] All environment variables set in both platforms
- [ ] CORS test passed (`curl` preflight request)
- [ ] Login works (valid credentials accepted)
- [ ] WebSocket connects (no 401/403 errors)
- [ ] Dashboard loads with client data
- [ ] Rate limiting is active
- [ ] Logs accessible (railway logs -f, vercel logs --tail)
- [ ] Monitoring/alerts configured
- [ ] Team notified that production is live 🚀

---

**Estimated Deploy Time: 15-20 minutes**
**Current Status: READY FOR DEPLOYMENT** ✅

