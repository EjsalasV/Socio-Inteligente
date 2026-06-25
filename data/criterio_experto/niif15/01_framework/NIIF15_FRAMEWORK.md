# NIIF 15 - Framework Ejecutable de Ingresos

> **Estado:** Framework universal de auditoría de ingresos bajo NIIF 15. Aplica a todos los sectores. Usar combinado con instancias sectoriales y matriz riesgo-hallazgo.

---

## Propósito de este Framework

NIIF 15 es abstracto. Un auditor lee la norma y sigue sin saber qué hacer.

**Este framework es un CHECKLIST EJECUTABLE:** te guía paso a paso por los 5 pasos de NIIF 15 y te anticipa qué buscar, qué validar, dónde hallan hallazgos típicos.

No reemplaza la norma. La hace usable.

---

## Los 5 Pasos de NIIF 15 en Auditoría

### **PASO 1: Identificar el Contrato**

**¿Qué es un contrato para NIIF 15?**
Un acuerdo (escrito, verbal, implícito por costumbre) donde:
- Partes están identificadas
- Derechos y obligaciones son claros
- Hay probabilidad de cobro
- Consideración (precio) se ha acordado

**¿QUÉ AUDITA?**

1. **¿Existe contrato documentado?**
   - Escrito: órdenes de compra, contratos formales, acuerdos email
   - Implícito: costumbre comercial (ej. retail: cliente entra a tienda = contrato)
   - Verbal: debe quedar evidencia posterior (ej. acta de aceptación, factura)

2. **¿Las partes son identificables?**
   - Cliente final (no distribuidor que revende)
   - Datos básicos del cliente en contrato o registro

3. **¿Hay probabilidad de cobro?**
   - Cliente solvente, sin disputas previas
   - Plazo de pago claro
   - Garantía o pago anticipado, si aplica

4. **¿El precio es determinable?**
   - Fijo, variable pero identificable, o puede estimarse razonablemente
   - No "se verá después" sin base de cálculo

**MICRO-EJEMPLO:**
```
✗ HALLAZO: Factura por USD 50k sin contrato, sin acta de servicios
  Riesgo: cliente puede disputar si cumplimiento no está claro

✓ CORRECTO: Contrato firmado + orden de compra + acta de aceptación
  = Contrato identificable
```

**→ SI FALLA:** Ingreso anticipado, cliente no identificado, o precio incierto.

---

### **PASO 2: Identificar Obligaciones de Desempeño**

**¿Qué es una obligación de desempeño?**
Un COMPROMISO separable que hace que el cliente reciba un bien/servicio DISTINTO.

No todas las líneas de un contrato son obligaciones separadas. Pueden ser:
- **1 obligación:** venta de producto (todo junto)
- **2 obligaciones:** producto + instalación
- **3 obligaciones:** desarrollo + soporte + licencia
- **5+ obligaciones:** obra por fases

**¿QUÉ AUDITA?**

1. **¿Cuántas obligaciones hay?**
   - ¿Cliente recibe bienes/servicios distintos?
   - ¿Están separables en términos económicos?
   - ¿Podría existir una sin la otra?

2. **¿Están todas documentadas?**
   - Matriz contrato → obligaciones
   - Especificación de cada una (alcance, plazo, entregables)
   - Criterio de cumplimiento (acta, certificado, factura periódica)

3. **¿El cliente está de acuerdo?**
   - Acta de análisis de requerimientos
   - Email de aprobación de especificaciones
   - Contrato/anexo que detalla cada obligación

**MICRO-EJEMPLO:**
```
CONTRATO: "Venta de máquina + instalación + garantía de 2 años"

✗ HALLAZO: Cliente reconoce ingresos por todo en un único asiento
  = Las 3 obligaciones NO están separadas

✓ CORRECTO: 
  - Obligación 1: Máquina (bien tangible)
  - Obligación 2: Instalación (servicio en fecha específica)
  - Obligación 3: Garantía (servicio durante 24 meses)
  = 3 obligaciones, cada una separada
```

**→ SI FALLA:** Mezcla obligaciones distintas, o confunde gastos con obligaciones.

---

### **PASO 3: Determinar el Precio de Transacción**

**¿Qué es precio de transacción?**
La **suma que esperas cobrar realmente** (no es lista de precios teórica).

Incluye:
- Monto fijo en contrato
- Descuentos acordados o estimados
- Bonificaciones por cumplimiento
- Retenciones o garantías

NO incluye:
- IVA (impuesto, no es parte del ingreso)
- Estimaciones que son especulación (si no hay base)

