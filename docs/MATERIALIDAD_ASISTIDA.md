## 📊 Materialidad Asistida - Guía Completa

### 🎯 Objetivo

Sugerir valores de materialidad basados en NIAs y reglas de negocio.
**El auditor siempre decide el valor final.**

### 📚 Fundamento Normativo

- **NIA 320**: Materialidad en la planificación y ejecución de auditoría
- **Benchmark**: Porcentajes de activos, patrimonio o ingresos según sector/tipo de entidad

### 🏗️ Archivos

#### 1. **data/catalogos/reglas_materialidad.yaml**
Define reglas por:
- `reglas_por_entidad`: SOCIEDAD_ANONIMA, COMPANIA_LIMITADA, etc.
- `reglas_por_sector`: comerciales, servicios, manufactura, etc.
- Cada regla contiene:
  - `base`: activos, patrimonio, ingresos
  - `porcentaje_min` y `porcentaje_max`: rango de materialidad
  - `descripcion`: notas sobre cuándo usar

#### 2. **domain/services/materialidad_service.py**
Servicio con 7 funciones principales.

#### 3. **data/clientes/{cliente}/materialidad.yaml**
Materialidad guardada para un cliente específico.

### 📖 Funciones Disponibles

#### 1. **obtener_regla_materialidad(cliente) → dict**
```python
regla = obtener_regla_materialidad("cliente_demo")
# {
#   'base': 'activos',
#   'porcentaje_min': 0.03,
#   'porcentaje_max': 0.05,
#   'origen': 'tipo_entidad: SOCIEDAD_ANONIMA'
# }
```

Busca:
1. Por `tipo_entidad` (SOCIEDAD_ANONIMA, etc.)
2. Por `sector` (comerciales, servicios, etc.)
3. Regla por defecto si no encuentra

#### 2. **obtener_base_materialidad(cliente, base) → float**
```python
base = obtener_base_materialidad("cliente_demo", "activos")
# 8325000.0
```

Extrae del Trial Balance:
- `activos` → ACTIVO total
- `pasivos` → PASIVO total
- `patrimonio` → PATRIMONIO total
- `ingresos` → INGRESOS total

#### 3. **calcular_materialidad(cliente, base_valor?) → dict**
```python
calculo = calcular_materialidad("cliente_demo")
# {
#   'materialidad_minima': 249750.00,
#   'materialidad_maxima': 416250.00,
#   'materialidad_sugerida': 333000.00,
#   'materialidad_desempeno': 249750.00,  # 75%
#   'error_trivial': 16650.00,             # 5%
#   'base_utilizada': 'activos',
#   'valor_base': 8325000.00,
#   'origen_regla': 'tipo_entidad: SOCIEDAD_ANONIMA'
# }
```

Calcula:
- **Min**: valor_base × porcentaje_min
- **Max**: valor_base × porcentaje_max
- **Sugerida**: (Min + Max) / 2
- **Desempeño**: Sugerida × 75% (NIA 320)
- **Error Trivial**: Sugerida × 5% (NIA 320)

#### 4. **sugerir_materialidad(cliente) → dict** ⭐ PRINCIPAL
```python
suggestion = sugerir_materialidad("cliente_demo")
# {
#   'cliente': 'cliente_demo',
#   'nombre_cliente': 'ABC Corporation S.A.',
#   'sector': 'comerciales',
#   'calculo': { ... cálculos completos ... },
#   'recomendacion': 'Para ABC Corporation...',
#   'proximos_pasos': [...]
# }
```

**Esto es lo que el auditor revisa y decide.**

#### 5. **guardar_sugerencia_materialidad(cliente, materialidad_elegida?) → bool**
```python
# Guardar con materialidad elegida
exito = guardar_sugerencia_materialidad("cliente_demo", 420000.00)

# O guardar con la sugerida (default)
exito = guardar_sugerencia_materialidad("cliente_demo")
```

Valida que esté en rango recomendado y guarda en:
`data/clientes/{cliente}/materialidad.yaml`

#### 6. **obtener_materialidad_guardada(cliente) → dict**
```python
guardada = obtener_materialidad_guardada("cliente_demo")
# {
#   'cliente': 'cliente_demo',
#   'materialidad_elegida': 420000.00,
#   'materialidad_desempeno': 315000.00,
#   'error_trivial': 21000.00,
#   'estado': 'REVISADA'
# }
```

Retorna None si no existe.

#### 7. **resumen_materialidad(cliente) → dict**
```python
resumen = resumen_materialidad("cliente_demo")
# {
#   'cliente': 'cliente_demo',
#   'nombre_cliente': 'ABC Corporation S.A.',
#   'materialidad_sugerida': 333000.00,
#   'materialidad_elegida': 420000.00,
#   'materialidad_desempeno': 315000.00,
#   'error_trivial': 21000.00,
#   'base': '5% de activos',
#   'estado': 'ESTABLECIDA'
# }
```

Para reportes y dashboards.

### 🔄 Flujo Típico

