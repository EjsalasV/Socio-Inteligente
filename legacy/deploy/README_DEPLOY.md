# SocioAI — Deploy en Streamlit Cloud + Cloudflare

## Paso 1: Streamlit Cloud

1. Ve a https://share.streamlit.io
2. Sign in con tu cuenta GitHub
3. Click "New app"
4. Selecciona:
   - Repository: tu-usuario/socioai
   - Branch: main
   - Main file path: app/app_streamlit.py
5. Click "Advanced settings":
   - Python version: 3.11
6. Click "Deploy"

## Paso 2: Agregar secretos en Streamlit Cloud

1. Una vez desplegada, ve a tu app → ⋮ → Settings → Secrets
2. Pega esto y rellena tus valores:
```toml
DEEPSEEK_API_KEY = "sk-tu-clave-aqui"
SOCIOAI_ENV = "production"
```

3. Click "Save" → la app se reinicia automáticamente

## Paso 3: Dominio personalizado con Cloudflare

1. En Streamlit Cloud → tu app → Settings → Custom domain
2. Escribe: socioai.tudominio.com
3. Streamlit te da un CNAME, ejemplo:
   abc123.streamlit.app

4. En Cloudflare → tu dominio → DNS → Add record:
   - Type: CNAME
   - Name: socioai
   - Target: abc123.streamlit.app
   - Proxy: OFF (gris, no naranja) ← importante

5. En Cloudflare → SSL/TLS → Overview:
   - Modo: Full

6. Esperar 5 minutos → visitar socioai.tudominio.com ✅

## Deploy automático

Cada git push a main → Streamlit Cloud
redespliega automáticamente. Sin configuración extra.

## Subir datos de clientes reales

Los clientes con datos sensibles NO van a GitHub.
Opciones:
- Cargarlos directamente desde la app (upload widget)
- Mantener cliente_demo como demo público
