## ✅ MÓDULO DE MATERIALIDAD ASISTIDA - COMPLETADO

### 📦 Archivos Creados

```
✅ domain/services/materialidad_service.py     - Servicio (7 funciones)
✅ data/catalogos/reglas_materialidad.yaml     - Reglas por entidad/sector
✅ data/clientes/cliente_demo/materialidad.yaml - Ejemplo guardado
✅ test_materialidad_service.py                 - Script de prueba
✅ docs/MATERIALIDAD_ASISTIDA.md               - Documentación completa
```

### 🎯 Concepto

**Materialidad Asistida = Sistema sugiere, Auditor decide**

```
Cliente
  ↓
Perfil (tipo_entidad, sector)
  ↓
Obtener Regla Aplicable
  ├─ Por tipo_entidad (SOCIEDAD_ANONIMA, etc.)
  ├─ Por sector (comerciales, servicios, etc.)
  └─ Regla por defecto si no aplica
  ↓
Obtener Base del TB (activos, patrimonio, ingresos)
  ↓
Calcular Materialidad (min, max, sugerida)
  ↓
✨ Sugerir al Auditor
  ├─ "Rango: $249k - $416k"
  ├─ "Sugerida: $333k"
  └─ "Base: 5% de Activos"
  ↓
Auditor Revisa y Decide (ej: $420k)
  ↓
Guardar Decisión
  ├─ Materialidad Elegida: $420k
  ├─ Desempeño (75%): $315k  [NIA 320]
  ├─ Error Trivial (5%): $21k [NIA 320]
  └─ Trazabilidad: Quién, cuándo, por qué
```

### 📊 7 Funciones Principales

| # | Función | Entrada | Salida | Uso |
|---|---------|---------|--------|-----|
| 1 | `obtener_regla_materialidad()` | cliente | dict regla | Determinar base % |
| 2 | `obtener_base_materialidad()` | cliente, base | float | Obtener activos/patrimonio |
| 3 | `calcular_materialidad()` | cliente | dict cálculos | Min/max/sugerida |
| 4 | `sugerir_materialidad()` ⭐ | cliente | dict sugerencia | **Lo que auditor revisa** |
| 5 | `guardar_sugerencia_materialidad()` | cliente, valores | bool | Guardar decisión |
| 6 | `obtener_materialidad_guardada()` | cliente | dict guardada | Cargar decisión |
| 7 | `resumen_materialidad()` | cliente | dict resumen | Reportes |

### 💡 Ejemplo de Uso

```python
from domain.services.materialidad_service import sugerir_materialidad, guardar_sugerencia_materialidad

# 1️⃣  Obtener sugerencia
suggestion = sugerir_materialidad("cliente_demo")

# Auditor ve:
# "Para ABC Corporation S.A., se sugiere usar materialidad de $333,000 
#  (5% de activos). Rango aceptable: $249,750 - $416,250"

# 2️⃣  Auditor decide (puede ser igual a sugerida o diferente)
materialidad_final = suggestion['calculo']['materialidad_sugerida']  # o $420,000

# 3️⃣  Guardar decisión
guardar_sugerencia_materialidad("cliente_demo", materialidad_final)
# Sistema automáticamente calcula:
# - Materialidad de Desempeño: $315,000 (75%)
# - Error Trivial: $21,000 (5%)
```

### 📋 Qué Calcula el Sistema

#### Entrada
```
Cliente: "ABC Corporation S.A."
Tipo Entidad: SOCIEDAD_ANONIMA
Sector: comerciales
Trial Balance Total Activos: $8,325,000
```

#### Proceso
```
1. Buscar Regla por SOCIEDAD_ANONIMA
   ✓ Encontrada: "3-5% de activos"

2. Obtener Base del TB
   ✓ Activos: $8,325,000

3. Calcular:
   Min = $8,325,000 × 3% = $249,750
   Max = $8,325,000 × 5% = $416,250
   Sugerida = ($249,750 + $416,250) / 2 = $333,000
   Desempeño = $333,000 × 75% = $249,750
   Error Trivial = $333,000 × 5% = $16,650
```

#### Salida
```
✅ Sugerencia Completa:
   Mínima:        $249,750
   Sugerida:      $333,000 ← RECOMENDACIÓN DEL SISTEMA
   Máxima:        $416,250
   
   NIA 320:
   Desempeño:     $249,750 (75%)
   Error Trivial: $16,650 (5%)
```

### 🏗️ Reglas de Materialidad

