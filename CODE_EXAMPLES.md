# 🔧 Ejemplos de Código - Mitigaciones Críticas

**Nuevo Socio AI - FastAPI + Next.js**  
**Última actualización:** 10 Abril 2026

---

## 1. Seguridad JWT + Secretos

### Backend: Auth renovado

**Archivo:** `backend/auth_secure.py` (NUEVO)

```python
from __future__ import annotations

import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.schemas import UserContext

# ✅ NUEVA ESTRATEGIA: Requerir secreto configurado, NUNCA generar
_SECRET = (os.getenv("JWT_SECRET_KEY") or "").strip()
_API_ENV = (os.getenv("API_ENV", "development") or "").strip().lower()

def _validate_secret():
    """Validar que secreto esté disponible en TODOS los ambientes."""
    if not _SECRET:
        env_context = (
            f"Current env: {_API_ENV or 'unknown'}, "
            f"CI={os.getenv('CI', '(not set)')}, "
            f"EXPORT_OPENAPI={os.getenv('EXPORT_OPENAPI', '(not set)')}"
        )
        raise RuntimeError(
            f"FATAL: JWT_SECRET_KEY no configurado. {env_context}\n"
            f"Actions:\n"
            f"  1. Generar: openssl rand -base64 32\n"
            f"  2. Guardar en Secret Manager\n"
            f"  3. Setear: export JWT_SECRET_KEY=<value>\n"
            f"  4. No regenerar cada build (seguridad CLAVE)"
        )

# Validar al import (fail fast)
_validate_secret()

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("JWT_EXPIRE_MINUTES", "60")
)

bearer_scheme = HTTPBearer(auto_error=False)


def create_access_token(
    *,
    sub: str,
    org_id: str,
    allowed_clientes: list[str],
    role: str,
    user_id: str = "",
    display_name: str = "",
    expires_minutes: int | None = None,
) -> tuple[str, int]:
    """Create JWT token con validaciones."""
    # Validar entrada
    sub = (sub or "").strip()
    if not sub:
        raise ValueError("sub (username/email) cannot be empty")
    
    role = (role or "auditor").strip().lower()
    if role not in {"admin", "socio", "manager", "auditor", "staff"}:
        raise ValueError(f"Invalid role: {role}")
    
    # Validar clientes
    if not isinstance(allowed_clientes, list):
        raise ValueError("allowed_clientes must be list")
    if not allowed_clientes and role != "auditor":
        raise ValueError("Admin/manager/socio must have at least one cliente allowed")
    
    minutes = expires_minutes or ACCESS_TOKEN_EXPIRE_MINUTES
    if minutes <= 0 or minutes > 1440:  # Max 1 day
        raise ValueError("expires_minutes must be between 1 and 1440")
    
    exp = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    payload = {
        "sub": sub,
        "org_id": org_id,
        "allowed_clientes": allowed_clientes,
        "role": role,
        "exp": exp,
        "iat": datetime.now(timezone.utc),  # Issued At
    }
    if user_id:
        payload["uid"] = (user_id or "").strip()
    if display_name:
        payload["display_name"] = (display_name or "").strip()
    
    try:
        token = jwt.encode(payload, _SECRET, algorithm=ALGORITHM)
        return token, minutes * 60
    except Exception as exc:
        raise RuntimeError(f"Token generation failed: {exc}") from exc


def decode_token(token: str) -> dict[str, Any]:
    """Decode JWT con validaciones strict."""
    if not token or not isinstance(token, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing or invalid format",
        )
    
    try:
        # Configurar PyJWT con strict validations
        payload = jwt.decode(
            token,
            _SECRET,
            algorithms=[ALGORITHM],
            options={
                "verify_signature": True,
                "verify_exp": True,  # Verify expiration
                "verify_iat": True,  # Verify issued-at time
                "require": ["sub", "org_id", "role", "exp"],  # Required claims
            }
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado",
        )
    except jwt.InvalidSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token firmado inválido",
        )
    except jwt.DecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token no pudo ser decodificado",
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> UserContext:
    """Extract user from JWT token con validación de seguridad."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )
    
    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid scheme: {credentials.scheme}. Expected 'Bearer'",
        )
    
    token = (credentials.credentials or "").strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is empty",
        )
    
    payload = decode_token(token)
    
    try:
        return UserContext(
            sub=str(payload.get("sub") or "").strip(),
            org_id=str(payload.get("org_id") or "socio-default-org"),
            allowed_clientes=[str(c) for c in payload.get("allowed_clientes", [])],
            role=str(payload.get("role") or "auditor"),
            user_id=str(payload.get("uid") or "").strip(),
            display_name=str(payload.get("display_name") or "").strip(),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        ) from exc
```

