# Decision de licencias del corpus piloto

Actualizado: 2026-08-09

## Decision operativa

Mientras no exista permiso o licencia documentada, SocioAI no incorpora el cuerpo oficial de las NIA ni de las NIIF al indice RAG. Puede recuperar fichas de interpretacion profesional interna redactadas en lenguaje propio, siempre que no reproduzcan extractos ni pretendan sustituir la norma.

Esto permite explicar como trabajar, que preguntar y como documentar, ademas de identificar la fuente y version candidata. No permite reproducir, resumir automaticamente desde el PDF ni sustituir el contenido oficial.

## IFAC e IAASB

La politica oficial para IA exige autorizacion previa cuando materiales IFAC se cargan, procesan, convierten a formatos legibles por maquina, usan como referencia, integran en prompts, embeddings o herramientas que generan contenido profesional. La regla aplica a usos internos, externos, comerciales y no comerciales.

Estado del piloto: `prior_written_permission_required`.

Accion externa: presentar en OPRI una solicitud que describa el uso en SocioAI, almacenamiento, proveedores de modelos, retencion, seguridad, usuarios, paises, contenido solicitado y modelo comercial.

## IFRS Foundation

La IFRS Foundation permite referencia privada o profesional, pero no reproduccion ni suministro de las Normas a terceros. El uso continuo de su material dentro de un producto o servicio requiere un acuerdo de licencia.

Estado del piloto: `product_license_required`.

Accion externa: completar el cuestionario de licenciatario describiendo exactamente si se desea texto completo, extractos, localizadores, traducciones o solamente enlaces y metadatos.

## Normativa oficial ecuatoriana

El articulo 107 del Codigo Ingenios establece que las disposiciones legales y reglamentarias, actos, decretos, acuerdos, resoluciones y otros textos oficiales no son objeto de proteccion por derecho de autor.

Estado del piloto: `official_text_not_copyright_protected`.

Esto no elimina los controles de integridad, version, vigencia, fuente oficial, localizador exacto ni revision humana.

## Implementacion

- Registro: `data/conocimiento_normativo/licencias_piloto.yaml`.
- Las ocho fichas del piloto: `modo_ingesta: interpretacion_profesional` y `origen_contenido: interpretacion_profesional_interna`.
- Los demas archivos internacionales heredados permanecen en `metadata_only` salvo permiso explicito o reclasificacion humana como interpretacion propia.
- Cada fragmento de interpretacion lleva una advertencia interna de orientacion, no cita y cotejo obligatorio.
- El quality gate reporta `ingesta_restringida_sin_metadata_only` si alguien intenta activar texto completo sin resolver la restriccion.
- Ninguna de estas decisiones habilita citas automaticamente.

## Fuentes oficiales

- IFAC, politica de IA: https://www.ifac.org/who-we-are/code-conduct
- IFAC, propiedad intelectual: https://www.ifac.org/ifac-intellectual-property
- IFAC OPRI: https://apps.ifac.org/opri/
- IFRS Foundation, propiedad intelectual: https://www.ifrs.org/legal/intellectual-property/
- IFRS Foundation, adopcion y copyright: https://www.ifrs.org/use-around-the-world/adoption-and-copyright/
- Codigo Ingenios, articulo 107: https://www.derechosintelectuales.gob.ec/wp-content/uploads/downloads/2021/enero/a_2_16_codigo_ingenios_enero_2021.pdf
