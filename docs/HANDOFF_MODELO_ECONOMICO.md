# Traspaso temporal a un modelo económico

Este documento permite continuar SocioAI en otro chat con un modelo de menor costo, sin alterar las decisiones de producto ni el trabajo visual pendiente.

## Cómo usar este documento

1. Abre un chat nuevo con el modelo económico.
2. Indícale como carpeta de trabajo: `C:\Users\echoe\Desktop\Nuevo Socio AI`.
3. Copia el prompt de la siguiente sección completo.
4. Pídele ejecutar **una tarea numerada por vez**.
5. No le pidas continuar automáticamente con toda la lista.

## Prompt inicial para el nuevo chat

```text
Trabajarás temporalmente como agente de mantenimiento del proyecto SocioAI ubicado en:

C:\Users\echoe\Desktop\Nuevo Socio AI

SocioAI es una herramienta y mentor para auditores. No es un CRM, no es un sistema de asignación de personal, no controla horas y no busca reemplazar plataformas como CaseWare. Su propósito es ayudar al auditor a comprender clientes, aprender, aplicar procedimientos y razonar con mejor criterio usando fuentes confirmadas.

Antes de modificar archivos:

1. Lee completamente:
   - docs/PRODUCTO_SOCIOAI_GUI_MAESTRA.md
   - docs/FLUJO_COMPLETO.md
   - docs/HANDOFF_MODELO_ECONOMICO.md
2. Revisa README.md y las instrucciones AGENTS.md que existan.
3. Ejecuta `git status --short` y conserva todos los cambios existentes. No borres, reviertas ni sobrescribas trabajo que no hayas creado.
4. Inspecciona únicamente los archivos necesarios para la tarea solicitada.

Reglas obligatorias durante esta etapa:

- Realiza solo la tarea numerada que yo solicite.
- No continúes automáticamente con la siguiente tarea.
- No rediseñes pantallas ni cambies la identidad visual “Expediente Vivo”.
- No cambies la arquitectura, el enfoque del producto ni el flujo principal.
- No modifiques prompts de auditoría, clasificación de riesgos, materialidad, reglas contables ni conclusiones técnicas.
- No alteres, elimines, archives ni recrees clientes reales.
- No ejecutes análisis de IA que consuman tokens del sistema sin autorización explícita.
- No cargues, elimines ni reemplaces documentos de clientes.
- No agregues dependencias salvo que sea indispensable y cuentes con mi autorización.
- No hagas commits, push, despliegues ni migraciones de base de datos sin autorización.
- No elimines funciones porque parezcan antiguas o innecesarias.
- Prefiere cambios pequeños, reversibles y fáciles de revisar.

Puedes:

- leer código y documentación;
- ejecutar lint, TypeScript, compilación y pruebas locales;
- corregir errores claramente reproducibles;
- mejorar accesibilidad y responsive sin rediseñar;
- añadir pruebas para comportamiento existente;
- mejorar mensajes de error y estados vacíos;
- documentar hallazgos técnicos;
- reducir duplicación mecánica cuando no cambie el comportamiento.

Proceso para cada tarea:

1. Explica brevemente qué revisarás.
2. Reproduce o verifica el problema antes de modificar, cuando sea posible.
3. Realiza el cambio mínimo necesario.
4. Ejecuta las pruebas proporcionales al cambio.
5. Revisa el diff para confirmar que no modificaste archivos ajenos a la tarea.
6. Detente y entrégame:
   - resultado;
   - archivos modificados;
   - pruebas ejecutadas y su resultado;
   - riesgos o asuntos pendientes;
   - cualquier decisión que deba reservarse para el modelo principal.

Si encuentras una decisión de producto, auditoría, arquitectura o IA que no esté definida, no la resuelvas. Regístrala como pendiente y detente.

No empieces todavía. Primero confirma que leíste los documentos y pregúntame qué número de tarea ejecutar.
```

## Tareas permitidas

