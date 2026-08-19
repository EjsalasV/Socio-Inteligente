# Diagnostico del corpus piloto

**Corte del manifiesto:** 2026-08-09
**Piloto:** Ingresos y Cuentas por Cobrar
**Estado:** DIAGNOSTICO AUTOMATICO; NO EQUIVALE A REVISION PROFESIONAL

## Resumen

- Entradas requeridas: 9
- Archivos encontrados: 9
- Fuentes habilitadas para citar: 0
- Archivos con indicadores de codificacion: 0
- Fuentes por identificar: 0

## Inventario priorizado

| Prioridad | Fuente | Archivo | Estado | Cita | Brechas detectadas |
|---:|---|---|---|---|---|
| 1 | NIA-240 | `data/conocimiento_normativo/nias/nia_240.md` | official_sources_identified | No | falta_localizador; licencia_pendiente |
| 2 | NIIF-15 | `data/conocimiento_normativo/niif_completas/niif_15.md` | official_sources_identified | No | falta_localizador; licencia_pendiente |
| 3 | NIA-315 | `data/conocimiento_normativo/nias/nia_315.md` | official_sources_identified | No | falta_localizador; licencia_pendiente |
| 4 | NIA-330 | `data/conocimiento_normativo/nias/nia_330.md` | official_sources_identified | No | falta_localizador; licencia_pendiente |
| 5 | NIA-500 | `data/conocimiento_normativo/nias/nia_500.md` | official_sources_identified | No | falta_localizador; licencia_pendiente |
| 6 | NIIF-9 | `data/conocimiento_normativo/niif_completas/niif_9.md` | official_sources_identified | No | falta_localizador; licencia_pendiente |
| 7 | NIIF-PYMES-23 | `data/conocimiento_normativo/niif_pymes/seccion_23.md` | official_sources_identified | No | falta_localizador; licencia_pendiente |
| 8 | NIIF-PYMES-11 | `data/conocimiento_normativo/niif_pymes/seccion_11.md` | official_sources_identified | No | falta_localizador; licencia_pendiente |
| 9 | ECUADOR-ADOPCION | `data/conocimiento_normativo/supercias/reglamento_auditoria_externa.md` | official_sources_identified | No | Sin brechas automaticas |

## Orden de trabajo

1. NIA 240: obtener acceso autorizado al texto oficial y cotejar localizadores por parrafo.
2. Solicitar permisos a IFAC y licencia de producto a IFRS Foundation; hasta entonces excluir texto oficial e indexar solo metadatos e interpretacion profesional propia.
3. Obtener y cotejar el texto consolidado del Reglamento sobre Auditoria Externa y las reformas posteriores al instructivo NIIF de 2019.
4. Obtener revision profesional local documentada de la matriz ecuatoriana de versiones y sus reglas de adopcion anticipada.
5. Confirmar el regulador de cada entidad y crear matrices separadas solo cuando el piloto necesite cubrir regimenes especiales.
6. Cotejar localizadores internacionales contra copias autorizadas y documentar la aprobacion humana por fuente y version.

## Regla de aprobacion

Una fuente solo cambia a `verified` mediante revision humana documentada. Que el archivo exista o no presente brechas automaticas no demuestra autoridad, vigencia, integridad, licencia ni aplicabilidad.

## Reproducir

```powershell
python scripts/audit_pilot_normative_corpus.py
```
