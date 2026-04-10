# 🎯 Plan de Acción Ejecutivo - Nuevo Socio AI

**Generado:** 10 abril 2026  
**Stack:** FastAPI + Next.js  
**Urgencia:** CRÍTICA

---

## ⚠️ HOTFIX REQUERIDO (24-48 horas)

### 1. **JWT Secret Management** 🔴 CRÍTICO
**Archivo:** `backend/auth.py`

```python
# CAMBIO REQUERIDO:

# ❌ ANTES (Lines 14-20)
if not _SECRET:
    if os.getenv("CI") or os.getenv("EXPORT_OPENAPI"):
        _SECRET = secrets.token_urlsafe(48)  # INSEGURO!
    else:
        raise RuntimeError("JWT_SECRET_KEY no esta configurado...")

# ✅ DESPUÉS
_SECRET = (os.getenv("JWT_SECRET_KEY") or "").strip()
if not _SECRET:
    raise RuntimeError(
        "FATAL: JWT_SECRET_KEY debe estar configurado en TODOS los ambientes.\n"
        "Usa: export JWT_SECRET_KEY=$(openssl rand -base64 32)\n"
        "O usa: aws secretsmanager get-secret-value --secret-id socio-jwt-secret"
    )
```

**Pasos:**
1. Generar secreto UNA VEZ: `openssl rand -base64 32`
2. Guardar en Secret Manager (Vault / AWS Secrets Manager / GitHub Secrets)
3. No regenerar cada build
4. Implementar rotación automática cada 90 días

**Tiempo:** 2 horas

---

### 2. **Remover Credenciales Hardcodeadas** 🔴 CRÍTICO
**Archivo:** `backend/routes/auth.py` + `frontend/app/page.tsx`

```python
# ❌ ANTES
_ADMIN_USER = os.getenv("ADMIN_USERNAME") or "joaosalas123@gmail.com"
_ADMIN_PASS = os.getenv("ADMIN_PASSWORD") or "1234"

# ✅ DESPUÉS
_ADMIN_USER = os.getenv("ADMIN_USERNAME", "").strip()
_ADMIN_PASS = os.getenv("ADMIN_PASSWORD", "").strip()

if not _ADMIN_USER or not _ADMIN_PASS:
    raise RuntimeError(
        "ADMIN_USERNAME y ADMIN_PASSWORD deben estar definidos.\n"
        "NUNCA usar credenciales por defecto en credenciales."
    )
```

**Pasos en Frontend:**
```typescript
// ❌ ANTES (frontend/app/page.tsx:21-23)
const [username, setUsername] = useState<string>("joaosalas123@gmail.com");
const [password, setPassword] = useState<string>("1234");

// ✅ DESPUÉS
const [username, setUsername] = useState<string>("");
const [password, setPassword] = useState<string>("");
```

**Tiempo:** 1 hora

---

### 3. **Implementar Rate Limiting** 🔴 CRÍTICO
**Archivo:** Crear middleware, aplicar a `/auth/login`

```python
# backend/middleware/rate_limit_middleware.py (NUEVO)
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# backend/main.py (MODIFICAR)
from backend.middleware.rate_limit_middleware import limiter

app = FastAPI()
app.state.limiter = limiter
app.include_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# backend/routes/auth.py (APLICAR DECORATOR)
@router.post("/login", response_model=ApiResponse)
@limiter.limit("5/minute")  # 5 intentos por minuto por IP
def login(request: Request, payload: LoginRequest) -> ApiResponse:
    # ... rest of code
```

**Pasos:**
1. Instalar: `pip install slowapi`
2. Configurar limiter global en main.py
3. Aplicar a `/auth/login`, `/chat/**`, `/api/hallazgos/**`
4. Retornar 429 Too Many Requests con Retry-After header

**Tiempo:** 3 horas

---

### 4. **Mover Token a httpOnly Cookie** 🔴 CRÍTICO
**Ubicaciones:** Backend auth + Frontend API client

```python
# backend/routes/auth.py (Response)
from fastapi.responses import JSONResponse

@router.post("/login", response_model=ApiResponse)
def login(payload: LoginRequest) -> JSONResponse:
    # ... auth logic ...
    response = JSONResponse(content={
        "status": "ok",
        "data": {"token_type": "bearer", "expires_in": ttl}
    })
    
    # AGREGAR TOKEN EN COOKIE HTTPONLY
    response.set_cookie(
        key="socio-auth",
        value=token,
        httponly=True,           # No accesible desde JS
        secure=True,             # HTTPS only
        samesite="Strict",       # CSRF protection
        max_age=ttl,
        path="/"
    )
    return response
```

```typescript
// frontend/lib/api.ts (MODIFICAR)
function getToken(): string | null {
    // ❌ ANTES: localStorage.getItem("socio_token")
    
    // DESPUÉS: Token ahora en cookie httpOnly automáticamente
    // No necesita JS para enviar, incluido en request automáticamente
    // Eliminar getToken() llamadas manuales
    return null;
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
    const headers = new Headers(init?.headers);
    
    // ❌ ANTES:
    // if (token) headers.set("Authorization", `Bearer ${token}`);
    
    // DESPUÉS: Cookie se envía automáticamente (no necesita JS)
    // Remover lógica de token manual
}
```