### Backend: Login renovado SEGURO

**Archivo:** `backend/routes/auth_secure.py`

```python
from __future__ import annotations

import os
import secrets
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials

from backend.auth_secure import create_access_token, get_current_user, bearer_scheme
from backend.repositories.identity_repository import store as identity_store
from backend.schemas import ApiResponse, AuthMeResponse, LoginRequest, TokenResponse, UserContext

router = APIRouter(prefix="/auth", tags=["auth"])
LOGGER = logging.getLogger("socio_ai.auth_secure")

# ✅ CAMBIO: No fallback a hardcoded. Requerir config.
_ADMIN_USERNAME = (os.getenv("ADMIN_USERNAME") or "").strip()
_ADMIN_PASSWORD = (os.getenv("ADMIN_PASSWORD") or "").strip()

# Validar que admin está configurado (fail fast en startup)
if not _ADMIN_USERNAME or not _ADMIN_PASSWORD:
    if not os.getenv("SKIP_ADMIN_CHECK"):  # Allow para tests
        LOGGER.warning(
            "⚠️  ADMIN_USERNAME/PASSWORD not configured. "
            "Users can only login via identity store."
        )


@router.post("/login", response_model=ApiResponse)
def login(request: Request, payload: LoginRequest) -> JSONResponse:
    """Login endpoint seguro con CSRF protection."""
    username = (payload.username or "").strip()
    password = (payload.password or "").strip()
    
    # Validar entrada
    if not username or not password:
        LOGGER.warning(f"Login attempt with empty credentials from {request.client.host}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username y password requeridos",
        )
    
    # Intentar authenticación
    user = None
    auth_source = "unknown"
    
    # 1. Primero, intentar identity store (si está configurado)
    if os.getenv("USE_IDENTITY_STORE", "true").lower() == "true":
        user = identity_store.authenticate(username, password)
        if isinstance(user, dict):
            auth_source = "identity_store"
    
    # 2. Fallback a admin account (si está configurado)
    if user is None and _ADMIN_USERNAME and _ADMIN_PASSWORD:
        user_ok = secrets.compare_digest(username, _ADMIN_USERNAME)
        pass_ok = secrets.compare_digest(password, _ADMIN_PASSWORD)
        if user_ok and pass_ok:
            user = {
                "username": _ADMIN_USERNAME,
                "user_id": "admin-builtin",
                "role": "admin",
                "display_name": "Admin",
                "active": True,
            }
            auth_source = "builtin_admin"
    
    # 3. Si no se autenticó, rechazar
    if user is None:
        LOGGER.warning(f"Failed login for user={username} from {request.client.host}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )
    
    # Validar que usuario está activo
    if not bool(user.get("active", True)):
        LOGGER.warning(f"Login attempt for inactive user={username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inactivo",
        )
    
    # Extraer atributos con validación
    user_id = str(user.get("user_id") or "").strip()
    role = str(user.get("role") or "auditor").strip().lower()
    display_name = str(user.get("display_name") or username).strip()
    
    # Obtener clientes permitidos
    allowed_clientes = identity_store.get_user_clientes(user_id) if user_id else []
    if not allowed_clientes and role in {"admin", "socio", "manager"}:
        allowed_clientes = _parse_allowed_clientes()
    
    # Generar token
    try:
        token, ttl = create_access_token(
            sub=username,
            org_id=os.getenv("SOCIO_ORG_ID", "socio-default-org"),
            allowed_clientes=allowed_clientes,
            role=role,
            user_id=user_id,
            display_name=display_name,
        )
    except Exception as exc:
        LOGGER.error(f"Token generation failed for user={username}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token generation error",
        )
    
    LOGGER.info(
        f"Login successful user={username} source={auth_source} role={role} "
        f"user_id={user_id} ttl={ttl}s"
    )
    
    # ✅ NUEVA ESTRATEGIA: Retornar token en httpOnly cookie + JSON
    response_data = ApiResponse(
        data=TokenResponse(access_token=token, expires_in=ttl).model_dump()
    )
    
    response = JSONResponse(
        status_code=status.HTTP_200_OK,
        content=response_data.model_dump()
    )
    
    # ✅ SET HTTPONLY COOKIE (No accessing from JavaScript)
    response.set_cookie(
        key="socio-auth",
        value=token,
        httponly=True,           # No JS access (prevents XSS theft)
        secure=True,             # HTTPS only
        samesite="Strict",       # CSRF protection
        max_age=ttl,             # Seconds
        path="/",                # Available to all paths
        domain=None,             # Current domain only
    )
    
    return response


@router.post("/logout")
def logout(response: JSONResponse = JSONResponse({"status": "ok"})):
    """Logout endpoint - clear cookie."""
    response.delete_cookie(key="socio-auth", path="/")
    return response


@router.get("/me", response_model=ApiResponse)
def me(user: UserContext = Depends(get_current_user)) -> ApiResponse:
    """Get current user info."""
    return ApiResponse(
        data=AuthMeResponse(
            sub=user.sub,
            user_id=user.user_id,
            display_name=user.display_name or user.sub,
            role=user.role,
            org_id=user.org_id,
            allowed_clientes=user.allowed_clientes,
        ).model_dump()
    )


def _parse_allowed_clientes() -> list[str]:
    """Parse ALLOWED_CLIENTES env var."""
    raw = (os.getenv("ALLOWED_CLIENTES") or "").strip()
    if not raw:
        return []
    if raw == "*":
        return ["*"]
    return [item.strip() for item in raw.split(",") if item.strip()]
```

