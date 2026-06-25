# Instancia: Venta Retail con Derecho de Retorno (Devoluciones Estimadas)

> **Patrón:** Cliente vende productos a consumidor o distribuidor con derecho de retorno dentro de período (30, 60, 90 días, o "no movido"). El riesgo principal es que auditor reconoce 100% del ingreso sin estimar devoluciones que ocurrirán.

> **Riesgo típico:** No estimar % de devoluciones; reconocer ingresos por monto full. Resultado: ingresos sobrestimados porque % significativo se retorna después.

---

## La Obligación (1 única, método mixto)

| Obligación | Tipo | Método | Plazo | Criterio de Cumplimiento |
|-----------|------|--------|-------|--------------------------|
| **Venta con Retorno** | venta_con_devolucion_estimada | punto_en_tiempo CON AJUSTE por variable | Día 1 (entrega) + 30-90 días (período retorno) | Entrega + período retorno vencido, O cliente confirma retención |

---

## Caso Real: Tienda de Ropa XYZ

```
VENTA REALIZADA: Enero 1, 2026
- Cantidad: 1,000 unidades de ropa
- Precio unitario: USD 50
- Precio bruto: USD 50,000
- Política de cliente: 30 días derecho de retorno

ANÁLISIS DE DEVOLUCIONES:
- Histórico de este cliente: 10% de devoluciones típicamente
- Sector retail: 8-15% típico
- Contrato especifica: "derecho de retorno 30 días"
- ESTIMACIÓN: 10% devoluciones esperadas = USD 5,000

PRECIO DE TRANSACCIÓN:
- Precio bruto: USD 50,000
- MENOS Devoluciones estimadas (10%): USD 5,000
- PRECIO DE TRANSACCIÓN = USD 45,000

RECONOCIMIENTO (punto en tiempo):
- Enero 1: Ingreso USD 45,000 (cliente tiene control de bien)
- Enero 1: Pasivo reversible USD 5,000 (devoluciones estimadas)
- Resultado: Ingreso neto USD 45,000

CIERRE DE PERÍODO (Enero 30):
- Plazo de retorno vence
- Devoluciones REALES: 85 unidades = USD 4,250
- Devoluciones estimadas: USD 5,000
- Diferencia: USD 750 (sobrestimado)
- REVERSIÓN: Reducir pasivo USD 750 → Ingreso USD 750
```

---

## Cómo Audita: Paso a Paso

### **PASO 1: Validar Contrato**

**¿Qué buscar?**
- ¿Existe política de retorno documentada?
- ¿Plazo de retorno es claro? (30, 60, 90 días)
- ¿Cliente y vendedor acuerdan el derecho de retorno?

**Checklist:**
```
□ Política de retorno existe y está escrita (no verbal)
□ Plazo: [N] días (ej. 30 días)
□ Especifica: ¿qué condiciones para retornar? (dañado, cambio de idea, etc.)
□ Cliente está de acuerdo: confirmado en email, contrato, o aceptación de términos
```

**Hallazgo si falta:**
"Venta sin política de retorno documentada. Cliente puede alegar derecho implícito."

---

### **PASO 2: Obligación (Solo 1, pero con variable)**

**¿Qué buscar?**
- La obligación es UNA: vender bien
- Pero tiene variable: devoluciones estimadas

**Checklist:**
```
□ Obligación: Vender bien (ropa, electrónica, etc.)
□ Criterio de cumplimiento: Entrega + plazo retorno vencido (O cliente confirma retención)
□ Variable: Devoluciones estimadas (% que se devuelve)
```

**Hallazgo si falta:**
"No se identificó que la venta tiene componente variable (devoluciones)."

---

### **PASO 3: Validar Precio de Transacción**

**¿Qué buscar?**
- Precio bruto: USD 50,000
- MENOS Devoluciones estimadas: USD 5,000 (10% estimado)
- Precio de transacción: USD 45,000

**Checklist:**
```
□ Precio bruto: USD [monto]

□ ANÁLISIS DE DEVOLUCIONES:
  - ¿Existe política de retorno? SÍ (del paso 1)
  - ¿Qué % se devuelve típicamente?
    □ Histórico de este cliente: [X]% (datos últimos 12 meses)
    □ Benchmarking de sector: [X]% (estudio o fuente)
    □ Especificación de contrato: [X]%
  - ¿% estimado es razonable? SÍ/NO (comparar con datos)
  
□ Devoluciones estimadas = Precio bruto × % devuelto = USD [monto]

□ Precio de transacción = Precio bruto - Devoluciones estimadas = USD [monto]

□ Análisis documentado: Email, archivo, o acta de análisis
```

**Hallazgo si falta:**
"Precio de transacción no ajustado por devoluciones. Se reconoce ingreso USD 50,000 cuando debería ser USD 45,000 (menos 10% estimado)."

---

### **PASO 4: Validar Asignación (No aplica, es obligación única)**

**Checklist:**
```
□ Obligación es única (no hay múltiples servicios)
□ Precio asignado = Precio de transacción = USD 45,000
```

---

### **PASO 5: Validar Reconocimiento**

**¿Qué buscar?**
- Ingreso se reconoce en punto_en_tiempo (cuando cliente recibe bien y tiene control)
- Pasivo reversible se crea por devoluciones estimadas

