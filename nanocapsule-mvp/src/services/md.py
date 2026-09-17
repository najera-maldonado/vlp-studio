"""
Puerta "Sobrevive" · Análisis MD (ILUSTRATIVO) + Preparador de DM.

Las curvas son ejemplos anclados a datos de PackMan. Portar: sustituir cada `points`
por los .dat reales de PackMan (frame, valor). El preparador genera inputs Packmol +
tLeaP reales para el sistema cápside+sustrato.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

from src.services.common import _max_radius, _pdb_centroid, structure_path


# --------------------------------------------------------------------------- #
# Análisis MD · curvas de ejemplo (ILUSTRATIVO — puerta 4 "sobrevive")
# --------------------------------------------------------------------------- #
def _curve_sana(n: int = 300) -> List[Dict[str, float]]:
    """RMSD que sube y converge (~2.8 Å)."""
    pts = []
    for i in range(n):
        base = 2.8 * (1 - math.exp(-i / 55.0))
        noise = 0.06 * math.sin(i * 0.7) + 0.04 * math.sin(i * 0.23)
        pts.append({"x": i, "y": round(max(0.0, base + noise), 3)})
    return pts


def _curve_explosion(n: int = 200) -> List[Dict[str, float]]:
    """Temperatura estable que explota a ~17.666 K (fallo de heat1)."""
    pts = []
    knee = int(n * 0.7)
    for i in range(n):
        if i < knee:
            y = 300 + 8 * math.sin(i * 0.5)
        else:
            t = (i - knee) / (n - knee)
            y = 300 + (17666 - 300) * (t ** 3)
        pts.append({"x": i, "y": round(y, 1)})
    return pts


def _curve_rmsf(n: int = 160, good: bool = True) -> List[Dict[str, float]]:
    """RMSF por residuo: con picos (correlaciona con factores B) o plano (bug)."""
    pts = []
    for i in range(n):
        if good:
            y = 1.0 + 0.8 * abs(math.sin(i * 0.15)) + 0.5 * abs(math.sin(i * 0.05))
        else:
            y = 1.4 + 0.3 * math.sin(i * 1.3)
        pts.append({"x": i, "y": round(y, 3)})
    return pts


def _curve_sasa(n: int = 300) -> List[Dict[str, float]]:
    """SASA que se estabiliza (~41.893 Å²)."""
    pts = []
    for i in range(n):
        base = 41893 * (0.6 + 0.4 * (1 - math.exp(-i / 40.0)))
        pts.append({"x": i, "y": round(base + 400 * math.sin(i * 0.6), 0)})
    return pts


def md_examples() -> Dict[str, Any]:
    """Ejemplos de output de PackMan (ilustrativos, anclados a datos reales)."""
    return {
        "illustrative": True,
        "source": "packmanreplicas1/1_2",
        "examples": [
            {"id": "sana", "name": "Producción sana", "desc": "RMSD que converge — lo que debería salir",
             "xlabel": "Frame", "ylabel": "RMSD (Å)", "anchor": "RMSD final 2.8 Å", "color": "#2e8b57",
             "points": _curve_sana()},
            {"id": "explosion", "name": "La explosión", "desc": "heat1 → 17.666 K · el fallo real",
             "xlabel": "Frame", "ylabel": "Temperatura (K)", "anchor": "pico 17.666 K", "color": "#FF2600",
             "points": _curve_explosion()},
            {"id": "rmsf_ok", "name": "RMSF ← factores B", "desc": "la validación gratis · r=0.81",
             "xlabel": "Residuo", "ylabel": "RMSF (Å)", "anchor": "r = 0.81", "color": "#378ADD",
             "points": _curve_rmsf(good=True)},
            {"id": "rmsf_bug", "name": "RMSF sin ajuste", "desc": "el bug de hoy · r=0.12",
             "xlabel": "Residuo", "ylabel": "RMSF (Å)", "anchor": "r = 0.12", "color": "#BA7517",
             "points": _curve_rmsf(good=False)},
            {"id": "sasa", "name": "SASA en el vacío", "desc": "métrica ciega al confinamiento",
             "xlabel": "Frame", "ylabel": "SASA (Å²)", "anchor": "~41.893 Å²", "color": "#7F77DD",
             "points": _curve_sasa()},
        ],
    }


# --------------------------------------------------------------------------- #
# Preparador de DM · box de simulación + archivos (ILUSTRATIVO)
# --------------------------------------------------------------------------- #
def md_box(capsid_name: str) -> Dict[str, Any]:
    """Caja de simulación centrada en la cápside (half = r_externo · 1.2)."""
    capsid_path = structure_path("capside", capsid_name)
    if not capsid_path.exists():
        raise FileNotFoundError(f"Cápside no encontrada: {capsid_name}")
    content = capsid_path.read_text()
    center = _pdb_centroid(content)
    r_outer = _max_radius(content, center)
    half = round(r_outer * 1.2, 1)
    return {
        "capsid": capsid_name,
        "center": [round(c, 1) for c in center],
        "box_half": half,
        "box_size": round(2 * half, 1),
        "r_outer": round(r_outer, 1),
    }


def md_prepare(capsid_name: str, n_substrate: int = 40, smiles: Optional[str] = None) -> Dict[str, Any]:
    """Prepara los inputs de DM (Packmol + tLeaP) para el sistema cápside+sustrato."""
    b = md_box(capsid_name)
    h = b["box_half"]
    packmol = (
        "tolerance 2.0\n"
        "filetype pdb\n"
        f"output {capsid_name}-sustrato.pdb\n\n"
        f"structure {capsid_name}.pdb\n"
        "  number 1\n"
        "  center\n"
        "  fixed 0. 0. 0. 0. 0. 0.\n"
        "end structure\n\n"
        "structure sustrato.pdb\n"
        f"  number {n_substrate}\n"
        f"  inside box {-h} {-h} {-h} {h} {h} {h}\n"
        "end structure\n"
    )
    leap = (
        "source leaprc.protein.ff19SB\n"
        "source leaprc.gaff2\n"
        "source leaprc.water.tip3p\n"
        f"sys = loadpdb {capsid_name}-sustrato.pdb\n"
        "# caja octaédrica truncada con ~10 A de agua\n"
        "solvateOct sys TIP3PBOX 10.0\n"
        "addIonsRand sys Na+ 0 Cl- 0\n"
        f"saveamberparm sys {capsid_name}.prmtop {capsid_name}.inpcrd\n"
        f"savepdb sys {capsid_name}-solvatado.pdb\n"
        "quit\n"
    )
    return {**b, "n_substrate": n_substrate, "smiles": smiles,
            "packmol_input": packmol, "leap_input": leap}
