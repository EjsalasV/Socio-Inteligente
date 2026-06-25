# Instancia: Servicios Plurianuales (Desarrollo + Soporte + Licencia)

> **Patrón:** Cliente contrata desarrollo de software + soporte técnico anual + licencia de software. Las 3 obligaciones tienen métodos de reconocimiento distintos. Muy común en implementaciones de ERP, CRM, aplicaciones personalizadas.

> **Riesgo típico:** No separar desarrollo de soporte; reconocer todo 100% cuando se activa sistema. Resultado: ingreso concentrado mes 1, cuando debería distribuirse en 12-36 meses.

---

## Las 3 Obligaciones

| Obligación | Tipo | Método | Plazo | Criterio de Cumplimiento |
|-----------|------|--------|-------|--------------------------|
| **1. Desarrollo** | servicio_por_avance | sobre_tiempo_por_avance | 3-6 meses | Acta de avance x hito, acta de aceptación final |
| **2. Soporte Técnico** | servicio_lineal_periodo | sobre_tiempo_lineal | 12 meses | Contrato activo, acta de disponibilidad mensual |
| **3. Licencia / Acceso** | servicio_licencia_software | punto_en_tiempo O sobre_tiempo_lineal | Inicio (punto) o 12 meses (lineal) | Activación de credenciales (punto) O cada mes vigente (lineal) |

---

## Caso Real: Cliente XYZ

```
CONTRATO FIRMADO: enero 2026
- Desarrollo de módulo de inventario: USD 40,000 (3 meses)
- Soporte técnico 1 año: USD 12,000
- Licencia software 1 año: USD 8,000
- TOTAL: USD 60,000

PRECIO DE TRANSACCIÓN:
- Precio fijo: USD 60,000 (USD 50,000 + IVA, sin descuentos)
- Retención: 0% (este cliente no tiene)
- Devoluciones estimadas: 0% (software no devuelve)
- Bonificaciones: 0%
- TOTAL A RECONOCER: USD 60,000

ASIGNACIÓN DE PRECIO:
- Desarrollo: USD 40,000 (67%)
  Razón: Precio observable; desarrollo separado cuesta eso
- Soporte: USD 12,000 (20%)
  Razón: Costo + margen; soporte anual típico USD 1k/mes
- Licencia: USD 8,000 (13%)
  Razón: Precio observable; software standalone cuesta USD 8k/año

RECONOCIMIENTO:
- Desarrollo: sobre_tiempo_por_avance
  Hito 1 (mes 1): 30% cumplido → USD 12,000
  Hito 2 (mes 2): 40% cumplido → USD 16,000
  Hito 3 (mes 3): 30% cumplido → USD 12,000
  
- Soporte: sobre_tiempo_lineal
  Enero-Diciembre: USD 1,000 cada mes (USD 12,000 / 12)
  
- Licencia: punto_en_tiempo (cuando sistema activa)
  Marzo 15 (cuando desarrollo finaliza): USD 8,000
```

---

## Cómo Audita: Paso a Paso

### **PASO 1: Validar Contrato**

**¿Qué buscar?**
- ¿Contrato escrito y firmado por ambas partes?
- ¿Se especifican las 3 partes (desarrollo, soporte, licencia)?
- ¿Hay plazo claro? (desarrollo 3 meses, soporte 12 meses)
- ¿Precio total es claro? (USD 60,000)

**Checklist:**
```
□ Contrato existe y está firmado
□ Especifica: desarrollo (fases), soporte (12 meses), licencia (plazo)
□ Precio total: USD [monto] sin contingencias
□ Aprobación de cliente: email de aceptación, acta de requerimientos
```

**Hallazgo si falta:**
"Contrato sin especificar partes separadas. Desarrollo y soporte están mezclados."

---

### **PASO 2: Validar Obligaciones (¿3 separadas?)**

**¿Qué buscar?**
- ¿Existe MATRIZ DE OBLIGACIONES que lista las 3?
- ¿Cada una tiene descripción (qué entrega)?
- ¿Cada una tiene criterio de cumplimiento claro?

**Checklist:**
```
□ Desarrollo: especificación de funcionalidades (módulos, reportes, integraciones)
□ Desarrollo: plazo de 3-6 meses
□ Desarrollo: criterio: "acta de aceptación de cliente"

□ Soporte: especificación (respuesta time, ticket resolution, disponibilidad)
□ Soporte: plazo de 12 meses
□ Soporte: criterio: "contrato vigente, acta mensual de disponibilidad"

□ Licencia: especificación (número de usuarios, módulos incluidos, plazo)
□ Licencia: criterio: "activación de credenciales" o "cada mes vigente"

□ MATRIZ está en archivo del cliente (email anexo, acta de requerimientos, o documento separate)
```

