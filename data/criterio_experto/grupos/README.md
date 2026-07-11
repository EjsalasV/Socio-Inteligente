# Grupos del Balance — Arquitectura de Conocimiento NIIF

La herramienta no organiza el conocimiento "por norma" sino **por grupo del balance**, porque así audita un auditor real. Cada grupo conecta su norma, su criterio ejecutable y sus vínculos con otros grupos.

## Estructura

```
grupos/
├─ MAPA_GRUPOS_NORMAS_VINCULOS.yml   ← EMPEZAR AQUÍ: los ~15 grupos, sus normas,
│                                       todos los vínculos, estado de construcción
├─ inventarios/NIC2_INVENTARIOS.md    ← construido
├─ gastos/GASTOS_COSTO_VENTAS.md      ← construido
├─ nomina/NIC19_NOMINA.md             ← construido (NIC 19 + Ecuador)
└─ impuestos/NIC12_IMPUESTOS.md       ← construido (NIC 12 + conciliación Ecuador)

Relacionados (fuera de esta carpeta):
├─ ../niif15/                         ← grupo INGRESOS (framework completo NIIF 15)
└─ ../por_area/*.md                   ← criterio existente: efectivo, cxc,
                                        propiedad inversión, patrimonio, impuestos activos
```

## Patrón de cada módulo de grupo

1. **Qué exige la norma** — aterrizada a preguntas auditables, no teoría
2. **Riesgos recurrentes** — lenguaje de socio revisor, contexto Ecuador
3. **Enfoque recomendado** — pruebas concretas (verbos operativos)
4. **Errores comunes del auditor** — trampas vistas en práctica
5. **Matriz riesgo → prueba → hallazgo** — con plantillas de redacción de hallazgo
6. **Vínculos** — chequeos de coherencia contra otros grupos (el criterio de socio)
7. **Revisión de calidad** — preguntas de cierre

## La regla de los vínculos

- Todos los vínculos se **declaran** en el mapa desde el día 1.
- Un vínculo se **activa** cuando ambos grupos están construidos.
- Un análisis de grupo **nunca se entrega sin correr sus vínculos activos** — pensar en relaciones cruzadas es lo que distingue a un socio de un checklist.

## Cómo lo usa el motor de análisis (visión)

```
Auditor: "Analiza inventarios del cliente XYZ"
   ↓
Motor arma contexto: módulo del grupo + criterio del sector + TB/mayor reales
   ↓
IA analiza riesgos internos + vínculos activos (corte vs. ingresos,
margen vs. gastos, eco tributario vs. impuestos)
   ↓
Reporta hallazgos con norma, prueba sugerida y evidencia esperada
```

## Estado

| Grupo | Estado |
|-------|--------|
| Ingresos (NIIF 15) | ✅ construido |
| Inventarios (NIC 2) | ✅ construido — pendiente validación socio |
| Gastos / Costo ventas | ✅ construido — pendiente validación socio |
| Nómina (NIC 19 + EC) | ✅ construido — pendiente validación socio |
| Impuestos (NIC 12 + EC) | ✅ construido — pendiente validación socio |
| Efectivo, CxC, Prop. inversión, Patrimonio | criterio existente en por_area/ |
| PPE, CxP, Obligaciones fin., Provisiones, Intangibles | pendientes por demanda |
