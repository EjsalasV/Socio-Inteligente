#!/usr/bin/env python3
"""
Script para cargar papeles de trabajo clasificados desde JSON a BD
"""
import json
import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Agregar parent dir al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.models.workpapers_template import WorkpapersTemplate, Base

def load_templates_from_json(json_path: str = "data/papeles_clasificados_enriquecido.json"):
    """Carga papeles desde JSON y los inserta en BD"""

    json_file = Path(json_path)
    if not json_file.exists():
        print(f"Error: {json_path} no existe")
        return False

    # Leer JSON
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    papeles = data.get("papeles", [])
    print(f"Encontrados {len(papeles)} papeles en {json_path}")

    # Crear sesión manualmente (sin usar get_session que es generator)
    try:
        from dotenv import load_dotenv
        import os
        load_dotenv()

        db_url = os.getenv("DATABASE_URL", "sqlite:///./test.db")
        engine = create_engine(db_url, echo=False)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
    except Exception as e:
        print(f"Error conectando a BD: {e}")
        # Si no hay BD, crear en memoria
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        print("Usando base de datos en memoria (desarrollo)")

    # Limpiar papeles existentes
    try:
        session.query(WorkpapersTemplate).delete()
        session.commit()
        print("Papeles previos eliminados")
    except Exception as e:
        print(f"Error limpiando papeles: {e}")
        session.rollback()

    # Insertar nuevos papeles
    inserted = 0
    errors = 0

    for p in papeles:
        try:
            template = WorkpapersTemplate(
                codigo=p.get("codigo"),
                numero=p.get("numero"),
                ls=p.get("ls"),
                nombre=p.get("nombre"),
                aseveracion=p.get("aseveracion"),
                importancia=p.get("importancia"),
                obligatorio=p.get("obligatorio"),
                descripcion=p.get("descripcion"),
                archivo_original=p.get("archivo_original"),
            )
            session.add(template)
            inserted += 1

        except Exception as e:
            print(f"Error insertando {p.get('codigo')}: {e}")
            errors += 1
            continue

    # Commit
    try:
        session.commit()
        print(f"\nExito! {inserted} papeles insertados")
        if errors > 0:
            print(f"Con {errors} errores")
        return True
    except Exception as e:
        print(f"Error en commit: {e}")
        session.rollback()
        return False
    finally:
        session.close()


if __name__ == "__main__":
    success = load_templates_from_json()
    sys.exit(0 if success else 1)