**Hallazgo si falta:**
"No existe matriz de obligaciones. Desarrollo, soporte y licencia no están claramente separados."

---

### **PASO 3: Validar Precio de Transacción**

**¿Qué buscar?**
- ¿Precio total es USD 60,000? ¿Hay descuentos, retenciones?
- ¿Se documentó análisis de cada componente?

**Checklist:**
```
□ Precio total del contrato: USD [monto]
□ ¿Hay descuentos? (por pago anticipado, volumen, etc.) → deducir
□ ¿Hay retención de cliente? (construcción típica, aquí NO) → deducir
□ ¿Hay devoluciones estimadas? (software NO devuelve) → deducir
□ Precio de transacción final: USD [monto] = Ingreso a reconocer

□ Análisis está documentado (email, acta, archivo de precio)
```

**Hallazgo si falta:**
"Precio reconocido por USD 60,000, pero cliente tiene 10% descuento por pago anticipado (USD 6k) que no fue deducido."

---

### **PASO 4: Validar Asignación de Precio**

**¿Qué buscar?**
- ¿MATRIZ DE ASIGNACIÓN existe? (cada obligación tiene monto)
- ¿Base de asignación está documentada?
- ¿Suma cuadra? (40k + 12k + 8k = 60k)

**Checklist:**
```
□ Desarrollo: USD 40,000 (40% del total)
  Base: Precio observable (desarrollos similares cuestan USD 40k)
  O Base: Costo + margen (costo USD 30k + 33% = USD 40k)

□ Soporte: USD 12,000 (20% del total)
  Base: Costo + margen (costo USD 8k + 50% = USD 12k)
  O Base: Benchmarking (soporte anual típico 1k/mes = 12k)

□ Licencia: USD 8,000 (13% del total)
  Base: Precio observable (software cuesta USD 8k/año)

□ Suma: 40k + 12k + 8k = 60k ✓

□ Matriz está documentada en archivo (email, acta, o documento separado)
```

**Hallazgo si falta:**
"Asignación entre las 3 obligaciones no está documentada. Desarrollo se asignó USD 50k (83%) sin justificación."

---

### **PASO 5: Validar Reconocimiento**

**¿Qué buscar?**

#### **5A: Desarrollo (sobre_tiempo_por_avance)**

```
□ Hito 1 (Análisis de Requerimientos):
  - Acta de cumplimiento: [FECHA]
  - % avance: 30% (documentado en acta)
  - Ingreso USD 12,000 reconocido: [FECHA]
  - Validar: Fecha acta ≤ Fecha asiento ✓

□ Hito 2 (Desarrollo Funcionalidades):
  - Acta de cumplimiento: [FECHA]
  - % avance: 40% (documentado en acta)
  - Ingreso USD 16,000 reconocido: [FECHA]
  - Validar: Acta ANTES de asiento ✓

□ Hito 3 (Testing y Aceptación Final):
  - Acta de aceptación: [FECHA] (firmada por cliente)
  - % avance: 30% (completado)
  - Ingreso USD 12,000 reconocido: [FECHA]
  - Validar: Cliente aceptó en esa fecha ✓

□ TOTAL DESARROLLO: 30% + 40% + 30% = 100% ✓
□ TOTAL INGRESO: 12k + 16k + 12k = 40k ✓
```

#### **5B: Soporte (sobre_tiempo_lineal)**

```
□ Enero: Soporte vigente → USD 1,000 (1/12 de 12k)
  - Acta de disponibilidad del servicio: SÍ/NO
  - Asiento registrado: [FECHA]

□ Febrero: Soporte vigente → USD 1,000
  - Acta de disponibilidad: SÍ/NO
  - Asiento registrado: [FECHA]

□ [Marzo a Diciembre: repetir]

□ TOTAL: 12 meses × USD 1,000/mes = USD 12,000 ✓

□ Si soporte se suspendió antes de 12 meses:
  - Acta de suspensión: [FECHA] (mes X)
  - Ingreso se reconoce solo hasta mes X
  - Diferencia se crea como pasivo (soporte prepagado no prestado)
```

#### **5C: Licencia (punto_en_tiempo)**

