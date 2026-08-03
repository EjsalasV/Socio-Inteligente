from backend.services.area_procedures_service import get_procedures_by_area
from backend.services.mentor_recommendation_service import recommend_learning_resources
from backend.services.normative_catalog_service import list_normative_catalog


def test_recommendations_only_reference_real_catalog_entries() -> None:
    area = "410"
    recommendations = recommend_learning_resources(
        area_code=area,
        account_name="Ingresos por ventas",
        reasoning_gap="Falta probar corte y ocurrencia",
        follow_up_question="¿Qué evidencia demuestra el período correcto?",
        learning_role="junior",
    )
    valid_procedures = {item["id"] for item in get_procedures_by_area(area)["procedimientos"]}
    valid_norms = {item["codigo"] for item in list_normative_catalog()}
    assert all(item["id"] in valid_procedures for item in recommendations["procedures"])
    assert all(item["code"] in valid_norms for item in recommendations["norms"])
    assert all(item["href"].startswith("/biblioteca?norma=") for item in recommendations["norms"])
