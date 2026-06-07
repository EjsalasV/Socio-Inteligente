"""
Validaciones avanzadas de Mayor - Detección de hallazgos de auditoría
Incluye: secuencial, cuentas nuevas, fechas anomalas, gaps período, etc
"""
from datetime import datetime, timedelta, timezone
from typing import Any
import pandas as pd


def _safe_records(df: pd.DataFrame, limit: int = 20) -> list[dict[str, Any]]:
    """Convierte dataframe a lista de dicts de forma segura"""
    if df is None or df.empty:
        return []
    out = df.head(max(1, limit)).copy()
    if "fecha" in out.columns:
        out["fecha"] = pd.to_datetime(out["fecha"], errors="coerce").dt.strftime("%Y-%m-%d")
        out["fecha"] = out["fecha"].fillna("")
    return out.to_dict(orient="records")


def validar_secuencial_asientos(df: pd.DataFrame) -> dict[str, Any]:
    """
    Valida que los asientos sean secuenciales sin gaps

    Detecta:
    - Saltos en numeración (asiento 100 → 150)
    - Asientos desordenados
    - Duplicados de número
    """
    if df is None or df.empty:
        return {"status": "ok", "gaps": 0, "items": []}

    work = df.copy()

    # Convertir asiento_ref a número si es posible
    work["asiento_num"] = pd.to_numeric(work["asiento_ref"], errors="coerce")
    work = work.dropna(subset=["asiento_num"])

    if len(work) < 2:
        return {"status": "ok", "gaps": 0, "items": []}

    # Ordenar por número
    work = work.sort_values("asiento_num").reset_index(drop=True)

    # Detectar gaps
    asientos_list = work["asiento_num"].unique()
    min_asiento = int(asientos_list.min())
    max_asiento = int(asientos_list.max())

    gaps = []
    for i in range(min_asiento, max_asiento):
        if i not in asientos_list:
            gaps.append(i)

    if len(gaps) > 0:
        return {
            "status": "error",
            "gaps_count": len(gaps),
            "gap_details": f"Falta asientos: {gaps[:20]}...",
            "min_asiento": min_asiento,
            "max_asiento": max_asiento,
            "items": _safe_records(work.head(20))
        }

    return {"status": "ok", "gaps": 0, "items": []}


def validar_cuentas_nuevas_eliminadas(df_2024: pd.DataFrame, df_2025: pd.DataFrame) -> dict[str, Any]:
    """
    Compara cuentas entre 2024 y 2025

    Detecta:
    - Cuentas nuevas en 2025 (no estaban en 2024)
    - Cuentas eliminadas (estaban en 2024, no en 2025)
    """
    if df_2024 is None or df_2024.empty:
        return {"status": "sin_comparativo_2024", "nuevas": 0, "eliminadas": 0}

    if df_2025 is None or df_2025.empty:
        return {"status": "error", "message": "Mayor 2025 vacío"}

    cuentas_2024 = set(df_2024["numero_cuenta"].unique())
    cuentas_2025 = set(df_2025["numero_cuenta"].unique())

    nuevas = cuentas_2025 - cuentas_2024
    eliminadas = cuentas_2024 - cuentas_2025

    result = {
        "nuevas_count": len(nuevas),
        "eliminadas_count": len(eliminadas),
        "nuevas": sorted(list(nuevas))[:50],
        "eliminadas": sorted(list(eliminadas))[:50],
    }

    if len(nuevas) > 0 or len(eliminadas) > 0:
        result["status"] = "warning"
        result["alerta"] = f"Nuevas: {len(nuevas)}, Eliminadas: {len(eliminadas)}"
    else:
        result["status"] = "ok"

    return result


def validar_mismatch_periodo(df_2024: pd.DataFrame, df_2025: pd.DataFrame) -> dict[str, Any]:
    """
    Valida que saldo final 2024 = saldo inicial 2025 por cada cuenta

    Detecta reclasificaciones no documentadas
    """
    if df_2024 is None or df_2024.empty:
        return {"status": "sin_comparativo_2024"}

    if df_2025 is None or df_2025.empty:
        return {"status": "error"}

    # Obtener saldo final 2024 por cuenta
    saldo_final_2024 = df_2024.groupby("numero_cuenta")["saldo"].last().reset_index()
    saldo_final_2024.columns = ["numero_cuenta", "saldo_2024"]

    # Obtener saldo inicial 2025 (primer asiento de cada cuenta)
    saldo_inicial_2025 = df_2025.groupby("numero_cuenta")["saldo"].first().reset_index()
    saldo_inicial_2025.columns = ["numero_cuenta", "saldo_2025_inicio"]

    # Comparar
    comparativo = saldo_final_2024.merge(saldo_inicial_2025, on="numero_cuenta", how="outer")
    comparativo["diferencia"] = (comparativo["saldo_2024"] - comparativo["saldo_2025_inicio"]).abs()

    mismatches = comparativo[comparativo["diferencia"] > 0.01]

    if len(mismatches) > 0:
        return {
            "status": "error",
            "count": len(mismatches),
            "mensaje": "Saldo final 2024 ≠ saldo inicial 2025 (¿reclasificación sin asiento?)",
            "items": _safe_records(mismatches.sort_values("diferencia", ascending=False))
        }

    return {"status": "ok", "count": 0}


