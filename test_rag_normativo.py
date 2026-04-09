from __future__ import annotations

from backend.services.rag_chat_service import retrieve_context_chunks

CLIENTE_ID = "empresa_xyz"

CASES = [
    {
        "query": "¿Qué procedimientos aplico en cuentas por cobrar con riesgo alto de valuación?",
        "filters": {"marco": "niif_pymes", "afirmacion": "valuacion"},
    },
    {
        "query": "¿Cuándo debo incluir párrafo de énfasis en el informe?",
        "filters": {"tipo": "NIA", "etapa": "cierre"},
    },
    {
        "query": "¿Cómo trato el impuesto diferido por provisiones no deducibles en Ecuador?",
        "filters": {"marco": "niif_completas", "temas": "impuesto_diferido"},
    },
    {
        "query": "¿Qué debo revelar sobre partes relacionadas en PYMES?",
        "filters": {"marco": "niif_pymes", "afirmacion": "presentacion"},
    },
    {
        "query": "¿Qué hago si encuentro indicios de fraude en ingresos?",
        "filters": {"tipo": "NIA", "etapa": "ejecucion"},
    },
]


def fmt(value):
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    return str(value or "")


for idx, case in enumerate(CASES, start=1):
    query = case["query"]
    filters = case["filters"]
    print("=" * 110)
    print(f"CASO {idx}")
    print(f"Consulta: {query}")
    print(f"Filtros: {filters}")

    chunks = retrieve_context_chunks(CLIENTE_ID, query, top_k=6, **filters)
    print(f"Chunks recuperados: {len(chunks)}")

    for i, ch in enumerate(chunks, start=1):
        meta = ch.get("metadata") if isinstance(ch.get("metadata"), dict) else {}
        print("-" * 110)
        print(f"#{i} score={float(ch.get('score', 0.0)):.2f}")
        print(f"source={ch.get('source', '')}")
        print(f"norma={meta.get('norma', '')}")
        print(f"fuente={meta.get('fuente', '')}")
        print(
            "meta: "
            f"tipo={meta.get('tipo', '')} | "
            f"marco={meta.get('marco', '')} | "
            f"etapas={fmt(meta.get('etapas', []))} | "
            f"afirmaciones={fmt(meta.get('afirmaciones_relacionadas', []))} | "
            f"temas={fmt(meta.get('temas', []))}"
        )
        excerpt = str(ch.get("excerpt") or "").replace("\n", " ")
        print(f"excerpt={excerpt[:260]}")

print("=" * 110)
print("Fin test_rag_normativo.py")
