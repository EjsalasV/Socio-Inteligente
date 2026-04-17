# 📋 CARTA DE CONTROL - Ejemplo de Reporte

**Cliente:** Empresa XYZ S.A.  
**Período:** 2026-01-31  
**Auditor Responsable:** jcarlos (Socio)  
**Fecha Reporte:** 2026-04-17

---

## 🎯 RESUMEN EJECUTIVO

| Métrica | Valor |
|---------|-------|
| Total Papeles Auditados | 78 |
| Total Hallazgos Identificados | 5 |
| Hallazgos SIN Efecto | 3 |
| Hallazgos CON Efecto | 1 |
| Ajustes Requeridos | 1 |
| % Hallazgos | 6.4% |

**Conclusión:** Se completó la auditoria de papeles de trabajo con hallazgos menores. 1 hallazgo requiere ajuste en los Estados Financieros.

---

## 📊 HALLAZGOS IDENTIFICADOS

### Hallazgo 1 - CON EFECTO (Requiere Ajuste)

**Código Papel:** 130.03  
**Nombre:** Conciliación cuentas por cobrar  
**Línea de Cuenta:** 130 (CXC)  
**Aseveración:** INTEGRIDAD  
**Motivo Auditor:** Validar que el saldo total de CXC en libros coincide con la suma detallada de clientes

**Observación Final (aprobada por Socio):**
> Encontrada diferencia de $2,500 en saldo CXC. Investigación identificó factura duplicada #4521 por $2,500.  
> Fue procesada dos veces en sistema (error de cargue).  
> Está siendo revertida por cliente en nota de crédito.  
> **Impacto:** CXC debe reducirse por $2,500 en EE.FF.

**Efecto Financiero:** CON_EFECTO  
**Impacto EE.FF.:** Reducción de CXC por $2,500, reducción de ingresos (error período anterior)  
**Acción Recomendada:** Ajuste de asiento: DR Devoluciones -$2,500 CR CXC -$2,500  
**Revisado por:** jcarlos (Socio)  
**Fecha:** 2026-04-16 15:45

---

### Hallazgo 2 - SIN EFECTO

**Código Papel:** 130.04  
**Nombre:** Resumen de antigüedad CXC  
**Línea de Cuenta:** 130 (CXC)  
**Aseveración:** INTEGRIDAD  
**Motivo Auditor:** Evaluar el riesgo de cobranza identificando saldos vencidos por período

**Observación Final (aprobada por Socio):**
> Cliente A tiene saldo vencido de $50,000 (60+ días).  
> Contacto con cliente confirma que será pagado próxima semana.  
> Cobro posterior al cierre ($50,000 recibido en 2026-04-05).

**Efecto Financiero:** SIN_EFECTO  
**Impacto EE.FF.:** Ninguno (se cobró en cierre correcto)  
**Acción Recomendada:** Documentado en archivo. No hay provisión requerida.  
**Revisado por:** jcarlos (Socio)  
**Fecha:** 2026-04-16 15:50

---

### Hallazgo 3 - SIN EFECTO

**Código Papel:** 110.08  
**Nombre:** Valor Neto Realizable (Inventario)  
**Línea de Cuenta:** 110 (Inventarios)  
**Aseveración:** VALORACIÓN  
**Motivo Auditor:** Evaluar si valor de mercado está por debajo de costo (aplicar NRV test)

**Observación Final (aprobada por Socio):**
> Identificado inventario obsoleto (producto XYZ) sin movimiento en 12 meses.  
> Costo en libros: $15,000 | Valor de mercado: $8,000.  
> Comparado con otros clientes similares - mercado bajó 20% este año.  
> Se requiere provisión de obsolescencia por $7,000.  
> Gerencia ha aceptado el ajuste.

**Efecto Financiero:** AJUSTE_REQUERIDO  
**Impacto EE.FF.:** Provisión gasto por obsolescencia $7,000 / DR Gasto, CR Provisión  
**Acción Recomendada:** Asiento: DR Gasto obsolescencia $7,000 CR Provisión inventario $7,000  
**Revisado por:** jcarlos (Socio)  
**Fecha:** 2026-04-16 16:00

---

### Hallazgo 4 - SIN EFECTO

