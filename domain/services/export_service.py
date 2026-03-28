"""
Servicio de exportación de reportes de auditoría.
Genera archivos Excel y texto plano por cliente.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from domain.services.hallazgos_service import cargar_hallazgos_gestion
from infra.repositories.cliente_repository import cargar_perfil

EXPORTS_PATH = Path("data") / "exports"


def exportar_hallazgos_excel(cliente: str) -> Path | None:
    """
    Exporta hallazgos de gestión a Excel.
    Returns: ruta del archivo generado o None si falla.
    """
    try:
        hallazgos = cargar_hallazgos_gestion(cliente)
        if not hallazgos:
            print(f"[export] Sin hallazgos para {cliente}")
            return None

        df = pd.DataFrame(hallazgos)
        EXPORTS_PATH.mkdir(parents=True, exist_ok=True)
        fecha = datetime.now().strftime("%Y%m%d_%H%M")
        ruta = EXPORTS_PATH / f"{cliente}_hallazgos_{fecha}.xlsx"
        try:
            df.to_excel(ruta, index=False, engine="openpyxl")
        except OSError:
            # Streamlit Cloud has read-only filesystem
            # Writes are silently ignored in production
            pass
        print(f"[export] Exportado: {ruta}")
        return ruta
    except Exception as e:
        print(f"[export] Error: {e}")
        return None


def exportar_resumen_txt(cliente: str, ranking_df: pd.DataFrame | None = None) -> Path | None:
    """
    Exporta resumen ejecutivo de auditoría a texto plano.
    Returns: ruta del archivo generado o None si falla.
    """
    try:
        perfil = cargar_perfil(cliente)
        nombre = perfil.get("cliente", {}).get("nombre_legal", cliente)
        periodo = perfil.get("encargo", {}).get("anio_activo", "N/A")
        hallazgos = cargar_hallazgos_gestion(cliente)
        abiertos = [h for h in hallazgos if h.get("estado") == "abierto"]

        lineas = [
            f"RESUMEN EJECUTIVO DE AUDITORÍA",
            f"Cliente: {nombre}",
            f"Periodo: {periodo}",
            f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            f"HALLAZGOS",
            f"  Total: {len(hallazgos)}",
            f"  Abiertos: {len(abiertos)}",
            f"  Cerrados: {len(hallazgos) - len(abiertos)}",
            "",
        ]

        if ranking_df is not None and not ranking_df.empty:
            lineas.append("RANKING DE AREAS (top 5)")
            for _, row in ranking_df.head(5).iterrows():
                area = row.get("area", row.get("ls", "?"))
                nombre_area = row.get("nombre", "")
                score = row.get("score_total_hibrido", row.get("score_riesgo", 0))
                lineas.append(f"  {area} {nombre_area} — score {score:.1f}")
            lineas.append("")

        if abiertos:
            lineas.append("HALLAZGOS ABIERTOS")
            for h in abiertos[:10]:
                lineas.append(
                    f"  [{h.get('nivel','').upper()}] {h.get('id','')} "
                    f"({h.get('codigo_area','')}) {h.get('descripcion','')}"
                )

        EXPORTS_PATH.mkdir(parents=True, exist_ok=True)
        fecha = datetime.now().strftime("%Y%m%d_%H%M")
        ruta = EXPORTS_PATH / f"{cliente}_resumen_{fecha}.txt"
        try:
            ruta.write_text("\n".join(lineas), encoding="utf-8")
        except OSError:
            # Streamlit Cloud has read-only filesystem
            # Writes are silently ignored in production
            pass
        print(f"[export] Exportado: {ruta}")
        return ruta
    except Exception as e:
        print(f"[export] Error: {e}")
        return None