**Pasos:**
1. Backend: Return token en httpOnly cookie
2. Frontend: Remover localStorage.getItem("socio_token")
3. Frontend: Remover manual header setting
4. Test con DevTools: Cookie debe tener flags HttpOnly + Secure + SameSite

**Tiempo:** 4 horas

---

### 5. **Agregar CSRF Tokens** 🔴 CRÍTICO
**Stack:** FastAPI + Next.js middleware

```python
# backend/middleware/csrf.py (NUEVO)
from fastapi import Request, HTTPException
from fastapi.responses import Response
import secrets
import time

class CSRFMiddleware:
    def __init__(self, app):
        self.app = app
        self.tokens: dict[str, tuple[str, float]] = {}
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        # GET: Generar y retornar token CSRF
        if request.method == "GET":
            token = secrets.token_urlsafe(32)
            self.tokens[token] = (token, time.time() + 3600)  # 1 hora
            scope["csrf_token"] = token
            await self.app(scope, receive, send)
            return
        
        # POST/PUT/DELETE: Validar token CSRF
        if request.method in {"POST", "PUT", "DELETE", "PATCH"}:
            token = request.headers.get("X-CSRF-Token")
            if not token or token not in self.tokens:
                raise HTTPException(status_code=403, detail="CSRF token inválido")
            del self.tokens[token]
        
        await self.app(scope, receive, send)

# backend/main.py
app.add_middleware(CSRFMiddleware)
```

```typescript
// frontend/lib/csrf.ts (NUEVO)
export async function getCsrfToken(): Promise<string> {
    const response = await fetch("/api/csrf-token", { method: "GET" });
    const data = await response.json();
    return data.token;
}

// frontend/lib/api.ts (MODIFICAR apiFetch)
async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
    const method = String(init?.method || "GET").toUpperCase();
    const headers = new Headers(init?.headers);
    
    if (method !== "GET") {
        const csrfToken = await getCsrfToken();
        headers.set("X-CSRF-Token", csrfToken);
    }
    
    // ... rest of code
}
```

**Tiempo:** 5 horas

---

## 📋 TASKS SECUENCIADAS

### Semana 1: Seguridad Crítica

**LUNES-MARTES** (Bloqueadores)
- [ ] **Task 1:** JWT Secret Management (Auth renovation)
  - Crear Secret Manager config (Vault/AWS)
  - Regenerate secret (store securely)
  - Update CI/CD pipeline
  - Test in staging

- [ ] **Task 2:** Remover Hardcoded Credentials
  - Remove from auth.py
  - Remove from login page
  - Update env examples
  - Verify identity store fallback

**MIÉRCOLES** (Rate Limiting + Auth Flow)
- [ ] **Task 3:** Rate Limiting Implementation
  - Install slowapi
  - Create middleware
  - Apply to auth/login
  - Test bruteforce protection

**JUEVES-VIERNES** (Token Security)
- [ ] **Task 4:** Move Token to httpOnly Cookie
  - Backend: implement set_cookie logic
  - Frontend: remove localStorage
  - Remove manual header setting
  - Integration tests

- [ ] **Task 5:** CSRF Token Implementation
  - Backend: create CSRF middleware
  - Frontend: getCsrfToken hook
  - Apply to all POST/PUT/DELETE
  - Test in browser

**TESTING INTEGRACIÓN**
- [ ] Manual auth flow testing
- [ ] Verify tokens en cookies (DevTools)
- [ ] Verify CSRF required
- [ ] Load testing (rate limit)

---

### Semana 2: Arquitectura Crítica

**LUNES-MARTES** (RAG Service Separation)
- [ ] **Task 6:** Separate RAG from Chat
  - Create RagService class (only retrieve)
  - Create LlmService class (only generate)
  - Create ChatService composer
  - Migrate rag_chat_service.py callers

**MIÉRCOLES-VIERNES** (Event Architecture)
- [ ] **Task 7:** Event-Driven Core
  - Implement event store
  - All mutations emit events
  - realtime_collab_service subscribes
  - Background tasks subscribe

**TESTING**
- [ ] Unit tests for services
- [ ] Integration tests for events
- [ ] Realtime collaboration tests

---

### Semana 3: Critical Audit Fixes

**LUNES-MARTES** (File Safety)
- [ ] **Task 8:** File Upload Security
  - Validate cliente_id (alphanumeric + _)
  - Add ClamAV scanning
  - Validate file magic bytes
  - Test path traversal mitigations

**MIÉRCOLES** (CORS)
- [ ] **Task 9:** CORS Hardening
  - Validate origin URLs (URL parsing)
  - Only allow https in production
  - Add origin whitelist validation
  - Remove unused expose headers

