# Roadmap bloqueado de SocioAI

**Fecha:** 5 de agosto de 2026
**Estado:** PLAN CERRADO PARA EJECUCIÓN
**Fuente de verdad:** `docs/PRODUCTO_SOCIOAI_GUI_MAESTRA.md`
**Regla:** el orden puede ajustarse por dependencias técnicas; la definición, los cinco pilares y el alcance del piloto no cambian sin evidencia admitida por el control de cambios.

## Primer paso siguiente

### Curar el corpus mínimo del piloto

Antes de desarrollar nuevas pantallas, memoria adicional o el verificador semántico, se debe completar un **Lote Normativo 1** para Ingresos y Cuentas por Cobrar:

- NIA 240, 315, 330 y 500;
- NIIF 15 y NIIF 9;
- NIIF para las PYMES, secciones 23 y 11;
- regulación ecuatoriana que determine adopción, presentación o aplicación local para el piloto.

Para cada fuente se debe registrar autoridad, nombre oficial, edición, jurisdicción, vigencia desde/hasta, periodos aplicables, URL oficial, localizador, licencia o derecho de uso, fecha de revisión y revisor. Los resúmenes internos deben enlazar cada afirmación relevante con el pasaje que la respalda.

**Criterio de salida:** el lote no termina por estar cargado. Termina cuando otra persona puede abrir cada cita, llegar al pasaje exacto y confirmar autoridad, versión, vigencia y sentido sin depender de la IA.

**Entregable:** manifiesto del corpus, fuentes habilitadas para citar, fuentes pendientes o retiradas y un conjunto inicial de preguntas con respuestas esperadas y casos de abstención.

Este es el único primer paso activo. Las fases siguientes permanecen cerradas hasta cumplir su criterio de salida.

## Fase 0 - Alineación

- Mantener la navegación MVP centrada en Mentor, contexto, fuentes, biblioteca, procedimientos y aprendizaje.
- Congelar módulos de papeles de trabajo, firmas, reportes y suite integral.
- No borrar módulos congelados antes del primer piloto pagado.
- Actualizar documentación y backlog conforme a la constitución bloqueada.

## Fase 1 - Biblioteca confiable

**Puerta de Calidad V1 implementada el 4 de agosto de 2026.** El índice activo se reconstruye por huella de contenido, excluye respaldos, separa orientación de cita verificada y mantiene la búsqueda web desactivada por defecto. Estado inicial de curación: 95 fuentes activas, 79 respaldos excluidos y 0 fuentes autorizadas todavía como cita normativa.

- Excluir `_backup` de la indexación RAG.
- Corregir duplicados y problemas de codificación.
- Clasificar cada contenido como oficial, resumen verificado, metodología, criterio práctico, pendiente o retirado.
- Registrar autoridad, edición, jurisdicción, vigencia, URL oficial, localizador y estado de revisión.
- Mantener versiones simultáneas cuando la vigencia dependa del periodo o adopción local.
- Validar manualmente las normas prioritarias para Ingresos y Cuentas por Cobrar.
- Probar recuperación, citas y abstención cuando no exista fuente suficiente.

### Fase 1B - Verificador Normativo Bloqueante V2

Esta fase inicia únicamente cuando el Lote Normativo 1 tenga fuentes aptas para citar.

- Dividir la respuesta en afirmaciones normativas identificables.
- Exigir que cada afirmación normativa apunte a uno o más pasajes del corpus autorizado.
- Comprobar existencia, metadatos, vigencia, jurisdicción y correspondencia semántica entre afirmación y pasaje.
- Bloquear citas inexistentes, ambiguas, desactualizadas o que no respalden lo afirmado.
- Reformular con fuentes válidas o declarar **“el corpus disponible no permite sustentar esta afirmación”**.
- Separar visualmente fuente verificada, orientación no verificada y limitación de cobertura.
- Registrar qué control pasó, cuál falló y por qué, sin exponer razonamiento interno del modelo.
- Mantener búsqueda web desactivada por defecto; una fuente web no entra al corpus por haber sido encontrada.

