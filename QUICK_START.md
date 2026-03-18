## 🚀 Quick Start - SocioAI Streamlit App

### 📋 Pasos Rápidos

#### Paso 1: Instalar Dependencias
```bash
pip install -r requirements.txt
```

#### Paso 2: Generar Datos de Prueba (Opcional pero Recomendado)
```bash
python generate_test_data.py
```

Esto crea:
- `tb.xlsx` con 39 cuentas de ejemplo
- `hallazgos_previos.yaml` con 3 hallazgos
- `patrones.yaml` con 3 patrones

#### Paso 3: Ejecutar la App
```bash
streamlit run app/app_streamlit.py
```

O usar el script auxiliar:
```bash
python run_streamlit.py
```

#### Paso 4: Usar la App
1. Se abrirá automáticamente en `http://localhost:8501`
2. Seleccionar cliente en el sidebar (ej: "cliente_demo")
3. Hacer clic en "Cargar Cliente"
4. Explorar las 5 tabs

### 🎯 Qué Hace Cada Tab

#### 📊 Resumen
- Perfil del cliente (nombre, RUC, sector, moneda)
- Balance general (activos, pasivos, patrimonio)
- Indicadores de riesgo (áreas por nivel)
- Concentración de áreas

#### 🎯 Áreas de Riesgo
- **Tabla de Ranking**: 5 áreas ordenadas por score de riesgo
  - Código, Nombre, Saldo, % del Total, # Cuentas
  - Scores por criterio: Materialidad, Variación, Complejidad
  - Score Total (0-100)
- **Gráfico**: Scores por criterio

#### 📈 Variaciones
- **Métricas**: # Cuentas con variación, Mayor variación, Total
- **Top 10**: Cuentas con variación significativa

#### 📋 Trial Balance
- **Tabla Completa**: Todos las cuentas con código, nombre, saldo
- **Filtro**: Por tipo de cuenta (Activo, Pasivo, etc.)
- **Estadísticas**: Cantidad, suma, máximo, mínimo

### 💻 Estructura del Código

```
app_streamlit.py
├── Configuración de Streamlit
├── Sidebar (Selector de cliente)
├── Carga de datos
│   ├── leer_perfil()
│   ├── leer_tb()
│   ├── calcular_variaciones()
│   └── calcular_ranking_areas()
├── Header (Métricas principales)
└── 4 Tabs
    ├── Tab 1: Resumen (balance + indicadores)
    ├── Tab 2: Áreas de Riesgo (ranking + gráfico)
    ├── Tab 3: Variaciones (top cuentas)
    └── Tab 4: Trial Balance (tabla + filtros)
```

### 🎨 Características de UI

✅ **Layout Ancho**: Mejor visualización de tablas
✅ **Tabs Organizadas**: 4 secciones temáticas
✅ **Métricas**: Con emojis para referencia rápida
✅ **Tablas Interactivas**: Con st.dataframe()
✅ **Gráficos**: Chart de scores por área
✅ **Barras de Progreso**: Para concentración de áreas
✅ **Colores**: Indicadores de riesgo (rojo, amarillo, verde)

### 🔄 Flujo de Datos

```
YAML (perfil.yaml)
    ↓
leer_perfil() → perfil dict
    ↓
    ├→ Mostrar en métricas
    └→ Mostrar en Tab 1

Excel (tb.xlsx)
    ↓
leer_tb() → DataFrame
    ↓
    ├→ obtener_resumen_tb() → Tab 1
    ├→ calcular_variaciones() → Tab 3
    ├→ calcular_ranking_areas() → Tab 2
    └→ Mostrar tabla → Tab 4
```

### 📊 Datos de Ejemplo (si ejecutas generate_test_data.py)

**Cliente Demo:**
- Nombre: ABC Corporation S.A.
- RUC: 1234567890001
- Sector: Comerciales
- Patrimonio: $8,325,000

**Trial Balance:**
- 39 cuentas
- Activos: ~$8,325,000
- Pasivos: ~$3,730,000
- Patrimonio: ~$8,325,000

### 🛠️ Personalización

Cambiar en `app_streamlit.py`:

```python
# Página
st.set_page_config(
    page_title="Tu Nombre",
    page_icon="🏢",
    layout="wide"
)

# Tabla Ranking
display_df.columns = ['Tu', 'Columna', 'Personalizada']
```

### 🐛 Troubleshooting

**Error: "AttributeError: module 'pandas' has no attribute 'read_excel'"**
```bash
pip install openpyxl
```

**Error: "ModuleNotFoundError: No module named 'streamlit'"**
```bash
pip install streamlit
```

**App lenta o no carga datos**
- Verificar que `data/clientes/cliente_demo/` existe
- Ejecutar `generate_test_data.py`
- Revisar en `docs/FLUJO_COMPLETO.md` los requisitos

### 📚 Documentación Relacionada

- [FLUJO_COMPLETO.md](FLUJO_COMPLETO.md) - Arquitectura del flujo
- [INTEGRACION_SERVICIOS.md](INTEGRACION_SERVICIOS.md) - Cómo funcionan los servicios
- [CLIENTE_REPOSITORY.md](CLIENTE_REPOSITORY.md) - Acceso a datos

### 🎓 Ejemplos Adicionales

Ver `test_flujo_completo.py` para más ejemplos de uso del sistema sin Streamlit.

### 🚀 Próximos Pasos

1. ✅ App Streamlit básica (completado)
2. ⏳ Integración con LLM para briefs automáticos
3. ⏳ Workflow de hallazgos interactivo
4. ⏳ Exportación a reportes (PDF/Excel)
5. ⏳ Sistema de usuarios y multi-tenant
