"""
Generadores de PDB sintéticos para los tests del motor de packing.

Una "cápside" es un cascarón de puntos sobre una esfera (radio mínimo conocido) con
varias cadenas separadas por ``TER``; una "enzima" es una nube pequeña de puntos. Son
geometrías de juguete: lo que se prueba es el motor (criterio, conteo, centrado,
semillas), no la ciencia.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Sequence, Tuple

Vec = Tuple[float, float, float]


def fibonacci_sphere(n: int, radius: float) -> List[Vec]:
    pts: List[Vec] = []
    golden = math.pi * (3.0 - math.sqrt(5.0))
    for i in range(n):
        y = 1 - (i / max(n - 1, 1)) * 2
        r = math.sqrt(max(0.0, 1 - y * y))
        theta = golden * i
        pts.append((radius * math.cos(theta) * r, radius * y, radius * math.sin(theta) * r))
    return pts


def write_pdb(path, coords: Sequence[Vec], n_chains: int = 1, center: Vec = (0.0, 0.0, 0.0)):
    """Escribe ATOM por coordenada, repartidos en ``n_chains`` cadenas con ``TER``."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    per_chain = max(1, math.ceil(len(coords) / n_chains))
    chains = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    lines = ["REMARK    synthetic structure for tests"]
    for i, (x, y, z) in enumerate(coords):
        chain = chains[(i // per_chain) % len(chains)]
        resseq = (i % 9999) + 1
        lines.append(
            f"ATOM  {i + 1:5d}  CA  ALA {chain}{resseq:4d}    "
            f"{x + center[0]:8.3f}{y + center[1]:8.3f}{z + center[2]:8.3f}  1.00  0.00           C"
        )
        if (i + 1) % per_chain == 0 or i == len(coords) - 1:
            lines.append("TER")
    lines.append("END")
    path.write_text("\n".join(lines) + "\n")
    return str(path)


def make_capsid(path, n_atoms: int = 12000, radius: float = 95.0, center: Vec = (0.0, 0.0, 0.0)):
    """Cascarón esférico de ``n_atoms`` átomos (> 10 000 a propósito: el antiguo fallback
    por conteo de líneas lo aceptaba sin una sola enzima)."""
    return write_pdb(path, fibonacci_sphere(n_atoms, radius), n_chains=4, center=center)


def make_enzyme(path, n_atoms: int = 50, radius: float = 8.0, center: Vec = (0.0, 0.0, 0.0)):
    return write_pdb(path, fibonacci_sphere(n_atoms, radius), n_chains=1, center=center)


def count_atoms(path) -> int:
    with open(path) as f:
        return sum(1 for ln in f if ln.startswith(("ATOM", "HETATM")))


def count_ter(path) -> int:
    with open(path) as f:
        return sum(1 for ln in f if ln.startswith("TER"))


def centroid(path) -> Vec:
    sx = sy = sz = 0.0
    n = 0
    with open(path) as f:
        for ln in f:
            if ln.startswith(("ATOM", "HETATM")):
                sx += float(ln[30:38])
                sy += float(ln[38:46])
                sz += float(ln[46:54])
                n += 1
    return (sx / n, sy / n, sz / n)
