Plantillas DOCX opcionales para render documental.

Archivos soportados:
- `carta_control_interno.docx`
- `notas_niif_pymes.docx`

Si no existen, el sistema usa un renderer por defecto (`template_version = v1-default`).

Contrato de template:
- Definido en `template_contracts.yaml`.
- Campos fijos: `template_version`, `document_type`, `placeholders_supported`, `required_sections`, `optional_sections`.

Trazabilidad de modo de template:
- `template_mode = custom` cuando existe archivo `.docx` en esta carpeta.
- `template_mode = default` cuando no existe template y se usa renderer base.
- `template_mode = fallback` cuando falla el renderer DOCX y se degrada salida.
