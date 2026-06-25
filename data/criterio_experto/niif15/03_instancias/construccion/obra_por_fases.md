# Instancia: Construcción por Fases (con Retención)

> **Patrón:** Contrato de obra civil dividida en 5-7 fases (cimientos, estructura, acabados, servicios, cierre). Cada fase tiene supervisor que certifica avance. Cliente retiene 5-10% hasta cierre total.

> **Riesgo típico:** (1) % avance estimado sin certificado de supervisor; (2) ingreso reconocido sin retención descontada; (3) cliente rechaza fase pero ingreso ya reconocido.

---

## La Obligación (Única vs. Múltiples - DEPENDE del contrato)

### **Caso A: Obligación ÚNICA (constructor debe hacer todas las fases)**
```
Si cliente puede rechazar fase 1 pero constructor SIGUE comprometido a hacer fase 2-5
→ Obligación única: "Construir edificio completo"
→ Método: sobre_tiempo_por_avance
→ Reconocimiento: % avance total × precio total

Ejemplo:
- Edificio completo (5 fases) = USD 1,000,000
- Fase 1 (cimientos) 15% → Ingreso USD 150,000
- Fase 2 (estructura) 25% → Ingreso USD 250,000
- [etc.]
```

### **Caso B: Obligaciones SEPARABLES (cliente puede aceptar/rechazar cada fase)**
```
Si contrato permite cliente aceptar fase 1 Y rechazar fases 2-5 SIN penalidad
→ 5 obligaciones separables (cada fase es obligación)
→ Método: punto_en_tiempo (cuando fase se acepta)
→ Reconocimiento: Cuando cliente acepta cada fase

Ejemplo:
- Fase 1 (cimientos): USD 150,000 → punto_en_tiempo cuando aceptada
- Fase 2 (estructura): USD 250,000 → punto_en_tiempo cuando aceptada
- [etc.]
```

**PARA AUDITORÍA: Revisar contrato cláusula de terminación. ¿Puede cliente cancelar sin terminar obra?**

---

## Caso Real: Construcción de Edificio Residencial

```
CONTRATO FIRMADO: enero 2026
- Obra: Edificio residencial 5 pisos, 20 departamentos
- Precio total: USD 1,000,000
- Plazo: 18 meses (enero 2026 - junio 2027)
- Retención cliente: 10% hasta cierre

FASES:
1. Cimientos + Movimiento de Tierra: USD 150,000 (15%)
2. Estructura (acero/concreto): USD 250,000 (25%)
3. Acabados (pisos, paredes, puertas): USD 350,000 (35%)
4. Servicios (electricidad, agua, gas): USD 150,000 (15%)
5. Cierre y entrega: USD 100,000 (10%)

RETENCIÓN:
- Cliente retiene 10% de cada fase hasta cierre total
- Retención fase 1: USD 15,000
- Retención fase 2: USD 25,000
- [etc.]
- Retención total acumulada: USD 100,000

RECONOCIMIENTO (suponiendo obligación ÚNICA):

ENERO 2026:
- Fase 1: 100% completada (cimientos)
- Certificado supervisor: "100% cumplido"
- Ingreso bruto: USD 150,000
- MENOS Retención (10%): USD 15,000
- INGRESO NETO: USD 135,000

MARZO 2026:
- Fase 2: 100% completada (estructura)
- Certificado supervisor: "100% cumplido"
- Ingreso bruto: USD 250,000
- MENOS Retención (10%): USD 25,000
- INGRESO NETO: USD 225,000

[Fases 3, 4 similares...]

JUNIO 2027:
- Cierre de obra (fase 5 + inspección final)
- Certificado final: "Obra completa y conforme"
- Retención acumulada liberada: USD 100,000
- INGRESO: USD 100,000

TOTAL INGRESO:
- Fase 1: USD 135,000
- Fase 2: USD 225,000
- Fase 3: USD 315,000
- Fase 4: USD 135,000
- Fase 5 + Retención liberada: USD 190,000
- TOTAL: USD 1,000,000 ✓
```

---

## Cómo Audita: Paso a Paso

### **PASO 1: Validar Contrato**

**¿Qué buscar?**
- ¿Contrato especifica fases claramente?
- ¿Cada fase tiene descripción, presupuesto, plazo?
- ¿Hay especificación técnica (planos, normas)?
- ¿Retención de cliente está documentada? (% y cuándo se libera)

**Checklist:**
```
□ Contrato principal + anexo técnico
□ Número de fases: [N] (ej. 5 fases)
□ Cada fase tiene:
  □ Descripción (qué se construye)
  □ Presupuesto (USD X)
  □ Plazo estimado (mes X)
  □ Criterio de aceptación (acta de supervisor)

□ Retención documentada:
  □ % retención: [X]% (ej. 10%)
  □ Se aplica a cada fase: SÍ/NO
  □ Cuándo se libera: Al cierre de obra / Inspección final / [Fecha]

□ Supervisión:
  □ ¿Quién es el supervisor? (nombre, autoridad)
  □ ¿Supervisor actúa por cliente o por constructor?
```

