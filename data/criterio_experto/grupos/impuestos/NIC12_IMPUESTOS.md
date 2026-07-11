# Grupo: Impuestos — Corriente, Diferido y Conciliación Tributaria (NIC 12 + Ecuador)

> **Estado:** borrador IA — pendiente validación por socio revisor. Marco: NIC 12, LRTI Ecuador, normativa SRI vigente al cierre.
> **Vínculos activos:** TODOS los grupos (la conciliación tributaria es transversal), nómina (15%), inventarios (obsolescencia), patrimonio (dividendos).
> **Complementa:** por_area/145_impuestos_activos.md (criterio existente de saldos a favor y crédito tributario).

---

## 1. La estructura del área (tres capas que se auditan distinto)

| Capa | Qué es | Cómo se audita |
|------|--------|----------------|
| **Impuesto corriente** | Lo que se paga al SRI por el año | Recálculo desde la conciliación tributaria |
| **Impuesto diferido** | Efecto futuro de diferencias contables-fiscales | Inventario de diferencias temporarias × tasa |
| **Cumplimiento formal** | Declaraciones, anexos, retenciones | Cruce contabilidad vs. declarado (104, 103, ATS, 101) |

**La lógica de socio:** el impuesto no se audita "revisando la cuenta de impuestos". Se audita **reconstruyendo la conciliación tributaria** — porque cada partida conciliatoria nace en OTRA área del balance. Por eso este grupo es el más vinculado de todos: es el punto donde todos los hallazgos del resto de áreas convergen.

**El orden del cálculo (sagrado, y donde más se equivocan):**
```
Utilidad contable antes de participación e impuestos
  − 15% participación trabajadores
  = Base contable
  + Gastos no deducibles
  − Ingresos exentos
  ± Otras partidas conciliatorias (amortización pérdidas, deducciones adicionales)
  = Base imponible
  × Tarifa IR vigente
  = Impuesto causado
```

---

## 2. Riesgos recurrentes

1. **Conciliación tributaria "de fórmula":** el cliente copia la del año pasado y ajusta números. No deducibles reales (multas, gastos personales, sin sustento, provisiones) no están sumados → impuesto subdeclarado → contingencia SRI con multas e intereses.
2. **Impuesto diferido ignorado o inventado:** firmas pequeñas suelen: (a) no reconocer ninguno, o (b) reconocer un activo diferido por pérdidas fiscales que nunca podrán usar. Ambos son hallazgos. El activo diferido exige **utilidades fiscales futuras probables** — con negocio en pérdidas recurrentes, no se sostiene.
3. **Contabilidad ≠ declaraciones:** ingresos del 104 vs. ingresos contables; compras del ATS vs. gasto contable; retenciones del 103 vs. gasto de nómina/honorarios. Diferencias sin conciliar = la primera fuente de glosas del SRI.
4. **Anticipo y crédito tributario mal arrastrados:** saldos a favor que vienen de años anteriores sin soporte, o que ya prescribieron (ver criterio 145).
5. **Contingencias tributarias no evaluadas:** glosas en firme, procesos de determinación en curso, años abiertos a fiscalización. ¿Provisión (probable) o revelación (posible)? Muchas veces: ninguna de las dos.
6. **Gasto de impuesto del año descuadrado:** gasto por impuesto = corriente + variación del diferido. Cuando el cliente "cuadra" el gasto contra lo pagado, el diferido queda huérfano.

## 3. Enfoque recomendado (pruebas concretas)

1. **Reconstruir la conciliación tributaria desde los hallazgos de las otras áreas** (no desde la del cliente): tomar los no deducibles detectados en gastos, nómina, inventarios → ¿están todos sumados? Después comparar contra la conciliación del cliente y explicar cada diferencia.
2. **Recalcular la secuencia completa:** utilidad → 15% → base → impuesto causado → menos retenciones y anticipo → impuesto por pagar/saldo a favor. Cuadrar contra formulario 101 y contra la provisión contable.
3. **Inventario de diferencias temporarias:** tabla con cada diferencia (obsolescencia, jubilación, deterioro CxC, depreciación acelerada, pérdidas amortizables), su saldo, su tasa y el diferido resultante. Comparar con lo registrado.
4. **Cruce declaraciones vs. contabilidad (12 meses):** ingresos 104 vs. mayor de ingresos; compras ATS vs. compras contables; retenciones 103 vs. gastos sujetos. Documentar y explicar cada brecha.
5. **Prueba del activo diferido por pérdidas:** proyección de utilidades fiscales del cliente con supuestos defendibles. Sin proyección razonable → el activo se castiga.
6. **Carta de abogados/asesor tributario + estado de procesos SRI:** años abiertos, glosas, recursos. Evaluar NIC 37 para cada uno.

