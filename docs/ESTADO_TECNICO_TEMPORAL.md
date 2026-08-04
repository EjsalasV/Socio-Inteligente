# Estado tecnico temporal

Fecha de ejecucion: 2026-08-04

Este documento registra una linea base tecnica reproducible para SocioAI, sin modificar comportamiento.

## Alcance revisado

- Scripts disponibles en `frontend/package.json`.
- Configuracion de pruebas y calidad en `pyproject.toml`.
- Dependencias del backend en `requirements.txt` y `backend/requirements.txt`.
- Estado actual de lint, compilacion del frontend y pruebas del backend.

## Scripts encontrados

### Frontend

Archivo: `frontend/package.json`

- `npm run dev` -> `next dev`
- `npm run build` -> `next build`
- `npm run start` -> `next start`
- `npm run lint` -> `eslint .`
- `npm run generate:types` -> `node ./scripts/generate-types.mjs`
- `npm run check:types-sync` -> genera tipos y valida que no haya diff en `lib/types.ts`

### Backend

No se encontraron scripts npm/pyproject dedicados para ejecucion de app o tests en el sentido de `package.json`.

Archivo: `pyproject.toml`

- `pytest` apunta a `tests`
- `addopts = "-v --tb=short"`
- cobertura configurada con umbral minimo de `60`

Dependencias relevantes:

- `requirements.txt`
- `backend/requirements.txt`

## Comandos ejecutados

```bash
cd frontend
npm run lint
```

Resultado:

- Exito con advertencias.
- 0 errores.
- 51 warnings.

Advertencias observadas:

- `@typescript-eslint/no-explicit-any`
- `react-hooks/exhaustive-deps`
- `@next/next/no-img-element`
- `no-restricted-syntax`
- `@typescript-eslint/no-unused-vars`
- `no-console`

```bash
cd frontend
npm run build
```

Resultado:

- Exito.
- Compilacion de Next.js completada correctamente.
- TypeScript ejecutado durante el build sin fallos.
- Generacion estatica completada.

```bash
python -m pytest tests -v
```

Resultado:

- Exito.
- `253 passed`
- `72 warnings`

Advertencias observadas durante las pruebas:

- `DeprecationWarning` por `fastapi.on_event`
- `DeprecationWarning` por `asyncio.iscoroutinefunction`
- `DeprecationWarning` por `datetime.utcnow()`
- `DeprecationWarning` por cookies por request en `starlette`
- `DeprecationWarning` por `HTTP_422_UNPROCESSABLE_ENTITY`

## Lectura tecnica

- El frontend esta funcional a nivel de lint y build.
- No hay errores de compilacion en el frontend.
- La bateria de backend esta verde.
- Hay deuda tecnica visible en warnings de lint y deprecations, pero no bloquea esta linea base.

## Comandos reproducibles

```bash
cd C:\Users\echoe\Desktop\Nuevo Socio AI\frontend
npm run lint
npm run build

cd C:\Users\echoe\Desktop\Nuevo Socio AI
python -m pytest tests -v
```

## Nota de conservacion

Durante esta tarea se respetaron los cambios existentes en el arbol de trabajo y no se corrigieron advertencias ni errores no solicitados.

## Flujo tecnico actual

### 1. Onboarding

- Entrada: `frontend/app/onboarding/[clienteId]/page.tsx`.
- Carga inicial:
  - `getPerfil(clienteId)` para leer el perfil base.
  - `GET /api/clientes/{clienteId}` para completar metadatos del cliente.
  - `getTiposEntidad()` para poblar el selector de tipo de entidad.
  - `getClienteDocumentos(clienteId)` para recuperar documentos de contexto.
- Guardado:
  - `updateCliente(...)` para metadatos basicos.
  - `savePerfil(clienteId, payload)` para persistir el perfil operativo.
  - `uploadClienteDocumento(...)` para documentos de contexto y periodos previos.
- Salida del flujo:
  - `router.push("/entity-profile/{clienteId}")` cuando el onboarding queda listo.
- IA:
  - este paso no llama IA; solo captura datos y documentos.

### 2. Cuestionario adaptativo y resultado del perfil

- Entrada: `frontend/app/entity-profile/[clienteId]/page.tsx`.
- Carga inicial:
  - `getEntityProfileDraft(clienteId)` -> `GET /api/entity-profile/{clienteId}/draft`.