---

## 2. Rate Limiting (Middleware)

### Backend: Rate Limit Middleware Seguro

**Archivo:** `backend/middleware/rate_limit.py` (NUEVO)

```python
from __future__ import annotations

import logging
import time
from typing import Callable

from fastapi import Request, status
from fastapi.responses import JSONResponse

LOGGER = logging.getLogger("socio_ai.rate_limit")


class InMemoryRateLimiter:
    """⚠️ Solo para desarrollo. Usar Redis en producción."""
    
    def __init__(self):
        self.requests: dict[str, list[float]] = {}
    
    def is_allowed(self, key: str, limit: int, window_seconds: int) -> bool:
        """Check if request is allowed under rate limit."""
        now = time.time()
        
        # Cleanup old requests
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove old requests outside window
        self.requests[key] = [
            ts for ts in self.requests[key]
            if (now - ts) < window_seconds
        ]
        
        # Check limit
        if len(self.requests[key]) >= limit:
            return False
        
        # Record this request
        self.requests[key].append(now)
        return True


class RateLimitMiddleware:
    """Rate limiting middleware for FastAPI."""
    
    def __init__(
        self,
        app,
        limiter: InMemoryRateLimiter | None = None,
    ):
        self.app = app
        self.limiter = limiter or InMemoryRateLimiter()
        
        # Rate limit per endpoint
        self.limits = {
            "/auth/login": {"limit": 5, "window": 60},      # 5 per minute
            "/auth/logout": {"limit": 10, "window": 60},    # 10 per minute
            "/chat/": {"limit": 20, "window": 60},          # 20 per minute
            "/clientes/": {"limit": 30, "window": 60},      # 30 per minute
            "DEFAULT": {"limit": 100, "window": 60},        # 100 per minute default
        }
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        # Get client IP
        client_ip = (
            request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            or request.client.host
            or "unknown"
        )
        
        # Find applicable limit
        path = request.url.path
        limit_config = self.limits.get("DEFAULT")
        
        for pattern, config in self.limits.items():
            if pattern != "DEFAULT" and path.startswith(pattern):
                limit_config = config
                break
        
        # Create rate limit key
        rate_limit_key = f"{client_ip}:{path}"
        
        # Check rate limit
        if not self.limiter.is_allowed(
            rate_limit_key,
            limit=limit_config["limit"],
            window_seconds=limit_config["window"]
        ):
            LOGGER.warning(
                f"Rate limit exceeded for {client_ip} on {path} "
                f"(limit: {limit_config['limit']} per {limit_config['window']}s)"
            )
            
            response = JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "status": "error",
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many requests. Please try again later.",
                    "retry_after": limit_config["window"],
                }
            )
            
            # Set Retry-After header
            response.headers["Retry-After"] = str(limit_config["window"])
            
            await response(scope, receive, send)
            return
        
        # Proceed to app
        await self.app(scope, receive, send)


# Usar en main.py:
# from backend.middleware.rate_limit import RateLimitMiddleware
# app.add_middleware(RateLimitMiddleware)
```