### Tarea 1 — Establecer una línea base técnica

Objetivo: determinar si el proyecto compila y qué pruebas ya existen, sin cambiar comportamiento.

Acciones:

- Revisar scripts disponibles en frontend y backend.
- Ejecutar lint y compilación del frontend.
- Ejecutar las pruebas existentes del backend.
- Registrar errores reales, separándolos de advertencias.
- Crear `docs/ESTADO_TECNICO_TEMPORAL.md` con resultados y comandos reproducibles.

No debe:

- arreglar todos los errores encontrados en la misma tarea;
- actualizar dependencias;
- modificar datos o migraciones.

Prompt corto:

```text
Ejecuta únicamente la Tarea 1 de docs/HANDOFF_MODELO_ECONOMICO.md. No corrijas todavía los problemas; crea la línea base técnica y detente.
```

### Tarea 2 — Corregir fallos de lint, tipos o compilación

Objetivo: corregir únicamente los fallos reproducibles encontrados en la Tarea 1.

Acciones:

- Resolver errores uno por uno.
- No aplicar reformateos masivos.
- No cambiar lógica funcional para silenciar TypeScript.
- Volver a ejecutar lint y compilación.

Prompt corto:

```text
Ejecuta únicamente la Tarea 2. Corrige los errores reproducibles registrados en docs/ESTADO_TECNICO_TEMPORAL.md con cambios mínimos. No cambies diseño ni comportamiento.
```

### Tarea 3 — Añadir pruebas al cuestionario adaptativo

Objetivo: proteger el comportamiento ya implementado en `entity-profile`.

Casos que debe cubrir:

- muestra una pregunta por vez;
- Continuar permanece deshabilitado si la respuesta requerida está vacía;
- Anterior y Continuar cambian de pregunta sin perder respuestas;
- Evaluar ronda conserva respuestas;
- una ronda adicional aparece únicamente cuando la API devuelve nuevas preguntas;
- el resultado final aparece cuando no quedan preguntas críticas;
- Modificar respuestas regresa al cuestionario;
- Confirmar perfil navega al Mentor solo después de confirmación exitosa;
- errores de API son visibles y no borran respuestas.

No debe llamar servicios de IA reales. Debe simular las respuestas de API.

Prompt corto:

```text
Ejecuta únicamente la Tarea 3. Añade pruebas automatizadas del flujo actual del cuestionario usando APIs simuladas. No cambies su diseño ni su lógica de producto.
```

### Tarea 4 — Añadir pruebas al Mentor

Objetivo: proteger la experiencia existente del Mentor.

Casos que debe cubrir:

- selección de Enséñame, Ayúdame y Desafíame;
- creación y apertura de conversación;
- renombrar y eliminar conversación;
- envío bloqueado cuando el texto está vacío;
- prefijo correcto según el modo seleccionado;
- apertura y cierre del menú de perfil;
- apertura del historial sin mostrarlo automáticamente en la portada;
- renderizado de Markdown y fuentes;
- error de API visible sin perder la conversación.

Debe usar APIs simuladas y no consumir tokens reales.

### Tarea 5 — Revisar accesibilidad sin rediseñar

Objetivo: detectar y corregir problemas objetivos de accesibilidad en Login, Mentor y Perfil de entidad.

Revisar:

- orden de tabulación;
- etiquetas de inputs y textareas;
- estados `aria-pressed`, `aria-expanded` y `aria-live`;
- contraste de textos pequeños;
- foco visible;
- botones con área mínima adecuada;
- uso correcto de encabezados;
- interacción mediante teclado.

No debe cambiar composición, estilo editorial ni textos de producto salvo etiquetas accesibles.

### Tarea 6 — Revisar responsive sin rediseñar

Objetivo: corregir desbordamientos en 360, 768, 1024 y 1440 píxeles.

Pantallas:

- Login.
- Mentor.
- Cuestionario adaptativo.
- Resultado del perfil.

