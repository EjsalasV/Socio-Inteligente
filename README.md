# SocioAI - Plataforma Inteligente de Auditoría

SocioAI es una plataforma de inteligencia artificial especializada en auditoría financiera, diseñada para automatizar y optimizar procesos de auditoría utilizando modelos de lenguaje avanzados (LLM).

## 🎯 Características Principales

- **Análisis Financiero Inteligente**: Lectura y análisis automático de balances y estados financieros
- **Gestión de Materialidad**: Cálculo automático de umbrales de materialidad según NIAs
- **Ranking de Riesgos**: Identificación y clasificación inteligente de áreas de riesgo
- **Briefing Automático**: Generación de briefings de auditoría por área
- **Consultas LLM**: Sistema de preguntas y respuestas basado en contexto normativo
- **Gestión de Hallazgos**: Registro y seguimiento de hallazgos de auditoría
- **RAG (Retrieval-Augmented Generation)**: Sistema de recuperación de información especializada

## 📁 Estructura del Proyecto

```
socio_ai/
├── app/                 # Aplicación principal (Streamlit y CLI)
├── core/               # Configuración y utilidades clave
├── domain/             # Lógica de negocio y servicios
├── analysis/           # Módulos de análisis financiero
├── llm/                # Integraciones con LLM
├── infra/              # Infraestructura (I/O, repositorios, RAG)
├── data/               # Datos, catálogos y conocimiento
├── tests/              # Pruebas unitarias e integración
└── docs/               # Documentación del proyecto
```

## 🚀 Instalación

```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
export OPENAI_API_KEY="tu-clave-api"
```

## 💻 Uso

### Interfaz Web (Streamlit)
```bash
streamlit run app/app_streamlit.py
```

### Interfaz CLI
```bash
python app/socio_ai.py --help
```

## 🔧 Configuración

Editar `config.yaml` para personalizar:
- Modelos de LLM disponibles
- Umbrales de materialidad
- Rutas de datos
- Configuración de logging

## 📚 Documentación

Consultar la carpeta `docs/` para:
- [Arquitectura del Sistema](docs/arquitectura.md)
- [Flujo de Procesos V1](docs/flujo_v1.md)
- [Decisiones Técnicas](docs/decisiones_tecnicas.md)
- [Roadmap](docs/roadmap.md)

## 🧪 Testing

```bash
pytest tests/ -v
```

## 📝 Licencia

Todos los derechos reservados.