### Production: Redis-based Rate Limiting

```python
# backend/middleware/rate_limit_redis.py (Producción)

import logging
import redis
from typing import Optional

LOGGER = logging.getLogger("socio_ai.rate_limit_redis")


class RedisRateLimiter:
    """Production-ready rate limiter using Redis."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url)
    
    def is_allowed(self, key: str, limit: int, window_seconds: int) -> bool:
        """Check if request allowed using sliding window algorithm."""
        try:
            current = self.redis.incr(key)
            
            if current == 1:
                # First request, set expiry
                self.redis.expire(key, window_seconds)
            
            if current > limit:
                return False
            
            return True
        except redis.RedisError as exc:
            LOGGER.error(f"Redis rate limit error: {exc}")
            # Fail open: allow request if Redis is down
            return True
```

---

## 3. CSRF Protection

### Backend: CSRF Middleware

**Archivo:** `backend/middleware/csrf.py` (NUEVO)

```python
from __future__ import annotations

import logging
import secrets
import time
from typing import Set, Tuple

from fastapi import Request, status
from fastapi.responses import JSONResponse

LOGGER = logging.getLogger("socio_ai.csrf")


class CSRFMiddleware:
    """CSRF token validation middleware."""
    
    def __init__(self, app, token_ttl_seconds: int = 3600):
        self.app = app
        self.token_ttl = token_ttl_seconds
        self.tokens: dict[str, Tuple[str, float]] = {}
        
        # Endpoints that don't require CSRF (GET requests)
        self.safe_methods = {"GET", "HEAD", "OPTIONS"}
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        method = request.method.upper()
        path = request.url.path
        
        # Skip CSRF for safe methods
        if method in self.safe_methods:
            await self.app(scope, receive, send)
            return
        
        # Skip CSRF for specific paths (e.g., /health)
        if path in {"/health", "/metrics"}:
            await self.app(scope, receive, send)
            return
        
        # Validate CSRF token
        csrf_token = request.headers.get("X-CSRF-Token", "").strip()
        
        if not csrf_token:
            LOGGER.warning(
                f"CSRF token missing for {method} {path} "
                f"from {request.client.host}"
            )
            response = JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "status": "error",
                    "code": "CSRF_TOKEN_MISSING",
                    "message": "CSRF token required",
                }
            )
            await response(scope, receive, send)
            return
        
        # Check token validity
        if csrf_token not in self.tokens:
            LOGGER.warning(
                f"CSRF token invalid for {method} {path} "
                f"from {request.client.host}"
            )
            response = JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "status": "error",
                    "code": "CSRF_TOKEN_INVALID",
                    "message": "CSRF token invalid or expired",
                }
            )
            await response(scope, receive, send)
            return
        
        # Check token expiry
        token_value, token_time = self.tokens[csrf_token]
        if time.time() - token_time > self.token_ttl:
            LOGGER.warning(f"CSRF token expired: {csrf_token}")
            del self.tokens[csrf_token]
            response = JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "status": "error",
                    "code": "CSRF_TOKEN_EXPIRED",
                    "message": "CSRF token expired",
                }
            )
            await response(scope, receive, send)
            return
        
        # Token is valid, consume it (one-time use)
        del self.tokens[csrf_token]
        
        # Proceed
        await self.app(scope, receive, send)
    
    def generate_token(self) -> str:
        """Generate new CSRF token."""
        token = secrets.token_urlsafe(32)
        self.tokens[token] = (token, time.time())
        return token
```

