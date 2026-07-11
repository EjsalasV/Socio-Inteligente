# Grupo: Inventarios (NIC 2)

> **Estado:** borrador IA — pendiente validación por socio revisor. Marco: NIIF completas / NIIF PYMES, contexto Ecuador.
> **Vínculos activos:** ingresos (corte), costo de ventas (margen), impuestos (obsolescencia no deducible).

---

## 1. Qué exige la norma (aterrizado a auditoría)

NIC 2 se reduce a **tres preguntas auditables**:

| Pregunta | Regla NIC 2 | Qué audita |
|----------|-------------|------------|
| **¿Existe?** | El inventario es activo si la entidad lo controla | Toma física, corte, mercadería en tránsito y en consignación |
| **¿A qué costo?** | Costo de adquisición/transformación, fórmulas FIFO o promedio (NO UEPS) | Composición del costo, método consistente, distribución de costos indirectos |
| **¿Vale eso?** | Menor entre costo y valor neto realizable (VNR) | Obsolescencia, lento movimiento, precios de venta bajo costo |

**Micro-ejemplo VNR:** producto en bodega al costo de USD 100. Precio de venta actual USD 90, gastos de venta USD 5 → VNR = USD 85. Ajuste requerido: USD 15 por unidad. Si el cliente no lo registró → hallazgo.

---

## 2. Riesgos recurrentes

1. **Inventario inexistente o inflado:** el saldo del mayor no está soportado por toma física. Clásico para maquillar resultados: inflar inventario final baja el costo de ventas y sube la utilidad.
2. **Corte incorrecto:** ventas de diciembre con salida de inventario en enero (doble activo: CxC + inventario), o compras recibidas en diciembre facturadas en enero (activo sin pasivo).
3. **Obsolescencia sin provisión:** ítems sin movimiento 12+ meses valorados al costo original. En Ecuador la baja de inventario exige acta notarizada y declaración juramentada para ser deducible — por eso los clientes la evitan, y el inventario "vale" cada vez más en libros y menos en la realidad.
4. **Costos indirectos mal asignados:** en manufactura, la distribución de CIF usa capacidad normal (NIC 2.13). Capacidad ociosa cargada al inventario = activo inflado; debe ir a gasto.
5. **Inventario en poder de terceros / consignación:** mercadería en consignación en tiendas sigue siendo inventario propio; mercadería recibida en consignación NO es inventario propio aunque esté en bodega.
6. **Método de costeo cambiado sin revelación:** pasar de promedio a FIFO en año de inflación de costos mueve el margen; el cambio requiere justificación y aplicación retroactiva.

## 3. Enfoque recomendado (pruebas concretas)

1. **Asistir a la toma física** (o inventario rotativo con evidencia): seleccionar ítems del listado a la bodega (existencia) y de la bodega al listado (integridad). Documentar diferencias y su ajuste.
2. **Prueba de corte:** últimos 5 documentos de venta y compra de diciembre + primeros 5 de enero. Cruzar factura ↔ guía de remisión ↔ kardex: fecha del documento = fecha del movimiento de inventario.
3. **Recalcular costo de ventas global:** inventario inicial + compras − inventario final = costo de ventas. Si no cuadra con el estado de resultados, hay ajustes manuales que explicar.
4. **Análisis de antigüedad y rotación por ítem/línea:** ítems sin movimiento >12 meses, rotación por línea vs. año anterior. Pedir precios de venta actuales de esos ítems → prueba de VNR.
5. **Contrastar margen bruto** por línea vs. año anterior y vs. sector: variación >3-5 puntos exige explicación económica (cambio de mezcla, precios, o error/manipulación).
6. **Confirmar inventario en poder de terceros** y revisar contratos de consignación en ambos sentidos.

## 4. Errores comunes del auditor

- Aceptar el listado valorizado del sistema sin amarrarlo al mayor Y a la toma física (los tres deben cuadrar).
- Hacer la prueba de corte solo del lado de ventas y olvidar compras (pasivos omitidos).
- Aceptar "no hay obsolescencia" verbal con un listado que muestra ítems de hace 3 años.
- No preguntar por inventario en tránsito (importaciones FOB embarcadas en diciembre: ya son del cliente aunque no hayan llegado).
- Revisar solo la existencia y olvidar la valuación (VNR) — la mitad de los hallazgos de inventario son de valuación, no de existencia.

---

## 5. Matriz Riesgo → Prueba → Hallazgo

| Riesgo | Prueba | Hallazgo si falla (plantilla) |
|--------|--------|-------------------------------|
| Inventario inexistente | Toma física, doble dirección | "Diferencia de USD X entre saldo contable y existencia física, no ajustada" |
| Corte de ventas | Últimos/primeros 5 documentos | "Ventas de diciembre por USD X con salida de inventario en enero: ingreso y CxC sobrestimados, inventario duplicado" |
| Corte de compras | Recepciones dic. vs. facturas ene. | "Compras recibidas en diciembre por USD X sin pasivo registrado" |
| Obsolescencia | Antigüedad + VNR de ítems lentos | "Ítems sin movimiento >12 meses por USD X valorados al costo, sin provisión por VNR" |
| Costo inflado (CIF) | Revisión de distribución con capacidad normal | "Capacidad ociosa por USD X capitalizada en inventario; debe reconocerse como gasto del período" |
| Consignación | Contratos + confirmación terceros | "Mercadería recibida en consignación por USD X registrada como inventario propio" |

---

## 6. Vínculos (chequeos de coherencia con otros grupos)

### → INGRESOS (activo)
- **Corte:** cada venta reconocida en diciembre debe tener salida de kardex en diciembre. Venta sin salida = ingreso anticipado + inventario inflado (doble hallazgo, ver NIIF 15 paso 5).
- **Señal:** ingresos suben pero inventario sube MÁS rápido → o compró de más (riesgo obsolescencia) o hay ventas ficticias devueltas al inventario.

### → COSTO DE VENTAS / GASTOS (activo)
- **Recálculo global:** inv. inicial + compras − inv. final = costo de ventas del estado de resultados. Diferencia = ajustes manuales por explicar.
- **Margen bruto:** (ingresos − costo) / ingresos vs. año anterior y sector. Inventario final sobrestimado infla el margen artificialmente — la manipulación más barata que existe.

### → CxP (declarado, se activa al construir CxP)
- Compras de diciembre facturadas en enero: buscar en recepciones de bodega, no en el registro contable.

### → IMPUESTOS (activo)
- Provisión por obsolescencia registrada contablemente NO es deducible hasta la baja física (acta, notario). Verificar que la conciliación tributaria la suma como gasto no deducible y que se reconoció el **impuesto diferido activo** por la diferencia temporaria.

---

## 7. Revisión de calidad (preguntas de cierre)

- ¿El saldo final cuadra en tres puntos: mayor = listado valorizado = toma física?
- ¿La prueba de corte cubrió ventas Y compras, con documentos de ambos lados del cierre?
- ¿Los ítems de lento movimiento tienen prueba de VNR con precios de venta reales?
- ¿El costo de ventas recalculado globalmente cuadra con el estado de resultados?
- ¿El margen bruto tiene explicación económica frente al año anterior?
- ¿La conciliación tributaria refleja la provisión de obsolescencia como no deducible?
