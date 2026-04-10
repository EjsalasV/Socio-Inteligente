# ✅ Pre-Deployment Checklist

Verifica estos puntos ANTES de hacer `git push` a Vercel + Railway

---

## 🚨 CRITICAL (Must-Have)

- [ ] **JWT_SECRET_KEY** es diferente de `dev-secret-*` en Railway
  ```
  Env → JWT_SECRET_KEY = long-random-string-min-32-chars
  ```

- [ ] **ALLOWED_ORIGINS** en Railway includes Vercel domain
  ```
  Env → ALLOWED_ORIGINS = https://socio-ai-frontend.vercel.app
  ```

- [ ] **NEXT_PUBLIC_WS_BASE** en Vercel apunta a Railway
  ```
  Env → NEXT_PUBLIC_WS_BASE = wss://socio-inteligente-production.up.railway.app
  ```

- [ ] **NEXT_PUBLIC_API_BASE** en Vercel apunta a Railway
  ```
  Env → NEXT_PUBLIC_API_BASE = https://socio-inteligente-production.up.railway.app
  ```

- [ ] **ADMIN_PASSWORD** cambiado del default `CHANGE_ME`
  ```
  Env → ADMIN_PASSWORD = <strong-unique-password>
  ```

- [ ] Tests locales pasan (`pytest -q`)
  ```bash
  cd /path/to/project
  python -m pytest -q --tb=no
  # Should show: ✅ 148 passed
  ```

- [ ] Frontend build local OK (`npm run build`)
  ```bash
  cd frontend
  npm run build
  # Should show: ✅ Compiled successfully
  ```

---

## 🔒 SECURITY

- [ ] No hay credenciales en `.env` committed a git (usa `.env.example`)
- [ ] JWT_SECRET_KEY > 32 caracteres
- [ ] ALLOWED_ORIGINS no includes `*` (específico a Vercel domain)
- [ ] ADMIN_USERNAME no es `admin` /`root` (sugiero `socio_admin_<random>`)
- [ ] Credentials for Supabase/Redis/LLM no están en código, solo env vars

---

## 🧪 FUNCTIONALITY

- [ ] Login funciona (credentials: admin user)
- [ ] Dashboard carga sin "Reconectando"
- [ ] WebSocket muestra usuarios "En línea" (> 0 en equipo)
- [ ] Pagination funciona en dashboard + papeles-trabajo
- [ ] Rate limit bloquea requests excesivos (5/min login)
- [ ] Error pages (404, 500) se muestran correctamente

---

## 🌐 INFRASTRUCTURE

- [ ] Railway backend service está deployable (Dockerfile+git)
- [ ] Vercel project linked a GitHub
- [ ] Domain configured (o usando `*.vercel.app`)
- [ ] Environment secrets en ambas plataformas (no hardcoded)

---

## 📊 MONITORING SETUP (Optional but recommended)

- [ ] Railway logs accessible (`railway logs -f`)
- [ ] Vercel logs accessible (Dashboard → Deployments → Logs)
- [ ] Error tracking enabled (Sentry, etc.)

---

## 🚀 DEPLOYMENT STEPS

### 1. Final verify en local

```bash
# Backend
cd /path
export JWT_SECRET_KEY="test-secret-32-chars-minimum!!!!"
python -m pytest -q --tb=no
# ✅ 148 passed

# Frontend
cd frontend
npm run build
# ✅ Compiled successfully
npm run check:types-sync
# ✅ no diffs
```

### 2. Push a GitHub main (si uses auto-deploy)

```bash
git add .
git commit -m "Production ready: 19/87 security+performance fixes"
git push origin main
```

**Vercel & Railway auto-deploy** en detectar cambios en main

### 3. OR Manual deploy

**Railway:**
```bash
railway link  # Link to Railway project
railway up    # Deploy current branch
```

**Vercel:**
```bash
vercel link   # Link to Vercel project
vercel deploy --prod  # Deploy to production
```

### 4. Verify post-deployment

```bash
# Check backend health
curl https://socio-inteligente-production.up.railway.app/health
# Expected: {"status": "ok", "rate_limit_backend": "redis" or "memory"}

# Check frontend loads
open https://socio-ai-frontend.vercel.app
# Expected: Login page loads without errors
```

### 5. Login test

1. Go to `https://socio-ai-frontend.vercel.app`
2. Login with ADMIN_USERNAME / ADMIN_PASSWORD
3. Verify dashboard loads
4. Open browser DevTools Console
5. Check `sessionStorage.getItem("socio_auth_token")` returns token
6. Header should show "En línea" + count > 0

---

## 🔧 TROUBLESHOOTING

| Issue | Cause | Fix |
|-------|-------|-----|
| "Reconectando" forever | WebSocket can't auth | Check sessionStorage has token, verify JWT_SECRET_KEY matches |
| CORS 403 on login | ALLOWED_ORIGINS mismatch | Update Railway ALLOWED_ORIGINS to include `https://socio-ai-frontend.vercel.app` |
| "0 en equipo" | WebSocket connection failed | Check browser console for WebSocket errors, look at Railway logs |
| Blank page on load | Frontend build failed | Check Vercel deployment logs, rebuild with `vercel deploy --prod` |
| Rate limit blocks legitimate | Rate limit too strict | Adjust LIMITS in backend/middleware/rate_limit.py if needed |

---

## 📋 CUSTOM DOMAIN (OPTIONAL)

If using custom domain instead of `*.vercel.app` + `*.railway.app`:

1. **Vercel:** Settings → Domains → Add `your-domain.com`
2. **Railway:** Settings → Custom Domain → Add `api.your-domain.com`
3. **Railway env:** Update ALLOWED_ORIGINS
   ```
   ALLOWED_ORIGINS=https://your-domain.com,https://socio-ai-frontend.vercel.app
   ```
4. **Vercel env:** Update API URLs
   ```
   NEXT_PUBLIC_API_BASE=https://api.your-domain.com
   NEXT_PUBLIC_WS_BASE=wss://api.your-domain.com
   ```

---

## ✅ SIGN-OFF

- [ ] All critical items checked
- [ ] Tests passing locally
- [ ] Deployment plan reviewed
- [ ] Team informed

**Status:** Ready for `git push main` → Auto-deploy to Vercel + Railway ✅

---

**Contact:** Check SESSION_SUMMARY.md for quick reference  
**Questions:** See DEPLOYMENT_VERCEL_RAILWAY.md for detailed setup
