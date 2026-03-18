## 🚀 Flujo Completo: run_cliente()

### 📋 Objetivo
Ejecutar análisis completo de un cliente desde carga de datos hasta ranking de riesgos.

### 🔄 Flujo

```
run_cliente("cliente_demo")
    ↓
1️⃣  Cargar perfil
    leer_perfil() → dict
    ↓
2️⃣  Cargar Trial Balance
    leer_tb() → pd.DataFrame
    ↓
3️⃣  Calcular variaciones
    calcular_variaciones() → pd.DataFrame
    ↓
4️⃣  Ranking de áreas
    calcular_ranking_areas() → pd.DataFrame
    ↓
✅ Retornar resumen ejecutivo
```

### 💻 Uso

#### Opción 1: Python directo
```python
from app.socio_ai import run_cliente

resultado = run_cliente("cliente_demo")
print(resultado['status'])  # 'EXITOSO'
print(resultado['areas_riesgo'])
```

#### Opción 2: CLI
```bash
python app/socio_ai.py cliente_demo
```

### 📊 Estructura de Salida

```json
{
  "status": "EXITOSO",
  "cliente": "cliente_demo",
  "perfil": {
    "nombre": "ABC Corp",
    "ruc": "1234567890",
    "sector": "comerciales",
    "moneda": "USD"
  },
  "balance": {
    "total_activos": 10000000,
    "total_pasivos": 5000000,
    "total_patrimonio": 5000000,
    "num_cuentas": 500
  },
  "variaciones": {
    "total_cuentas_variacion": 15,
    "mayor_variacion": 250000,
    "cuentas_top_5": ["CxC", "Inventarios", ...]
  },
  "areas_riesgo": {
    "areas_alto_riesgo": 2,
    "areas_medio_riesgo": 1,
    "areas_bajo_riesgo": 2,
    "patrimonio_total": 5000000,
    "concentracion_principal_area": 35.5
  },
  "top_areas": [
    {
      "ranking": 1,
      "area": "130",
      "nombre": "Cuentas por Cobrar",
      "score_riesgo": 65.3
    },
    ...
  ]
}
```

### 🎯 Componentes

#### 1. **Cargar Perfil**
```python
from domain.services.leer_perfil import leer_perfil
perfil = leer_perfil("cliente_demo")
# Retorna: dict con nombre, RUC, sector, etc.
```

#### 2. **Cargar TB**
```python
from analysis.lector_tb import leer_tb
tb = leer_tb("cliente_demo")
# Retorna: DataFrame con cuentas y saldos
```

#### 3. **Variaciones**
```python
from analysis.variaciones import calcular_variaciones
variaciones = calcular_variaciones("cliente_demo")
# Retorna: DataFrame con cuentas con cambios significativos
```

#### 4. **Ranking de Áreas**
```python
from analysis.ranking_areas import calcular_ranking_areas
ranking = calcular_ranking_areas("cliente_demo")
# Retorna: DataFrame ordenado por score de riesgo
```

### 🎨 Salida en Consola

```
======================================================================
🚀 INICIANDO ANÁLISIS: cliente_demo
======================================================================

📋 PASO 1: Cargando perfil cliente...
----------------------------------------------------------------------
✅ Cliente cargado: ABC Corp
   RUC: 1234567890
   Sector: comerciales

📊 PASO 2: Cargando trial balance...
----------------------------------------------------------------------
✅ TB cargado: 500 cuentas
   Total Activos: $10,000,000
   Total Pasivos: $5,000,000
   Total Patrimonio: $5,000,000

📈 PASO 3: Calculando variaciones...
----------------------------------------------------------------------
✅ Variaciones calculadas: 15 cuentas
   Mayor variación: $250,000
   Top cuentas: CxC, Inventarios

🎯 PASO 4: Calculando ranking de áreas...
----------------------------------------------------------------------
✅ Ranking de áreas calculado:
   1. Cuentas por Cobrar        | Score:  65.3 | $3,500,000
   2. Efectivo                  | Score:  58.7 | $2,100,000
   3. Patrimonio                | Score:  48.2 | $5,000,000

   📊 Indicadores clave:
   - Áreas alto riesgo: 2
   - Áreas medio riesgo: 1
   - Concentración principal área: 35.0%

======================================================================
📌 RESUMEN EJECUTIVO
======================================================================

✅ ANÁLISIS COMPLETADO EXITOSAMENTE
   Cliente: ABC Corp
   Cuentas procesadas: 500
   Patrimonio total: $5,000,000
   Áreas alto riesgo: 2

   ⚠️  ÁREAS A PRIORIZAR:
      1. Cuentas por Cobrar (Score: 65.3)
      2. Efectivo (Score: 58.7)

======================================================================
```

### 🛡️ Manejo de Errores

- ✅ Cliente no existe → retorna `status: 'ERROR'`
- ✅ TB no existe → retorna `status: 'ERROR'`
- ✅ Validaciones automáticas en cada paso
- ✅ Nunca rompe la ejecución

### 🧪 Testing

```bash
# Ejecutar flujo completo
python test_flujo_completo.py

# O probar desde Python directamente
python -c "from app.socio_ai import run_cliente; run_cliente('cliente_demo')"
```

### ♻️ Reutilizable

Cada componente es independiente y puede usarse por separado:

```python
# Solo con perfil
from domain.services.leer_perfil import leer_perfil
perfil = leer_perfil("cliente_demo")

# Solo TB + variaciones
from analysis.lector_tb import leer_tb
from analysis.variaciones import calcular_variaciones
tb = leer_tb("cliente_demo")
var = calcular_variaciones("cliente_demo")

# Solo ranking
from analysis.ranking_areas import calcular_ranking_areas
ranking = calcular_ranking_areas("cliente_demo")
```

### 🚀 Próximos Pasos

1. Crear `materialidad_service.py` para cálculos de materialidad
2. Integrar LLM para generar briefings automáticos
3. Implementar workflow de hallazgos
4. Crear vista Streamlit interactiva
5. Agregar exportación a reportes (PDF/Excel)
