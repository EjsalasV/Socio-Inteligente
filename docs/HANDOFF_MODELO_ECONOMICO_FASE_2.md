# Plan para modelo económico — Fase 2

Esta fase continúa después del cierre validado en `docs/CIERRE_MODELO_ECONOMICO.md`.

El modelo económico debe ejecutar **una tarea por vez**, detenerse y esperar autorización. No debe hacer commit ni push.

## Prompt inicial

```text
Continúa el mantenimiento de SocioAI en:

C:\Users\echoe\Desktop\Nuevo Socio AI

Antes de actuar, lee completamente:

- docs/PRODUCTO_SOCIOAI_GUI_MAESTRA.md
- docs/HANDOFF_MODELO_ECONOMICO.md
- docs/CIERRE_MODELO_ECONOMICO.md
- docs/HANDOFF_MODELO_ECONOMICO_FASE_2.md

Revisa también las instrucciones AGENTS.md que existan y ejecuta `git status --short`.

Trabaja únicamente en la tarea de Fase 2 que yo indique. No continúes automáticamente con otra.

Reglas:

- No cambies la visión, navegación ni identidad visual de SocioAI.
- No rediseñes pantallas.
- No cambies prompts, materialidad, riesgos, normas ni razonamiento de auditoría.
- No cambies arquitectura de IA, modelos, memoria ni consumo de tokens.
- No alteres clientes, documentos, bases locales ni preferencias.
- No ejecutes llamadas reales a modelos de IA.
- Usa mocks en pruebas de frontend y backend.
- No agregues dependencias sin necesidad demostrada.
- No borres archivos ni limpies el worktree.
- No hagas commit, push, merge, reset, checkout o despliegue.
- Conserva cambios existentes que no pertenezcan a tu tarea.

Para cada tarea:

1. Reproduce o documenta el estado inicial.
2. Implementa el cambio mínimo.
3. Ejecuta pruebas específicas.
4. Ejecuta lint y build si tocaste frontend.
5. Revisa el diff de tus archivos.
6. Actualiza `docs/CIERRE_MODELO_ECONOMICO_FASE_2.md`.
7. Detente y espera revisión.

No empieces todavía. Confirma los límites y pregúntame qué número de tarea ejecutar.
```

## Tarea 11 — Error recuperable en onboarding

Objetivo: corregir el bug documentado donde la carga inicial del onboarding puede fallar sin feedback suficiente.

Debe:

- mostrar un mensaje visible y accesible;
- ofrecer `Reintentar`;
- conservar la navegación para volver a Clientes;
- distinguir fallo de carga y fallo de guardado;
- no borrar información ya ingresada;
- añadir pruebas con APIs simuladas.

No debe cambiar las preguntas, documentos requeridos ni diseño general.

Prompt:

```text
Ejecuta únicamente la Tarea 11 de docs/HANDOFF_MODELO_ECONOMICO_FASE_2.md. Implementa error recuperable en onboarding con pruebas simuladas y detente.
```

## Tarea 12 — E2E del cuestionario adaptativo

Objetivo: cubrir el recorrido del cuestionario sin usar IA ni datos reales.

Casos:

- una pregunta visible por vez;
- respuesta obligatoria antes de continuar;
- Anterior conserva respuestas;
- Evaluar muestra estado de procesamiento;
- API simulada puede devolver ronda 2;
- ausencia de vacíos abre el resultado final;
- error 422 conserva respuestas;
- Modificar respuestas vuelve a la entrevista.

Usar Playwright ya instalado. No añadir otra librería E2E.

## Tarea 13 — E2E del resultado del perfil

Objetivo: proteger la validación profesional previa al Mentor.

Casos:

- hechos, antecedentes, cambios e hipótesis permanecen separados;
- las secciones expandibles funcionan por teclado;
- aceptar, descartar y dejar pendiente usan el endpoint correcto;
- un error de decisión queda visible;
- Confirmar navega al Mentor solo con respuesta exitosa;
- un error de confirmación no cambia de pantalla.

Todas las API deben ser simuladas.

## Tarea 14 — Acciones de conversaciones accesibles

Objetivo: resolver el hallazgo de acciones dependientes de hover.

Debe:

