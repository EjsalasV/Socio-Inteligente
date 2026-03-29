"""
Unit tests for core SocioAI modules:
- domain/services/estado_area_yaml.py
- domain/services/leer_perfil.py
- infra/repositories/cliente_repository.py
- analysis/ranking_areas.py
"""

from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pandas as pd
import pytest

from domain.services.leer_perfil import (
    cargar_perfil as leer_perfil_compat,
    leer_perfil,
    obtener_cliente,
    obtener_encargo,
    obtener_materialidad,
    obtener_nombre_cliente,
    obtener_sector,
    validar_perfil_basico,
)
from infra.repositories import cliente_repository
from analysis import ranking_areas

# ══════════════════════════════════════════════════════════════
# MODULE 1 — estado_area_yaml.py
# ══════════════════════════════════════════════════════════════

from domain.services.estado_area_yaml import (
    cargar_estado_area,
    estructura_area_vacia,
    extraer_hallazgos_abiertos,
    guardar_estado_area,
    obtener_notas_area,
    obtener_pendientes_area,
    obtener_procedimientos_area,
    ruta_estado_area,
)


class TestEstadoAreaYaml:
    def test_estructura_area_vacia_campos(self):
        data = estructura_area_vacia(" 425.2 ")
        assert data["codigo"] == "425.2"
        assert data["procedimientos"] == []
        assert data["hallazgos_abiertos"] == []
        assert data["notas"] == []
        assert data["pendientes"] == []
        assert "_fuente_yaml" in data

    def test_ruta_estado_area(self):
        ruta = ruta_estado_area("cliente_demo", "130")
        s = str(ruta)
        assert "cliente_demo" in s
        assert "areas" in s
        assert s.endswith("130.yaml")

    def test_cargar_estado_area_no_existe(self):
        fake_path = Path("data/clientes/x/areas/999.yaml")
        with (
            patch("domain.services.estado_area_yaml.ruta_estado_area", return_value=fake_path),
            patch("pathlib.Path.exists", return_value=False),
        ):
            out = cargar_estado_area("x", "999")
        assert out["codigo"] == "999"
        assert out["procedimientos"] == []

    def test_cargar_estado_area_yaml_dict(self):
        fake_path = Path("data/clientes/x/areas/130.yaml")
        contenido = {
            "codigo": "130",
            "estado_area": "en_revision",
            "notas": ["ok"],
        }
        with (
            patch("domain.services.estado_area_yaml.ruta_estado_area", return_value=fake_path),
            patch("pathlib.Path.exists", return_value=True),
            patch(
                "builtins.open",
                mock_open(read_data="codigo: '130'\nestado_area: en_revision\nnotas:\n  - ok\n"),
            ),
            patch("domain.services.estado_area_yaml.yaml.safe_load", return_value=contenido),
        ):
            out = cargar_estado_area("x", "130")

        assert out["codigo"] == "130"
        assert out["estado_area"] == "en_revision"
        assert out["notas"] == ["ok"]
        assert out["_fuente_yaml"]

    def test_cargar_estado_area_yaml_invalido(self):
        fake_path = Path("data/clientes/x/areas/bad.yaml")
        with (
            patch("domain.services.estado_area_yaml.ruta_estado_area", return_value=fake_path),
            patch("pathlib.Path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data="- a\n- b\n")),
            patch("domain.services.estado_area_yaml.yaml.safe_load", return_value=["a", "b"]),
        ):
            with pytest.raises(ValueError):
                cargar_estado_area("x", "bad")

    def test_guardar_estado_area_no_io_real(self):
        fake_path = Path("data/clientes/x/areas/130.yaml")
        mock_file = mock_open()

        with (
            patch("domain.services.estado_area_yaml.ruta_estado_area", return_value=fake_path),
            patch.object(Path, "mkdir", return_value=None),
            patch("builtins.open", mock_file),
            patch("domain.services.estado_area_yaml.yaml.safe_dump") as mock_dump,
        ):
            ruta = guardar_estado_area(
                "x", "130", {"estado_area": "ejecutado", "_fuente_yaml": "tmp"}
            )

        assert str(ruta).endswith("130.yaml")
        args, kwargs = mock_dump.call_args
        payload = args[0]
        assert payload["codigo"] == "130"
        assert payload["estado_area"] == "ejecutado"
        assert "fecha_actualizacion" in payload
        assert "_fuente_yaml" not in payload

    def test_extraer_hallazgos_abiertos(self):
        estado = {
            "hallazgos_abiertos": [
                "Hallazgo A",
                {"descripcion": "Hallazgo B", "estado": "abierto"},
                {"descripcion": "Hallazgo C", "estado": "cerrado"},
                {"descripcion": " ", "estado": "pendiente"},
            ]
        }
        out = extraer_hallazgos_abiertos(estado)
        assert "Hallazgo A" in out
        assert "Hallazgo B" in out
        assert "Hallazgo C" not in out

    def test_getters_estado_area(self):
        estado = {
            "procedimientos": [{"id": "p1"}],
            "notas": ["nota", "", "  "],
            "pendientes": ["pendiente 1", ""],
        }
        assert obtener_procedimientos_area(estado) == [{"id": "p1"}]
        assert obtener_notas_area(estado) == ["nota"]
        assert obtener_pendientes_area(estado) == ["pendiente 1"]


# ══════════════════════════════════════════════════════════════
# MODULE 2 — leer_perfil.py
# ══════════════════════════════════════════════════════════════


PERFIL_VALIDO = {
    "cliente": {
        "nombre_legal": "ABC Corp S.A.",
        "nombre_corto": "ABC",
        "ruc": "1790000000001",
        "sector": "comerciales",
        "tipo_entidad": "SOCIEDAD_ANONIMA",
    },
    "encargo": {
        "anio_activo": 2025,
        "marco_referencial": "NIIF",
        "tipo_encargo": "auditoria",
    },
    "materialidad": {
        "estado_materialidad": "preliminar",
        "preliminar": {
            "materialidad_global": 100000,
            "materialidad_desempeno": 75000,
            "error_trivial": 5000,
        },
    },
}


class TestLeerPerfil:
    def test_leer_perfil_none_si_vacio(self):
        with patch("domain.services.leer_perfil.repo_cargar_perfil", return_value={}):
            assert leer_perfil("cliente_x") is None

    def test_leer_perfil_valido(self):
        with patch("domain.services.leer_perfil.repo_cargar_perfil", return_value=PERFIL_VALIDO):
            out = leer_perfil("cliente_x")
        assert out is not None
        assert out["cliente"]["nombre_legal"] == "ABC Corp S.A."

    def test_leer_perfil_invalido(self):
        with patch("domain.services.leer_perfil.repo_cargar_perfil", return_value={"cliente": {}}):
            assert leer_perfil("cliente_x") is None

    def test_compat_cargar_perfil_alias(self):
        with patch("domain.services.leer_perfil.repo_cargar_perfil", return_value=PERFIL_VALIDO):
            out = leer_perfil_compat("cliente_x")
        assert out is not None

    def test_getters_perfil(self):
        assert obtener_cliente(PERFIL_VALIDO)["nombre_legal"] == "ABC Corp S.A."
        assert obtener_encargo(PERFIL_VALIDO)["marco_referencial"] == "NIIF"
        assert obtener_materialidad(PERFIL_VALIDO)["estado_materialidad"] == "preliminar"
        assert obtener_nombre_cliente(PERFIL_VALIDO) == "ABC Corp S.A."
        assert obtener_sector(PERFIL_VALIDO) == "comerciales"

    def test_validar_perfil_basico(self):
        validar_perfil_basico(PERFIL_VALIDO)
        with pytest.raises(ValueError):
            validar_perfil_basico("no_dict")
        with pytest.raises(ValueError):
            validar_perfil_basico({"cliente": {}, "encargo": {}})


# ══════════════════════════════════════════════════════════════
# MODULE 3 — cliente_repository.py
# ══════════════════════════════════════════════════════════════


class TestClienteRepository:
    def test_cargar_perfil_ok(self):
        m = mock_open(read_data="cliente:\n  nombre_legal: ABC\n")
        with (
            patch.object(Path, "exists", return_value=True),
            patch("builtins.open", m),
            patch(
                "infra.repositories.cliente_repository.yaml.safe_load",
                return_value={"cliente": {"nombre_legal": "ABC"}},
            ),
        ):
            out = cliente_repository.cargar_perfil("abc")
        assert out == {"cliente": {"nombre_legal": "ABC"}}

    def test_cargar_perfil_no_existe(self):
        with patch.object(Path, "exists", return_value=False):
            out = cliente_repository.cargar_perfil("abc")
        assert out == {}

    def test_cargar_tb_ok(self):
        df = pd.DataFrame({"a": [1], "b": [2]})
        excel_obj = MagicMock()
        excel_obj.sheet_names = ["Hoja1"]
        with (
            patch.object(Path, "exists", return_value=True),
            patch("infra.repositories.cliente_repository.pd.ExcelFile", return_value=excel_obj),
            patch("infra.repositories.cliente_repository.pd.read_excel", return_value=df),
        ):
            out = cliente_repository.cargar_tb("abc")
        assert isinstance(out, pd.DataFrame)
        assert len(out) == 1

    def test_cargar_hallazgos_variantes(self):
        m = mock_open(read_data="hallazgos: []")
        with (
            patch.object(Path, "exists", return_value=True),
            patch("builtins.open", m),
            patch(
                "infra.repositories.cliente_repository.yaml.safe_load",
                return_value={"hallazgos": [1, 2]},
            ),
        ):
            out = cliente_repository.cargar_hallazgos("abc")
        assert out == [1, 2]

    def test_cargar_patrones_variantes(self):
        m = mock_open(read_data="patrones: []")
        with (
            patch.object(Path, "exists", return_value=True),
            patch("builtins.open", m),
            patch(
                "infra.repositories.cliente_repository.yaml.safe_load",
                return_value={"patrones": ["x"]},
            ),
        ):
            out = cliente_repository.cargar_patrones("abc")
        assert out == ["x"]

    def test_guardar_materialidad_ok(self):
        m = mock_open()
        with patch("builtins.open", m), patch.object(Path, "mkdir", return_value=None):
            ok = cliente_repository.guardar_materialidad("abc", {"m": 1})
        assert ok is True


# ══════════════════════════════════════════════════════════════
# MODULE 4 — ranking_areas.py
# ══════════════════════════════════════════════════════════════


class TestRankingAreas:
    def test_seleccionar_filas_area_por_ls_exacto(self):
        df = pd.DataFrame(
            {
                "ls": ["14", "200", "14"],
                "codigo": ["140", "200", "141"],
                "saldo_actual": [10, 20, 30],
            }
        )
        out, method = ranking_areas.seleccionar_filas_area_por_ls(df, "14")
        assert method == "ls_exact"
        assert len(out) == 2
        assert set(out["ls"].astype(str)) == {"14"}

    def test_seleccionar_filas_no_broad_match_si_ls_presente(self):
        df = pd.DataFrame(
            {
                "ls": ["14", "200"],
                "codigo": ["140", "200"],
                "saldo_actual": [10, 20],
            }
        )
        out, method = ranking_areas.seleccionar_filas_area_por_ls(df, "1")
        assert out.empty
        assert method == "ls_exact_no_match"

    def test_calcular_ranking_none_si_tb_vacio(self):
        with patch("analysis.ranking_areas.leer_tb", return_value=pd.DataFrame()):
            out = ranking_areas.calcular_ranking_areas("cliente_x")
        assert out is None

    def test_calcular_ranking_basico(self):
        tb = pd.DataFrame(
            {
                "ls": ["14", "200", "14"],
                "codigo": ["140", "200", "141"],
                "saldo_actual": [1000, -500, 250],
                "nombre": ["Inv A", "Pat", "Inv B"],
            }
        )
        areas = [
            {
                "codigo": "14",
                "titulo": "Inversiones no corrientes",
                "clase": "Activo",
                "categoria_general": "Activo",
            },
            {
                "codigo": "200",
                "titulo": "Patrimonio",
                "clase": "Patrimonio",
                "categoria_general": "Patrimonio",
            },
            {"codigo": "1", "titulo": "PPE", "clase": "Activo", "categoria_general": "Activo"},
        ]

        with (
            patch("analysis.ranking_areas.leer_tb", return_value=tb),
            patch("analysis.ranking_areas.calcular_variaciones", return_value=pd.DataFrame()),
            patch(
                "analysis.ranking_areas.leer_perfil",
                return_value={"cliente": {"sector": "holding"}},
            ),
            patch(
                "analysis.ranking_areas.calcular_materialidad",
                return_value={"materialidad_desempeno": 1000},
            ),
            patch("analysis.ranking_areas.detectar_expert_flags", return_value=[]),
            patch("analysis.ranking_areas.cargar_areas_catalogo", return_value=areas),
        ):
            out = ranking_areas.calcular_ranking_areas("cliente_x")

        assert out is not None
        assert not out.empty
        assert set(["area", "nombre", "score_riesgo", "presente", "con_saldo"]).issubset(
            set(out.columns)
        )

        row_14 = out[out["area"] == "14"].iloc[0]
        row_1 = out[out["area"] == "1"].iloc[0]
        assert bool(row_14["presente"]) is True
        assert bool(row_1["presente"]) is False
