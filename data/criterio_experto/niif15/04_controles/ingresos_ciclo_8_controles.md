# 8 Controles Universales del Ciclo de Ingresos

> **Estado:** Framework universal. Aplica a TODO cliente bajo NIIF 15, independientemente del sector. Estos 8 controles mitiguen los riesgos más comunes en reconocimiento de ingresos.

---

## Propósito

Un auditor NO DEBERÍA tener que leer NIIF 15 página por página. Debería validar que el cliente tiene estos 8 controles internos. Si los tiene, el riesgo de ingreso incorrecto es bajo.

**Si falta un control = hallazgo potencial.**

---

## Los 8 Controles

### **Control 1: Aprobación Formal del Contrato**

**¿Qué es?**
Alguien con autoridad (gerente de ventas, abogado, aprobador de crédito) valida y aprueba ANTES de que comience el cumplimiento.

**¿Por qué importa?**
Si contrato se "acepta" sin aprobación formal, hay riesgo de:
- Términos no autorizados (precio incorrecto, plazo irreal)
- Cliente no solvente
- Obligaciones no claras

**¿Cómo debería funcionar?**

```
Vendedor prepara contrato
       ↓
Aprobador legal/comercial revisa (cláusulas, cliente, precio)
       ↓
Aprobador autoriza ("OK para ejecutar")
       ↓
Cliente firma
       ↓
Se inicia cumplimiento
```

**¿Qué busca auditor?**

- ¿Existe evidencia de aprobación antes de cumplimiento? (email, acta, stamp)
- ¿Quién aprobó? (¿tiene autoridad?)
- ¿Se documentó la aprobación? (no es verbal)

**Hallazgo si falta:**
"Contrato USD XXX iniciado sin aprobación documentada. Riesgo de términos no autorizados."

---

### **Control 2: Identificación de Obligaciones de Desempeño**

**¿Qué es?**
ANTES de reconocer ingreso, alguien analiza: "¿Cuántas obligaciones separables tiene este contrato?"

**¿Por qué importa?**
Si no se identifica claramente, hay riesgo de:
- Mezclar servicios (una obligación vs. varias)
- Reconocer todo de una vez (cuando debería ser lineal)
- No separar garantía/mantenimiento de bien principal

**¿Cómo debería funcionar?**

```
Contrato se firma
       ↓
ANALISTA ejecuta: "¿Cuántas obligaciones?"
       ↓
Documenta en MATRIZ: Obligación 1, 2, 3...
       ↓
Cliente confirma análisis (acta de requerimientos)
       ↓
Cada obligación tiene criterio de cumplimiento claro
```

**¿Qué busca auditor?**

- ¿Existe MATRIZ DE OBLIGACIONES documentada?
- ¿Se identificaron TODAS las obligaciones separables?
- ¿Cada obligación tiene criterio de cumplimiento?
- ¿Cliente confirmó el análisis?

**Hallazgo si falta:**
"Contrato de servicios (desarrollo + soporte + licencia) tratado como 1 obligación. Debería ser 3. Riesgo de reconocimiento incorrecto."

---

### **Control 3: Asignación de Precio a Cada Obligación**

**¿Qué es?**
Si hay múltiples obligaciones, cada una tiene un monto asignado. La suma = precio total.

**¿Por qué importa?**
Si asignación es arbitraria, hay riesgo de:
- Sobrevalorar obligación de punto_en_tiempo (ingreso inmediato)
- Subvalorar obligación de sobre_tiempo (ingreso diferido)
- Resultado: ingresos incorrectos en períodos

**¿Cómo debería funcionar?**

```
Contrato tiene precio total: USD 100k
       ↓
ANALISTA crea MATRIZ DE ASIGNACIÓN:
  - Obligación 1 (desarrollo): USD 40k
  - Obligación 2 (soporte lineal 24 meses): USD 30k
  - Obligación 3 (licencia): USD 30k
  - TOTAL: USD 100k
       ↓
BASE: Precios observables o estimados documentados
       ↓
REVISIÓN: ¿Suma cuadra? ¿Base es razonable?
```

**¿Qué busca auditor?**

- ¿Existe MATRIZ DE ASIGNACIÓN?
- ¿Base de asignación está documentada? (observable o estimada)
- ¿Suma de obligaciones = Precio total?
- ¿Matriz fue revisada si contrato cambió?

**Hallazgo si falta:**
"Asignación de precio entre obligaciones no documentada. Ingreso podría estar sesgado a períodos iniciales. Riesgo de mal timing."

---

### **Control 4: Evaluación del Método de Reconocimiento (Punto vs. Tiempo)**

**¿Qué es?**
ANTES de reconocer, alguien determina: "¿Esta obligación se cumple en punto_en_tiempo o sobre_tiempo?"

**¿Por qué importa?**
Elegir mal el método = ingresos completamente incorrectos:
- Servicio lineal reconocido 100% en mes 1 (vs. 1/12 cada mes)
- Construcción por fases reconocida sin acta de cumplimiento
- Bien reconocido antes de aceptación cliente

