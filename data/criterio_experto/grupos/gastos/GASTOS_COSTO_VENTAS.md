# Grupo: Costo de Ventas y Gastos Operativos

> **Estado:** borrador IA — pendiente validación por socio revisor. Marco: NIC 1, NIC 2 (costo), principio de devengo. Contexto Ecuador (deducibilidad, bancarización, retenciones).
> **Vínculos activos:** inventarios (recálculo costo), ingresos (margen), nómina (cuadre planillas), impuestos (no deducibles).

---

## 1. Qué se audita en gastos (las 4 afirmaciones que importan)

| Afirmación | Pregunta | Prueba típica |
|------------|----------|---------------|
| **Ocurrencia** | ¿El gasto es real y del negocio? | Vouching: factura + retención + pago + evidencia del servicio recibido |
| **Integridad (corte)** | ¿Están TODOS los gastos del año? | Búsqueda de pasivos no registrados: pagos de enero-febrero por servicios de diciembre |
| **Clasificación** | ¿Gasto o activo? ¿Costo o gasto? | Revisión de capitalizaciones, mantenimientos mayores, CIF |
| **Exactitud** | ¿El monto y período son correctos? | Recálculos globales (depreciación, intereses, nómina), prorrateos de seguros/arriendos pagados por anticipado |

**El error de enfoque más común:** vouchear 40 facturas al azar y concluir. El gasto se audita mejor con **analíticas globales + corte** que con muestreo puro: recalcular depreciación, intereses y nómina cubre el 60-70% del gasto operativo con tres pruebas.

---

## 2. Riesgos recurrentes

1. **Gastos omitidos (corte):** servicios de noviembre-diciembre facturados o pagados en enero sin provisión. La utilidad del año queda inflada. Es EL hallazgo de gastos en firmas pequeñas.
2. **Gastos personales del accionista en la compañía:** vehículos, viajes, consumos, remodelaciones de casa. En firma familiar, asumir que existen hasta probar lo contrario. Doble efecto: gasto no deducible + posible distribución encubierta a relacionadas.
3. **Gastos sin sustento válido:** sin factura autorizada, sin retención emitida, o pagados en efectivo sobre el umbral de bancarización → no deducibles. El hallazgo no es solo contable, es tributario.
4. **Capitalización vs. gasto invertido:** mantenimientos mayores enviados a gasto (para bajar impuestos) o gastos ordinarios capitalizados (para mostrar utilidad). Revisar contra política y NIC 16.
5. **Gastos con partes relacionadas sin sustancia:** management fees, regalías, servicios corporativos. ¿Hay contrato, evidencia del servicio, precio de mercado? Sin eso: no deducible + partes relacionadas no reveladas.
6. **Prorrateos ignorados:** seguros, arriendos, licencias anuales pagados por adelantado y enviados 100% a gasto del período de pago.

## 3. Enfoque recomendado (pruebas concretas)

1. **Búsqueda de pasivos no registrados (obligatoria):** revisar pagos y facturas recibidas de enero-febrero del año siguiente → ¿el servicio/bien corresponde a diciembre o antes? Si sí, ¿estaba provisionado?
2. **Recálculos globales:** depreciación (saldos × vidas útiles), gasto financiero (deuda promedio × tasa), nómina (ver módulo nómina). Diferencias >materialidad de ejecución → investigar.
3. **Analítica mensual por rubro:** gastos por mes y por cuenta vs. año anterior. Picos inusuales (diciembre cargado de gastos) y ausencias (un mes sin arriendo) son las mejores señales.
4. **Vouching dirigido, no aleatorio:** seleccionar por riesgo — gastos redondos, proveedores nuevos, cuentas "varios/otros", reembolsos a accionistas, gastos justo bajo umbrales de aprobación.
5. **Cruce con declaraciones:** gasto contable vs. compras declaradas (ATS/104) — diferencias grandes anticipan problemas con el SRI.
6. **Revisar la cuenta "otros gastos" completa** si es material: es donde vive todo lo que no quisieron clasificar.

## 4. Errores comunes del auditor

- Auditar gastos solo por muestreo de facturas y no hacer NINGUNA analítica global.
- Hacer la búsqueda de pasivos no registrados revisando solo el módulo de compras (los gastos omitidos suelen estar en pagos directos y caja chica).
- Aceptar reembolsos de gastos al gerente/accionista sin detalle de qué se reembolsa.
- No cruzar el gasto de arriendo con el contrato (y con la relación: ¿el local es del accionista?).
- Concluir "gasto razonable" comparando solo contra presupuesto del cliente, no contra evidencia externa.

---

## 5. Matriz Riesgo → Prueba → Hallazgo

| Riesgo | Prueba | Hallazgo si falla (plantilla) |
|--------|--------|-------------------------------|
| Gastos omitidos | Pasivos no registrados (pagos ene-feb) | "Gastos de [año] por USD X registrados en [año+1]; utilidad sobrestimada" |
| Gastos personales | Vouching dirigido a rubros sensibles | "Gastos sin relación con el giro por USD X (detalle); no deducibles y posible beneficio a accionista" |
| Sin sustento | Factura + retención + bancarización | "Gastos por USD X sin comprobante válido / pagados en efectivo sobre umbral; no deducibles" |
| Clasificación | Revisión capitalizaciones y mantenimientos | "Mantenimiento mayor por USD X enviado a gasto; correspondía capitalizar (o viceversa)" |
| Relacionadas sin sustancia | Contrato + evidencia + precio mercado | "Management fee a relacionada por USD X sin contrato ni evidencia del servicio" |
| Prorrateo | Seguros/arriendos anticipados | "Prima anual USD X cargada 100% al gasto; USD Y corresponde al siguiente ejercicio" |

---

## 6. Vínculos (chequeos de coherencia con otros grupos)

### → INVENTARIOS (activo)
- **Recálculo obligatorio:** inv. inicial + compras − inv. final = costo de ventas. No cuadra → ajustes manuales por explicar.
- Compras crecen pero inventario y ventas no → ¿a dónde fue lo comprado? (gasto personal, faltantes, ventas no registradas).

### → INGRESOS (activo)
- **Margen bruto** vs. año anterior y sector: variación >3-5 puntos sin explicación económica = riesgo en costo O en ingresos.
- Gastos de venta (comisiones, fletes) deben moverse CON las ventas: comisiones planas con ventas crecientes = gasto omitido o comisiones ficticias.

### → NÓMINA (activo)
- Gasto de sueldos y beneficios del estado de resultados cuadra con planillas IESS + provisiones (ver módulo nómina, cuadre global).

### → CxP (declarado, se activa al construir CxP)
- Todo gasto devengado sin factura al cierre debe tener provisión en CxP/acumulados.

### → IMPUESTOS (activo)
- Cada gasto no deducible detectado alimenta la conciliación tributaria. Verificar que el cliente los sumó de vuelta; gastos no deducibles "olvidados" = contingencia con el SRI.

---

## 7. Revisión de calidad (preguntas de cierre)

- ¿Se hizo la búsqueda de pasivos no registrados con pagos y facturas del año siguiente?
- ¿Los tres recálculos globales (depreciación, intereses, nómina) cuadran contra el mayor?
- ¿El costo de ventas recalculado desde inventarios cuadra con resultados?
- ¿La analítica mensual identificó picos/ausencias y todos tienen explicación?
- ¿Los gastos con relacionadas tienen contrato, evidencia y precio defendible?
- ¿Los no deducibles detectados están en la conciliación tributaria del cliente?