- Guardado de respuestas:
  - `saveEntityProfileAnswers(clienteId, answers)` -> `PUT /api/entity-profile/{clienteId}/answers`.
  - El borrador se guarda en `data/clientes/{clienteId}/entity_profile_draft.json` y se actualiza de forma atomica.
- Pendientes:
  - `updateEntityProfilePending(clienteId, questionId, input)` -> `PUT /api/entity-profile/{clienteId}/pending/{questionId}`.
  - Persiste en el mismo `entity_profile_draft.json`.
- Analisis:
  - `analyzeEntityProfile(clienteId, force)` -> `POST /api/entity-profile/{clienteId}/analyze`.
  - Usa IA para construir `entity_summary`, `changes`, `prior_findings`, `risk_hypotheses` y `estimate_hypotheses`.
  - El analisis se guarda dentro del mismo borrador.
  - El backend respeta `AI_CLIENT_DATA_ENABLED`, `LM_STUDIO_BASE_URL`, `OPENAI_CHAT_MODEL` y `DEEPSEEK_*`.
- Confirmacion:
  - `confirmEntityProfile(clienteId)` -> `POST /api/entity-profile/{clienteId}/confirm`.
  - Tras confirmar, la UI navega a `"/socio-chat/{clienteId}"`.
- IA:
  - solo se llama en `analyzeEntityProfile(...)` y en la confirmacion derivada del resultado si ya existe analisis.
  - el guardado de respuestas y de pendientes no llama IA.

### 3. Mentor

- Entrada: `frontend/app/socio-chat/[clienteId]/page.tsx`.
- Carga inicial:
  - `useDashboard(clienteId)` -> `GET /dashboard/{clienteId}`.
  - `useRiskEngine(clienteId)` para areas criticas sugeridas.
  - `useWorkflow(clienteId)` para fase actual.
- Conversaciones:
  - `getChatConversations(clienteId)` -> `GET /chat/{clienteId}/conversations`.
  - `createChatConversation(clienteId)` -> `POST /chat/{clienteId}/conversations`.
  - `renameChatConversation(clienteId, conversationId, title)` -> `PATCH /chat/{clienteId}/conversations/{conversationId}`.
  - `deleteChatConversation(clienteId, conversationId)` -> `DELETE /chat/{clienteId}/conversations/{conversationId}`.
- Historial:
  - `getChatHistory(clienteId, conversationId)` -> `GET /chat/{clienteId}/history`.
  - El historial se guarda en `data/clientes/{clienteId}/chat_history.json`.
  - Las conversaciones se guardan en `data/clientes/{clienteId}/chat_conversations.json`.
- Envio de mensajes:
  - `postChat(clienteId, payload)` -> `POST /chat/{clienteId}`.
  - El backend guarda el mensaje del auditor y la respuesta del asistente en el historial.
- IA:
  - `POST /chat/{clienteId}` puede usar `rag_chat_service.generate_chat_response(...)`.
  - Si `USE_AUDITOR_PIPELINE_CHAT` esta activo, el backend puede pasar por `execute_pipeline(...)`.
  - Carga de conversaciones e historial no llama IA.

### 4. Estados principales del frontend

- Login: `isLoading`, `error`, `showPassword`.
- Onboarding: `loading`, `saving`, `error`, `success`.
- Cuestionario/resultado: `loading`, `saving`, `analyzing`, `roundStatus`, `reviewMode`, `pendingSavingId`, `questionIndex`.
- Mentor: `dashboardLoading`, `dashboardError`, `loadingConversations`, `loadingHistory`, `sending`, `chatNotice`, `showThread`, `profileOpen`, `mentorMode`.

### 5. Comportamiento ante errores

- `frontend/lib/api.ts` agrega auth y CSRF, y ante `401` limpia la sesion local.
- `authFetchJson(...)` y `authFetchBlob(...)` traducen errores HTTP a mensajes legibles.
- En UI:
  - Login muestra `role="alert"` si falla la autenticacion.
  - Mentor muestra banners inline para carga, historial y errores de chat.
  - El perfil muestra `role="alert"` o `role="status"` segun el caso.
- Errores esperados:
  - `404`: recurso o conversacion no encontrada.
  - `409`: conflicto de actualizacion.
  - `422`: validacion o estado del perfil incompleto.
  - `500` y `503`: fallo interno o servicio de IA no disponible.

