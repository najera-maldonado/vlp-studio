"""Golden test de REGRESIÓN CIENTÍFICA (no solo de código).

Congela resultados numéricos conocidos del cálculo de "radio de sección mínima" de un
sustrato (RDKit + PCA) — la ciencia de la puerta 1 ("¿cabe por el poro?"). Si un cambio
futuro altera la geometría o el algoritmo, esto lo caza aunque el código no truene.

Por qué aquí y no en test_smoke: los tests de humo validan FORMA/cableado; esto valida
VALOR científico. Corre en CI porque `substrate_section` usa solo RDKit+numpy (seed fijo,
determinista) — NO los motores pesados (HOLE/PyMOL/Vina), que no están en CI.

Se compara con TOLERANCIA (no igualdad exacta): el embedding 3D de RDKit puede variar en
el 2º decimal entre plataformas. La tolerancia (0.2 Å) sobrevive ese ruido pero caza una
regresión real (que movería el radio mucho más).
"""

import pytest

from src.services.pore import substrate_section

TOL = 0.2  # Å — absorbe variación de plataforma; una regresión real es >> esto.

# Valores de referencia (RDKit 2025.9.1, seed 42), medidos 2026-09-17.
GOLDEN = {
    "CCO": 1.02,  # etanol (molécula pequeña)
    "OCC1OC(O)C(O)C(O)C1O": 1.95,  # glucosa (sustrato insignia)
    "CC(=O)Oc1ccccc1C(=O)O": 1.15,  # aspirina
}


@pytest.mark.parametrize("smiles,expected", GOLDEN.items())
def test_substrate_section_golden(smiles, expected):
    got = substrate_section(smiles)
    assert got == pytest.approx(expected, abs=TOL), (
        f"Regresión científica: {smiles} dio {got} Å, referencia {expected} Å "
        f"(tol ±{TOL}). Si el cambio es intencional, actualiza el valor golden."
    )


def test_substrate_section_deterministic():
    # El seed está fijo → mismo SMILES debe dar exactamente el mismo valor.
    smiles = "OCC1OC(O)C(O)C(O)C1O"
    valores = {substrate_section(smiles) for _ in range(3)}
    assert len(valores) == 1, f"No determinista: {valores}"


def test_substrate_section_invalid_smiles():
    with pytest.raises(ValueError):
        substrate_section("no-es-un-smiles")