- mantener Renombrar y Eliminar disponibles mediante teclado;
- hacerlas descubribles en pantallas táctiles;
- conservar el diseño de Expediente Vivo;
- no cambiar las confirmaciones ni endpoints;
- ampliar las pruebas E2E del Mentor.

No debe crear un rediseño del historial.

## Tarea 15 — Pruebas unitarias de errores de interfaz

Objetivo: probar `frontend/lib/ui-errors.ts`.

Cubrir:

- sesión expirada;
- 404;
- 409;
- 422;
- 500;
- error HTTP desconocido;
- Error estándar;
- string;
- valor desconocido con fallback;
- ausencia de filtración del detalle técnico para errores 500.

Si el frontend no dispone de runner unitario, primero debe proponer la alternativa más pequeña y detenerse antes de instalar dependencias.

## Tarea 16 — Contratos HTTP del Mentor y perfil

Objetivo: ampliar pruebas backend de autorización y errores, sin modificar contratos existentes.

Cubrir:

- cliente autorizado y no autorizado;
- conversación inexistente;
- sesión de Mentor de otro usuario;
- perfil incompleto;
- decisión sobre hipótesis inexistente;
- payload inválido;
- respuestas vacías;
- estructura estable del envelope de error.

No debe tocar prompts ni servicios LLM.

## Tarea 17 — Estados vacíos consistentes

Objetivo: revisar solamente estados vacíos funcionales.

Pantallas:

- Mentor sin conversaciones;
- Mentor sin alertas de riesgo;
- Perfil sin fuentes anteriores;
- Perfil sin hipótesis;
- Biblioteca sin resultados;
- Guía de procedimientos sin coincidencias.

Debe reutilizar componentes y estilos existentes. No rediseñar.

## Tarea 18 — Higiene de artefactos locales

Objetivo: evitar que resultados de pruebas vuelvan a aparecer como cambios Git.

Puede proponer o añadir reglas específicas en `.gitignore` para:

- `.playwright-mcp/`;
- `frontend/test-results/`;
- `frontend/playwright-report/`;
- `frontend/tmp/`;
- capturas de verificación en la raíz;
- carpetas temporales conocidas.

Antes de cambiar `.gitignore`, debe comprobar que ninguna ruta contenga documentación o evidencia que el proyecto quiera versionar. No debe borrar archivos existentes.

## Tarea 19 — Medición de carga del Mentor

Objetivo: medir, no rediseñar, la carga inicial.

Debe registrar:

- solicitudes realizadas al abrir Mentor;
- cuáles son bloqueantes;
- solicitudes duplicadas;
- tiempos aproximados con backend local;
- render inicial y aparición del contenido principal;
- oportunidades de diferir o cachear.

Entregable: sección nueva en `docs/ESTADO_TECNICO_TEMPORAL.md`.

No debe cambiar código de producción en esta tarea.

## Tarea 20 — Auditoría de dependencias y deprecaciones

Objetivo: preparar decisiones futuras sin actualizar paquetes.

Debe:

- listar dependencias directas desactualizadas;
- identificar vulnerabilidades reportadas por herramientas locales;
- clasificar advertencias de FastAPI, Starlette, SQLAlchemy y Python;
- indicar impacto y dificultad;
- separar actualización segura, migración y cambio de arquitectura.

No debe ejecutar actualizaciones, migraciones ni cambios masivos.

## Orden recomendado

1. Tarea 11.
2. Tarea 12.
3. Tarea 13.
4. Tarea 14.
5. Tarea 15.
6. Tarea 16.
7. Tarea 17.
8. Tarea 18.
9. Tarea 19.
10. Tarea 20.

Después de cada tres tareas, volver al modelo revisor antes de continuar. Los puntos de revisión sugeridos son:

- después de 11–13;
- después de 14–16;
- después de 17–20.

## Formato del cierre de Fase 2

El modelo debe mantener:

`docs/CIERRE_MODELO_ECONOMICO_FASE_2.md`

Con esta estructura:

```text
# Cierre del modelo económico — Fase 2

## Tareas completadas
## Archivos modificados por tarea
## Pruebas ejecutadas
## Problemas corregidos
## Problemas pendientes
## Cambios que requieren revisión principal
## Posibles cambios fuera de alcance
## Estado de Git
```

No debe hacer commit ni push. La integración siempre queda a cargo del modelo revisor.