```
□ Fecha activación del sistema: [FECHA] (ej. marzo 15)
  - Email de activación: SÍ/NO
  - Credenciales enviadas al cliente: SÍ/NO
  - Cliente confirma acceso: SÍ/NO

□ Ingreso USD 8,000 reconocido: [FECHA] = Fecha activación ✓

□ Si método es sobre_tiempo_lineal en lugar de punto:
  - Enero: USD 667 (1/12 de 8k)
  - Febrero: USD 667
  - Marzo: USD 666
  - [etc.]
  - Asegurarse que es congruente con contrato
```

---

## Hallazgos Típicos (TOP 5)

### **HALLAZGO 1: No se separó desarrollo de soporte**
```
Encontrado: Ingreso USD 60,000 reconocido 100% cuando sistema se activó (marzo).
Problema: Soporte anual (USD 12,000) debería reconocerse linealmente (USD 1,000/mes).
Impacto: Ingreso concentrado en marzo, cuando debería ser marzo + 11 meses más.
Corrección: Revertir USD 11,000 de marzo, reconocer USD 1,000 cada mes futura.
```

### **HALLAZGO 2: Desarrollo sin actas de hito**
```
Encontrado: Desarrollo USD 40,000 dividido en 3 hitos, pero solo tiene acta de cierre final.
Problema: Hitos 1 y 2 se reconocieron sin acta de cumplimiento.
Impacto: Ingreso anticipado en hito 1 y 2.
Corrección: Solicitar actas retroactivas o revertir hitos sin evidencia.
```

### **HALLAZGO 3: Asignación de precio sin base documentada**
```
Encontrado: Desarrollo USD 50,000 (83%), Soporte USD 8,000 (13%), Licencia USD 2,000 (3%).
Problema: No hay documento que justifique esa asignación (es arbitraria).
Impacto: Concentra ingreso en desarrollo, cuando soporte debería ser más.
Corrección: Documentar base observable o estimada; re-asignar si corresponde.
```

### **HALLAZGO 4: Soporte se reconoce sin validación de prestación**
```
Encontrado: Soporte USD 1,000/mes se reconoce automáticamente, sin acta de disponibilidad.
Problema: Si servicio se suspendió mes 5-8, ingreso se sigue reconociendo igual.
Impacto: Ingreso sin cumplimiento.
Corrección: Implementar acta mensual de disponibilidad; suspender ingreso si servicio no se prestó.
```

### **HALLAZGO 5: Licencia se reconoce antes de activación**
```
Encontrado: Licencia USD 8,000 reconocida en enero (cuando contrato se firma).
Problema: Sistema no se activó hasta marzo.
Impacto: Ingreso anticipado 2 meses.
Corrección: Revertir a marzo (fecha de activación), crear pasivo en enero-febrero.
```

---

## Matriz de Pruebas (Qué Validar)

| Qué Validar | Cómo | Qué Buscar | Hallazgo Si Falta |
|------------|------|-----------|-------------------|
| **Contrato claró** | Leer especificación | Desarrollo, Soporte, Licencia separados | "Contrato sin especificar obligaciones" |
| **Matriz obligaciones** | Pedir a cliente | Documento que lista las 3 obligaciones | "No existe matriz de obligaciones" |
| **Asignación precio** | Revisar archivo | Desarrollo 40k, Soporte 12k, Licencia 8k con base | "Asignación no documentada" |
| **Hitos desarrollo** | Comparar actas vs. asientos | 3 actas de hito con % y fechas | "Desarrollo sin actas de hito" |
| **Soporte lineal** | Validar últimos 6 meses | Cada mes: acta + asiento USD 1,000 | "Soporte reconocido sin validación mensual" |
| **Licencia activación** | Confirmar fecha activación | Email de activación, credenciales, confirmación cliente | "Licencia reconocida antes de activar" |
| **Reconciliación** | Comparar ingreso acumulado vs. cumplimiento | 3 meses desarrollo: 100% reconocido? | "No existe reconciliación" |

---

## Preguntas de Cierre para Socio Revisor

- ¿Se separaron claramente las 3 obligaciones?
- ¿Cada hito de desarrollo tiene acta de cumplimiento antes del asiento?
- ¿Soporte se reconoce linealmente (no 100% mes 1)?
- ¿Si contrato cambió (alcance, plazo, precio), se re-analizó NIIF 15?
- ¿El cliente tiene proceso de reconciliación mensual?