**¿QUÉ AUDITA?**

1. **¿El precio está claramente establecido?**
   - Contrato fijo: verificar moneda y monto
   - Precio variable: ¿hay fórmula clara? ¿índices verificables?
   - Hito-based: ¿matriz de costos × hito?

2. **¿Se descontó lo que NO vas a cobrar?**
   - Descuento 10% por pagos al contado
   - Bonificación 5% si cumple antes de fecha
   - Retención de cliente (5-10% hasta cierre)
   - Devolucionable (cliente puede retornar, estima % que retorna)

3. **¿El precio está actualizado?**
   - ¿Cambios de especificación actualizaron el contrato?
   - ¿Cambios de moneda (si hay)? ¿dónde se registran?
   - ¿Modificaciones de plazo afectaron el precio?

**MICRO-EJEMPLO:**
```
CONTRATO: "Desarrollo por USD 100k"
Cliente estimó:
  - Monto fijo: USD 100k
  - Descuento por pago anticipado: -USD 10k
  - PRECIO DE TRANSACCIÓN: USD 90k

✗ HALLAZO: Ingreso reconocido por USD 100k
  = No descontó anticipado

✓ CORRECTO: Reconocer USD 90k (lo que realmente cobrará)
  + USD 10k pasivo (anticipado no devengado aún)
```

**→ SI FALLA:** Ingreso por montos incorrectos, descuentos no restados, devoluciones no estimadas.

---

### **PASO 4: Asignar Precio a Cada Obligación**

**¿Qué es asignación de precio?**
Repartir el PRECIO TOTAL entre cada obligación, según su VALOR RELATIVO.

**Métodos:**
1. **Precio independiente observable:** Si la obligación se vende separadamente, usa ese precio
2. **Precio independiente estimado:** Si no se vende sola, estima (encuesta, análisis de mercado)
3. **Método de margen esperado:** Costo esperado + margen

**¿QUÉ AUDITA?**

1. **¿Existe matriz de asignación?**
   - Obligación 1: USD 40k (40%)
   - Obligación 2: USD 30k (30%)
   - Obligación 3: USD 30k (30%)
   - TOTAL: USD 100k (100%)

2. **¿La asignación tiene base?**
   - ¿Precios observables de mercado?
   - ¿Estimaciones documentadas (análisis, benchmarking)?
   - ¿Justificación del % asignado?

3. **¿La suma cuadra?**
   - Suma de obligaciones = Precio de transacción
   - Si hay cambios de especificación, ¿actualizaron la matriz?

**MICRO-EJEMPLO:**
```
CONTRATO: Equipo USD 35k + Instalación USD 8k + Mantenimiento (24 meses) = ?

Precio total observado en mercado: USD 50k
(porque paquete "llave en mano" cuesta eso)

✓ CORRECTO ASIGNACIÓN:
  - Equipo: USD 28k (56% de USD 50k, porque equipo solo cuesta USD 35k en mercado)
  - Instalación: USD 10k (20%, porque es servicio especializado)
  - Mantenimiento: USD 12k (24%, porque garantía de 24 meses cuesta USD 6k/año)

✗ HALLAZO: Asignó todo al equipo (USD 50k) sin separar obligaciones
  = Ingreso concentrado en punto_en_tiempo, no reconoce mantenimiento lineal
```

**→ SI FALLA:** Asignaciones arbitrarias, sin base documentada, o que no cuadran.

---

### **PASO 5: Reconocer Ingreso Cuando Se Cumpla Obligación**

**¿Cuándo se cumple una obligación?**

**OPCIÓN A: PUNTO EN TIEMPO** (momento específico)
- Cliente recibe bien y tiene control (entrega física)
- Cliente recibe acceso y tiene control (software activado)
- Cliente acepta cumplimiento (acta de aceptación)

**OPCIÓN B: SOBRE TIEMPO** (durante período)
- Servicio lineal: 1 mes contrato = reconoce 1/12 ingresos cada mes
- Servicio por avance: % cumplido = % de ingreso (construcción, desarrollo por hitos)
- Garantía: obligación lineal durante vigencia

**¿QUÉ AUDITA?**

1. **¿Cuál es el método correcto?**
   - Bien tangible → punto_en_tiempo (cuando cliente tiene control)
   - Servicio por período → sobre_tiempo lineal
   - Desarrollo por hitos → sobre_tiempo por avance
   - Garantía/mantenimiento → sobre_tiempo lineal