## 4. Errores comunes del auditor

- Auditar impuestos al final y aislado, cuando la conciliación depende de hallazgos de TODAS las demás áreas (hacerlo al final está bien; hacerlo aislado, no).
- Aceptar la conciliación del cliente como punto de partida en lugar de reconstruirla.
- Revisar el diferido "por movimiento" en lugar de por inventario de diferencias (el saldo debe poder demostrarse desde cero cada año).
- Olvidar que el 15% de participación va ANTES: un ajuste de auditoría a la utilidad cambia participación E impuesto en cascada.
- No revisar hechos posteriores tributarios: la declaración presentada en abril del año siguiente es evidencia directa de la provisión al cierre.

---

## 5. Matriz Riesgo → Prueba → Hallazgo

| Riesgo | Prueba | Hallazgo si falla (plantilla) |
|--------|--------|-------------------------------|
| No deducibles omitidos | Reconstrucción de conciliación | "Gastos no deducibles por USD X no incluidos en conciliación; impuesto subdeclarado USD Y + multas e intereses" |
| Diferido inexistente | Inventario de diferencias | "Diferencias temporarias por USD X sin impuesto diferido reconocido (detalle por partida)" |
| Diferido no recuperable | Proyección utilidades fiscales | "Activo diferido USD X por pérdidas sin evidencia de utilidades futuras probables; requiere castigo" |
| Contabilidad ≠ declarado | Cruce 104/103/ATS vs. mayores | "Diferencia de USD X entre ingresos declarados y contables sin conciliación; riesgo de determinación SRI" |
| Contingencias | Carta abogados + procesos SRI | "Glosa/proceso por USD X calificado como probable sin provisión (o posible sin revelación)" |
| Cascada 15%→IR | Recálculo secuencial | "Ajustes de auditoría por USD X no recalcularon participación e impuesto; efecto neto USD Y" |

---

## 6. Vínculos (chequeos de coherencia con otros grupos)

### → TODOS (regla transversal, activa)
Cada hallazgo de otra área tiene un **eco tributario** que debe verificarse:

| Hallazgo en otra área | Eco en impuestos |
|----------------------|------------------|
| Gasto personal del accionista (gastos) | No deducible + posible dividendo presunto |
| Provisión obsolescencia (inventarios) | No deducible → diferencia temporaria → diferido activo |
| Pagos fuera de IESS (nómina) | Gasto no deducible |
| Deterioro de CxC sobre límite legal (cxc) | Exceso no deducible → temporaria |
| Jubilación patronal <10 años (nómina) | No deducible → temporaria |
| Ajuste a ingresos (NIIF 15) | Cambia base del 15% y del IR en cascada |

**Regla del motor:** al cerrar el análisis de cualquier grupo, sus hallazgos con eco tributario se apilan automáticamente en la conciliación reconstruida de este grupo.

### → NÓMINA (activo)
- Orden: 15% antes del IR. Todo ajuste de utilidad recalcula ambos.

### → PATRIMONIO (declarado, se activa con módulo patrimonio)
- Dividendos: soportados en utilidades reales + acta; retenciones sobre distribución; coherencia con el 101.

### → HECHOS POSTERIORES (transversal)
- La declaración 101 presentada después del cierre valida (o desmiente) la provisión registrada.

---

## 7. Revisión de calidad (preguntas de cierre)

- ¿La conciliación fue RECONSTRUIDA por el auditor, no solo revisada?
- ¿Todos los no deducibles hallados en otras áreas están en la conciliación?
- ¿El diferido se demuestra con inventario de diferencias partida por partida?
- ¿El activo diferido por pérdidas tiene proyección de utilidades que lo sostenga?
- ¿Los cruces 104/103/ATS vs. contabilidad están documentados con diferencias explicadas?
- ¿Ajustes de auditoría propuestos recalcularon la cascada 15% → IR?
- ¿Se evaluaron contingencias tributarias con carta de abogados?
