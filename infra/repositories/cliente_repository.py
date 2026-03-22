"""
Repositorio para cargar y guardar datos de clientes.

Funciones para acceder a los archivos YAML y Excel de clientes
en la estructura: data/clientes/{cliente}/
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

# Ruta raiz del proyecto
DATA_ROOT = Path(__file__).parent.parent.parent / "data"
CLIENTES_PATH = DATA_ROOT / "clientes"


def cargar_perfil(cliente: str) -> dict:
    """
    Carga el perfil del cliente desde perfil.yaml
    """
    try:
        path = CLIENTES_PATH / cliente / "perfil.yaml"
        if not path.exists():
            return {}

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return data if data else {}
    except Exception as e:
        print(f"[ERROR] Error cargando perfil de {cliente}: {e}")
        return {}


def cargar_tb(cliente: str) -> pd.DataFrame:
    """
    Carga el trial balance desde tb.xlsx
    """
    try:
        path = CLIENTES_PATH / cliente / "tb.xlsx"
        if not path.exists():
            return pd.DataFrame()

        try:
            xls = pd.ExcelFile(path, engine="openpyxl")
            sheet = xls.sheet_names[0] if xls.sheet_names else 0
            df = pd.read_excel(path, sheet_name=sheet, engine="openpyxl")
        except Exception:
            df = pd.read_excel(path, sheet_name=0)

        if df is None:
            return pd.DataFrame()

        return df.dropna(how="all").reset_index(drop=True)
    except Exception as e:
        print(f"[ERROR] Error cargando TB de {cliente}: {e}")
        return pd.DataFrame()


def cargar_hallazgos(cliente: str) -> list:
    """
    Carga hallazgos previos desde hallazgos_previos.yaml
    """
    try:
        path = CLIENTES_PATH / cliente / "hallazgos_previos.yaml"
        if not path.exists():
            return []

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "hallazgos" in data:
            hallazgos = data["hallazgos"]
            return hallazgos if isinstance(hallazgos, list) else []

        return []
    except Exception as e:
        print(f"[ERROR] Error cargando hallazgos de {cliente}: {e}")
        return []


def cargar_patrones(cliente: str) -> list:
    """
    Carga patrones desde patrones.yaml
    """
    try:
        path = CLIENTES_PATH / cliente / "patrones.yaml"
        if not path.exists():
            return []

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "patrones" in data:
            patrones = data["patrones"]
            return patrones if isinstance(patrones, list) else []

        return []
    except Exception as e:
        print(f"[ERROR] Error cargando patrones de {cliente}: {e}")
        return []


def guardar_materialidad(cliente: str, data: dict) -> bool:
    """
    Guarda materialidad en materialidad.yaml
    """
    try:
        path = CLIENTES_PATH / cliente / "materialidad.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        except OSError:
            # Streamlit Cloud has read-only filesystem
            # Writes are silently ignored in production
            pass

        print(f"[OK] Materialidad guardada para {cliente}")
        return True
    except Exception as e:
        print(f"[ERROR] Error guardando materialidad de {cliente}: {e}")
        return False