**Hallazgo si falta:**
"Contrato sin especificar fases claramente. No hay descripción técnica ni plazo de cada fase."

---

### **PASO 2: Validar Obligaciones**

**¿Qué buscar?**
- ¿Es obligación ÚNICA o MÚLTIPLES (por fase)?
- ¿Contrato permite cliente rechazar fase sin rechazar obra total?

**Checklist:**
```
□ Si cliente PUEDE rechazar una fase sin impedir las demás:
  → 5 obligaciones separables (cada fase es 1)
  → Método: punto_en_tiempo (cuando fase aceptada)

□ Si cliente NO PUEDE rechazar (debe hacer todas o ninguna):
  → 1 obligación única: "Construir edificio completo"
  → Método: sobre_tiempo_por_avance

□ Determinación está documentada (email con cliente, acta de requerimientos)
```

**Hallazgo si falta:**
"No está claro si cada fase es obligación separable o si es 1 obligación única."

---

### **PASO 3: Validar Precio de Transacción**

**¿Qué buscar?**
- Precio total: USD 1,000,000
- Retención: 10% = USD 100,000
- Precio de transacción: USD 900,000 (neto de retención)

**Checklist:**
```
□ Precio total del contrato: USD [monto]

□ Retención:
  □ % retención: [X]%
  □ Retención total: Precio total × % = USD [monto]
  
□ Precio de transacción = Precio total - Retención = USD [monto]

□ Análisis está documentado (contrato, acta de precios)
```

**Hallazgo si falta:**
"Precio reconocido USD 1,000,000. Retención 10% (USD 100,000) NO fue descontada del ingreso."

---

### **PASO 4: Validar Asignación (Fases)**

**¿Qué buscar?**
- Si es obligación ÚNICA: Asignación es por fases (cada fase recibe % de precio)
- Si son obligaciones MÚLTIPLES: Asignación es por fase (cada obligación tiene precio)

**Checklist:**
```
□ Fase 1: USD 150,000 (15% de 1,000,000)
  □ Base: Presupuesto de contrato, planos, análisis de costo

□ Fase 2: USD 250,000 (25% de 1,000,000)
  [etc.]

□ Suma total: 15% + 25% + 35% + 15% + 10% = 100% ✓

□ Matriz de asignación por fase está documentada
```

**Hallazgo si falta:**
"Asignación de precio por fases no documentada. Fases no tienen presupuesto claro."

---

### **PASO 5: Validar Reconocimiento (Por Fase)**

**¿Qué buscar?**

#### **POR CADA FASE:**

```
□ CERTIFICADO DE SUPERVISOR:
  - Documento oficial: Acta de supervisión / Certificado de avance
  - Fecha: [FECHA] (ej. enero 31)
  - % cumplimiento: [X]% (ej. 100% para fase 1)
  - Firma: Supervisor (no constructor)
  - Especificación: "Cimientos completados conforme planos"

□ ACEPTACIÓN DE CLIENTE:
  - ¿Cliente firmó aceptación de fase? SÍ/NO
  - O ¿Cliente pagó la factura (implica aceptación)?
  - Fecha aceptación: [FECHA]

□ INGRESO CALCULADO:
  - Ingreso bruto: Precio de fase × % cumplido
  - MENOS Retención (10%): Ingreso bruto × 10%
  - INGRESO NETO: Para reconocer
  
  Ejemplo:
  - Fase 1 precio: USD 150,000
  - % cumplido: 100%
  - Ingreso bruto: USD 150,000
  - Retención: USD 15,000
  - Ingreso neto a reconocer: USD 135,000

□ ASIENTO CONTABLE:
  - Fecha: FECHA ACEPTACIÓN (no antes)
  - Monto: Ingreso neto USD [monto]
  - Descripción: "Ingreso fase X - Certificado supervisor"
  - Pasivo retención: "Retención cliente fase X" USD [monto]

□ VALIDACIÓN: ACTA ANTES DE ASIENTO ✓
```

#### **SI CLIENTE RECHAZA FASE:**

```
□ Acta de rechazo: ¿Existe documento?
□ Razón: No conforme, defectos, incumplimiento, etc.
□ Impacto:
  - ¿Se revirtió ingreso ya reconocido? (si aplica)
  - ¿Se corrigió la obra?
  - ¿Se re-auditó cuando se corrigió?
```

#### **AL CIERRE (Cuando se libera retención):**