2. **¿Hay evidencia de cumplimiento?**
   - Punto en tiempo: acta de entrega, acta de aceptación, certificado
   - Sobre tiempo: contrato vigente, acta periódica de avance, factura de período
   - Garantía: contrato de mantenimiento, recibos de servicio

3. **¿Cuándo registró?**
   - ¿Fecha de cumplimiento = fecha del asiento contable?
   - ¿No anticipó antes de cumplir?
   - ¿No retrasó después de cumplir?

**MICRO-EJEMPLO:**
```
CONTRATO: Desarrollo de software USD 100k en 3 fases (cada mes)

✓ CORRECTO:
  - Mes 1: Cumple fase 1 → Acta de avance 33% → Ingreso USD 33k
  - Mes 2: Cumple fase 2 → Acta de avance 66% → Ingreso USD 33k
  - Mes 3: Cumple fase 3 → Acta de cierre 100% → Ingreso USD 34k

✗ HALLAZO: Reconoció todo en el mes 1 (USD 100k)
  = Reconoció sin evidencia de cumplimiento en fases posteriores
  = Hallazgo: "Ingreso anticipado sin evidencia de fase 2 y 3"
```

**→ SI FALLA:** Ingresos anticipados (antes de cumplir), ingresos retrasados (después de cumplir), o método incorrecto.

---

## Resumen: Preguntas de Cierre por Paso

| Paso | Pregunta Clave |
|------|---|
| **1. Identificar contrato** | ¿Existe contrato documentado, con cliente y precio claro? |
| **2. Obligaciones** | ¿Cuántas obligaciones separables hay? ¿Están documentadas? |
| **3. Precio** | ¿Cuál es el monto que realmente cobrará (con descuentos, retenciones)? |
| **4. Asignación** | ¿Cómo distribuyó el precio entre obligaciones? ¿Tiene base? |
| **5. Reconocimiento** | ¿Cuándo cumple? ¿Tiene evidencia? ¿Cuándo registra? |

---

## Cómo Usar Este Framework

### **Para Auditor Junior**
1. Lee los 5 pasos (arriba)
2. Revisa el checklist de preguntas
3. Ve a la **instancia específica** de tu cliente (Ej. "servicios/plurianuales.md")
4. Usa el checklist en la instancia
5. Compara contra la **matriz riesgo→hallazgo** para anticipar problemas

### **Para Socio Revisor**
1. Valida que el junior cubrió los 5 pasos
2. Revisa que la **matriz riesgo→hallazgo** fue aplicada
3. Confirma que la **evidencia de cumplimiento** está documentada
4. Pregunta: "Si cliente disputa, ¿tu conclusión aguanta?"

### **Para Firmas Pequeñas sin Especialista NIIF 15**
1. Usa este framework + instancia relevante = checklist ejecutable
2. No necesitas 300 páginas de norma
3. Necesitas saber: ¿cuántas obligaciones? ¿cuándo se cumplen?

---

## Próximos Pasos

- **Taxonomía:** Ver tipos_obligacion.yml, metodos_reconocimiento.yml, tipos_evidencia.yml
- **Instancias:** Elige tu sector (servicios, retail, bienes, construcción)
- **Controles:** Cubre los 8 controles universales de ingresos
- **Hallazgos:** Usa matriz_riesgo_hallazgo_ejecutable.yml

---

## Preguntas Frecuentes

**P: ¿Qué pasa si no hay contrato escrito?**
A: NIIF 15 acepta contratos implícitos (costumbre comercial). Pero AUDITORÍA exige evidencia: acta de aceptación, factura, confirmación cliente. Si no hay nada, es **hallazgo de presentación** (no se evidencia claramente en estados).

**P: ¿Puedo reconocer ingreso si aún no cobré?**
A: Sí. NIIF 15 es por cumplimiento, no por cobro. Pero valida que el cliente es solvente y tienes esperanza razonable de cobro. Si no, es **riesgo crediticio**, no ingreso.

**P: ¿Qué pasa con devoluciones estimadas?**
A: El PRECIO DE TRANSACCIÓN debe incluir devoluciones estimadas. Si estimas 10% de devolución, reduces el ingreso 10% hoy y creas una pasivo por devoluciones. Ves matriz_riesgo_hallazgo para hallazgo típico.

**P: ¿Constructor con obra por fases es obligaciones separadas?**
A: DEPENDE del contrato. Si cliente puede rechazar una fase y el constructor debe hacer otras fases = 1 obligación (construir todo). Si cada fase es separable = múltiples obligaciones. Revisa construccion/obra_por_fases.md.

