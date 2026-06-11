"""Regresion: resolucion de directorios de clientes.

La resolucion debe ser exacta (o sufijo de anio exacto del mismo id).
Un cliente_id parecido al de otro cliente jamas debe resolver a la
carpeta de ese otro cliente, y los ids con separadores de ruta deben
rechazarse.
"""
from __future__ import annotations

import pytest

from backend.repositories.file_repository import FileRepository, is_safe_cliente_id


@pytest.fixture()
def repo(tmp_path):
    (tmp_path / "data" / "clientes").mkdir(parents=True)
    return FileRepository(root=tmp_path)


def _mkdir_cliente(repo: FileRepository, name: str) -> None:
    (repo.data_clientes / name).mkdir()


def test_exact_directory_is_preferred(repo) -> None:
    _mkdir_cliente(repo, "acme")
    _mkdir_cliente(repo, "acme_2024")
    assert repo._resolve_cliente_dir("acme").name == "acme"


def test_year_suffix_of_same_id_resolves_to_latest(repo) -> None:
    _mkdir_cliente(repo, "acme_2023")
    _mkdir_cliente(repo, "acme_2024")
    assert repo._resolve_cliente_dir("acme").name == "acme_2024"


def test_similar_id_never_resolves_to_another_clients_dir(repo) -> None:
    """'acme' no debe resolver a 'acme_corp_2024' (otro cliente)."""
    _mkdir_cliente(repo, "acme_corp_2024")
    resolved = repo._resolve_cliente_dir("acme")
    assert resolved.name == "acme"
    assert not resolved.exists()


def test_id_that_is_substring_of_other_does_not_cross(repo) -> None:
    """'bustamante_fabara_ip' vs 'bustamante_fabara_ip_cl': sin cruces."""
    _mkdir_cliente(repo, "bustamante_fabara_ip_cl_2024")
    resolved = repo._resolve_cliente_dir("bustamante_fabara_ip")
    assert resolved.name == "bustamante_fabara_ip"
    assert not resolved.exists()


def test_longer_id_does_not_fall_back_to_shorter_base(repo) -> None:
    _mkdir_cliente(repo, "acme_2024")
    resolved = repo._resolve_cliente_dir("acme_holding")
    assert resolved.name == "acme_holding"
    assert not resolved.exists()


@pytest.mark.parametrize(
    "bad_id",
    ["..", "../otro", "a/b", "a\\b", ".", "x" * 65, "a.b"],
)
def test_unsafe_cliente_id_is_rejected(repo, bad_id) -> None:
    assert not is_safe_cliente_id(bad_id)
    with pytest.raises(ValueError):
        repo.cliente_dir(bad_id)


@pytest.mark.parametrize("empty_id", ["", "   ", None])
def test_empty_cliente_id_resolves_to_missing_sentinel(repo, empty_id) -> None:
    """Flujos globales sin cliente leen defaults: ruta inexistente, sin error."""
    path = repo.cliente_dir(empty_id)
    assert path.parent == repo.data_clientes
    assert not path.exists()


@pytest.mark.parametrize(
    "good_id",
    ["acme", "test-001", "cliente_demo_001", "SI_99283", "compañía_x"],
)
def test_safe_cliente_ids_are_accepted(repo, good_id) -> None:
    assert is_safe_cliente_id(good_id)
    path = repo.cliente_dir(good_id)
    assert path.parent == repo.data_clientes