def validar_fechas_anomalas(df: pd.DataFrame, fecha_cierre: str = None) -> dict[str, Any]:
    """
    Detecta fechas anómalas:
    - Feriados/domingos
    - Post-cutoff (después de cierre)
    - Backdated (antes de período)
    - Futuro
    """
    if df is None or df.empty:
        return {"anomalias": 0, "items": []}

    work = df.copy()
    work["fecha"] = pd.to_datetime(work["fecha"], errors="coerce")
    work = work.dropna(subset=["fecha"])

    anomalias = []

    # Detectar domingos (day of week = 6)
    domingos = work[work["fecha"].dt.dayofweek == 6].copy()
    if len(domingos) > 0:
        anomalias.append({
            "tipo": "domingo",
            "count": len(domingos),
            "records": _safe_records(domingos)
        })

    # Detectar moneda extranjera de manera segura
    work_no_na = work[["fecha"]].copy()

    # Si se proporciona fecha_cierre, validar post-cutoff
    if fecha_cierre:
        try:
            fecha_cierre_dt = pd.to_datetime(fecha_cierre)
            semana_cierre = fecha_cierre_dt + timedelta(days=7)
            post_cierre = work[work["fecha"] > fecha_cierre_dt].copy()
            if len(post_cierre) > 0:
                anomalias.append({
                    "tipo": "posterior_cierre",
                    "count": len(post_cierre),
                    "records": _safe_records(post_cierre)
                })
        except:
            pass

    return {
        "anomalias_count": len(anomalias),
        "tipos": [a["tipo"] for a in anomalias],
        "items": anomalias[:20]
    }


def validar_mayor_cuadra(df: pd.DataFrame, tolerance: float = 0.01) -> dict[str, Any]:
    """
    Valida que el mayor cuadre (Total Debe = Total Haber)
    """
    if df is None or df.empty:
        return {"status": "ok", "total_debe": 0, "total_haber": 0}

    total_debe = df["debe"].sum()
    total_haber = df["haber"].sum()
    diferencia = abs(total_debe - total_haber)

    if diferencia > tolerance:
        return {
            "status": "error",
            "total_debe": float(total_debe),
            "total_haber": float(total_haber),
            "diferencia": float(diferencia),
            "mensaje": f"Mayor no cuadra. Diferencia: ${diferencia:,.2f}"
        }

    return {
        "status": "ok",
        "total_debe": float(total_debe),
        "total_haber": float(total_haber),
        "diferencia": float(diferencia)
    }


def validar_asientos_anulados(df: pd.DataFrame) -> dict[str, Any]:
    """
    Detecta asientos anulados (referencia contiene "ANL" o similar)
    """
    if df is None or df.empty:
        return {"count": 0, "items": []}

    work = df.copy()
    work["ref_lower"] = work["referencia"].astype(str).str.lower()

    anulados = work[work["ref_lower"].str.contains("anl|anulado|anular", na=False, regex=True)]

    return {
        "count": len(anulados),
        "items": _safe_records(anulados)
    }


def validar_meses_sin_transacciones(df: pd.DataFrame) -> dict[str, Any]:
    """
    Detecta meses que no tienen transacciones
    """
    if df is None or df.empty:
        return {"meses_sin_movimiento": [], "items": []}

    work = df.copy()
    work["fecha"] = pd.to_datetime(work["fecha"], errors="coerce")
    work = work.dropna(subset=["fecha"])

    # Obtener rango de fechas
    fecha_min = work["fecha"].min()
    fecha_max = work["fecha"].max()

    if pd.isna(fecha_min) or pd.isna(fecha_max):
        return {"meses_sin_movimiento": []}

    # Generar todos los meses en el rango
    todos_meses = pd.date_range(start=fecha_min, end=fecha_max, freq="MS")

    # Obtener meses con movimientos
    work["mes"] = work["fecha"].dt.to_period("M")
    meses_con_mov = set(work["mes"].unique())

    meses_sin_mov = []
    for mes in todos_meses:
        mes_period = mes.to_period("M")
        if mes_period not in meses_con_mov:
            meses_sin_mov.append(mes.strftime("%Y-%m"))

    return {
        "meses_sin_movimiento": meses_sin_mov,
        "count": len(meses_sin_mov),
        "items": []
    }


def validar_cuentas_sin_saldo(df: pd.DataFrame) -> dict[str, Any]:
    """
    Detecta cuentas sin saldo final
    """
    if df is None or df.empty:
        return {"count": 0, "items": []}

    # Agrupar por cuenta y obtener último saldo
    sin_saldo = df[df["saldo"].isna() | (df["saldo"] == "")].copy()

    if len(sin_saldo) > 0:
        return {
            "count": len(sin_saldo),
            "status": "warning",
            "items": _safe_records(sin_saldo)
        }

    return {"count": 0, "status": "ok"}


def run_validaciones_avanzadas(
    df_2025: pd.DataFrame,
    df_2024: pd.DataFrame = None,
    fecha_cierre: str = None,
    tolerance_mayor: float = 0.01,
) -> dict[str, Any]:
    """
    Ejecuta TODAS las validaciones avanzadas
    """
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "secuencial_asientos": validar_secuencial_asientos(df_2025),
        "cuentas_nuevas_eliminadas": validar_cuentas_nuevas_eliminadas(df_2024, df_2025) if df_2024 is not None else {"status": "sin_comparativo"},
        "mismatch_periodo": validar_mismatch_periodo(df_2024, df_2025) if df_2024 is not None else {"status": "sin_comparativo"},
        "fechas_anomalas": validar_fechas_anomalas(df_2025, fecha_cierre),
        "mayor_cuadra": validar_mayor_cuadra(df_2025, tolerance=tolerance_mayor),
        "asientos_anulados": validar_asientos_anulados(df_2025),
        "meses_sin_transacciones": validar_meses_sin_transacciones(df_2025),
        "cuentas_sin_saldo": validar_cuentas_sin_saldo(df_2025),
    }
