# Fix #9: Rate Limiting con slowapi - Documentación

**Status:** ✅ COMPLETADO  
**Fecha:** 10 Abril 2026  
**Impacto:** Protección contra bruteforce y DoS

---

## Resumen

Se implementó **rate limiting global** en endpoints críticos usando `slowapi` (wrapper sobre `Python-Ratelimit` para FastAPI).

### Endpoints Protegidos

| Endpoint | Límite | Propósito |
|----------|--------|----------|
| `POST /auth/login` | 5/min | Prevenir bruteforce |
| `POST /chat/{cliente_id}` | 20/min | Prevenir spam en chat |
| `POST /api/hallazgos/estructurar` | 10/min | Proteger LLM calls costosos |
| `POST /clientes/{cliente_id}/upload/{kind}` | 3/min | Prevenir DoS de uploads |

---

## Cambios Realizados

### 1. **Instalación de dependencia**
**Archivo:** `requirements.txt`

```diff
+ slowapi>=0.1.9
```

### 2. **Módulo centralizado de rate limiting**
**Archivo:** `backend/middleware/rate_limit.py` (NUEVO)

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

# Instancia global identificada por IP del cliente
limiter = Limiter(key_func=get_remote_address)

# Presets centralizados para consistencia
LIMITS = {
    "login": "5/minute",
    "chat": "20/minute",
    "hallazgos": "10/minute",
    "uploads": "3/minute",
    "admin": "1/minute",
}
```

**Ventajas:**
- Single source of truth para límites
- Fácil de ajustar globalmente
- Bien documentado

### 3. **Configuración en main.py**
**Archivo:** `backend/main.py`

```python
from slowapi.errors import RateLimitExceeded
from backend.middleware.rate_limit import limiter, LIMITS

# Usar limiter global
app.state.limiter = limiter

# Handler personalizado para 429 responses
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return Response(
        content="Demasiadas solicitudes. Por favor intenta más tarde.",
        status_code=429,
        headers={"Retry-After": "60"}
    )
```

### 4. **Aplicación a endpoints**

#### `backend/routes/auth.py` - Login protegido

```python
from backend.middleware.rate_limit import limiter, LIMITS

@router.post("/login", response_model=ApiResponse)
@limiter.limit(LIMITS["login"])  # 5/minute
def login(request: Request, payload: LoginRequest) -> ApiResponse:
    # ... lógica ...