Debe conservar la identidad “Expediente Vivo”. Solo corregirá cortes, superposiciones, scroll horizontal y controles inaccesibles.

### Tarea 7 — Mejorar estados de carga y errores

Objetivo: hacer visibles fallos reales sin alterar el flujo.

Revisar:

- carga inicial del perfil;
- evaluación entre rondas;
- análisis final;
- confirmación del perfil;
- carga del Mentor;
- envío de mensajes;
- historial de conversaciones;
- respuestas 401, 404, 409, 422 y 500.

No debe inventar reintentos automáticos ni ocultar errores.

### Tarea 8 — Revisar archivos temporales y artefactos

Objetivo: identificar archivos que no deberían formar parte del producto sin eliminarlos.

Acciones:

- listar capturas, reportes temporales, cachés y archivos generados;
- comprobar `.gitignore`;
- clasificar cada archivo como código, documentación, evidencia QA, dato local o basura probable;
- entregar una propuesta de limpieza.

Importante: en esta tarea no debe borrar nada.

### Tarea 9 — Documentar el flujo técnico actual

Objetivo: actualizar documentación técnica sin redefinir el producto.

Documentar:

- Onboarding → cuestionario → resultado → Mentor;
- endpoints utilizados;
- estados principales del frontend;
- qué pasos llaman IA y cuáles no;
- dónde se guardan respuestas, análisis y conversaciones;
- comportamiento ante errores.

No debe cambiar código salvo enlaces de documentación rotos.

### Tarea 10 — Inventario de deuda técnica

Objetivo: preparar trabajo futuro para el modelo principal.

Clasificar hallazgos en:

- bugs comprobados;
- duplicación;
- falta de pruebas;
- rendimiento;
- seguridad;
- accesibilidad;
- decisiones de arquitectura;
- decisiones de producto;
- asuntos técnicos de auditoría.

No debe solucionar decisiones de arquitectura, producto o auditoría. Debe registrar evidencia, archivos afectados, impacto y recomendación preliminar.

## Orden recomendado

Ejecutar así:

1. Tarea 1 — línea base.
2. Tarea 2 — estabilidad de compilación, solo si la línea base detecta fallos.
3. Tarea 3 — pruebas del cuestionario.
4. Tarea 4 — pruebas del Mentor.
5. Tarea 5 — accesibilidad.
6. Tarea 6 — responsive.
7. Tarea 7 — carga y errores.
8. Tarea 9 — documentación técnica.
9. Tarea 10 — deuda técnica.
10. Tarea 8 — propuesta de limpieza, sin borrar.

## Trabajo reservado para el modelo principal

No delegar temporalmente:

- rediseños completos;
- cambios en la visión o posicionamiento de SocioAI;
- arquitectura de memoria e IA;
- selección y enrutamiento de modelos;
- calidad del razonamiento de auditoría;
- prompts técnicos del Mentor;
- clasificación y priorización de riesgos;
- materialidad;
- interpretación de NIA, NIIF o regulación;
- migraciones o cambios de esquema;
- eliminación de módulos o datos;
- cambios en onboarding, rondas o resultado que alteren decisiones ya acordadas.

## Formato obligatorio de entrega del modelo económico

```text
Tarea ejecutada: [número y nombre]

Resultado:
[qué quedó hecho]

Archivos modificados:
- [archivo]

Pruebas ejecutadas:
- [comando]: [resultado]

Pendientes:
- [pendiente o “ninguno”]

Reservado para el modelo principal:
- [decisión o “ninguno”]

Me detengo aquí y no comienzo otra tarea sin autorización.
```

## Recomendación para ahorrar uso

- Mantener cada chat centrado en una sola tarea.
- No adjuntar nuevamente todos los documentos del cliente.
- No pedir auditorías generales del repositorio.
- Dar al modelo el número exacto de tarea.
- Abrir un chat nuevo si el contexto crece demasiado.
- Volver al modelo principal cuando aparezca una decisión de producto, auditoría, arquitectura o IA.
