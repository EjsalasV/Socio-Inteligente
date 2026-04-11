# 🚀 INTERACTIVE DEPLOYMENT CHECKLIST - April 11, 2026

**Generated:** April 11, 2026  
**Status:** ✅ READY FOR PRODUCTION DEPLOYMENT

---

## ✅ Pre-Deployment Validation (ALL PASSING)

```
Backend Tests:           181/181 ✅
Frontend Build:          SUCCESS ✅
Git Status:              All committed (69f2d83) ✅
CLI Tools:               Railway 4.36.1 ✅, Vercel 50.44.0 ✅
```

---

## 🔐 AUTHENTICATION STATUS

| Tool | Status | Action Required |
|------|--------|------------------|
| **Railway CLI** | ❌ NOT LOGGED IN | `railway login` (one-time) |
| **Vercel CLI** | ✅ LOGGED IN (ejsalasv) | Ready to deploy |

---

## 📋 STEP-BY-STEP DEPLOYMENT

### STEP 1: Login to Railway (One-time, ~30 seconds)

```powershell
# Command
railway login

# What happens:
# 1. Browser will open to railway.app
# 2. Login with your Railway account
# 3. Copy the token from the page
# 4. Paste token back in terminal
# 5. Prompt will confirm: "✅ Logged in as: [your-username]"
```

**⏸️ PAUSE HERE** - Run `railway login` before continuing

---

### STEP 2: Link Railway Project (One-time, ~10 seconds)

```powershell
# Command
railway link

# What happens:
# 1. Terminal will list your Railway projects
# 2. Select "socio-inteligente" (or your backend service name)
# 3. Prompt confirms: "✅ Linked to project: socio-inteligente"

# If you don't see your project, create one in Railway Dashboard first
```

**⏸️ PAUSE HERE** - Run `railway link` before continuing

---

### STEP 3: Create/Verify Railway Environment Variables

**📍 Location:** Railway Dashboard → Your Project → Variables

Set these **8 environment variables** (use strong values for production):

```
# AUTHENTICATION
ENV=production
JWT_SECRET_KEY=your-secure-32-char-key-here-change-me-now-!!!!!
ADMIN_USERNAME=socio_admin_prod_2026
ADMIN_PASSWORD=your-strong-unique-password-here-change-me

# NETWORKING & CORS
ALLOWED_ORIGINS=https://socio-ai-frontend.vercel.app,https://yourdomain.com
SOCIO_ORG_ID=org-socio-main

# LLM (keep existing values or update)
AI_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
```

⚠️ **CRITICAL:** Make sure `ALLOWED_ORIGINS` matches your Vercel domain exactly

**✅ After setting vars:** Go to next step

---

### STEP 4: Deploy Backend to Railway

#### Option A: Automatic Deploy (Recommended)

```powershell
# This pushes to GitHub, Railway detects changes and auto-deploys
git push origin main
```

**Expected behavior:**
- GitHub receives push (no output)
- Railway webhook triggers automatically
- Live logs appear in Railway Dashboard
- ~3-5 minutes for full deployment

#### Option B: Manual Deploy

```powershell
# Manual command to Railway
railway up
```

**While deploying:**
- Watch real-time logs:
  ```powershell
  railway logs -f
  ```
- Should see: `"Application successfully started"` or similar
- Check when ready: `curl http://localhost:8000/health` (test locally first)

**⏸️ WAIT** - Let deployment finish (~5 minutes, check logs)

---

### STEP 5: Verify Backend Deployment

```powershell
# Check health from production
$backendUrl = "https://socio-inteligente-production.up.railway.app"
Invoke-WebRequest -Uri "$backendUrl/health" -Method Get

# Expected response: {"status": "ok"}
```

If health check fails:
- Check Railway logs: `railway logs -f`
- Verify environment variables are set
- Check for errors in startup logs

**✅ If health OK:** Continue to frontend

---

### STEP 6: Deploy Frontend to Vercel

#### Link Vercel Project (One-time)

```powershell
cd frontend
vercel link
```

When prompted:
- **Project name:** `socio-ai-frontend` (or your choice)
- **Directory:** `./` (default, press Enter)
- **Framework:** `Next.js` (default, press Enter)
- **Build cmd:** `npm run build` (default, press Enter)
- **Output directory:** `.next` (default, press Enter)

---

### STEP 7: Set Vercel Environment Variables

**📍 Location:** Vercel Dashboard → Settings → Environment Variables

Set these **5 variables**:

```
NEXT_PUBLIC_API_BASE=https://socio-inteligente-production.up.railway.app
NEXT_PUBLIC_WS_BASE=wss://socio-inteligente-production.up.railway.app
NEXT_PUBLIC_API_TIMEOUT_MS=20000
NEXT_PUBLIC_HEAVY_TIMEOUT_MS=45000
NEXT_PUBLIC_DASHBOARD_AREAS_PAGE_SIZE=8
```

**✅ After saving vars:** Go to next step

---

### STEP 8: Deploy Frontend to Vercel

#### Option A: Automatic Deploy (Recommended)

```powershell
git push origin main
```

Vercel automatically detects changes and redeploys.