**¿Cómo debería funcionar?**

```
Cada obligación tiene MÉTODO DE RECONOCIMIENTO documentado:
  - Obligación 1: PUNTO_EN_TIEMPO (acta de aceptación)
  - Obligación 2: SOBRE_TIEMPO_LINEAL (24 meses, USD 1.25k/mes)
  - Obligación 3: SOBRE_TIEMPO_LINEAL (1 año, USD 2.5k/mes)
       ↓
DOCUMENTACIÓN: ¿Por qué ese método? (referencia a NIIF 15 o política)
       ↓
REVISIÓN: ¿El método es congruente con la obligación?
```

**¿Qué busca auditor?**

- ¿El método está documentado para cada obligación?
- ¿El método es el correcto (NIIF 15)?
- ¿Hay justificación del método?

**Hallazgo si falta:**
"Obligación de servicio lineal (soporte 12 meses) reconocida 100% en mes 1. Debería ser sobre_tiempo_lineal. Ingreso sobre-estimado en mes 1."

---

### **Control 5: Evidencia de Cumplimiento Antes del Reconocimiento**

**¿Qué es?**
NO se reconoce ingreso SIN evidencia de que obligación se cumplió. La evidencia es:
- Acta de entrega (bien)
- Acta de aceptación (servicio)
- Certificado de funcionamiento (bien con instalación)
- Acta de avance (construcción por fases)

**¿Por qué importa?**
Si no hay evidencia, hay riesgo de:
- Ingreso anticipado (antes de cumplir)
- Ingreso sin cumplimiento (cliente nunca recibió)
- Actas falsificadas (ejecutor firma, no cliente)

**¿Cómo debería funcionar?**

```
Obligación se cumple (bien entregado, acta aceptado, fase completada)
       ↓
EVIDENCIA se genera: ACTA FIRMADA POR CLIENTE (no solo ejecutor)
       ↓
ANTES de reconocer ingreso, auditor REQUIERE acta en archivo
       ↓
FECHA ACTA = FECHA RECONOCIMIENTO (no es especulación)
```

**¿Qué busca auditor?**

- ¿Existe acta/certificado de cumplimiento?
- ¿Acta es firmada por CLIENTE (no ejecutor)?
- ¿Firma es auténtica (no falsificada)?
- ¿Fecha de acta ≤ fecha de asiento contable?

**Hallazgo si falta:**
"Ingreso USD XXX reconocido sin acta de aceptación. Solo hay factura interna. Riesgo de ingreso anticipado o no cumplido."

---

### **Control 6: Método de Cumplimiento vs. Registro Contable**

**¿Qué es?**
Garantizar que CÓMO se cumple la obligación = CÓMO se registra contablemente.

**¿Por qué importa?**
Si hay desalineación, hay riesgo de:
- Ingreso se registra antes de cumplimiento
- Ingreso se registra en período incorrecto
- Cambios de contrato no se reflejan en contabilidad

**¿Cómo debería funcionar?**

```
PUNTO EN TIEMPO:
  - Obligación se cumple: Cliente firma acta (15 de mayo)
  - Contabilidad registra: 15 de mayo
  
SOBRE TIEMPO LINEAL:
  - Obligación se cumple: Cada día de los 24 meses
  - Contabilidad registra: USD XXX el último día de cada mes
  
SOBRE TIEMPO POR AVANCE:
  - Obligación se cumple: 33% mes 1, 33% mes 2, 34% mes 3
  - Contabilidad registra: 33% × precio cada vez que acta aprobada
  
CAMBIO DE CONTRATO:
  - Contrato se modifica (alcance, plazo, precio)
  - Contabilidad AJUSTA reconocimientos futuros (acumula anterior)
```

**¿Qué busca auditor?**

- ¿La fecha de asiento = fecha de cumplimiento?
- ¿El monto del asiento = el correcto según obligación?
- ¿Si hubo cambios de contrato, se reflejaron en futuro?
- ¿No hay "actos" por cobrar no cumplidos?

**Hallazgo si falta:**
"Ingreso USD XXX reconocido en marzo, pero acta de cumplimiento es de junio. Ingreso anticipado 3 meses."

---

### **Control 7: Reconciliación Periódica de Ingresos**

**¿Qué es?**
Cada período (mes, trimestre), alguien compara:
- Contabilidad: ¿Cuánto ingreso reconocimos?
- Realidad: ¿Cuánto progreso realmente hay?
- Resultado: ¿Cuadran o hay diferencia?

**¿Por qué importa?**
Si no hay reconciliación, hay riesgo de:
- Ingresos no justificados acumulándose
- Servicios no prestados pero ingreso reconocido
- Cambios de contrato sin actualizar cálculos

**¿Cómo debería funcionar?**

```
CADA MES:
  1. Listar TODOS los contratos activos
  2. Para cada contrato:
     - ¿Cuál fue % progreso real? (acta de avance, acta de disponibilidad)
     - ¿Cuánto ingreso debería reconocerse?
     - ¿Cuánto reconocimos en contabilidad?
     - ¿Cuadran? Si no → INVESTIGAR
  3. Registrar diferencias y ajustes
```