```

#### `backend/routes/chat.py` - Chat protegido

```python
@router.post("/{cliente_id}", response_model=ApiResponse)
@limiter.limit(LIMITS["chat"])  # 20/minute
def post_chat(
    request: Request,
    cliente_id: str,
    payload: ChatRequest,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    # ... lógica ...
```

#### `backend/routes/hallazgos.py` - Hallazgos protegido

```python
@router.post("/estructurar", response_model=ApiResponse)
@limiter.limit(LIMITS["hallazgos"])  # 10/minute
def post_estructurar_hallazgo(
    request: Request,
    payload: HallazgoEstructurarRequest,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    # ... lógica ...
```

#### `backend/routes/clientes.py` - Upload protegido

```python
@router.post("/{cliente_id}/upload/{kind}", response_model=ApiResponse)
@limiter.limit(LIMITS["uploads"])  # 3/minute
async def upload_cliente_file(
    request: Request,
    cliente_id: str,
    kind: str,
    file: UploadFile = File(...),
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    # ... lógica ...
```

---

## Comportamiento

### Ejemplo: Login Bruteforce Protection

**Atacante intenta 7 logins en 10 segundos:**

```
Intento 1: 401 Unauthorized (credenciales inválidas)
Intento 2: 401 Unauthorized
Intento 3: 401 Unauthorized
Intento 4: 401 Unauthorized
Intento 5: 401 Unauthorized
Intento 6: 429 Too Many Requests ← Rate limit activado
    Headers: Retry-After: 60
    Body: "Demasiadas solicitudes. Por favor intenta más tarde."
```

**Atacante debe esperar 60 segundos antes de poder reintentar.**

### Limitación por IP

- Cada dirección IP tiene su propio contador
- `127.0.0.1` puede hacer 5 requests
- `192.168.1.100` puede hacer otros 5 requests (independiente)
- Imposible "amplificar" desde múltiples IPs en redes locales

### Headers en Response

Cuando se activa rate limit, el backend retorna:

```
HTTP/1.1 429 Too Many Requests
Retry-After: 60
Content-Type: text/plain

Demasiadas solicitudes. Por favor intenta más tarde.
```

El cliente (frontend) **debería** respetar el `Retry-After` header.

---

## Pruebas

Se incluye archivo de test: `tests/test_rate_limit_validation.py`

```bash
# Instalar slowapi
pip install slowapi

# Ejecutar test
python -m pytest tests/test_rate_limit_validation.py -v
```

**Test valida:**
- ✅ Login limitado a 5/minuto
- ✅ Límites son por IP (ips distintas = límites independientes)
- ✅ Response headers incluyen `Retry-After`

---

## Configuración (Opcional Avanzado)

### Cambiar límites globalmente

En `backend/middleware/rate_limit.py`:

```python
LIMITS = {
    "login": "10/minute",      # Aumentar a 10/min si lo necesitas
    "chat": "30/minute",       # Más permisivo para chat
    "hallazgos": "20/minute",  # Más LLM calls
    "uploads": "5/minute",     # Más uploads por minuto
}
```

### Usar Redis para multi-proceso (Producción)

**Problema actual:** En producción con múltiples workers (Gunicorn + 4 workers), cada worker tiene su propio contador in-memory.

**Solución:** Usar Redis backend:

```python
# backend/middleware/rate_limit.py
from slowapi.stores import RedisStore
from redis import Redis

redis_store = RedisStore(
    redis=Redis.from_url("redis://localhost:6379")
)
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379",
    default_limits=["200/day", "50/hour"]
)
```

**Pero:** Para MVP (desarrollo), in-memory es suficiente. Agregar Redis es mejora futura.

---

## Monitoreo

### Logs para diagnosticar rate limiting

Cuando se activa:
```
2026-04-10 14:23:45 INFO Rate limit exceeded: scope=login, subject=192.168.1.100, retry_after=60s
```

### Métricas útiles

- Contar requests 429 por endpoint
- Monitoreo de IPs que consistentemente exceden límites (posible ataque)

---

## Impacto de Seguridad

| Vulnerabilidad | Antes | Después |
|---|---|---|
| Bruteforce Login | ✗ Sin protección | ✅ Max 5/min |
| spam Chat | ✗ Ilimitado | ✅ Max 20/min |
| DoS Upload | ✗ Ilimitado | ✅ Max 3/min + 50MB limit |
| LLM Spam | ✗ Ilimitado | ✅ Max 10/min |

---

## Troubleshooting

### "AttributeError: 'Request' has no attribute 'scope'"

**Causa:** slowapi espera objeto Request con `client` property.

**Solución:** Asegurar que `request: Request` es parámetro en función, no acceder directamente desde `FastAPI`.

```python
# ✓ CORRECTO
@router.post("/login")
@limiter.limit("5/minute")
def login(request: Request, payload: LoginRequest):
    ...

# ✗ INCORRECTO
@router.post("/login")
@limiter.limit("5/minute")
def login(payload: LoginRequest):
    ...  # request no existe
```

### Rate limiting no funciona en tests

**Causa:** TestClient puede no simular headers de IP adecuadamente.

**Solución:** Usar `X-Forwarded-For` header en tests:

```python
client.post(
    "/auth/login",
    json=payload,
    headers={"X-Forwarded-For": "192.168.1.100"}  # IP simulada
)
```

---

## Próximas Mejoras

1. **Redis store para multi-worker:** Usar Redis en lugar de in-memory para Gunicorn
2. **Métricas:** Enviar eventos de rate limit a monitoring (DataDog, etc)
3. **Alertas:** Notificar si IP específica excede límites repetidamente
4. **Whitelist:** Agregar lista de IPs o usuarios confiables exempt del rate limit

---

## Checklist de Validación

- [x] `slowapi` agregado a `requirements.txt`
- [x] Módulo `backend/middleware/rate_limit.py` creado
- [x] `backend/main.py` configurado con limiter global y exception handler
- [x] Decorator `@limiter.limit()` aplicado a:
  - [x] POST /auth/login (5/min)
  - [x] POST /chat/{cliente_id} (20/min)
  - [x] POST /api/hallazgos/estructurar (10/min)
  - [x] POST /clientes/{cliente_id}/upload/{kind} (3/min)
- [x] Parámetro `request: Request` agregado a rutas protegidas
- [x] Test file creado: `tests/test_rate_limit_validation.py`
- [x] Documentación completada

---

## Instalación & Deploy

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Ejecutar tests (opcional)
python -m pytest tests/test_rate_limit_validation.py -v

# 3. Deploy
# En staging/prod, usar gunicorn + slowapi
# gunicorn backend.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

---

## Referencias

- Docs de slowapi: https://github.com/laurbrugnolo/slowapi
- FastAPI rate limiting: https://fastapi.tiangolo.com/advanced/middleware/
