# SocioAI - Plataforma Inteligente de Auditoría

SocioAI es una plataforma de inteligencia artificial especializada en auditoría financiera, diseñada para automatizar y optimizar procesos de auditoría utilizando modelos de lenguaje avanzados (LLM).

## 🎯 Características Principales

- **Persistencia de Datos**: Base de datos PostgreSQL en Railway (producción) / SQLite (desarrollo)
- **Gestión de Clientes**: CRUD completo con almacenamiento persistente
- **Gestión de Auditorías**: Creación y seguimiento de auditorías por período
- **Análisis Financiero Inteligente**: Lectura y análisis automático de balances
- **Gestión de Materialidad**: Cálculo automático de umbrales según NIAs
- **Ranking de Riesgos**: Identificación y clasificación de áreas de riesgo
- **API RESTful**: Endpoints documentados con OpenAPI/Swagger
- **Autenticación JWT**: Seguridad basada en tokens con CSRF protection

## 📁 Estructura del Proyecto

```
Nuevo Socio AI/
├── backend/                    # FastAPI application
│   ├── models/                # SQLAlchemy ORM models
│   │   ├── __init__.py       # Shared SQLAlchemy Base
│   │   ├── client.py         # Client model
│   │   ├── audit.py          # Audit model
│   │   └── ...               # Other models
│   ├── routes/                # API endpoints
│   │   ├── clientes.py       # Client & Audit endpoints
│   │   └── ...               # Other routes
│   ├── utils/
│   │   └── database.py       # Database configuration & init
│   ├── main.py               # FastAPI app
│   └── migrations/            # Database migrations
├── frontend/                   # Next.js/React application
│   ├── app/                  # Next.js app directory
│   ├── components/           # React components
│   ├── lib/
│   │   └── types.ts          # Generated OpenAPI types
│   └── package.json
├── tests/                      # Pytest test suite
│   └── conftest.py           # Database initialization for tests
├── data/                       # Data files and knowledge base
└── docs/                       # Documentation
```

## 🚀 Quick Start

### Backend Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env and add:
# - JWT_SECRET_KEY (for authentication)
# - DATABASE_URL (for production, optional)

# Run tests (initializes SQLite automatically)
python -m pytest tests/ -v

# Start development server
python -m uvicorn backend.main:app --reload --port 8000
```

**Note**: Without DATABASE_URL, the app uses SQLite fallback for local development.

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Generate types from backend OpenAPI
npm run generate:types

# Start development server
npm run dev
```

Visit `http://localhost:3000`

### Database Configuration (Vercel Production)

1. **Get PostgreSQL URL from Railway**:
   - Railway → Your Project → Postgres → Connect
   - Copy the PostgreSQL URI

2. **Add to Vercel**:
   - Vercel → Your Project → Settings → Environment Variables
   - Add `DATABASE_URL` with the PostgreSQL URI
   - Click Save

3. **Verify**:
   - Deploy your project
   - Check Vercel logs for `[OK] Database initialized`

See `FIX_DATABASE_URL.md` for detailed troubleshooting.

## 🔑 Key Endpoints

### Clients
- `GET /api/clientes` - List all clients (requires auth)
- `POST /api/clientes` - Create new client (admin/manager/socio only)
- `GET /api/clientes/{cliente_id}` - Get client details

### Audits
- `GET /api/clientes/{cliente_id}/auditorias` - List audits for client
- `POST /api/clientes/{cliente_id}/auditorias` - Create new audit
- `PUT /api/clientes/{cliente_id}/auditorias/{audit_id}` - Update audit status

### Documentation
- `GET /docs` - Interactive Swagger UI
- `GET /redoc` - ReDoc documentation

## 🗄️ Database

### Architecture

- **Production**: PostgreSQL on Railway
- **Development/Tests**: SQLite (`test.db`)
- **ORM**: SQLAlchemy with shared Base instance
- **Migrations**: SQL files in `backend/migrations/`

### Models

All models inherit from shared Base in `backend/models/__init__.py`:

```python
from backend.models import Base

class Client(Base):
    __tablename__ = "clients"
    # ... columns
```

### Initialization

Database tables are created automatically:
- **On app startup**: `init_db()` called in `backend/main.py`
- **In tests**: `conftest.py` initializes database before running tests

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_api_security.py -v

# Run with coverage
python -m pytest tests/ --cov=backend --cov-report=html

# Current status: 185 tests passing ✅
```

## 🔐 Security

- **Authentication**: JWT bearer tokens
- **Authorization**: Role-based access control (admin, manager, socio, staff)
- **CSRF Protection**: Token validation for mutating operations
- **Rate Limiting**: Per-endpoint rate limits
- **Environment Variables**: Secrets in `.env` (never in git)

## 🛠️ Development Workflow

### Making Changes

1. **Backend**: Edit files in `backend/`, tests will auto-reload
2. **Frontend**: Edit files in `frontend/`, Next.js hot reloads
3. **Types**: Run `npm run generate:types` if backend API changes
4. **Tests**: Run `pytest` to verify changes

### Git Workflow

```bash
# After making changes
git add .
git commit -m "Fix: description of changes"
git push
```

## 📚 Documentation

- [Database Architecture](ARQUITECTURA_BD.txt)
- [Database Setup Guide](SETUP_PERSISTENCIA.md)
- [Troubleshooting DATABASE_URL](FIX_DATABASE_URL.md)
- [Project Status](ESTADO_ACTUAL.txt)
- [Checklist](CHECKLIST_DB.md)

## 🐛 Troubleshooting

**SQLite table errors in tests**
- Solution: Ensure `conftest.py` is in `tests/` directory
- The fixture `setup_database` initializes tables automatically

**DATABASE_URL not configured**
- Local: App falls back to SQLite automatically ✅
- Vercel: Must add DATABASE_URL environment variable
- Check `FIX_DATABASE_URL.md` for detailed steps

**Type generation mismatches**
- Run: `cd frontend && npm run generate:types`
- Commit the updated `lib/types.ts`

## 📊 Project Status

- ✅ Database persistence implemented
- ✅ Client & Audit CRUD endpoints
- ✅ JWT authentication & CSRF protection
- ✅ All tests passing (185/185)
- ✅ Type-safe frontend with generated types
- 🚀 Ready for production deployment

## 📝 License

Todos los derechos reservados.

## 👥 Team

Built with Claude AI assistance.

---

**Last Updated**: 2026-04-17  
**Status**: Stable ✅
