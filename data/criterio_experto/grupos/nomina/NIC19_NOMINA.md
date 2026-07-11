# Grupo: Nómina y Beneficios a Empleados (NIC 19 + Ecuador)

> **Estado:** borrador IA — pendiente validación por socio revisor. Marco: NIC 19, Código de Trabajo Ecuador, Ley de Seguridad Social (IESS).
> **Vínculos activos:** gastos (cuadre global), impuestos (participación 15%, deducibilidad), beneficios largo plazo (jubilación patronal).

---

## 1. El mapa de la nómina ecuatoriana (qué debe existir al cierre)

| Concepto | Base legal | Cómo se audita |
|----------|-----------|----------------|
| Sueldos y salarios | Contrato / Código de Trabajo | Cuadre contable vs. planillas IESS vs. roles |
| Aporte patronal IESS (11.15% + extras) | LSS | Recálculo: base imponible × tasa; planillas pagadas |
| Décimo tercero (1/12 de lo ganado en el año dic-nov) | Código de Trabajo | Recálculo global + provisión al cierre por lo devengado |
| Décimo cuarto (1 SBU por año escolar) | Código de Trabajo | Recálculo: # empleados × SBU proporcional |
| Vacaciones (1/24 de lo ganado) | Código de Trabajo | Provisión por días no gozados; la deuda acumulada de años |
| Fondos de reserva (8.33% desde año 2) | LSS | Recálculo sobre empleados con +1 año |
| Participación trabajadores 15% | Código de Trabajo | 15% sobre utilidad ANTES de impuestos (ver vínculo impuestos) |
| Jubilación patronal y desahucio | Código de Trabajo / NIC 19 | Estudio actuarial para plantilla relevante (obligación por empleados 10+ años, devengo desde el año 1) |

**La lógica de socio:** la nómina es de los pocos rubros con **evidencia externa completa** (planillas IESS, formulario 107, décimos legalizados en Ministerio de Trabajo). Si el gasto contable no cuadra con esa evidencia externa, alguien está mintiendo: o a la contabilidad, o al IESS, o al SRI.

---

## 2. Riesgos recurrentes

1. **Gasto contable ≠ planillas IESS:** sueldos en contabilidad mayores que la base IESS = pagos "por fuera" (bonos no aportados) → contingencia laboral e IESS, y el exceso puede ser no deducible.
2. **Provisiones de beneficios incompletas al cierre:** décimos y vacaciones devengados y no provisionados. Vacaciones es la clásica: años acumulados sin gozar y sin pasivo.
3. **Jubilación patronal sin estudio actuarial:** empresas con empleados antiguos y ninguna provisión, o provisión "del año pasado más algo". NIC 19 exige cálculo actuarial (el devengo empieza desde el primer año, no al cumplir 10).
4. **Participación trabajadores 15% mal calculada:** la base es la utilidad contable antes de impuestos, con ajustes específicos; errores aquí arrastran el impuesto a la renta (se calcula después del 15%).
5. **Empleados fantasma o servicios simulados:** roles con personas que no existen o familiares que no trabajan; honorarios profesionales recurrentes que son relación laboral encubierta (contingencia: IESS + beneficios retroactivos).
6. **Liquidaciones y juicios laborales:** ex-empleados demandando; ¿provisión o revelación según NIC 37? Pedir carta de abogados y cruzar con el sistema judicial.

## 3. Enfoque recomendado (pruebas concretas)

1. **Cuadre global de tres fuentes (la prueba reina):**
   `Gasto contable de nómina ≈ Planillas IESS del año + provisiones netas de beneficios + pagos no aportables justificados`
   Diferencia material → investigar línea por línea qué se paga por fuera del IESS y por qué.
2. **Recálculo global de beneficios:** décimo tercero (masa salarial dic-nov ÷ 12), décimo cuarto (empleados × SBU), fondos de reserva (8.33% de elegibles), vacaciones (saldo de días no gozados × última remuneración ÷ 24... según política). Comparar con provisión registrada.
3. **Recálculo del 15% participación:** utilidad contable antes de impuestos × 15%. Verificar contra la provisión y contra el formulario 101 del año anterior (¿se pagó hasta abril?).
4. **Jubilación patronal:** pedir el estudio actuarial vigente; validar datos de entrada (plantilla, edades, antigüedad, salarios) contra roles reales. Sin estudio + plantilla con antigüedad → hallazgo casi seguro.
5. **Prueba de existencia de empleados** (en clientes de riesgo): muestra de roles → contrato, aviso de entrada IESS, transferencia bancaria a cuenta personal, y para casos sensibles, verificación física/funcional.
6. **Revisar honorarios recurrentes:** mismo "proveedor" persona natural facturando todos los meses, con horario y subordinación = relación laboral encubierta.

