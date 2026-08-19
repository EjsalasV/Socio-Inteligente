# Contexto minimo: cura normativa del piloto

Actualizado: 2026-08-09

## Producto fijo

SocioAI es un mentor de auditoria con trazabilidad, no un reemplazo del juicio profesional ni un gestor de papeles de trabajo tipo Caseware. El piloto cubre solo Ingresos y Cuentas por Cobrar. Si no esta documentado, no existe.

## Regla de calidad

Una fuente no puede sustentar citas hasta tener autoridad, version, vigencia, jurisdiccion, aplicacion local, URL oficial, localizador exacto, derecho de uso y revision humana. Ante una brecha, el sistema orienta o se abstiene y declara el limite.

## Estado actual

- NIA 240, 315, 330 y 500: fuentes y vigencias internacionales identificadas; la adopcion SCVS por referencia esta documentada en la matriz. Faltan copias autorizadas, localizadores, permisos y aprobacion humana.
- NIIF 15 y NIIF 9: fuentes y vigencias internacionales identificadas; la incorporacion automatica para SCVS general esta documentada. Faltan copias autorizadas, localizadores, licencia comercial y aprobacion humana.
- NIIF para PYMES Secciones 23 y 11: segunda edicion 2015 hasta 2026 y tercera edicion 2025 desde 2027, salvo adopcion anticipada documentada. Faltan localizadores, licencia comercial y aprobacion humana.
- Ecuador - marco contable: Resolucion SCVS-INC-DNCDN-2019-0009 cotejada; perfiles IFRS Foundation e IFAC documentan incorporacion automatica o por referencia. El perfil IFRS data de 2016, por lo que la matriz conserva revision humana obligatoria.
- Ecuador - auditoria externa: articulo 1 del reglamento base de 2016 y perfil IFAC 2026 respaldan adopcion NIA por referencia; falta cotejar un texto consolidado con todas las reformas.
- Matriz temporal: `data/conocimiento_normativo/supercias/matriz_versiones_ecuador.yaml` resuelve versiones candidatas solo para SCVS societario general. Reguladores especiales quedan fuera de alcance.
- Revision profesional: existe un registro separado vinculado al SHA-256 de la matriz. Permanece `pending`; un cambio posterior de la matriz invalida automaticamente cualquier aprobacion anterior.
- Quality gate: una fuente marcada `verificado` tambien debe documentar revisor, rol, fecha, alcance y evidencia para poder habilitar citas.
- Licencias: IFAC requiere permiso previo para procesar sus materiales con IA; IFRS Foundation requiere licencia para uso continuo en un producto. El texto oficial queda fuera del RAG, pero las ocho fichas propias del piloto operan como `interpretacion_profesional`, sin citas y con cotejo obligatorio.
- Textos oficiales ecuatorianos: el articulo 107 del Codigo Ingenios los excluye de proteccion por derecho de autor; se mantienen controles de integridad, vigencia, localizador y revision humana.
- Adopcion anticipada: nunca se infiere; requiere evidencia documental definida por la matriz y decision humana.
- Modelo temporal de almacenamiento: metadatos, referencias oficiales y resumenes propios; no texto normativo completo.
- Casos de comportamiento: la suite YAML esta conectada a un guard determinista del chat. Las citas exactas no verificadas y las conclusiones automaticas se bloquean antes de llamar al LLM; la orientacion sin cita sigue permitida.
- Control de salida: el chat valida atribuciones normativas, cantidades de seleccion y hechos del expediente. Si el primer borrador falla, permite una sola reparacion conjunta; si persiste una oracion insegura, la retira y revalida el resto. Si el contenido restante tampoco pasa, bloquea la respuesta completa.
- Verificador de hechos: contrasta afirmaciones con respuestas confirmadas del perfil, distingue antecedentes de hechos del periodo activo y exige lenguaje condicional para hipotesis no documentadas.
- Trazabilidad de calidad: cada consulta registra hashes de pregunta y respuesta, fuentes, proveedor, modelo, controles aplicados, reparaciones, redacciones y decision de publicacion. No duplica el texto completo ni expone razonamiento interno.
- Alpha local: aviso global de producto no final, consentimiento especifico, uso exclusivo de datos ficticios o anonimizados, prohibicion de reutilizar datos de clientes para entrenamiento o criterio compartido, feedback por respuesta y encuesta de sesion con metricas de utilidad, aprendizaje, ahorro y disposicion de pago.
- Guia de testers: `docs/GUIA_ACEPTACION_ALPHA_INGRESOS_CXC.md` contiene 15 casos y criterios de aprobacion para el ciclo piloto.
- Pipeline estructurado: diferencia `[FUENTE n]` verificada de `[ORIENTACION n]`, bloquea citas estructuradas inseguras, oculta la salida cruda bloqueada y expone solo citas realmente usadas.
- Solicitudes: existen borradores IFAC e IFRS con alcance limitado al MVP y campos `[[CONFIRMAR]]` para identidad, seguridad, proveedor, retencion, usuarios y modelo comercial.
- Siguiente paso tecnico: ejecutar el conjunto controlado de aceptacion del piloto y exponer la trazabilidad afirmacion/fuente cuando existan fuentes autorizadas para cita.
- Siguiente paso externo: registrar la opinion profesional sobre la matriz, completar los campos empresariales/tecnicos de las solicitudes y presentarlas por OPRI y el cuestionario IFRS.

## Archivos a leer

- `docs/PRODUCTO_SELLADO.md`
- `docs/ROADMAP_MVP_90_DIAS.md`
- `docs/CORPUS_PILOTO_DIAGNOSTICO.md`
- `data/conocimiento_normativo/manifest_piloto_ingresos_cxc.yaml`
- `data/conocimiento_normativo/casos_prueba_piloto.yaml`

## Comandos de verificacion

```powershell
python scripts/audit_pilot_normative_corpus.py
python scripts/check_normative_matrix_review.py
python -m pytest tests/test_normative_version_service.py tests/test_normative_quality_gate.py tests/test_rag_cache_service.py
git diff --check
```

## Instruccion para retomar con pocos tokens

Abrir una tarea nueva y pedir: "Lee `docs/CONTEXTO_MINIMO_CURA_NORMATIVA.md` y ejecuta el siguiente paso sin redefinir el producto".
