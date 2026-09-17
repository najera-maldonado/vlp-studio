"""
Puerta "Fuera" · De-inmunización (ILUSTRATIVO).

Mapa ΔMHC vs ΔΔG. Portar en el futuro: sustituir por NetMHCIIpan + FEP.
Ancla real: Bing 2024 · R312Q (mutación de-inmunizante validada en AAV).
"""

from __future__ import annotations

from typing import Any, Dict

# Cada mutante: dmhc (X, negativo = silencia el epítopo) y ddg (Y, negativo =
# estabiliza la cápside). DIANA = cuadrante inferior-izquierdo (silencia + estabiliza).
_DEIMMUNO = {
    "anchor": {"name": "R312Q", "source": "Bing 2024"},
    "anclas": [
        {"puerta": "01 · mapa", "herramienta": "NetMHCIIpan", "ancla": "epítopo 307–319"},
        {"puerta": "02 · barrido", "herramienta": "EMMP · 27 HLA", "ancla": "R312Q"},
        {"puerta": "03 · ΔΔG", "herramienta": "MD · FEP", "ancla": "ventana tolerada"},
        {"puerta": "04 · función", "herramienta": "transducción", "ancla": "cobro funcional"},
    ],
    "mutants": [
        {"name": "WT", "dmhc": 0.0, "ddg": 0.0, "cat": "wt"},
        {"name": "R312Q", "dmhc": -1.8, "ddg": -0.6, "cat": "pasa"},
        {"name": "K137R", "dmhc": -1.2, "ddg": -0.9, "cat": "pasa"},
        {"name": "N272A", "dmhc": -0.9, "ddg": -0.4, "cat": "pasa"},
        {"name": "S268T", "dmhc": -1.5, "ddg": -0.2, "cat": "pasa"},
        {"name": "A315V", "dmhc": 0.8, "ddg": -0.3, "cat": "no_silencia"},
        {"name": "T330K", "dmhc": 1.4, "ddg": -0.7, "cat": "no_silencia"},
        {"name": "Q285E", "dmhc": 0.6, "ddg": 0.2, "cat": "no_silencia"},
        {"name": "P250G", "dmhc": 0.3, "ddg": 1.2, "cat": "rompe"},
        {"name": "G265W", "dmhc": -0.5, "ddg": 1.5, "cat": "rompe"},
        {"name": "F129D", "dmhc": 0.9, "ddg": 1.0, "cat": "rompe"},
        {"name": "R312W", "dmhc": -1.0, "ddg": 1.3, "cat": "rompe"},
    ],
    "illustrative": True,
}


def deimmuno_data() -> Dict[str, Any]:
    """Mapa de-inmunización (ilustrativo). Portar: sustituir por NetMHCIIpan+FEP."""
    return _DEIMMUNO
