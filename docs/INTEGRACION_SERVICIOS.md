## 🔗 Integración: Cliente Repository + Servicios

### 📦 Arquitectura

```
cliente_repository (Base Layer)
    ↓
    ├→ leer_perfil.py (Servicio de Negocio)
    └→ lector_tb.py (Servicio de Análisis)
```

### ✅ Implementado

#### 1. **leer_perfil.py** (`domain/services/`)
Wrapper inteligente para cargar perfiles con validaciones.

**Funciones:**
- `leer_perfil(cliente)` - Carga perfil con validaciones
- `obtener_datos_clave(cliente)` - Devuelve resumen rápido
- `validar_cliente(cliente)` - Verifica si cliente existe

**Ejemplo:**
```python
from domain.services.leer_perfil import leer_perfil

perfil = leer_perfil("cliente_demo")
print(perfil['nombre'])  # "ABC Corp"
print(perfil['sector'])  # "comerciales"
```

#### 2. **lector_tb.py** (`analysis/`)
Wrapper inteligente para cargar/procesar trial balance.

**Funciones:**
- `leer_tb(cliente)` - Carga TB con transformaciones
- `obtener_resumen_tb(cliente)` - Totales por tipo
- `filtrar_por_tipo(cliente, tipo)` - Filtra por ACTIVO/PASIVO/etc.
- `filtrar_por_saldo_minimo(cliente, min)` - Cuentas significativas
- `obtener_cuentas_por_area(cliente, codigo)` - Cuentas del área

**Ejemplo:**
```python
from analysis.lector_tb import leer_tb, obtener_resumen_tb

tb = leer_tb("cliente_demo")
print(tb.shape)  # (500, 5)

resumen = obtener_resumen_tb("cliente_demo")
print(resumen['ACTIVO'])  # 10000000.00
```

### 🏗️ Flujo Completo

```python
# 1. Cargar datos base
from domain.services.leer_perfil import leer_perfil
from analysis.lector_tb import leer_tb

perfil = leer_perfil("cliente_demo")
tb = leer_tb("cliente_demo")

# 2. Análisis por área
from analysis.lector_tb import obtener_cuentas_por_area
cuentas_cxc = obtener_cuentas_por_area("cliente_demo", "130")

# 3. Calcular materialidad
resumen = obtener_resumen_tb("cliente_demo")
total_activos = resumen.get('ACTIVO', 0)
materialidad = total_activos * 0.05

# 4. Identificar cuentas significativas
from analysis.lector_tb import filtrar_por_saldo_minimo
significativas = filtrar_por_saldo_minimo("cliente_demo", materialidad)

# 5. Almacenar materialidad
from infra.repositories.cliente_repository import guardar_materialidad
guardar_materialidad("cliente_demo", {
    "total_activos": total_activos,
    "threshold": materialidad
})
```

### 🛡️ Manejo de Errores

Todos los servicios:
- ✅ Validan datos
- ✅ Retornan `None` o vacío si falla
- ✅ Imprime mensajes de error
- ✅ **Nunca rompen ejecución**

### 📊 Transformaciones Automáticas

`lector_tb.py` enriquece automáticamente:
- Normaliza nombres de columnas (minúsculas)
- Clasifica cuentas por tipo (ACTIVO, PASIVO, etc.)
- Calcula valores absolutos
- Valida estructura

### 🧪 Probar Integración

```bash
python test_integracion_completa.py
```

### 🔄 Sin Rutas Directas

**ANTES:**
```python
df = pd.read_excel("data/clientes/cliente_demo/tb.xlsx")
```

**AHORA:**
```python
from analysis.lector_tb import leer_tb
df = leer_tb("cliente_demo")
```

### ✨ Ventajas

✅ Código centralizado - Un solo punto de verdad  
✅ Fácil de mantener - Cambios en un lugar  
✅ Reutilizable - Mismo código en cualquier servicio  
✅ Testeable - Interfaces claras  
✅ Compatible - No rompe código existente  