### 6. Dato persistido

- Perfil base y onboarding: `data/clientes/{clienteId}/perfil.yaml`.
- Borrador del perfil de entidad: `data/clientes/{clienteId}/entity_profile_draft.json`.
- Conversaciones del Mentor: `data/clientes/{clienteId}/chat_conversations.json`.
- Historial del Mentor: `data/clientes/{clienteId}/chat_history.json`.
- Documentos de contexto: `data/clientes/{clienteId}/documentos_text/`.

## Inventario de deuda tecnica

### Bugs comprobados

| Hallazgo | Evidencia | Archivos afectados | Impacto | Recomendacion preliminar |
|---|---|---|---|---|
| Fallo de carga del onboarding sin feedback visible | El `catch` del `load()` en onboarding no asigna `error` ni renderiza un estado de fallo. | `frontend/app/onboarding/[clienteId]/page.tsx` | Si falla `getPerfil`, `getTiposEntidad` o `getClienteDocumentos`, la pantalla puede quedar en silencio o solo cambiar el estado interno. | Mostrar un estado de error recuperable con mensaje y accion de reintento. |

### Accesibilidad

| Hallazgo | Evidencia | Archivos afectados | Impacto | Recomendacion preliminar |
|---|---|---|---|---|
| Acciones de renombrar/eliminar en Mentor dependen de hover | Los botones usan `opacity-0 transition group-hover:opacity-100`. | `frontend/app/socio-chat/[clienteId]/page.tsx` | En pantallas tactiles o navegacion por teclado esas acciones no quedan igual de descubribles. | Hacer visibles las acciones en mobile y darles un menu explicito o texto accesible. |

### Seguridad

| Hallazgo | Evidencia | Archivos afectados | Impacto | Recomendacion preliminar |
|---|---|---|---|---|
| Token de autenticacion almacenado en `localStorage` y `sessionStorage` | `setSessionState` guarda `socio_auth_token` y `apiFetch` lo reutiliza como fallback. | `frontend/app/page.tsx`, `frontend/lib/auth-session.ts`, `frontend/lib/api.ts` | Aumenta la superficie frente a XSS si alguna pagina logra inyectar script. | Mantenerlo solo si el backend lo exige; documentar la justificacion y evaluar cookie HttpOnly como objetivo futuro. |

### Falta de pruebas

| Hallazgo | Evidencia | Archivos afectados | Impacto | Recomendacion preliminar |
|---|---|---|---|---|
| No hay cobertura automatica para errores de onboarding y estados de Mentor | El flujo de carga fallo se descubrio por inspeccion manual; no existe test especifico del caso. | `frontend/app/onboarding/[clienteId]/page.tsx`, `frontend/app/socio-chat/[clienteId]/page.tsx`, `frontend/app/entity-profile/[clienteId]/page.tsx` | Un cambio pequeño en mensajes o estados puede romper la visibilidad de errores sin ser detectado. | Agregar pruebas E2E o de componentes para carga fallida, 404, 409, 422 y 500. |

### Rendimiento

| Hallazgo | Evidencia | Archivos afectados | Impacto | Recomendacion preliminar |
|---|---|---|---|---|
| Carga inicial del Mentor compone varias consultas antes de estabilizar la pantalla | El componente depende de `useDashboard`, `useRiskEngine`, `useWorkflow`, conversaciones e historial. | `frontend/app/socio-chat/[clienteId]/page.tsx`, `frontend/lib/hooks/useDashboard.ts` | El primer render puede sentirse mas lento y sensible a latencia de red. | Medir TTFB/CLS del flujo y revisar si alguna consulta puede diferirse o cachearse mejor. |

### Duplicacion

| Hallazgo | Evidencia | Archivos afectados | Impacto | Recomendacion preliminar |
|---|---|---|---|---|
| Manejo de errores repetido entre pantallas | Varias pantallas construyen banners y mensajes similares con la misma logica de estado. | `frontend/app/page.tsx`, `frontend/app/socio-chat/[clienteId]/page.tsx`, `frontend/app/entity-profile/[clienteId]/page.tsx` | Dificulta mantener consistencia visual y de mensajes. | Consolidar patrones compartidos en helpers o componentes comunes sin cambiar el comportamiento. |

### Arquitectura

