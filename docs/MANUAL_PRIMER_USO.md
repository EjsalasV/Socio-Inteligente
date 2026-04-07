# Manual de Primer Uso - Socio AI

Este manual explica, paso a paso, como usar el sistema por primera vez.
Esta pensado para un auditor que entra por primera vez al flujo completo:
cliente -> datos -> analisis -> briefing -> hallazgos -> control de calidad -> reporte.

## 1. Objetivo del sistema

Socio AI te ayuda a:

1. Priorizar areas de riesgo con base en datos (TB y mayor).
2. Generar briefings por area con soporte normativo.
3. Estructurar hallazgos con criterio tecnico.
4. Controlar calidad antes de emitir.
5. Mantener trazabilidad entre respuesta, evidencia y norma.

## 2. Requisitos minimos

Antes de iniciar, confirma:

1. Python y dependencias instaladas (`requirements.txt` o `requirements.api.txt`).
2. Node.js instalado para frontend.
3. Archivo `.env` configurado en raiz del proyecto.
4. Clave de LLM configurada:
   - `DEEPSEEK_API_KEY` (recomendado en esta version), o
   - `OPENAI_API_KEY`.
5. Variable `ALLOWED_CLIENTES` configurada.
   - Si esta vacia, el login funciona pero no tendras acceso a clientes.

## 3. Levantar el sistema en local

En una terminal (backend):

```bash
uvicorn backend.main:app --reload --port 8000
```

En otra terminal (frontend):

```bash
npm --prefix frontend run dev
```

Frontend por defecto:

```text
http://localhost:3000
```

Backend por defecto:

```text
http://localhost:8000
```

## 4. Primer ingreso

1. Abre la pantalla de login.
2. Ingresa usuario y clave.
   - Por defecto de desarrollo (si no se cambio en `.env`):
     - usuario: `joaosalas123@gmail.com`
     - clave: `1234`
3. Inicia sesion.
4. Selecciona cliente en la vista de clientes.
5. Si no existe, crea un cliente nuevo y entra a onboarding.

## 5. Configuracion inicial de un cliente (onboarding)

En onboarding completa al menos:

1. Datos de cliente.
2. Marco contable (`niif_pymes` o `niif_completas`).
3. Periodo de trabajo.
4. Parametros de materialidad base.
5. Estado inicial de workflow.

Recomendacion: no avances de fase sin completar obligatorios de la fase actual.

## 6. Carga de datos base (obligatorio para analisis util)

Carga, como minimo:

1. `tb.xlsx` (trial balance).
2. `mayor.xlsx` (si aplica en tu flujo).

Sin TB no tendras ranking de riesgo confiable, y el briefing sera mas generico.

## 7. Flujo recomendado de trabajo diario

### Paso 1: Revisar dashboard y riesgo

1. Abre `dashboard`.
2. Abre `risk-engine`.
3. Confirma top de areas con mayor riesgo.

### Paso 2: Entrar a un area activa

1. Abre `areas/{cliente}/{area}`.
2. Revisa cuentas y aseveraciones vinculadas.
3. Marca checks de revision en cuentas clave.

### Paso 3: Generar briefing por area

1. Clic en `Generar Briefing`.
2. Revisa:
   - por que importa el area,
   - procedimientos sugeridos,
   - normativa activada,
   - chunks usados.
3. Usa `normas activadas` para validar soporte rapido.

### Paso 4: Estructurar hallazgos

1. Escribe la condicion detectada.
2. Clic en `Estructurar Hallazgo`.
3. Revisa condicion, criterio, causa, efecto y recomendacion.
4. Ajusta texto final antes de guardar en papeles/reportes.

### Paso 5: Registrar ahorro de tiempo (opcional pero recomendado)

1. Ingresa `Manual (min)` y `Con AI (min)`.
2. Clic en `Guardar Medicion`.
3. Esto alimenta metricas operativas de productividad.

## 8. Control de calidad antes de emitir

Usa el pre-check de calidad (revisor mixto):

1. Endpoint: `POST /api/quality/pre-emit-check`.
2. Resultado:
   - `status: blocked` -> no emitir todavia.
   - `status: ok` -> puede continuar con warnings si existen.

Reglas bloqueantes tipicas:

1. Afirmaciones criticas sin cobertura.
2. Hallazgos criticos abiertos sin plan/respuesta.
3. Conclusion tecnica insuficiente en riesgo alto.
4. Inconsistencia material con materialidad documentada.

## 9. Plantillas por fase y progresion

Antes de avanzar de fase:

1. Consulta plantilla:
   - `GET /workflow/{cliente_id}/phase-template`
2. Revisa `missing_required`.
3. Si falta algo critico, completa y registra cambios.
4. Avanza solo cuando `can_advance=true`.

Registro de cambios por campo:

- `POST /workflow/{cliente_id}/field-history`

## 10. Trazabilidad y soporte

Cada briefing/hallazgo guarda trazabilidad:

1. Norma usada.
2. Fuente/chunk.
3. Hash de chunk.
4. Area.
5. Timestamp.

Esto permite explicar de donde salio cada recomendacion.

## 11. Vigencia normativa mensual

La deteccion de cambios normativos se ejecuta de forma mensual (no por consulta).

Ejecucion manual:

```bash
python -m backend.jobs.monthly_normativa_refresh
```

Endpoint interno equivalente:

```text
POST /api/normativa/refresh-monthly
```

Si una norma citada tiene cambio pendiente, veras warning de vigencia.
No bloquea respuesta, pero baja confianza hasta revision del equipo.

## 12. Errores comunes y como resolverlos

### Error 401 / token expirado

Accion:

1. Cierra sesion.
2. Inicia sesion otra vez.

### "LLM no configurado"

Accion:

1. Configura `DEEPSEEK_API_KEY` en `.env`.
2. Reinicia backend.

### "Sin acceso a clientes" aunque login correcto

Accion:

1. Configura `ALLOWED_CLIENTES` en `.env`.
2. Usa `*` en desarrollo si necesitas acceso total.

### Briefing muy generico

Accion:

1. Verifica TB cargado.
2. Verifica marco y afirmaciones criticas en el area.
3. Revisa que RAG este indexado y con base normativa limpia.

## 13. Checklist rapido de primer dia

1. Login correcto.
2. Cliente seleccionado.
3. TB cargado.
4. Riesgo revisado.
5. Briefing generado en al menos 1 area.
6. 1 hallazgo estructurado.
7. Pre-check de calidad ejecutado.
8. Pendientes criticos identificados antes de emitir.

---

Version: V1.2  
Uso recomendado: auditor semisenior/senior en ejecucion y cierre.

