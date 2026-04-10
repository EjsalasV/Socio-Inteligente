# Backend (FastAPI)

Run local API:

```bash
uvicorn backend.main:app --reload --port 8000
```

Export OpenAPI contract:

```bash
python backend/scripts/export_openapi.py
```

## Checklist de entorno (staging aislado)

Variables minimas recomendadas para pruebas E2E:

- `ENV=production`
- `ALLOWED_ORIGINS=https://<tu-frontend-staging>.vercel.app,http://localhost:3000`
- `JWT_SECRET_KEY=<secreto-jwt>`
- `AI_PROVIDER=openai|deepseek`
- `OPENAI_API_KEY=<opcional-si-usas-openai>`
- `OPENAI_CHAT_MODEL=<opcional>`
- `DEEPSEEK_API_KEY=<opcional-si-usas-deepseek>`
- `DEEPSEEK_CHAT_MODEL=<opcional>`
- `DEEPSEEK_BASE_URL=https://api.deepseek.com`
- `SUPABASE_URL=<opcional>`
- `SUPABASE_ANON_KEY=<opcional>`
- `SUPABASE_SERVICE_ROLE_KEY=<opcional>`
- `SUPABASE_TIMEOUT_SECONDS=8` (legacy/fallback)
- `SUPABASE_TIMEOUT_CONNECT_SECONDS=2` (timeout de conexion)
- `SUPABASE_TIMEOUT_READ_SECONDS=8` (timeout de lectura)
- `SUPABASE_MAX_RETRIES=1` (reintentos para errores transitorios)
- `SUPABASE_RETRY_BACKOFF_SECONDS=0.15`
- `SUPABASE_CIRCUIT_FAIL_THRESHOLD=3` (abre degradacion tras N fallos seguidos)
- `SUPABASE_CIRCUIT_OPEN_SECONDS=30` (durante este tiempo usa fallback local)
- `APP_LOG_FORMAT=json` (`json` recomendado para observabilidad)
- `OBSERVABILITY_WINDOW_SIZE=2000` (muestras recientes para metricas runtime)
- `OBSERVABILITY_TOP_PATHS=25` (maximo de endpoints en ranking de latencia/error)
