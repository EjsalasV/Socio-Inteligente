"""
Grupo Criteria Service - Conecta el criterio experto por grupo del balance
(data/criterio_experto/grupos/) al motor de análisis y al chat.

El mapa maestro (MAPA_GRUPOS_NORMAS_VINCULOS.yml) define los grupos, sus
normas, sus módulos ejecutables y los vínculos cruzados. Este servicio:
- Resuelve a qué grupo pertenece un área del TB (por código o nombre)
- Carga el módulo del grupo y sus vínculos ACTIVOS
- Construye bloques compactos de criterio para inyectar en prompts de IA
"""

from __future__ import annotations

import logging
import re
import unicodedata
from pathlib import Path
from typing import Any

import yaml

LOGGER = logging.getLogger("socio_ai.grupo_criteria")

ROOT = Path(__file__).resolve().parents[2]
CRITERIA_ROOT = ROOT / "data" / "criterio_experto"
MAPA_PATH = CRITERIA_ROOT / "grupos" / "MAPA_GRUPOS_NORMAS_VINCULOS.yml"

# El grupo ingresos vive en niif15/ (framework completo); el mapa lo referencia
# como directorio, no como archivo. Override explícito al documento resumen.
GRUPO_MODULO_OVERRIDES: dict[str, str] = {
    "ingresos": "niif15/01_framework/NIIF15_FRAMEWORK.md",
}

# Palabras clave de nombres de cuenta/área → grupo. Complementa el match por
# código porque los planes de cuentas de los clientes no son uniformes.
GRUPO_KEYWORDS: dict[str, tuple[str, ...]] = {
    "efectivo": ("efectivo", "caja", "banco"),
    "cxc": ("cuentas por cobrar", "cartera", "clientes", "documentos por cobrar", "deterioro cartera"),
    "inventarios": ("inventario", "existencia", "mercaderia", "mercadería", "materia prima", "producto terminado"),
    "ppe": ("propiedad planta", "propiedades planta", "activo fijo", "maquinaria", "depreciacion", "depreciación", "vehiculo", "vehículo", "edificio"),
    "intangibles": ("intangible", "plusvalia", "plusvalía", "marca", "licencia de software"),
    "propiedades_inversion": ("propiedad de inversion", "propiedades de inversion", "propiedad de inversión", "propiedades de inversión"),
    "impuestos_activos": ("impuesto", "credito tributario", "crédito tributario", "iva", "retencion", "retención", "diferido", "sri"),
    "cxp": ("cuentas por pagar", "proveedores", "documentos por pagar"),
    "obligaciones_financieras": ("prestamo", "préstamo", "obligacion financiera", "obligación financiera", "sobregiro", "deuda bancaria"),
    "provisiones": ("provision", "provisión", "contingencia", "litigio"),
    "beneficios_empleados": ("jubilacion patronal", "jubilación patronal", "desahucio", "beneficios definidos"),
    "patrimonio": ("patrimonio", "capital social", "reserva", "resultados acumulados", "aportes futuras"),
    "ingresos": ("ingreso", "venta", "servicios prestados"),
    "costo_ventas_gastos": ("costo de venta", "costo de ventas", "gasto", "compras"),
    "nomina": ("nomina", "nómina", "sueldo", "salario", "beneficios sociales", "decimo", "décimo", "iess", "remuneracion", "remuneración", "participacion trabajadores", "participación trabajadores"),
}

_MAPA_CACHE: dict[str, Any] = {"mtime": None, "data": None}