**Código Papel:** 425.03  
**Nombre:** Conciliación cuentas por pagar  
**Línea de Cuenta:** 425 (CXP)  
**Aseveración:** INTEGRIDAD  
**Motivo Auditor:** Validar que CXP en libros coincide con suma de acreencias por pagar

**Observación Final:**
> Conciliación de CXP vs facturas por pagar: diferencia de $500.  
> Identificada factura de proveedor pendiente de imputar.  
> Fue recibida el 2026-02-28 pero no fue contabilizada hasta 2026-04-01.  
> Pertenece al período anterior.

**Efecto Financiero:** SIN_EFECTO  
**Impacto EE.FF.:** Ajuste período anterior (no afecta períodomás actual)  
**Acción Recomendada:** Ajuste contable reversión período anterior  
**Revisado por:** jcarlos (Socio)  
**Fecha:** 2026-04-16 16:10

---

### Hallazgo 5 - SIN EFECTO

**Código Papel:** 324.04  
**Nombre:** Declaración de IVA  
**Línea de Cuenta:** 324 (Impuestos Pasivo)  
**Aseveración:** PRESENTACIÓN  
**Motivo Auditor:** Validar que IVA de ventas está correctamente liquidado vs compras

**Observación Final:**
> IVA a pagar calculado: $25,000 (ventas IVA menos compras IVA).  
> Declaración presentada: $25,000 ✓ Coincide perfectamente.

**Efecto Financiero:** SIN_EFECTO  
**Impacto EE.FF.:** Ninguno  
**Acción Recomendada:** Ninguna. Correctamente presentado.  
**Revisado por:** jcarlos (Socio)  
**Fecha:** 2026-04-16 16:15

---

## 📈 RESUMEN POR LÍNEA DE CUENTA

| L/S | Nombre | Total Papeles | Hallazgos | Hallazgos con Efecto |
|-----|--------|---------------|-----------|----------------------|
| 130 | CXC | 7 | 2 | 1 |
| 110 | Inventarios | 6 | 1 | 1 |
| 425 | CXP | 5 | 1 | 0 |
| 324 | Impuestos Pasivo | 7 | 1 | 0 |
| Otras | ... | 53 | 0 | 0 |
| **TOTAL** | | **78** | **5** | **2** |

---

## 📋 CLASIFICACIÓN DE HALLAZGOS

### Por Efecto Financiero

- **SIN EFECTO:** 3 hallazgos (60%)
  - Asuntos documentados pero sin impacto en EE.FF.
  
- **CON EFECTO:** 1 hallazgo (20%)
  - Ajuste en CXC por $2,500
  
- **AJUSTE REQUERIDO:** 1 hallazgo (20%)
  - Provisión inventario $7,000

---

## 🎯 AJUSTES PROPUESTOS

### Ajuste 1: Reversión factura duplicada CXC

```
Fecha: 2026-04-16
Concepto: Reversión factura duplicada #4521

Débito   Devoluciones            $2,500
  Crédito   Cuentas por Cobrar           $2,500
```

### Ajuste 2: Provisión por obsolescencia

```
Fecha: 2026-04-16
Concepto: Provisión inventario obsoleto (Producto XYZ)

Débito   Gasto por Obsolescencia $7,000
  Crédito   Provisión Inventario         $7,000
```

---

## 📝 CONCLUSIONES

1. ✅ Se completó auditoria de 78 papeles de trabajo
2. ✅ Se identificaron 5 hallazgos (3 sin efecto, 1 con efecto, 1 ajuste)
3. ⚠️ Se requieren 2 ajustes por $9,500 total
4. ✅ Todos los hallazgos fueron aprobados por Socio
5. ✅ No hay problemas de integridad o fraude sospechosos
6. ✅ Control interno operando efectivamente

---

## 📋 OBSERVACIONES IMPORTANTES

- La duplicada en CXC fue identificada por Junior, aprobada por Senior, y finalmente ajustada por Socio
- La provisión de inventario fue evaluada aplicando NRV test conforme a NIIF
- Todos los ajustes requieren contabilización antes de emitir Estados Financieros
- Los papeles de trabajo contienen documentación de apoyo completa

---

**Elaborado por:** jcarlos (Socio Auditor)  
**Revisado por:** Junta Directiva  
**Fecha:** 2026-04-17  
**Estado:** APROBADO
