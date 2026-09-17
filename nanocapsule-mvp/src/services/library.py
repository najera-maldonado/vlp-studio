"""
Puerta "Biblioteca" · cápsides y enzimas disponibles, con datos reales.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from src.core import paths
from src.services.common import (
    _count_atoms_chains,
    _fetcher,
    _pdb_code,
    structure_path,
)

# Rol/uso de cada enzima (por código PDB). Honesto: solo GCase es terapéutica;
# el resto son proteínas modelo/reporteras que hay realmente en la biblioteca.
_ENZYME_ROLE = {
    "1OGS": {"enfermedad": "Gaucher", "rol": "terapéutica"},
    "1ED8": {"enfermedad": "—", "rol": "enzima modelo"},
    "4EUL": {"enfermedad": "—", "rol": "reporter fluorescente"},
    "1LCI": {"enfermedad": "—", "rol": "reporter bioluminiscente"},
}

_T_NUMBER = {3: "T=3", 4: "T=4", 7: "T=7"}


def list_library() -> Dict[str, Any]:
    """Devuelve las cápsides y enzimas disponibles."""
    capsides = _fetcher.list_available_capsides()
    enzymes = _fetcher.list_available_enzymes()
    return {
        "capsides": capsides,
        "enzymes": enzymes,
        "total_combinations": len(capsides) * len(enzymes),
    }


def _load_enzyme_volumes() -> Dict[str, Dict[str, float]]:
    """Lee vdw_volumes_results.txt (V excl y Rg reales) indexado por código PDB."""
    vol_file = paths.INPUT_DIR / "Enzimas" / "vdw_volumes_results.txt"
    out: Dict[str, Dict[str, float]] = {}
    if not vol_file.exists():
        return out
    for line in vol_file.read_text().splitlines()[1:]:  # salta cabecera
        parts = line.split("\t")
        if len(parts) < 5:
            continue
        label = parts[0]  # p.ej. "Alkaline Phosphatase (1ED8)"
        code = label.split("(")[-1].rstrip(")").strip() if "(" in label else label
        try:
            out[code] = {"rg": float(parts[3]), "volume": float(parts[4])}
        except ValueError:
            continue
    return out


def library_detail() -> Dict[str, Any]:
    """Biblioteca enriquecida con datos reales (átomos, cadenas, Rg, volumen, radio)."""
    # Radio interno cacheado (global; solo lo atribuimos si existe el fichero).
    cached_radius: Optional[float] = None
    radius_file = paths.PROJECT_ROOT / "radio_interno.txt"
    if radius_file.exists():
        try:
            cached_radius = float(radius_file.read_text().strip())
        except ValueError:
            cached_radius = None

    capsides = []
    for name in _fetcher.list_available_capsides():
        try:
            text = structure_path("capside", name).read_text()
            atoms, chains = _count_atoms_chains(text)
        except OSError:
            atoms, chains = 0, 0
        capsides.append({
            "name": name,
            "pdb": _pdb_code(name),
            "atoms": atoms,
            "chains": chains,
            "t_number": _T_NUMBER.get(chains, f"T={chains}" if chains else "—"),
            # El radio cacheado corresponde a BMV (la única calculada hasta ahora).
            "radius": cached_radius if name.startswith("BMV") else None,
        })

    volumes = _load_enzyme_volumes()
    enzymes = []
    for name in _fetcher.list_available_enzymes():
        try:
            text = structure_path("enzima", name).read_text()
            atoms, chains = _count_atoms_chains(text)
        except OSError:
            atoms, chains = 0, 0
        code = _pdb_code(name)
        vol = volumes.get(code, {})
        role = _ENZYME_ROLE.get(code, {"enfermedad": "—", "rol": "—"})
        enzymes.append({
            "name": name,
            "pdb": code,
            "atoms": atoms,
            "chains": chains,
            "rg": vol.get("rg"),
            "volume": vol.get("volume"),
            "enfermedad": role["enfermedad"],
            "rol": role["rol"],
        })

    return {"capsides": capsides, "enzymes": enzymes}