#### Option B: Manual Deploy

```powershell
cd frontend
vercel deploy --prod
```

**Wait for:** `✅ Production: https://socio-ai-frontend.vercel.app [copied]`

**⏸️ WAIT** - Frontend building (~2-3 minutes)

---

### STEP 9: Verify Frontend Deployment

```powershell
# Open in browser
start https://socio-ai-frontend.vercel.app

# Or use curl to check status
$frontendUrl = "https://socio-ai-frontend.vercel.app"
(Invoke-WebRequest -Uri $frontendUrl).StatusCode  # Should return 200

# Also check Vercel logs
vercel logs --tail
```

**Should show:**
- Landing page loads
- No "Cannot GET /" errors
- No console errors (open DevTools F12)

**✅ If page loads:** Continue to integration testing

---

### STEP 10: CORS & WebSocket Integration Test

#### 10a: Test CORS Preflight

```powershell
$backendUrl = "https://socio-inteligente-production.up.railway.app"
$frontendUrl = "https://socio-ai-frontend.vercel.app"

$response = Invoke-WebRequest `
  -Uri "$backendUrl/auth/login" `
  -Method Options `
  -Headers @{
    "Origin" = $frontendUrl
    "Access-Control-Request-Method" = "POST"
    "Access-Control-Request-Headers" = "Content-Type"
  } `
  -SkipHttpErrorCheck

$response.Headers | Select-Object "Access-Control-Allow-Origin"
# Should show: https://socio-ai-frontend.vercel.app
```

#### 10b: Test WebSocket from Browser Console

1. Open https://socio-ai-frontend.vercel.app
2. Press F12 (DevTools)
3. Go to **Console** tab
4. Paste this:

```javascript
// Test WebSocket connection
const token = sessionStorage.getItem("socio_auth_token") || "test-token";
const wsUrl = `wss://socio-inteligente-production.up.railway.app/ws/clientes/cliente_demo?module=dashboard&token=${token}`;

const ws = new WebSocket(wsUrl);

ws.onopen = () => {
  console.log("✅ WebSocket CONNECTED");
};

ws.onerror = (e) => {
  console.error("❌ WebSocket ERROR:", e);
};

ws.onmessage = (m) => {
  console.log("📨 Message received:", m.data);
};
```

**If you see:** `✅ WebSocket CONNECTED` → Integration working ✅

---

### STEP 11: Production Validation Checklist

#### Backend Checks
- [ ] `/health` endpoint responds with 200
- [ ] Login endpoint accepts credentials
- [ ] Rate limiting active (test with 10 rapid requests to `/auth/login`)
- [ ] No 5xx errors in `railway logs -f`
- [ ] Database connections working (if using Supabase)

#### Frontend Checks
- [ ] Landing page loads (< 3 seconds)
- [ ] No "Cannot GET" errors
- [ ] Console is clean (F12 → Console tab)
- [ ] No CORS errors
- [ ] Vercel logs show successful deployment

#### Integration Checks
- [ ] Login workflow: username/password → token issued
- [ ] Dashboard loads after login
- [ ] WebSocket connects (checked in Step 10b)
- [ ] Real-time updates work (open 2 browser tabs, make change in one)
- [ ] Rate limiting blocks excessive requests

**✅ If all pass:** You're live! 🎉

---

### STEP 12: Setup Monitoring (Optional but Recommended)

#### Railway Monitoring
```powershell
# Real-time logs with search
railway logs -f --search "error"

# Check deployment history
railway logs --deployment-history

# If something breaks, rollback:
git revert HEAD
git push origin main
# Railway re-deploys automatically
```

#### Vercel Monitoring
- Dashboard → Deployments → Click a deployment → Logs
- Or: `vercel logs --tail` (real-time)

#### Free Uptime Monitoring
- Sign up at https://uptimerobot.com
- Monitor: `https://socio-inteligente-production.up.railway.app/health`
- Alert to your email if site goes down

---

## 🆘 Troubleshooting Common Issues

| Problem | Check | Fix |
|---------|-------|-----|
| CORS 403 | ALLOWED_ORIGINS in Railway | Exact match with Vercel domain (no typos) |
| WebSocket "Reconectando" | JWT_SECRET_KEY match | Regenerate tokens, clear browser cache |
| "0 en equipo" seen | WebSocket auth | Check browser console for 401 errors |
| API Timeout | Large payloads | Use pagination (already implemented) |
| Rate limit blocking | Legitimate traffic | Check RATE_LIMIT_* env vars in Railway |
| Frontend won't build | Vercel logs | `vercel logs --tail` for specific error |
| Backend won't start | Railway logs | `railway logs -f` for specific error |

---

## 📊 Final Status

```
┌─────────────────────────────────────┐
│  DEPLOYMENT READINESS REPORT        │
├─────────────────────────────────────┤
│  Backend:      181 tests ✅         │
│  Frontend:     build OK ✅          │
│  CLI Tools:    installed ✅         │
│  Git:          sync'd ✅            │
│  Estimated Time: 20-30 min          │
└─────────────────────────────────────┘
```

---

**Let's go live! 🚀**

Next: Start with **STEP 1: `railway login`**