```
□ Acta de cierre de obra:
  - Inspección final: Toda obra conforme
  - Constructor y cliente firman acta de entrega
  - Fecha: [FECHA] (ej. junio 30)

□ Retención liberada: USD 100,000
  - Ingreso final: USD 100,000 (por liberación de retención)
  - Asiento: Reversión de pasivo "Retención" → Ingreso

□ VALIDAR: Retención se reconoce en fecha de cierre, no antes
```

---

## Hallazgos Típicos (TOP 5)

### **HALLAZGO 1: % avance sin certificado de supervisor**
```
Encontrado: Fase 2 (estructura 100% cumplida) reconocida USD 225,000.
Problema: No existe acta de supervisor que certifique 100%.
Impacto: Ingreso es estimación de constructor, no evidencia independiente.
Corrección: Solicitar certificado de supervisor O revertir ingreso.
```

### **HALLAZGO 2: Ingreso reconocido sin descontar retención**
```
Encontrado: Fase 1 ingreso reconocido USD 150,000.
Problema: Retención 10% (USD 15,000) NO fue descontada.
Impacto: Ingreso sobrestimado; pasivo de retención no se creó.
Corrección: Reducir ingreso USD 15,000, crear pasivo USD 15,000.
```

### **HALLAZGO 3: Fase rechazada pero ingreso no se revirtió**
```
Encontrado: Fase 2 (estructura) ingreso USD 225,000 reconocido en marzo.
Problema: En junio cliente rechazó fase 2 (defectos). Ingreso no se revirtió.
Impacto: Ingreso ficticio por USD 225,000 (+ retención USD 22,500).
Corrección: Revertir ingreso y pasivo, re-auditar cuando fase se corrija.
```

### **HALLAZGO 4: Retención no se libera hasta cierre**
```
Encontrado: Obra cerrada julio. Retención acumulada USD 100,000 nunca se reconoció.
Problema: Acta de cierre no genera ingreso de retención liberada.
Impacto: Ingreso faltante USD 100,000 en cierre.
Corrección: Reconocer USD 100,000 cuando acta de cierre se firma.
```

### **HALLAZGO 5: Avance real vs. certificado no cuadra**
```
Encontrado: Certificado supervisor fase 3: 80% cumplido.
Problema: Cliente reclama solo 40% visible (obra atrasada, trabajo incompleto).
Impacto: Ingreso podría ser incorrecto; riesgo de futuro rechazo.
Corrección: Validar independientemente % real, ajustar si es material.
```

---

## Matriz de Pruebas

| Qué Validar | Cómo | Qué Buscar | Hallazgo Si Falta |
|------------|------|-----------|-------------------|
| **Fases especificadas** | Leer anexo técnico | 5-7 fases con descripción, presupuesto, plazo | "Fases no están especificadas" |
| **Supervisor designado** | Revisar contrato | Nombre, autoridad, independencia del supervisor | "No hay supervisor designado o no es independiente" |
| **Certificado por fase** | Pedir actas de supervisión | Acta 1, Acta 2, [etc.] con fecha y % | "Fase reconocida sin certificado" |
| **Aceptación cliente** | Email, firma en acta, pago | Cliente confirma conformidad de fase | "Fase reconocida sin aceptación cliente" |
| **Retención documentada** | Revisar contrato | % retención (ej. 10%) y cuándo se libera | "Retención no está documentada" |
| **Ingreso neto calculado** | Validar asiento | Ingreso = (Fase precio × % cumplido) - Retención | "Ingreso no descontó retención" |
| **Fecha cumplimiento** | Comparar acta vs. asiento | Acta ≤ Asiento (no anticipado) | "Ingreso anticipado (antes de certificado)" |
| **Retención liberada** | Revisar acta de cierre | Acta cierre + ingreso retención liberada | "Retención nunca se liberó" |

---

## Preguntas de Cierre para Socio Revisor

- ¿Cada fase tiene acta de supervisor independiente?
- ¿% avance está certificado (no estimado)?
- ¿Retención se descontó del ingreso (no se reconoce 100%)?
- ¿Si cliente rechazó fase, se revirtió ingreso?
- ¿Al cierre, se reconoció ingreso por retención liberada?
- ¿Hay evidencia de que obra se entregó completamente?

---

## Diferencia: Obligación Única vs. Múltiples

```
OBLIGACIÓN ÚNICA (más común):
- Constructor se compromete a edificio COMPLETO
- Si cliente rechaza fase 2, constructor sigue obligado a fases 3-5
- Método: sobre_tiempo_por_avance (% avance total)
- Hallazgo típico: % avance estimado sin supervisor

OBLIGACIONES MÚLTIPLES (menos común):
- Cliente puede rechazar cada fase sin impedir otras
- Contrato permite terminar después de fase 2
- Método: punto_en_tiempo (cuando cada fase se acepta)
- Hallazgo típico: Cliente rechaza fase pero ingreso no se revierte
```

**Para auditar: Leer cláusula de terminación. ¿Qué pasa si cliente cancela a mitad?**

