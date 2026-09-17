"""
Infraestructura y helpers compartidos por las puertas del Studio.

Aquí vive lo que usan varios módulos de servicio (biblioteca, pore, md, packing):
la config y el fetcher únicos del proceso, y utilidades de parsing de PDB. No debe
importar de los módulos de puerta (para no crear ciclos).
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List

from src.core import paths
from src.core.config import ConfigManager
from src.io.structure_fetcher import StructureFetcher

# Una sola instancia de configuración y fetcher para todo el proceso.
_config = ConfigManager()
_fetcher = StructureFetcher(str(paths.INPUT_DIR))


def _pdb_code(name: str) -> str:
    """Código PDB derivado del nombre de carpeta (último token tras '_')."""
    return name.rsplit("_", 1)[-1] if "_" in name else name


def _count_atoms_chains(pdb_text: str) -> tuple[int, int]:
    """Nº de átomos y de cadenas únicas de un PDB."""
    atoms = 0
    chains = set()
    for line in pdb_text.split("\n"):
        if line.startswith(("ATOM", "HETATM")):
            atoms += 1
            if len(line) > 21:
                chains.add(line[21])
    return atoms, len(chains)


def _pdb_centroid(pdb_text: str) -> List[float]:
    """Centroide (media de coordenadas) de los átomos de un PDB."""
    sx = sy = sz = 0.0
    n = 0
    for line in pdb_text.split("\n"):
        if line.startswith(("ATOM", "HETATM")) and len(line) >= 54:
            try:
                sx += float(line[30:38])
                sy += float(line[38:46])
                sz += float(line[46:54])
                n += 1
            except ValueError:
                continue
    if n == 0:
        return [0.0, 0.0, 0.0]
    return [sx / n, sy / n, sz / n]


def _max_radius(pdb_text: str, center: List[float]) -> float:
    """Distancia máxima de un átomo al centro (radio externo aprox de la cápside)."""
    cx, cy, cz = center
    r2max = 0.0
    for line in pdb_text.split("\n"):
        if line.startswith(("ATOM", "HETATM")) and len(line) >= 54:
            try:
                dx = float(line[30:38]) - cx
                dy = float(line[38:46]) - cy
                dz = float(line[46:54]) - cz
            except ValueError:
                continue
            r2 = dx * dx + dy * dy + dz * dz
            if r2 > r2max:
                r2max = r2
    return math.sqrt(r2max)


def structure_path(structure_type: str, name: str) -> Path:
    """Ruta absoluta al PDB de una estructura ('capside' o 'enzima')."""
    return Path(_fetcher.get_structure_path(structure_type, name)).resolve()


def structure_info(structure_type: str, name: str) -> Dict[str, Any]:
    """Metadatos ligeros de una estructura (nº de átomos, tamaño)."""
    path = structure_path(structure_type, name)
    if not path.exists():
        raise FileNotFoundError(f"Estructura no encontrada: {structure_type}/{name}")

    atoms = 0
    with open(path, "r") as f:
        for line in f:
            if line.startswith(("ATOM", "HETATM")):
                atoms += 1

    size = path.stat().st_size
    return {
        "name": name,
        "type": structure_type,
        "atoms": atoms,
        "size_bytes": size,
        "size_mb": round(size / 1024 / 1024, 2),
    }


def read_structure_pdb(structure_type: str, name: str) -> str:
    """Contenido crudo de un PDB de entrada, para servir al visor 3D."""
    path = structure_path(structure_type, name)
    if not path.exists():
        raise FileNotFoundError(f"Estructura no encontrada: {structure_type}/{name}")
    return path.read_text()