### Backend: CSRF Endpoint

```python
# backend/routes/csrf.py (NUEVO)

from fastapi import APIRouter, Request
from backend.middleware.csrf import csrf_middleware
from backend.schemas import ApiResponse

router = APIRouter(prefix="/csrf", tags=["csrf"])


@router.get("/token")
def get_csrf_token(request: Request) -> ApiResponse:
    """Get a CSRF token for form submissions."""
    csrf_middleware = request.app.csrf_middleware  # Injected by middleware
    token = csrf_middleware.generate_token()
    
    return ApiResponse(data={"token": token})
```

### Frontend: CSRF Fetch Wrapper

**Archivo:** `frontend/lib/csrf.ts` (NUEVO)

```typescript
/**
 * CSRF Token Management for Next.js
 */

let cachedCsrfToken: string | null = null;

export async function getCsrfToken(): Promise<string> {
    if (cachedCsrfToken) {
        return cachedCsrfToken;
    }
    
    try {
        const response = await fetch("/api/csrf/token", { method: "GET" });
        if (!response.ok) {
            throw new Error("Failed to get CSRF token");
        }
        
        const data = await response.json();
        cachedCsrfToken = data.data?.token;
        
        if (!cachedCsrfToken) {
            throw new Error("No token in response");
        }
        
        return cachedCsrfToken;
    } catch (error) {
        console.error("CSRF token fetch failed:", error);
        throw error;
    }
}

export function invalidateCsrfToken(): void {
    cachedCsrfToken = null;
}

export async function apiFetchWithCsrf<T>(
    path: string,
    init?: RequestInit
): Promise<T> {
    const method = String(init?.method || "GET").toUpperCase();
    const headers = new Headers(init?.headers);
    
    // Add CSRF token for non-GET requests
    if (method !== "GET") {
        const csrfToken = await getCsrfToken();
        headers.set("X-CSRF-Token", csrfToken);
    }
    
    // Make request
    const response = await fetch(path, {
        ...init,
        method,
        headers,
    });
    
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    return response.json();
}
```

### Frontend: Usage Example

```typescript
// frontend/components/example.tsx

import { apiFetchWithCsrf } from "@/lib/csrf";

export function MyForm() {
    const handleSubmit = async (formData: FormData) => {
        try {
            const result = await apiFetchWithCsrf(
                "/api/clientes",
                {
                    method: "POST",
                    body: JSON.stringify({
                        nombre: formData.get("nombre"),
                        sector: formData.get("sector"),
                    }),
                }
            );
            
            console.log("Success:", result);
        } catch (error) {
            console.error("Failed:", error);
        }
    };
    
    return (
        <form onSubmit={(e) => {
            e.preventDefault();
            handleSubmit(new FormData(e.currentTarget));
        }}>
            <input name="nombre" placeholder="Nombre" required />
            <input name="sector" placeholder="Sector" />
            <button type="submit">Crear Cliente</button>
        </form>
    );
}
```

---

## 4. Token Seguro (httpOnly Cookie)

### Backend: Login con httpOnly Cookie