**Criterios de salida del Verificador V2:**

- cero citas inventadas en el conjunto controlado del piloto;
- toda cita abre la fuente y el localizador correctos;
- pruebas negativas bloquean fuentes inexistentes, versiones incorrectas y pasajes que no sustentan la afirmación;
- el sistema declara falta de cobertura en vez de completar por estimación;
- un auditor puede revisar la trazabilidad afirmación → pasaje → fuente → versión;
- la frase pública **“Diseñado para no inventar”** permanece deshabilitada hasta documentar estos resultados.

## Fase 2 - Memoria estructurada

- Conservar historial completo de mensajes con política configurable de retención.
- Generar diario por sesión o día.
- Generar resumen educativo semanal y consolidación mensual.
- Promover a memoria durable solo observaciones, declaraciones, diferencias, hipótesis, evidencia, decisiones, fundamentos, tareas, pendientes, revisiones y cambios relevantes.
- Incorporar estados candidato, confirmado, descartado y reemplazado.
- Separar memoria del encargo y memoria educativa del usuario.
- Mostrar una línea de tiempo y un briefing para nuevos integrantes.

## Fase 3 - Piloto Ingresos y Cuentas por Cobrar

- Implementar el método universal: comprender, relacionar, evaluar, responder y concluir.
- Conectar reconocimiento, facturación, cartera, recaudo y deterioro.
- Probar empresas comerciales y de servicios.
- Relacionar hechos, aseveraciones, riesgos, procedimientos, fuentes y decisiones humanas.
- No incorporar otras áreas durante el piloto.

## Fase 4 - Mentor por nivel

- Convertir Enséñame, Ayúdame y Desafíame en comportamientos distintos.
- Preguntar antes de entregar conclusiones a perfiles en aprendizaje.
- Mostrar omisiones, contradicciones y alternativas a perfiles de revisión.
- Permitir que gerente o socio documenten fundamentos que el equipo pueda comprender después.
- Mantener el aprendizaje como apoyo visible, no como evaluación laboral secreta.

## Fase 5 - Validación

- Construir casos controlados de Ingresos y Cuentas por Cobrar.
- Comparar SocioAI con ChatGPT o Claude Projects usando las mismas fuentes.
- Medir tiempo, citas, errores, observaciones de revisión, comprensión, retorno y disposición de pago.
- Ejecutar piloto con datos anonimizados antes de información real.
- Ampliar áreas únicamente si el piloto demuestra valor y existe compromiso comercial.

## Fase 6 - Audio como fuente

- Permitir carga de audio existente; no grabación integrada en el MVP.
- Transcribir con marcas de tiempo y participantes cuando sea posible.
- Extraer declaraciones, compromisos, documentos solicitados y pendientes como candidatos.
- Exigir revisión humana antes de incorporar elementos a la memoria durable.
- Tratar explicaciones verbales como contexto pendiente de corroboración, no como evidencia suficiente por sí sola.

## Fuera del roadmap activo

- Revisión completa de papeles de trabajo.
- Firmas, preparadores y revisores.
- Horas, asignaciones y CRM.
- Archivo oficial del encargo.
- Edición autónoma de Excel.
- Agentes que controlen el computador.
- Bots para reuniones.
- Nuevas áreas antes de validar Ingresos y Cuentas por Cobrar.

## Orden cerrado de ejecución

1. Curar y aprobar el Lote Normativo 1.
2. Construir y validar el Verificador Normativo Bloqueante V2.
3. Completar la memoria estructurada necesaria para el ciclo piloto.
4. Implementar el recorrido Ingresos y Cuentas por Cobrar con el método de cinco pasos.
5. Adaptar Enséñame, Ayúdame y Desafíame por nivel profesional.
6. Ejecutar casos controlados y pilotos con datos anonimizados.
7. Incorporar audio como fuente después de validar el núcleo.

No se adelantan fases por conveniencia visual o entusiasmo tecnológico. Seguridad y correcciones críticas pueden ejecutarse en cualquier momento, pero no alteran este orden de producto.