**¿Qué busca auditor?**

- ¿Existe archivo de RECONCILIACIÓN MENSUAL?
- ¿Reconciliación compara: progreso real vs. ingreso contable?
- ¿Diferencias se investigan y documentan?
- ¿Hay evidencia de revisión (revisada por gerente)?

**Hallazgo si falta:**
"No existe reconciliación de ingresos vs. progreso. Riesgo de ingresos no justificados acumularse sin detección."

---

### **Control 8: Revisión de Modificaciones de Contrato**

**¿Qué es?**
Si contrato cambia (alcance, plazo, precio), hay un proceso para:
1. Documentar el cambio (RFC, orden de cambio)
2. Actualizar análisis NIIF 15 (obligaciones, precio, asignación)
3. Ajustar reconocimientos futuros (acumula lo anterior)

**¿Por qué importa?**
Si cambios no están documentados, hay riesgo de:
- Ingreso incorrecto porque especificación cambió
- Precio incorrecto sin orden de cambio
- Cliente y vendedor entienden cosas distintas
- Cambios "verbales" que ejecutor recuerda mal

**¿Cómo debería funcionar?**

```
Cliente solicita cambio (email, reunión)
       ↓
ANÁLISIS: ¿Cómo afecta a obligaciones, precio, cronograma?
       ↓
ORDEN DE CAMBIO: Se documenta el cambio, autorización, nuevo precio
       ↓
ACTUALIZACIÓN: Se actualizan:
  - Matriz de obligaciones (si cambió alcance)
  - Asignación de precio (si cambió precio)
  - Método de reconocimiento (si cambió cronograma)
  - Cálculo de futuro ingreso (acumula anterior, reconoce nuevo)
       ↓
EVIDENCIA: Cliente confirma el cambio (firma RFC)
```

**¿Qué busca auditor?**

- ¿Existe archivo de CAMBIOS/RFCs?
- ¿Cada cambio se documentó?
- ¿Se re-analizó NIIF 15 después del cambio?
- ¿Se ajustaron reconocimientos futuros?
- ¿Cliente confirmó el cambio?

**Hallazgo si falta:**
"Contrato USD 100k cambió a USD 120k; no hay orden de cambio. Nuevo precio no fue analizado NIIF 15. Ingreso podría estar incorrecto."

---

## Cómo Usar Esta Matriz de 8 Controles

### **Para Auditor Junior**
1. Por cada contrato auditado, valida que existen los 8 controles
2. Si falta uno → es potencial hallazgo
3. Usa como checklist: ¿Está documentado? ¿Funciona?

### **Para Socio Revisor**
1. Cuando revisa archivo, pregunta: "¿Se validó que el cliente tiene los 8 controles?"
2. Si cliente es repetidor, controles deberían estar en lugar
3. Si es cliente nuevo, controles pueden estar débiles (hallazgo esperado)

### **Para Cliente Previniendo**
1. Si es cliente que quiere mejorar, dile: "Implementa estos 8 controles"
2. No son costosos (es proceso, no tecnología)
3. Reducen riesgo de hallazgos NIIF 15

---

## Matriz de Riesgo → Control

| Riesgo | Control que lo Mitiga | Si Falta |
|--------|----------------------|----------|
| Contrato no autorizado | 1. Aprobación | Términos no autorizados |
| Obligaciones no separadas | 2. Identificación | Ingreso por monto/método incorrecto |
| Precio mal asignado | 3. Asignación | Ingreso sesgado a períodos iniciales |
| Método de reconocimiento incorrecto | 4. Evaluación del método | Ingresos totalmente mal timing |
| Ingreso sin cumplimiento | 5. Evidencia | Ingresos anticipados o ficticios |
| Ingreso en período incorrecto | 6. Reconciliación método-contable | Ingresos desalineados |
| Ingresos no revisados | 7. Reconciliación periódica | Ingresos fantasma sin detección |
| Cambios de contrato sin actualizar | 8. Revisión de cambios | Ingreso basado en especificación vieja |

---

## Checklist Pre-Cierre para Auditor

```
□ ¿Cliente tiene proceso de aprobación de contratos?
□ ¿Se identifican obligaciones separables (matriz)?
□ ¿Se asigna precio a cada obligación?
□ ¿Se determina método de reconocimiento (punto vs. tiempo)?
□ ¿Hay evidencia de cumplimiento antes de reconocer?
□ ¿Fecha de cumplimiento ≤ fecha de asiento?
□ ¿Hay reconciliación periódica de progreso vs. ingreso?
□ ¿Los cambios de contrato se documentan y se re-analizan?

SI TODOS ESTÁN EN LUGAR:
  → Riesgo bajo de ingreso incorrecto
  → Hallazgo solo si evidencia no cuadra

SI FALTAN 1-2:
  → Riesgo medio
  → Debes profundizar en esos contratos

SI FALTAN 3+:
  → Riesgo alto
  → Posible hallazgo material
```