**Checklist:**
```
□ Fecha de entrega: [FECHA] (ej. enero 1)
  - Documento: Acta de entrega, shipping documento, confirmación cliente

□ Ingreso reconocido en [FECHA]: USD 45,000 (precio de transacción)
  - Validar: Asiento contable en esa fecha
  - Validar: Monto = Precio bruto MENOS devoluciones estimadas

□ Pasivo reversible (devoluciones estimadas): USD 5,000
  - Validar: Está contabilizado (cuenta clara, ej. "Pasivo por devolucionables")
  - Validar: Se revisa periódicamente

□ SEGUIMIENTO (cuando plazo de retorno vence o devoluciones ocurren):
  - Acta de cierre de período (ej. enero 30 → 30 días vencido)
  - Devoluciones REALES: [N] unidades = USD [monto]
  - Pasivo estimado vs. Pasivo real:
    □ Si estimado > real: REVERTIR exceso a ingreso
    □ Si estimado < real: AJUSTAR (puede afectar períodos anteriores)
    
  Ejemplo:
  - Pasivo estimado: USD 5,000
  - Devoluciones reales: USD 4,250
  - REVERSO: USD 750 (reconocer ingreso adicional)
```

---

## Hallazgos Típicos (TOP 5)

### **HALLAZGO 1: Ingresos sin estimar devoluciones**
```
Encontrado: Venta enero USD 50,000 reconocida 100%.
Problema: Cliente tiene 30% política retorno. Histórico: 25% se devuelve.
Impacto: Ingreso USD 12,500 sobrestimado (25% de 50k).
Corrección: Reducir ingreso enero USD 12,500, crear pasivo USD 12,500.
```

### **HALLAZGO 2: % devolución estimado incorrecto**
```
Encontrado: Se usó 5% devoluciones estimadas (USD 2,500).
Problema: Histórico de cliente de últimos 12 meses: 15% devoluciones.
Impacto: Ingreso sobrestimado en USD 5,000 (diferencia 15% - 5%).
Corrección: Actualizar a 15%, crear pasivo adicional USD 5,000.
```

### **HALLAZGO 3: Pasivo reversible no fue creado**
```
Encontrado: Ingreso reconocido USD 50,000; no hay pasivo por devoluciones.
Problema: 10% devoluciones estimadas (USD 5,000) no se contabilizó.
Impacto: Ingreso no está neteado; Balance sheet no refleja obligación.
Corrección: Crear pasivo USD 5,000 (cuenta: "Pasivo por devolucionables").
```

### **HALLAZGO 4: Pasivo no se reversa cuando devoluciones no ocurren**
```
Encontrado: Enero pasivo USD 5,000 creado. Febrero (30 días vencido): cliente no devolvió.
Problema: Pasivo se deja igual; no se reversa.
Impacto: Pasivo artificial reduce ingresos de febrero.
Corrección: Revertir pasivo USD 5,000; reconocer ingreso adicional febrero.
```

### **HALLAZGO 5: Devoluciones reales materialmente distintas de estimadas**
```
Encontrado: Estimado 10% (USD 5,000). Real hasta cierre: 25% (USD 12,500).
Problema: Estimación fue significativamente baja.
Impacto: Ingreso de enero necesita ajuste (reducir USD 7,500 adicionales).
Corrección: Ajustar a real; investigar por qué % fue tan distinto.
```

---

## Matriz de Pruebas

| Qué Validar | Cómo | Qué Buscar | Hallazgo Si Falta |
|------------|------|-----------|-------------------|
| **Política retorno** | Leer política escrita | Plazo (30, 60, 90 días) claro | "Política de retorno no documentada" |
| **Análisis devoluciones** | Revisar archivo | % histórico vs. % estimado vs. sector | "% devoluciones no estimado" |
| **Precio transacción** | Validar cálculo | Precio bruto - % devoluciones = ingreso | "Ingreso reconocido 100% sin deducir devoluciones" |
| **Pasivo reversible** | Revisar contabilidad | Cuenta "Pasivo devolucionables" USD X | "Pasivo reversible no fue creado" |
| **Fecha reconocimiento** | Comparar acta vs. asiento | Entrega = Reconocimiento | "Ingreso anticipado (antes de entrega)" |
| **Seguimiento devoluciones** | Auditar períodos siguientes | ¿Se registran devoluciones reales? | "Devoluciones ocurren pero no se registran" |
| **Reverso de pasivo** | Validar cierre | Pasivo estimado vs. real → ajuste | "Pasivo no se revisa ni ajusta" |

---

## Preguntas de Cierre para Socio Revisor

- ¿Cliente tiene política de retorno documentada?
- ¿Se estimó % de devoluciones? ¿Base (histórico, sector)?
- ¿Ingreso = Precio bruto - Devoluciones estimadas?
- ¿Pasivo reversible fue creado?
- ¿Se valida periódicamente que devoluciones reales se alinean con estimadas?
- ¿Si % real fue material vs. estimado, se ajustó?

---

## Diferencia: Distribuidor vs. Venta Consignación

### **Distribuidor (Retorno Típico)**
```
Vendedor → Distribuidor → Consumidor
Contrato: Distribuidor puede retornar "no movido"
Política: 30-90 días
Estimación: Basada en historia de este distribuidor
```

### **Venta Consignación (Retorno Asegurado)**
```
Vendedor → Tienda (en consignación) → Consumidor
Contrato: Tienda paga SOLO lo que vende
Política: TODO lo que no se vende se devuelve
Estimación: 100% menos lo que se espera vender (inverso)
```

**Para auditar consignación:**
- Ingreso = Unidades vendidas × Precio (no bruto)
- Todo lo que está en tienda: Activo (inventory), no ingreso
- Cuando cliente compra: Ingreso
- Cuando retorna: Se reversa

