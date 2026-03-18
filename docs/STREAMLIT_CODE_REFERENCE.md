## 📋 Bloque de Código: Uso de Streamlit en app_streamlit.py

Este es el flujo principal que implementé. Puedes copiarlo como referencia:

### ✅ Estructura Principal

```python
import streamlit as st
from domain.services.leer_perfil import leer_perfil, obtener_datos_clave
from analysis.lector_tb import leer_tb, obtener_resumen_tb
from analysis.variaciones import calcular_variaciones, resumen_variaciones
from analysis.ranking_areas import calcular_ranking_areas, obtener_indicadores_clave

# Configurar página
st.set_page_config(page_title="SocioAI", layout="wide")

# SIDEBAR: Selector de cliente
cliente_seleccionado = st.sidebar.selectbox(
    "Seleccionar Cliente",
    options=["cliente_demo", "bf_holding_2025", "bustamante_fabara_ip_2025"]
)

# CARGAR DATOS
perfil = leer_perfil(cliente_seleccionado)
tb = leer_tb(cliente_seleccionado)
ranking_areas = calcular_ranking_areas(cliente_seleccionado)
variaciones = calcular_variaciones(cliente_seleccionado)
resumen_tb = obtener_resumen_tb(cliente_seleccionado)

# HEADER
st.title("📊 SocioAI - Auditoría Inteligente")

# MÉTRICAS
col1, col2, col3, col4 = st.columns(4)
col1.metric("🏢 Cliente", perfil.get('nombre'))
col2.metric("📋 RUC", perfil.get('ruc'))
col3.metric("🏭 Sector", perfil.get('sector'))
col4.metric("💱 Moneda", perfil.get('moneda'))

st.divider()

# TABS
tab1, tab2, tab3, tab4 = st.tabs(["Resumen", "Áreas de Riesgo", "Variaciones", "TB"])

with tab1:
    st.subheader("Balance General")
    c1, c2, c3 = st.columns(3)
    c1.metric("Activos", f"${resumen_tb.get('ACTIVO', 0):,.0f}")
    c2.metric("Pasivos", f"${resumen_tb.get('PASIVO', 0):,.0f}")
    c3.metric("Patrimonio", f"${resumen_tb.get('PATRIMONIO', 0):,.0f}")

with tab2:
    st.subheader("Ranking de Áreas")
    st.dataframe(ranking_areas, use_container_width=True)

with tab3:
    st.subheader("Variaciones")
    st.dataframe(variaciones.head(10), use_container_width=True)

with tab4:
    st.subheader("Trial Balance")
    st.dataframe(tb, use_container_width=True)
```

### 🔄 Flujo Simplificado

```
app_streamlit.py
├─ Importar funciones
├─ Configurar Streamlit
├─ Sidebar: selector cliente
├─ Cargar datos:
│  ├─ leer_perfil()
│  ├─ leer_tb()
│  ├─ calcular_ranking_areas()
│  └─ calcular_variaciones()
├─ Mostrar header (con métricas)
├─ Crear 4 tabs
│  ├─ Tab 1: Balance
│  ├─ Tab 2: Ranking
│  ├─ Tab 3: Variaciones
│  └─ Tab 4: TB completo
└─ Footer
```

### 💡 Componentes Clave

**1. Selector de Cliente (Sidebar)**
```python
cliente = st.sidebar.selectbox("Seleccionar Cliente", opciones)
```

**2. Cargar Datos**
```python
perfil = leer_perfil(cliente)
tb = leer_tb(cliente)
ranking = calcular_ranking_areas(cliente)
```

**3. Mostrar Métricas**
```python
col1, col2, col3 = st.columns(3)
col1.metric("Label", "Valor")
```

**4. Mostrar Tablas**
```python
st.dataframe(df, use_container_width=True)
```

**5. Crear Tabs**
```python
tab1, tab2 = st.tabs(["Tab 1", "Tab 2"])
with tab1:
    st.write("Contenido")
```

### 🎨 Personalización

**Cambiar colores:**
```python
st.markdown("""
    <style>
    .metric-card { background-color: #f0f2f6; }
    </style>
""", unsafe_allow_html=True)
```

**Agregar dividers:**
```python
st.divider()
```

**Mostrar gráficos:**
```python
st.bar_chart(datos)
st.line_chart(datos)
```

### 🚀 Ejecutar

```bash
streamlit run app/app_streamlit.py
```

**URL:** http://localhost:8501

### 📌 Notas Importantes

- Sin LLM en la app actual (solo análisis de datos)
- Los datos se cargan directamente desde archivos (rápido)
- Compatible con múltiples clientes (selector en sidebar)
- Usa session_state de Streamlit para estado persistente
- Tablas interactivas (sorteable, buscable)