## 4. Errores comunes del auditor

- Auditar la nómina revisando roles mes a mes en lugar del cuadre global de tres fuentes (más trabajo, menos hallazgos).
- Aceptar la provisión de vacaciones "del sistema" sin pedir el reporte de días acumulados por empleado.
- Olvidar que el 15% participación se calcula ANTES del impuesto a la renta, y el impuesto DESPUÉS del 15% (el orden importa; hacerlo al revés cambia ambos).
- No pedir estudio actuarial porque "la empresa es pequeña" — la obligación de jubilación patronal no depende del tamaño sino de la antigüedad de la plantilla.
- Revisar solo el gasto y olvidar los pasivos: décimos por pagar, IESS por pagar, participación por pagar deben cuadrar con lo declarado/pagado después del cierre.

---

## 5. Matriz Riesgo → Prueba → Hallazgo

| Riesgo | Prueba | Hallazgo si falla (plantilla) |
|--------|--------|-------------------------------|
| Pagos fuera de IESS | Cuadre global 3 fuentes | "Gasto de nómina excede base IESS en USD X sin justificación; contingencia laboral/IESS y gasto potencialmente no deducible" |
| Provisiones incompletas | Recálculo décimos/vacaciones | "Provisión de [beneficio] subestimada en USD X; pasivo omitido al cierre" |
| Jubilación patronal | Estudio actuarial + datos entrada | "No existe provisión actuarial de jubilación patronal; plantilla con [N] empleados de [X]+ años de antigüedad" |
| 15% mal calculado | Recálculo sobre utilidad correcta | "Participación trabajadores calculada sobre base errónea; diferencia USD X que además afecta el impuesto a la renta" |
| Empleados fantasma | Existencia (contrato+IESS+banco) | "Empleados en rol sin aviso de entrada IESS / sin transferencia a cuenta personal por USD X" |
| Laboral encubierto | Honorarios recurrentes | "Honorarios mensuales a [persona] con características de relación laboral; contingencia IESS y beneficios retroactivos por USD X estimado" |

---

## 6. Vínculos (chequeos de coherencia con otros grupos)

### → GASTOS (activo)
- El gasto de nómina del estado de resultados (sueldos + beneficios + aporte patronal) debe reconstruirse desde planillas IESS + provisiones. Es parte del recálculo global de gastos.

### → IMPUESTOS (activo)
- **Orden del cálculo:** utilidad contable → menos 15% participación → base para conciliación tributaria → impuesto a la renta. Error en nómina arrastra los dos.
- Gastos de nómina no soportados en IESS: verificar tratamiento en conciliación (no deducibles).
- Provisiones de jubilación patronal: deducibilidad limitada (solo empleados 10+ años, con condiciones) → diferencia temporaria e impuesto diferido.

### → PROVISIONES (declarado, se activa al construir provisiones)
- Juicios laborales de ex-empleados: carta de abogados, probable → provisión, posible → revelación.

### → BENEFICIOS LARGO PLAZO (activo)
- La provisión actuarial (jubilación/desahucio) debe ser coherente con la plantilla real: si la empresa tiene 40 empleados con 8+ años y la provisión es USD 5k, algo está mal aunque haya "estudio".

### → PARTES RELACIONADAS (transversal)
- Familiares del accionista en rol: ¿trabajan realmente? ¿remuneración de mercado? Sobresueldos a relacionados = distribución encubierta.

---

## 7. Revisión de calidad (preguntas de cierre)

- ¿El cuadre de tres fuentes (contabilidad / IESS / formulario 107) cierra con diferencias explicadas?
- ¿Cada beneficio social tiene recálculo global vs. provisión registrada?
- ¿Existe estudio actuarial vigente y sus datos de entrada cuadran con la plantilla real?
- ¿El 15% y el impuesto a la renta se calcularon en el orden correcto?
- ¿Los pasivos laborales al cierre se pagaron/declararon correctamente en el año siguiente (hechos posteriores)?
- ¿Se preguntó por juicios laborales y hay carta de abogados que lo soporte?