#### 6 Tipos de Entidad
```yaml
SOCIEDAD_ANONIMA      → 3-5% de activos
COMPANIA_LIMITADA     → 3-5% de activos  
PERSONA_NATURAL       → 5-10% de activos
COOPERATIVA           → 2-5% de patrimonio
ONG                   → 2-5% de patrimonio
FUNERARIA             → 5-10% de activos
```

#### 6 Sectores
```yaml
comerciales           → 3-5% de activos
servicios             → 5-10% de ingresos
manufactura           → 3-5% de activos
financiero            → 1-3% de activos (restrictivo)
agricultura           → 5-10% de activos
sin_fines_de_lucro    → 2-5% de patrimonio
```

### 📁 Archivos de Configuración

#### 1. **reglas_materialidad.yaml**
Contiene reglas por entidad y sector.
Esta es la base de conocimiento que el sistema usa.

```yaml
reglas_por_entidad:
  SOCIEDAD_ANONIMA:
    base: "activos"
    porcentaje_min: 0.03
    porcentaje_max: 0.05
    descripcion: "Empresas mercantiles..."

reglas_por_sector:
  comerciales:
    base: "activos"
    porcentaje_min: 0.03
    porcentaje_max: 0.05
```

#### 2. **materialidad.yaml** (por cliente)
Guarda la decisión del auditor.

```yaml
cliente: "cliente_demo"
materialidad_sugerida: 333000.00
materialidad_elegida: 420000.00      ← Decisión del auditor
materialidad_desempeno: 315000.00    ← Calculado (75%)
error_trivial: 21000.00              ← Calculado (5%)
```

### 🧪 Testing

```bash
python test_materialidad_service.py
```

### ✨ Características Clave

✅ **Asistida, no automática**
   - Sistema recomienda, auditor decide

✅ **NIA 320 Compliant**
   - Calcula desempeño (75%) y error trivial (5%) automáticamente

✅ **Flexible**
   - Soporta múltiples bases: activos, patrimonio, ingresos

✅ **Escalable**
   - Fácil agregar nuevas reglas en YAML

✅ **Trazable**
   - Guarda origen de regla, decisión, y auditor

✅ **Robusto**
   - Manejo de errores, usa defaults si falta info

✅ **Integrable**
   - Listo para usar en Streamlit, reportes, APIs

### 🔄 Flujo de Negocio Completo

```
1. Auditor Inicia Análisis
   ├─ Carga cliente
   └─ Necesita definir materialidad
   
2. Sistema Sugiere
   sugerir_materialidad(cliente)
   ├─ Lee perfil
   ├─ Obtiene regla
   ├─ Calcula TB
   └─ Propone materialidad
   
3. Auditor Revisa
   ├─ Ve sugerencia: $333k
   ├─ Rango: $249k - $416k
   ├─ Puede aceptar o cambiar
   └─ Decide (ej: $420k)
   
4. Sistema Registra
   guardar_sugerencia_materialidad(cliente, 420000)
   ├─ Valida rango
   ├─ Calcula derivadas
   ├─ Guarda trazabilidad
   └─ ✅ Listo para usar
   
5. Sistema Utiliza en Análisis
   ├─ Ranking de áreas usa materialidad
   ├─ Variaciones filtradas por materialidad
   ├─ Reportes incluyen materialidad
   └─ Auditoría guiada por materialidad
```

### 📌 Regla de Precedencia

```
Obtener Regla:
  1. Si existe tipo_entidad normalizado → usar regla de entidad
  2. Si no, buscar sector normalizado → usar regla de sector
  3. Si tampoco → usar regla por defecto (3-5% activos)
```

### 🚀 Próximas Integraciones

1. **Streamlit UI** - Input interactivo para auditor
2. **Dashboard** - Mostrar materialidad en resumen
3. **Ranking de Áreas** - Usar materialidad para clasificar
4. **Reporte Personalizado** - Incluir materialidad en PDF
5. **Validación de Variaciones** - Marcar variaciones > materialidad

### 💻 Código Listo para Copiar y Pegar

El archivo `materialidad_service.py` está 100% funcional.
Incluye:
- ✅ Importaciones necesarias
- ✅ Manejo de errores
- ✅ Validaciones
- ✅ Docstrings con ejemplos
- ✅ Comentarios inline

**Solo cópialos y úsalos.**

### 📖 Documentación

- Completa en: [docs/MATERIALIDAD_ASISTIDA.md](../docs/MATERIALIDAD_ASISTIDA.md)
- Ejemplos en: [test_materialidad_service.py](../test_materialidad_service.py)
- Configuración: [data/catalogos/reglas_materialidad.yaml](../data/catalogos/reglas_materialidad.yaml)

---

**🎉 Módulo completo y listo para usar en auditoría asistida.**