```
1. Auditor inicia análisis de nuevo cliente
   ↓
2. Sistema sugiere materialidad
   sugerir_materialidad("cliente_demo")
   ↓
3. Auditor revisa sugerencia
   "Base: 5% de activos"
   "Rango: $249k - $416k"
   "Sugerida: $333k"
   ↓
4. Auditor decide (ej: $420k)
   ↓
5. Sistema guarda decisión
   guardar_sugerencia_materialidad("cliente_demo", 420000)
   ↓
6. Sistema calcula derivadas (NIA 320)
   - Desempeño: 315k (75%)
   - Error Trivial: 21k (5%)
   ↓
7. Usar en análisis
   resumen = obtener_materialidad_guardada("cliente_demo")
```

### 💡 Ejemplo de Uso Completo

```python
from domain.services.materialidad_service import (
    sugerir_materialidad,
    guardar_sugerencia_materialidad,
    obtener_materialidad_guardada
)

# Paso 1: Obtener sugerencia
suggestion = sugerir_materialidad("cliente_demo")
print(suggestion['recomendacion'])

# Output:
# "Para ABC Corporation S.A., se sugiere usar materialidad de $333,000 
#  (5% de activos). Rango aceptable: $249,750 - $416,250"

# Paso 2: Auditor revisa y elige (ej: 10% más conservadora)
materialidad_final = suggestion['calculo']['materialidad_sugerida'] * 1.1

# Paso 3: Guardar
guardar_sugerencia_materialidad("cliente_demo", materialidad_final)

# Paso 4: Usar en análisis posterior
datos = obtener_materialidad_guardada("cliente_demo")
print(f"Desempeño: ${datos['materialidad_desempeno']:,.0f}")
print(f"Error Trivial: ${datos['error_trivial']:,.0f}")
```

### 📊 Reglas de Materialidad

#### Por Tipo de Entidad
```yaml
SOCIEDAD_ANONIMA:    3-5% de activos (empresas mercantiles)
COMPANIA_LIMITADA:   3-5% de activos (pymes)
COOPERATIVA:         2-5% del patrimonio
ONG:                 2-5% del patrimonio
FUNERARIA:           5-10% de activos
```

#### Por Sector
```yaml
comerciales:         3-5% de activos
servicios:           5-10% de ingresos
manufactura:         3-5% de activos
financiero:          1-3% de activos (más restrictivo)
agricultura:         5-10% de activos
sin_fines_de_lucro:  2-5% del patrimonio
```

### 🛡️ Manejo de Errores

- ✅ Si no encuentra regla → usa regla por defecto
- ✅ Si TB no existe → retorna None con advertencia
- ✅ Si materialidad fuera de rango → advierte pero guarda
- ✅ Nunca rompe ejecución

### 📝 Archivo YAML de Materialidad

```yaml
cliente: "cliente_demo"
nombre_cliente: "ABC Corporation S.A."

# Sugerencia del sistema
materialidad_sugerida: 333000.00

# Decisión del auditor
materialidad_elegida: 420000.00

# Derivadas (NIA 320)
materialidad_desempeno: 315000.00    # 75%
error_trivial: 21000.00              # 5%

# Trazabilidad
base_utilizada: "activos"
valor_base: 8325000.00
porcentaje_aplicado: 5.05
origen_regla: "tipo_entidad: SOCIEDAD_ANONIMA"

# Aprobación
estado: "REVISADA"
aprobada_por: "Auditor Senior"
fecha_aprobacion: "2026-03-16"
```

### 🧪 Testing

```bash
python test_materialidad_service.py
```

Prueba todas las funciones paso a paso.

### 🚀 Integración en Streamlit

```python
from domain.services.materialidad_service import sugerir_materialidad

st.subheader("Materialidad Sugerida")

suggestion = sugerir_materialidad(cliente)

if suggestion:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Mínima",
            f"${suggestion['calculo']['materialidad_minima']:,.0f}"
        )
    
    with col2:
        st.metric(
            "Sugerida", 
            f"${suggestion['calculo']['materialidad_sugerida']:,.0f}",
            delta="Recomendación del Sistema"
        )
    
    with col3:
        st.metric(
            "Máxima",
            f"${suggestion['calculo']['materialidad_maxima']:,.0f}"
        )
    
    st.info(suggestion['recomendacion'])
    
    # Input para que auditor confirme
    materialidad_confirmada = st.number_input(
        "Materialidad Confirmada",
        value=suggestion['calculo']['materialidad_sugerida'],
        step=1000.0
    )
    
    if st.button("Guardar Materialidad"):
        from domain.services.materialidad_service import guardar_sugerencia_materialidad
        guardar_sugerencia_materialidad(cliente, materialidad_confirmada)
        st.success("✅ Materialidad guardada")
```

### 📌 Notas Importantes

1. **Asistida, no automática**: El sistema sugiere, el auditor decide
2. **NIA 320 compliant**: Calcula desempeño y error trivial automáticamente
3. **Flexible**: Soporta múltiples bases (activos, patrimonio, ingresos)
4. **Trazable**: Guarda origen de la regla y decisión del auditor
5. **Reutilizable**: Funciona para cualquier cliente en la estructura

### 🎓 Referencias

- NIA 320: Materialidad en la Planificación y Ejecución de Auditoría
- Benchmarks de auditoría estándar por sector
- Normativas de auditoría de Ecuador (Supercias)

---

**Próximo paso**: Integrar en Streamlit app para que auditor use interactivamente.
