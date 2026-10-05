"""
Geometría básica sobre archivos PDB en Python puro (sin PyMOL).

Centrar una estructura es una traslación de coordenadas: no necesita PyMOL. Hacerlo
aquí elimina el modo de fallo "PyMOL no disponible → la cápside entra sin centrar"
(AUDITORIA_PACKING, PK-02) y, de paso, conserva los registros ``TER`` y el resto del
archivo, que ``cmd.save`` de PyMOL reescribía (P-22, primera pérdida 180 → 3).
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

Vector = Tuple[float, float, float]


def pdb_centroid(pdb_path) -> Optional[Vector]:
    """Centroide (media aritmética de coordenadas) de las líneas ATOM/HETATM."""
    sx = sy = sz = 0.0
    n = 0
    with open(pdb_path, "r", errors="replace") as f:
        for line in f:
            if line.startswith(("ATOM", "HETATM")) and len(line) >= 54:
                try:
                    sx += float(line[30:38])
                    sy += float(line[38:46])
                    sz += float(line[46:54])
                except ValueError:
                    continue
                n += 1
    if n == 0:
        return None
    return (sx / n, sy / n, sz / n)


def translate_pdb(src, dst, shift: Vector) -> str:
    """
    Copia ``src`` en ``dst`` sumando ``shift`` a las coordenadas de ATOM/HETATM.

    Todas las demás líneas (``TER``, ``CRYST1``, ``REMARK``, ``END``…) se copian tal
    cual, y de cada línea atómica solo cambian las columnas 31-54.
    """
    dx, dy, dz = shift
    src = Path(src)
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(src, "r", errors="replace") as fin, open(dst, "w") as fout:
        for line in fin:
            if line.startswith(("ATOM", "HETATM")) and len(line) >= 54:
                try:
                    x = float(line[30:38]) + dx
                    y = float(line[38:46]) + dy
                    z = float(line[46:54]) + dz
                except ValueError:
                    fout.write(line)
                    continue
                fout.write(f"{line[:30]}{x:8.3f}{y:8.3f}{z:8.3f}{line[54:]}")
            else:
                fout.write(line)
    return str(dst)


def center_pdb(src, dst) -> Tuple[str, Vector]:
    """
    Escribe en ``dst`` la estructura de ``src`` trasladada para que su centroide quede
    en el origen. Devuelve la ruta escrita y el centroide original.

    Raises:
        ValueError: si el archivo no contiene átomos.
    """
    centroid = pdb_centroid(src)
    if centroid is None:
        raise ValueError(f"El PDB no contiene átomos: {src}")
    translate_pdb(src, dst, (-centroid[0], -centroid[1], -centroid[2]))
    return str(dst), centroid
