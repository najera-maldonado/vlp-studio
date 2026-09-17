"""
Rutas absolutas del proyecto, resueltas una sola vez.

Este módulo es la única fuente de verdad para las ubicaciones de directorios.
Elimina las rutas relativas frágiles ("../../Input") que dependían de que el
proceso se ejecutara desde src/web. Ahora todo se resuelve respecto a la raíz
del proyecto (nanocapsule-mvp/), sin importar el directorio de trabajo actual.
"""

from pathlib import Path

# src/core/paths.py -> src/core -> src -> raíz del proyecto
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

INPUT_DIR = PROJECT_ROOT / "Input"
CAPSIDES_DIR = INPUT_DIR / "Capsides"
ENZYMES_DIR = INPUT_DIR / "Enzimas"

OUTPUT_DIR = PROJECT_ROOT / "Output"
GENERATED_DIR = OUTPUT_DIR / "Generated_PDBs"

CONFIG_FILE = PROJECT_ROOT / "config" / "default.yaml"

# Pipelines hermanos (motores reales de las puertas del embudo).
POROMANIA_DIR = PROJECT_ROOT.parent / "Poromania.v.1.2."


def ensure_output_dirs() -> None:
    """Crea los directorios de salida si no existen."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