```python
# backend/routes/auth_secure.py (actualizado)

from fastapi.responses import JSONResponse

@router.post("/login", response_model=ApiResponse)
def login(request: Request, payload: LoginRequest) -> JSONResponse:
    # ... auth logic ...
    
    token, ttl = create_access_token(...)
    
    # Return token data (password auth, bearer token, etc)
    response_data = ApiResponse(
        data=TokenResponse(access_token="<REDACTED>", expires_in=ttl)
    )
    
    response = JSONResponse(
        status_code=status.HTTP_200_OK,
        content=response_data.model_dump()
    )
    
    # ✅ NUEVO: Set httpOnly cookie (secure + samesite)
    response.set_cookie(
        key="socio-auth",
        value=token,
        httponly=True,           # Not accessible from JS (XSS protection)
        secure=True,             # HTTPS only
        samesite="Strict",       # CSRF protection (no same-site requests)
        max_age=ttl,
        path="/",
        domain=None,             # Current domain only
    )
    
    return response
```

### Frontend: Automatic Cookie Handling

```typescript
// frontend/lib/api.ts (actualizado)

// ❌ OLD - Token in localStorage (vulnerable)
// function getToken(): string | null {
//     return localStorage.getItem("socio_token");
// }

// ✅ NEW - Token in httpOnly cookie (automatic)
// No need to manually get/send token!
// Browsers automatically send cookies with requests

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
    const headers = new Headers(init?.headers);
    
    // ✅ Cookie sent automatically by browser
    // No manual "Authorization" header needed
    
    const isFormData = typeof FormData !== "undefined" && init?.body instanceof FormData;
    if (!isFormData && !headers.has("Content-Type")) {
        headers.set("Content-Type", "application/json");
    }
    
    const response = await fetch(buildApiUrl(path), {
        ...init,
        headers,
        credentials: "include",  // Important! Include cookies
    });
    
    if (response.status === 401) {
        // Token expired
        window.location.href = "/login";
        throw new TokenExpiredError("Token expired. Redirecting to login...");
    }
    
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }
    
    return response.json();
}
```

---

## 5. Path Traversal Prevention

### Backend: Input Validation

```python
# backend/routes/clientes.py (actualizado)

import re
from pathlib import Path

# ✅ Validar cliente_id contra formato esperado
VALID_CLIENTE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,50}$")

def validate_cliente_id(cliente_id: str) -> str:
    """Validate cliente_id format to prevent path traversal."""
    if not cliente_id:
        raise ValueError("cliente_id cannot be empty")
    
    if not VALID_CLIENTE_ID_PATTERN.match(cliente_id):
        raise ValueError(
            f"cliente_id must match pattern [a-zA-Z0-9_-], got: {cliente_id}"
        )
    
    return cliente_id


@router.get("/{cliente_id}/documentos", response_model=ApiResponse)
def get_cliente_documentos(
    cliente_id: str,
    user: UserContext = Depends(get_current_user)
) -> ApiResponse:
    # ✅ Validate format first
    try:
        cliente_id = validate_cliente_id(cliente_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    
    # ✅ Authorize access
    authorize_cliente_access(cliente_id, user)
    
    # Now safe to use cliente_id in path
    docs = [ClienteDocumento(**doc).model_dump() for doc in list_documentos(cliente_id)]
    return ApiResponse(data=docs)
```

---

## 6. Service Injection (Testability)

### Backend: RAG Service Separation

```python
# backend/services/rag_service.py (NUEVO)

from abstract.typing import Protocol
from typing import Any

class RagRetriever(Protocol):
    """Interface for RAG retrieval."""
    def retrieve(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        ...

class LlmGenerator(Protocol):
    """Interface for LLM generation."""
    def generate(self, prompt: str, context: str) -> str:
        ...

class RagService:
    """Dedicated RAG retrieval service (no generation)."""
    
    def __init__(self, retriever: RagRetriever):
        self.retriever = retriever
    
    def retrieve_context(self, query: str) -> list[dict[str, Any]]:
        """Retrieve context chunks for query."""
        return self.retriever.retrieve(query, top_k=10)

class LlmService:
    """Dedicated LLM generation service (no retrieval)."""
    
    def __init__(self, generator: LlmGenerator):
        self.generator = generator
    
    def generate_response(self, prompt: str, context: str) -> str:
        """Generate response given prompt and context."""
        return self.generator.generate(prompt, context)

class ChatService:
    """Chat orchestrator (uses RagService + LlmService)."""
    
    def __init__(self, rag: RagService, llm: LlmService):
        self.rag = rag
        self.llm = llm
    
    def chat(self, message: str) -> dict[str, Any]:
        """Process user message: retrieve -> generate."""
        # 1. Retrieve context
        context_chunks = self.rag.retrieve_context(message)
        context_text = "\n\n".join(
            [f"[{c['source']}]\n{c['excerpt']}" for c in context_chunks]
        )
        
        # 2. Generate response
        prompt = f"Question: {message}\n\nContext:\n{context_text}"
        response = self.llm.generate_response(prompt, context_text)
        
        return {
            "answer": response,
            "context_sources": [c["source"] for c in context_chunks],
        }
```

