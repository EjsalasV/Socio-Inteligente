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
