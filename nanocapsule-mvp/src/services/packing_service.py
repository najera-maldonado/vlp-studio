"""
Capa de aplicación (casos de uso) para el diseño de nanocápsulas — FACHADA.

Esta es la frontera limpia entre los adaptadores de entrada (Flask, un futuro CLI,
tests) y el dominio. Desde VLP-03 la lógica vive repartida por PUERTA en módulos
propios; este archivo solo re-exporta la API pública para que los adaptadores sigan
haciendo `from src.services import packing_service as svc` sin cambios.

Dónde está cada cosa ahora:
- común/infra ......... src/services/common.py   (_config, structure_path, info, read)
- Biblioteca .......... src/services/library.py
- Pac-Pore ............ src/services/pore.py
- De-inmunización ..... src/services/deimmuno.py
- Análisis MD + DM .... src/services/md.py
- Studio 3D / packing . src/services/packing.py

Para añadir una puerta nueva: crea su módulo y re-expórtalo aquí. Nada más se toca.
"""

from __future__ import annotations

# Infra compartida (app.py usa svc._config).
from src.services.common import (
    _config,
    read_structure_pdb,
    structure_info,
    structure_path,
)

# De-inmunización
from src.services.deimmuno import deimmuno_data

# Biblioteca
from src.services.library import library_detail, list_library

# Análisis MD + preparador de DM
from src.services.md import md_box, md_examples, md_prepare

# Studio 3D / packing
from src.services.packing import (
    calculate_radius,
    preview,
    preview_substrate,
    run_experiment,
)

# Pac-Pore
from src.services.pore import (
    dock_correlate,
    evaluate_mutant,
    hole_structures,
    pore_channel_content,
    pore_channels,
    pore_config,
    pore_profile,
    run_hole,
    screen_mutants,
    substrate_section,
)

__all__ = [
    "_config",
    "read_structure_pdb",
    "structure_info",
    "structure_path",
    "list_library",
    "library_detail",
    "deimmuno_data",
    "md_box",
    "md_examples",
    "md_prepare",
    "dock_correlate",
    "evaluate_mutant",
    "hole_structures",
    "pore_channel_content",
    "pore_channels",
    "pore_config",
    "pore_profile",
    "run_hole",
    "screen_mutants",
    "substrate_section",
    "calculate_radius",
    "preview",
    "preview_substrate",
    "run_experiment",
]
