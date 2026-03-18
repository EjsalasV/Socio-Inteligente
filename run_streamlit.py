"""
Script auxiliar para ejecutar Streamlit con la app_streamlit.py

Uso:
    python run_streamlit.py
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Ejecutar Streamlit con app_streamlit.py"""
    
    # Obtener ruta del proyecto
    project_root = Path(__file__).parent
    app_path = project_root / "app" / "app_streamlit.py"
    
    # Verificar que el archivo existe
    if not app_path.exists():
        print(f"❌ Error: No se encontró {app_path}")
        sys.exit(1)
    
    print("🚀 Iniciando SocioAI Streamlit App...")
    print(f"📁 Ubicación: {app_path}")
    print("🌐 Abriendo en: http://localhost:8501")
    print("\n" + "="*60)
    print("Para detener: presionar Ctrl+C")
    print("="*60 + "\n")
    
    # Cambiar al directorio del proyecto
    os.chdir(project_root)
    
    # Ejecutar streamlit
    try:
        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", str(app_path)],
            check=False
        )
    except KeyboardInterrupt:
        print("\n\n⛔ App detenida por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error ejecutando Streamlit: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
