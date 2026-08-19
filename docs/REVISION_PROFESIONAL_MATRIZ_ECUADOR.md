# Paquete de revision profesional: matriz Ecuador

## Objetivo

Validar profesionalmente la metodologia usada para seleccionar versiones candidatas de NIIF, NIIF para las PYMES y NIA en encargos de companias sujetas al regimen societario general de la SCVS.

Esta revision no aprueba tratamientos contables, riesgos de auditoria ni conclusiones de un encargo. Tampoco habilita citas normativas. Las licencias, localizadores y revisiones individuales de cada fuente permanecen como controles separados.

## Archivos sujetos a revision

- `data/conocimiento_normativo/supercias/matriz_versiones_ecuador.yaml`
- `data/conocimiento_normativo/supercias/reglamento_auditoria_externa.md`
- `data/conocimiento_normativo/manifest_piloto_ingresos_cxc.yaml`
- `data/conocimiento_normativo/supercias/matriz_versiones_ecuador_revision.yaml`

## Afirmaciones que debe validar el revisor

1. El alcance se limita a companias bajo SCVS societario general y excluye bancos, entidades financieras, SEPS y otros reguladores especiales.
2. Para NIIF completas, los pronunciamientos nuevos o modificados se incorporan automaticamente y se seleccionan segun su fecha de vigencia internacional para el inicio del periodo.
3. La SCVS adopta NIIF para las PYMES por referencia y sin modificaciones; la edicion 2015 corresponde hasta 2026 y la tercera edicion 2025 desde 2027.
4. La SCVS adopta NIA por referencia y sin modificaciones; la NIA 240 Revisada 2025 corresponde a periodos iniciados desde el 15 de diciembre de 2026.
5. La NIA 315 Revisada 2019 corresponde a periodos iniciados desde el 15 de diciembre de 2021.
6. Las propuestas de revision de NIA 330 y NIA 500 de 2026 no son requerimientos vigentes.
7. La adopcion anticipada no se infiere: exige evidencia de la opcion permitida, decision documentada y evaluacion jurisdiccional segun corresponda.
8. La Resolucion SCVS-INC-DNCDN-2019-0009 y el Reglamento sobre Auditoria Externa no tienen reformas posteriores que cambien estas conclusiones para el alcance definido.

## Fuentes institucionales para el cotejo

- IFRS Foundation, perfil jurisdiccional de Ecuador: https://www.ifrs.org/use-around-the-world/use-of-ifrs-standards-by-jurisdiction/view-jurisdiction/ecuador/
- IFAC, perfil de Ecuador actualizado en febrero de 2026: https://www.ifac.org/about-ifac/membership/profile/ecuador
- SCVS, Resolucion SCVS-INC-DNCDN-2019-0009: https://www.supercias.gob.ec/bd_supercias/descargas/lotaip/a2/2019/OCTUBRE/RO_No._39.pdf
- Reglamento sobre Auditoria Externa: https://www.gob.ec/sites/default/files/regulations/2020-03/Documento_REGLAMENTO-AUDITOR%C3%8DA-EXTERNA.pdf
- IFRS Foundation, tercera edicion de NIIF para las PYMES: https://www.ifrs.org/news-and-events/news/2025/02/iasb-issues-major-update-smes-accounting-standard/
- IAASB, NIA 240 Revisada: https://www.iaasb.org/publications/isa-240-revised-auditor-s-responsibilities-relating-fraud-audit-financial-statements
- IAASB, NIA 315 Revisada 2019: https://www.iaasb.org/news-events/2019-12/iaasb-enhances-and-modernizes-isa-315-more-robust-risk-assessment

## Registro requerido

El profesional debe completar en `matriz_versiones_ecuador_revision.yaml`:

- `status`: `approved` o `rejected`;
- `reviewer_name` y `reviewer_role`;
- `review_date` en formato `AAAA-MM-DD`;
- `scope`, indicando exactamente que afirmaciones reviso;
- `conclusion`, incluyendo reservas o excepciones;
- `evidence_reference`, por ejemplo acta, ticket o memorando conservado por la organizacion.

No debe modificar manualmente `matrix_sha256`. Si cambia la matriz, se debe generar un registro nuevo y repetir la revision.

## Comprobacion

```powershell
python scripts/check_normative_matrix_review.py
python scripts/check_normative_matrix_review.py --require-approved
```

El segundo comando debe fallar mientras la revision este pendiente, rechazada, incompleta o vinculada a otra version de la matriz.