### Backend: Dependency Injection

```python
# backend/main.py (actualizado)

from backend.services.rag_service import RagService, LlmService, ChatService
from backend.services.rag_chat_service import DeepseekLlmGenerator

def get_rag_service() -> RagService:
    """Dependency: RagService."""
    from backend.services.rag_chat_service import retrieve_context_chunks
    
    class RagRetrieverImpl:
        def retrieve(self, query: str, top_k: int = 5):
            return retrieve_context_chunks(query, top_k=top_k)
    
    return RagService(retriever=RagRetrieverImpl())

def get_llm_service() -> LlmService:
    """Dependency: LlmService."""
    return LlmService(generator=DeepseekLlmGenerator())

def get_chat_service(
    rag: RagService = Depends(get_rag_service),
    llm: LlmService = Depends(get_llm_service),
) -> ChatService:
    """Dependency: ChatService (composed)."""
    return ChatService(rag=rag, llm=llm)

# Use in routes
@router.post("/chat/{cliente_id}")
def post_chat(
    cliente_id: str,
    payload: ChatRequest,
    chat: ChatService = Depends(get_chat_service),
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    authorize_cliente_access(cliente_id, user)
    
    result = chat.chat(payload.message)
    
    return ApiResponse(data=result)
```

### Frontend: Testing Example

```typescript
// Test with mocked LLM
const mockLlm = {
    generate: (prompt: string) => "Mocked response"
};

const chatService = new ChatService(
    new RagService(mockRetriever),
    new LlmService(mockLlm)
);

const result = await chatService.chat("Test question");
console.assert(result.answer === "Mocked response");
```

---

## Checklist de Implementación

```markdown
# Implementación de Mitigaciones

## Seguridad JWT
- [ ] Crear backend/auth_secure.py
- [ ] Reemplazar imports en routes/auth.py
- [ ] Remover secrets.token_urlsafe() fallback
- [ ] Test login flow
- [ ] Validar token claims

## Rate Limiting
- [ ] Crear backend/middleware/rate_limit.py
- [ ] Integrar en main.py
- [ ] Test /auth/login bruteforce protection
- [ ] Monitorear 429 responses

##  CSRF Protection
- [ ] Crear backend/middleware/csrf.py
- [ ] Crear frontend/lib/csrf.ts
- [ ] Crear /csrf/token endpoint
- [ ] Aplicar en todos POST/PUT/DELETE
- [ ] Test form submissions

## httpOnly Cookie
- [ ] Modificar auth.py set_cookie logic
- [ ] Remover localStorage token operations
- [ ] Remover manual Authorization header
- [ ] Test cookie en DevTools

## Path Traversal
- [ ] Crear VALID_CLIENTE_ID_PATTERN
- [ ] Aplicar validate_cliente_id() en rutas
- [ ] Test con malicious inputs (../, ..\\, etc)

## Service Injection
- [ ] Crear RagService + LlmService abstractions
- [ ] Refactorizar rag_chat_service.py
- [ ] Inyectar en FastAPI Depends
- [ ] Unit tests mocked LLM
```

---

**Fin del documento**  
**Status:** Listo para implementación inmediata  
**Prioridad:** CRÍTICA (Semana 1)