**JUEVES** (Repository Pattern)
- [ ] **Task 10:** Abstract Repository
  - Create Repository interface
  - Move Path operations to repository
  - Dependency inject repository
  - Prepare for DB migration

**VIERNES** (Documentation)
- [ ] Document all changes
- [ ] Update SECURITY.md
- [ ] Create incident response playbook

---

### Semana 4: Performance Fixes

**LUNES-MARTES** (Dashboard Pagination)
- [ ] **Task 11:** Dashboard Endpoints Split
  - Split get_dashboard into:
    - /dashboard/kpis
    - /dashboard/areas
    - /dashboard/workflow
    - /dashboard/materialidad
  - Implement pagination
  - Add caching headers

**MIÉRCOLES** (RAG Caching)
- [ ] **Task 12:** RAG Query Caching
  - Add Redis cache layer
  - TTL=1 hour
  - Invalidate on document ingest
  - Monitor cache hit rate

**JUEVES-VIERNES** (Frontend Improvements)
- [ ] **Task 13:** React Query Implementation
  - Replace custom hooks
  - Central cache management
  - Deduplication of requests
  - Retry logic

**TESTING**
- [ ] Performance profiling
- [ ] Load testing dashboard
- [ ] Cache invalidation tests

---

### Semana 5: Testing Infrastructure

**LUNES-MARTES** (LLM/RAG Testability)
- [ ] **Task 14:** Service Testability
  - Inject LLM client
  - Create mock providers
  - Unit tests for services
  - Fix threading issues (rate limiter)

**MIÉRCOLES-JUEVES** (E2E Testing)
- [ ] **Task 15:** End-to-End Tests (Playwright)
  - Login flow
  - Client creation
  - Chat interaction
  - File upload
  - Critical workflows

**VIERNES** (Integration)
- [ ] **Task 16:** OpenAPI Schema Sync
  - Auto-generate frontend types
  - Validate types in CI
  - Update tests

---

## 📊 Metrics to Track

### Security Metrics
```
JWT Secret Rotation:       [ ] Daily in staging, weekly in prod
Rate Limit Effectiveness:  [ ] <1% bruteforce attempts succeed
CSRF Token Coverage:       [ ] 100% of POST/PUT/DELETE
Token Leakage:            [ ] 0 tokens in logs/errors
```

### Performance Metrics
```
Dashboard Load Time:       [ ] <2s (from 5-10s)
Dashboard Payload Size:    [ ] <500KB (from 5-10MB)
RAG Cache Hit Rate:        [ ] >60%
First Contentful Paint:    [ ] <1.5s
```

### Code Quality
```
Test Coverage:             [ ] >70% (from ~0%)
Critical Bugs:             [ ] 0 (from 18)
Code Smells:               [ ] <5 (from 18)
```

---

## 📝 Checklist de Validación

### Pre-Deployment
- [ ] All hotfixes implemented
- [ ] Security audit passed
- [ ] Performance tests passed (< 2s dashboard load)
- [ ] No hardcoded credentials in codebase
- [ ] All env vars documented
- [ ] Error messages don't leak info

### Post-Deployment
- [ ] Monitor error rates (< 1%)
- [ ] Check rate limit metrics
- [ ] Verify token security (HttpOnly set)
- [ ] Confirm CSRF tokens sent
- [ ] Performance metrics baseline

### Ongoing
- [ ] Weekly security scanning (bandit/semgrep)
- [ ] Monthly dependency updates
- [ ] Quarterly penetration testing
- [ ] Continuous monitoring of error logs

---

## 💰 Estimación de Esfuerzo

| Semana | Focus | Horas | Personas |
|--------|-------|-------|----------|
| 1 | Seguridad Crítica | 40 | 2 (Backend/Frontend) |
| 2 | Arquitectura | 35 | 2 |
| 3 | Audit Fixes | 30 | 2 |
| 4 | Performance | 25 | 2 |
| 5 | Testing | 30 | 3 (2 QA) |
| **Total** | | **160** | **~2.5 people** |

**Timeline:** 5 semanas (1 mes y 1 semana) con equipo de 2-3 personas

---

## 🚨 Risk Mitigation

### Si no se hacen cambios
- **Week 1:** Application vulnerable to multiple exploits
- **Week 2:** Data breach likely (session hijacking)
- **Week 3:** Regulatory/compliance violation (if audited)
- **Week 4+:** Reputation damage, loss of clients

### Rollback Plan
- All changes backward-compatible
- DB migrations reversible (if implemented)
- Feature flags for gradual rollout
- Staging validation before prod

---

## 📞 Escalation

- **Security Team:** Review hotfixes
- **DB Team:** Prepare for eventual migration
- **DevOps:** Setup Secret Manager, monitoring
- **QA:** Prepare test scenarios

---

**Status:** Ready for implementation  
**Last Updated:** 10 Abril 2026  
**Next Review:** After SEMANA 1 completion