def _normalize(text: str) -> str:
    lowered = str(text or "").strip().lower()
    decomposed = unicodedata.normalize("NFD", lowered)
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def load_mapa() -> dict[str, Any]:
    """Carga el mapa maestro con cache por mtime."""
    try:
        mtime = MAPA_PATH.stat().st_mtime_ns
    except Exception:
        return {}
    if _MAPA_CACHE["mtime"] == mtime and isinstance(_MAPA_CACHE["data"], dict):
        return _MAPA_CACHE["data"]
    try:
        data = yaml.safe_load(MAPA_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        LOGGER.warning("No se pudo cargar el mapa de grupos: %s", exc)
        return {}
    if not isinstance(data, dict):
        return {}
    _MAPA_CACHE["mtime"] = mtime
    _MAPA_CACHE["data"] = data
    return data


def list_grupos() -> dict[str, Any]:
    mapa = load_mapa()
    grupos = mapa.get("grupos") if isinstance(mapa.get("grupos"), dict) else {}
    out: dict[str, Any] = {}
    for key, info in grupos.items():
        if not isinstance(info, dict):
            continue
        out[key] = {
            "nombre": info.get("nombre", key),
            "codigo_area": str(info.get("codigo_area", "") or ""),
            "normas": info.get("normas", []),
            "estado": info.get("estado", ""),
            "modulo": info.get("modulo", ""),
        }
    return out


def resolve_grupo(area_codigo: str = "", area_nombre: str = "") -> str:
    """
    Resuelve el grupo del balance para un área del TB.
    Match por código (exacto o por prefijo en ambas direcciones) y por
    palabras clave del nombre. Devuelve "" si no hay match.
    """
    mapa = load_mapa()
    grupos = mapa.get("grupos") if isinstance(mapa.get("grupos"), dict) else {}
    code = str(area_codigo or "").strip()
    name = _normalize(area_nombre)

    if code:
        for key, info in grupos.items():
            if not isinstance(info, dict):
                continue
            grupo_code = str(info.get("codigo_area", "") or "").strip()
            if not grupo_code:
                continue
            if code == grupo_code or code.startswith(grupo_code) or grupo_code.startswith(code):
                return key

    if name:
        # Orden de especificidad: keywords más largas primero para que
        # "jubilacion patronal" gane sobre "patronal"/"patrimonio" etc.
        matches: list[tuple[int, str]] = []
        for key, keywords in GRUPO_KEYWORDS.items():
            if key not in grupos:
                continue
            for kw in keywords:
                if _normalize(kw) in name:
                    matches.append((len(kw), key))
        if matches:
            matches.sort(reverse=True)
            return matches[0][1]
    return ""


def _extract_sections(content: str, wanted_keywords: tuple[str, ...]) -> str:
    """Extrae del módulo .md solo las secciones '## ...' cuyo título matchea."""
    if not content:
        return ""
    parts = re.split(r"(?m)^## ", content)
    selected: list[str] = []
    for part in parts[1:]:
        title = _normalize(part.split("\n", 1)[0])
        if any(_normalize(kw) in title for kw in wanted_keywords):
            selected.append("## " + part.strip())
    return "\n\n".join(selected)


def get_grupo_criteria(grupo: str) -> dict[str, Any]:
    """
    Devuelve el criterio completo de un grupo: contenido del módulo,
    normas y vínculos (marcando cuáles están activos).
    """
    mapa = load_mapa()
    grupos = mapa.get("grupos") if isinstance(mapa.get("grupos"), dict) else {}
    key = _normalize(grupo).replace(" ", "_")
    info = grupos.get(key)
    if not isinstance(info, dict):
        return {"found": False, "grupo": key, "content": "", "vinculos": [], "normas": []}

    modulo_rel = GRUPO_MODULO_OVERRIDES.get(key) or str(info.get("modulo", "") or "")
    content = ""
    if modulo_rel and modulo_rel not in {"pendiente"}:
        modulo_path = CRITERIA_ROOT / modulo_rel
        if modulo_path.is_file():
            content = _read_text(modulo_path)

    vinculos: list[dict[str, Any]] = []
    raw_vinculos = info.get("vinculos") if isinstance(info.get("vinculos"), list) else []
    for v in raw_vinculos:
        if not isinstance(v, dict):
            continue
        vinculos.append(
            {
                "con": str(v.get("con", "") or ""),
                "chequeo": str(v.get("chequeo", "") or ""),
                "activo": bool(v.get("activo", False)),
            }
        )

    return {
        "found": bool(content),
        "grupo": key,
        "nombre": info.get("nombre", key),
        "normas": info.get("normas", []),
        "estado": info.get("estado", ""),
        "source_path": modulo_rel,
        "content": content,
        "vinculos": vinculos,
    }


def build_grupo_context_block(grupo: str, *, compact: bool = True, max_chars: int = 6000) -> str:
    """
    Bloque de contexto de UN grupo para inyectar en prompts:
    normas + (riesgos, matriz, vínculos del módulo) + chequeos activos del mapa.
    En modo compact solo van las secciones ejecutables, no el módulo completo.
    """
    data = get_grupo_criteria(grupo)
    if not data.get("found") and not data.get("vinculos"):
        return ""

    normas = ", ".join(str(n) for n in data.get("normas", []) or [])
    lines: list[str] = [f"[GRUPO: {data.get('nombre', grupo)}" + (f" | Normas: {normas}]" if normas else "]")]

    content = str(data.get("content") or "")
    if content:
        if compact:
            extracted = _extract_sections(
                content, ("riesgos", "matriz", "vinculos", "errores comunes")
            )
            lines.append(extracted or content[:max_chars])
        else:
            lines.append(content)

    activos = [v for v in data.get("vinculos", []) if v.get("activo") and v.get("chequeo")]
    if activos:
        lines.append("CHEQUEOS CRUZADOS OBLIGATORIOS (vínculos activos):")
        for v in activos:
            lines.append(f"- vs. {v['con']}: {v['chequeo']}")

    block = "\n\n".join(lines).strip()
    if len(block) > max_chars:
        block = block[:max_chars].rsplit("\n", 1)[0] + "\n[... criterio truncado]"
    return block


def detect_grupos_from_accounts(account_names: list[str], limit: int = 5) -> list[str]:
    """
    Detecta qué grupos están presentes en un TB a partir de los nombres de
    cuenta. Devuelve grupos con módulo construido, ordenados por frecuencia.
    """
    counts: dict[str, int] = {}
    for raw_name in account_names or []:
        grupo = resolve_grupo(area_nombre=str(raw_name))
        if grupo:
            counts[grupo] = counts.get(grupo, 0) + 1
    if not counts:
        return []
    ranked = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
    result: list[str] = []
    for grupo, _freq in ranked:
        if get_grupo_criteria(grupo).get("found"):
            result.append(grupo)
        if len(result) >= limit:
            break
    return result


def build_analysis_criteria_block(
    account_names: list[str],
    *,
    max_grupos: int = 4,
    max_chars_total: int = 14000,
) -> str:
    """
    Bloque de criterio experto para el analizador inteligente de TB:
    los grupos detectados en el balance, cada uno con sus riesgos, matriz
    riesgo→hallazgo y chequeos cruzados activos.
    """
    grupos = detect_grupos_from_accounts(account_names, limit=max_grupos)
    if not grupos:
        return ""
    per_grupo_budget = max(2000, max_chars_total // max(len(grupos), 1))
    blocks: list[str] = []
    for grupo in grupos:
        block = build_grupo_context_block(grupo, compact=True, max_chars=per_grupo_budget)
        if block:
            blocks.append(block)
    if not blocks:
        return ""
    header = (
        "EXPERT AUDIT CRITERIA (criterio experto por grupo del balance):\n"
        "Usa estos riesgos, matrices y chequeos cruzados como lente principal del análisis. "
        "Los CHEQUEOS CRUZADOS son obligatorios: valida la coherencia entre grupos "
        "(corte, márgenes, cuadres globales, eco tributario) contra los saldos reales."
    )
    return header + "\n\n" + "\n\n---\n\n".join(blocks)
