# Manual de Uso del Sistema (Primer Dia)

Este manual es para alguien que **ya entra al sistema** y necesita saber que hacer, en que orden, y como cerrar una auditoria sin perder trazabilidad.

## 1. Objetivo de trabajo

Al terminar una jornada deberias lograr:

1. Priorizar areas de riesgo.
2. Generar briefing por area con soporte normativo.
3. Estructurar hallazgos con criterio tecnico.
4. Validar calidad antes de pasar de fase o emitir.

## 2. Flujo recomendado de uso (orden real)

## Paso 1 - Entrar y seleccionar cliente

1. Inicia sesion.
2. Ve a la pantalla de clientes.
3. Abre el cliente activo del encargo.

Resultado esperado: cliente y periodo activo confirmados.

## Paso 2 - Revisar contexto general del encargo

1. Entra a `Dashboard`.
2. Revisa:
   - riesgo global,
   - materialidad,
   - fase actual del workflow,
   - alertas pendientes.

Resultado esperado: sabes en que etapa estas y que tan sensible es el encargo.

## Paso 3 - Priorizar areas por riesgo

1. Entra a `Risk Engine`.
2. Identifica top areas por score.
3. Selecciona la primera area de trabajo (normalmente alto riesgo).

Resultado esperado: orden de trabajo definido por riesgo, no por intuicion.

## Paso 4 - Abrir area activa

1. Ve a `Areas` y abre el codigo L/S correspondiente (ej. 130 CxC, 150 Inventarios, 300 Ingresos).
2. Revisa:
   - cuentas del lead schedule,
   - aseveraciones asociadas,
   - checks pendientes.

Resultado esperado: area lista para ejecutar procedimientos.

## Paso 5 - Generar briefing de area

1. Haz clic en `Generar Briefing`.
2. Verifica que el briefing incluya:
   - por que importa esa area,
   - aseveraciones expuestas,
   - procedimientos sugeridos,
   - normativa activada.
3. Revisa `chunks usados` y `normas activadas` para validar soporte.

Resultado esperado: plan operativo concreto para ejecutar esa area.

## Paso 6 - Ejecutar y documentar evidencia

Durante la ejecucion del area:

1. Marca checks por cuenta/procedimiento.
2. Registra evidencia clave en papeles de trabajo.
3. Si aparece desviacion, prepara condicion para hallazgo.

Resultado esperado: avance tecnico con evidencia trazable.

## Paso 7 - Estructurar hallazgo

1. En `Estructurador de Hallazgo`, escribe la condicion detectada.
2. Genera hallazgo.
3. Revisa y ajusta:
   - condicion,
   - criterio,
   - causa,
   - efecto,
   - recomendacion.

Resultado esperado: hallazgo util para carta de control o cierre.

## Paso 8 - Registrar tiempo (opcional recomendado)

En la misma vista de area:

1. Ingresa minutos manuales.
2. Ingresa minutos con AI.
3. Guarda medicion.

Resultado esperado: metrica real de ahorro para seguimiento operativo.

## Paso 9 - Control de calidad antes de avanzar

Usa el pre-check de calidad:

- `POST /api/quality/pre-emit-check`

Interpreta resultado:

1. `status=blocked`: no avances, corrige bloqueantes.
2. `status=ok` con warnings: puedes avanzar, pero revisa observaciones.

Bloqueantes tipicos:

1. Aseveraciones criticas sin cobertura.
2. Hallazgos criticos abiertos sin plan/respuesta.
3. Conclusiones tecnicas debiles en areas de riesgo alto.
4. Inconsistencias con materialidad.

Resultado esperado: control tecnico antes de cambiar fase o emitir.

## Paso 10 - Usar plantilla de fase para no reescribir trabajo

Consulta plantilla de fase:

- `GET /workflow/{cliente_id}/phase-template`

Que revisar:

1. `missing_required`.
2. `can_advance`.
3. campos prellenados.

Si haces ajuste manual de un campo relevante, registra historial:

- `POST /workflow/{cliente_id}/field-history`

Resultado esperado: continuidad entre planificacion, ejecucion y cierre sin duplicar trabajo.

## 3. Como leer la trazabilidad (muy importante)

Cada briefing/hallazgo guarda:

1. norma,
2. fuente_chunk,
3. chunk_id,
4. area_codigo,
5. timestamp.

Uso practico:

1. Si alguien pregunta "de donde salio esto", abres trazabilidad y respondes con evidencia.
2. Si hay discrepancia, vuelves al chunk exacto y corriges criterio.

## 4. Alertas de vigencia normativa

Si ves advertencia tipo:

`Verificar vigencia... cambio detectado pendiente de revision`

significa:

1. Se detecto posible cambio normativo mensual (tributario/regulatorio).
2. No bloquea el trabajo, pero debes validar antes de emitir criterio final.

## 5. Checklist rapido de uso diario

1. Cliente correcto abierto.
2. Riesgo y fase revisados.
3. Area priorizada por score.
4. Briefing generado y revisado.
5. Evidencia cargada.
6. Hallazgo estructurado (si aplica).
7. Pre-check de calidad ejecutado.
8. Bloqueantes resueltos antes de avanzar.

---

Version: V1.2  
Enfoque: uso operativo del sistema en auditoria (no instalacion).

