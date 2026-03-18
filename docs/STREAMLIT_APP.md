## 🚀 Ejecutar Aplicación Streamlit

### 📋 Requisitos

- Python 3.9+
- Dependencias instaladas: `pip install -r requirements.txt`

### ▶️ Ejecutar

```bash
streamlit run app/app_streamlit.py
```

Esto abrirá la aplicación en: `http://localhost:8501`

### 🎯 Características

✅ **Selector de Cliente** - Dropdown con clientes disponibles
✅ **Perfil** - Muestra nombre, RUC, sector, moneda
✅ **Balance General** - Activos, Pasivos, Patrimonio
✅ **Indicadores de Riesgo** - Áreas por nivel de riesgo
✅ **Ranking de Áreas** - Score por criterios
✅ **Variaciones** - Cuentas con cambios significativos
✅ **Trial Balance** - Tabla completa con filtros
✅ **Gráficos** - Visualización de scores

### 📊 Secciones

#### 1. Configuración (Sidebar)
- Selector de cliente
- Botón para cargar/recargar

#### 2. Resumen 
- Métricas del cliente
- Balance general
- Indicadores de riesgo
- Concentración de áreas

#### 3. Áreas de Riesgo
- Tabla de ranking
- Scores por criterio
- Gráfico de componentes

#### 4. Variaciones
- Top cuentas con variación
- Impacto de cambios

#### 5. Trial Balance
- Tabla completa
- Filtros por tipo de cuenta
- Estadísticas

### 💻 Uso

1. Ejecutar: `streamlit run app/app_streamlit.py`
2. Ver la app en el navegador
3. Seleccionar cliente del dropdown
4. Hacer clic en "Cargar Cliente"
5. Explorar las 5 tabs con información

### 🎨 Diseño

- Layout ancho para mejor visualización
- Tabs para organizar información
- Métricas con emojis
- Tablas interactivas
- Gráficos de barras
- Barras de progreso

### ⚙️ Configuración

Cambiar valores en `st.set_page_config()`:
- `page_title` - Título de la pestaña
- `page_icon` - Icono
- `layout` - "wide" o "centered"

### 📌 Notas

- Sin LLM todavía (próxima fase)
- Datos en tiempo real desde archivos
- Carga automática sin necesidad de refresh F5
- Compatible con múltiples clientes