| Hallazgo | Evidencia | Archivos afectados | Impacto | Recomendacion preliminar |
|---|---|---|---|---|
| El perfil de entidad y el chat persisten estado en JSON por cliente | El perfil usa `entity_profile_draft.json`; el Mentor usa `chat_conversations.json` y `chat_history.json`. | `backend/services/entity_profile_service.py`, `backend/services/chat_conversation_service.py`, `backend/repositories/file_repository.py` | Funciona bien para desarrollo, pero concentra estado mutable en el filesystem y complica concurrencia y migracion futura. | Mantener como estado actual, pero planear abstraccion mas formal si aumenta la carga multiusuario. |

### Asuntos tecnicos de auditoria

| Hallazgo | Evidencia | Archivos afectados | Impacto | Recomendacion preliminar |
|---|---|---|---|---|
| La salida estructurada del analisis de perfil depende de un contrato JSON muy especifico | El prompt exige una forma exacta y el servicio sanitiza listas, referencias y confianza. | `backend/services/entity_profile_analysis_service.py` | Un cambio de formato del LLM puede degradar silenciosamente la calidad de la evidencia o vaciar campos. | Mantener validacion de esquema y pruebas de contrato sobre el JSON esperado. |
| Las decisiones del perfil quedan acopladas al borrador analitico | Las hipotesis se guardan y reaplican desde el mismo archivo del borrador. | `backend/services/entity_profile_service.py`, `backend/services/entity_profile_analysis_service.py` | Es practico hoy, pero mezcla conocimiento preliminar, analisis y decisiones en un solo artefacto. | Documentar claramente el contrato y considerar separacion futura si crece el flujo. |

## Medicion de carga del Mentor

### Contexto de la medicion

- Frontend local: `http://localhost:3000`.
- Backend local: `http://127.0.0.1:8000`.
- Cliente medido: `2025_01`, porque ese expediente ya tiene Trial Balance y Mayor cargados.
- Sesion usada: cookie `socio-auth` + `localStorage` con token valido.
- Ruta medida: `/socio-chat/2025_01`.

### Tiempos observados

- `DOMContentLoaded`: `1.15 s`.
- `load`: `1.19 s`.
- `first-paint` y `first-contentful-paint`: `0.92 s`.
- Hero del Mentor visible: `6.23 s`.
- Compositor de mensaje visible: `6.24 s`.

### Solicitudes observadas

- `GET /api/auth/me` x2.
- `GET /api/user/preferences`.
- `GET /api/chat/2025_01/conversations` x2.
- `GET /api/trial-balance/2025_01/status`.
- `GET /api/clientes` x2.
- `GET /api/workflow/2025_01` x2.
- `GET /api/dashboard/2025_01?areas_page=1&areas_page_size=8`.
- `GET /api/chat/2025_01/history?conversation_id=1129e26554cd411a9d98`.
- `GET /api/risk-engine/2025_01` x2.

### Lectura tecnica

- La solicitud que realmente desbloquea el shell del Mentor es `GET /api/dashboard/2025_01?areas_page=1&areas_page_size=8`; el hero y el compositor aparecen alrededor de `6.2 s`.
- `auth/me` se solicita dos veces por la validacion inicial de sesion y por la inicializacion de los hooks de la pagina.
- `clientes`, `workflow`, `risk-engine` y `chat/conversations` se repiten una vez cada uno, lo que sugiere consultas paralelas desde componentes distintos sin deduplicacion compartida.
- `chat/history` entra despues de resolver la conversacion reciente seleccionada.
- El `first contentful paint` ocurre antes del Mentor visible, asi que el primer render del layout no es el cuello de botella principal; el punto critico es la carga de datos del shell editorial.

### Oportunidades de mejora

- Compartir cache o coalescencia para `auth/me`, `clientes`, `workflow`, `risk-engine` y `chat/conversations`.
- Diferir `chat/history` hasta que la conversacion se abra o realmente se necesite.
- Revisar si el shell del Mentor puede mostrar una version parcial mientras termina de resolver el dashboard.

### Decisiones de producto o arquitectura a reservar

- Si el token de autenticacion debe seguir en `localStorage` para compatibilidad o migrar a un esquema mas estricto.
- Si las acciones de conversacion en Mentor deben permanecer visibles siempre en mobile o moverse a un menu explicito.
- Si el estado del perfil y del chat debe seguir en archivos JSON por cliente o migrar a una capa persistente mas formal.
