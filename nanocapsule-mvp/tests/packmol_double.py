"""
Doble de PACKMOL para los tests del motor de packing.

Aquí no hay PACKMOL instalado (ni en CI), así que el motor se ejecuta contra un
ejecutable de prueba que lee el ``.inp`` por stdin como PACKMOL, escribe un PDB de
salida y un log con las CADENAS REALES de PACKMOL (tomadas de los dos logs commiteados
en ``tests/fixtures/packmol_logs``: versiones 20.14.3 y 21.0.1).

Comportamiento configurable (dict ``cfg`` horneado en el script envoltorio):

- ``capacity``: a partir de cuántas copias "no cabe". Si ``number`` ≤ capacity →
  éxito (``Success!``, violación final ``final_violation``). Si no → fallo honesto:
  ``ENDED WITHOUT PERFECT PACKING``, escribe ``<output>_FORCED`` y, como hace PACKMOL
  durante la optimización, también deja escrito ``<output>`` (``write_partial_output``);
  sale con ``fail_exit_code`` (por defecto 173, el de las versiones modernas; usar 0
  para simular versiones antiguas).
- ``mode="capsid_only"``: éxito en el log, pero el PDB solo contiene la cápside (el
  peor caso de AUDITORIA_PACKING P-02: cero enzimas colocadas).
- ``ignore_center``: no honra la palabra clave ``center`` (deja la cápside donde estaba).
- ``sleep``: segundos de espera antes de hacer nada (para probar el timeout).
- ``crash``: termina con código 1 sin escribir nada.

Uso desde los tests: ``install_double(tmp_path, capacity=4)`` devuelve la ruta de un
ejecutable que el motor puede invocar como ``packmol_executable``.
"""

from __future__ import annotations

import json
import math
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

TESTS_DIR = Path(__file__).resolve().parent

# --------------------------------------------------------------------------- #
# Texto del log (cadenas reales de PACKMOL)
# --------------------------------------------------------------------------- #
_HEADER = """
################################################################################

 PACKMOL - Packing optimization for the automated generation of
 starting configurations for molecular dynamics simulations.

                                                              Version 20.14.3

################################################################################

  Packmol must be run with: packmol < inputfile.inp

  Userguide at: http://m3g.iqm.unicamp.br/packmol

  Reading input file... (Control-C aborts)
  Types of coordinate files specified: pdb
  Seed for random number generator:      {seed}
  Output file: {output}
  Number of independent structures:            {n_structures}
  Distance tolerance:    {tolerance}
  Total number of atoms:       {n_atoms}
"""

_ITERATION = """
--------------------------------------------------------------------------------

  Starting GENCAN loop:           {loop}
  Scaling radii by:    1.0000000000000000

  Packing:|0                                                        100%|
          |*************************************************************|

  Function value from last GENCAN loop: f = .38048E+00
  Best function value before: f = .39430E+00
  Improvement from best function value:     3.50 %
  Improvement from last loop:     3.50 %
  Maximum violation of target distance:     {violation:.6f}
  Maximum violation of the constraints: .12571E-01
  All-type function value: .38048E+00

--------------------------------------------------------------------------------

  Current solution written to file: {output}
"""

_SUCCESS = """
################################################################################

  Packing all molecules together

################################################################################

  Solution written to file: {output}

################################################################################

                                 Success!
              Final objective function value: .00000E+00
              Maximum violation of target distance:   {violation:.6f}
              Maximum violation of the constraints: .00000E+00

--------------------------------------------------------------------------------

              Please cite this work if Packmol was useful:

           L. Martinez, R. Andrade, E. G. Birgin, J. M. Martinez,
         PACKMOL: A package for building initial configurations for
                   molecular dynamics simulations.
          Journal of Computational Chemistry, 30:2157-2164,2009.

################################################################################

   Running time:    2.10059285      seconds.

--------------------------------------------------------------------------------
"""

_FAILURE = """
  Current point written to file: {output}

################################################################################

                         ENDED WITHOUT PERFECT PACKING:
                         The output file:

                         {output}_FORCED

                         contains the best solution found.

                         Very likely, if the input data was correct,
                         it is a reasonable starting configuration.
                         Check commentaries above for more details.

################################################################################

   Running time:    91.3304443      seconds.

--------------------------------------------------------------------------------
"""


# --------------------------------------------------------------------------- #
# Parser mínimo del .inp
# --------------------------------------------------------------------------- #
def parse_inp(text: str) -> Dict[str, Any]:
    spec: Dict[str, Any] = {"output": None, "seed": None, "tolerance": None, "structures": []}
    current = None
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        tokens = line.split()
        key = tokens[0]
        if current is None:
            if key == "output":
                spec["output"] = tokens[1]
            elif key == "seed":
                spec["seed"] = int(tokens[1])
            elif key == "tolerance":
                spec["tolerance"] = float(tokens[1])
            elif key == "structure":
                current = {
                    "file": tokens[1],
                    "number": 1,
                    "fixed": None,
                    "center": False,
                    "sphere": None,
                    "radius": None,
                }
        else:
            if key == "end":
                spec["structures"].append(current)
                current = None
            elif key == "number":
                current["number"] = int(tokens[1])
            elif key == "fixed":
                current["fixed"] = [float(t) for t in tokens[1:7]]
            elif key == "center":
                current["center"] = True
            elif key == "inside" and tokens[1] == "sphere":
                current["sphere"] = [float(t) for t in tokens[2:6]]
            elif key == "radius":
                current["radius"] = float(tokens[1])
    return spec


# --------------------------------------------------------------------------- #
# Utilidades PDB
# --------------------------------------------------------------------------- #
def read_atom_lines(path: str) -> List[str]:
    with open(path, "r") as f:
        return [ln.rstrip("\n") for ln in f if ln.startswith(("ATOM", "HETATM"))]


def centroid(lines: Sequence[str]) -> Tuple[float, float, float]:
    sx = sy = sz = 0.0
    for ln in lines:
        sx += float(ln[30:38])
        sy += float(ln[38:46])
        sz += float(ln[46:54])
    n = len(lines) or 1
    return (sx / n, sy / n, sz / n)


def translate(lines: Sequence[str], shift: Tuple[float, float, float]) -> List[str]:
    dx, dy, dz = shift
    out = []
    for ln in lines:
        x = float(ln[30:38]) + dx
        y = float(ln[38:46]) + dy
        z = float(ln[46:54]) + dz
        out.append(f"{ln[:30]}{x:8.3f}{y:8.3f}{z:8.3f}{ln[54:]}")
    return out


def _lattice_offsets() -> List[Tuple[int, int, int]]:
    pts = [(i, j, k) for i in range(-3, 4) for j in range(-3, 4) for k in range(-3, 4)]
    pts.sort(key=lambda p: (p[0] ** 2 + p[1] ** 2 + p[2] ** 2, p))
    return pts


def place_copies(
    enzyme_lines: Sequence[str],
    n_copies: int,
    sphere: Sequence[float],
    spacing: float,
) -> List[str]:
    """Coloca ``n_copies`` copias de la enzima en una rejilla dentro de la esfera."""
    cx, cy, cz, radius = sphere
    ex, ey, ez = centroid(enzyme_lines)
    offsets = _lattice_offsets()
    out: List[str] = []
    for k in range(n_copies):
        o = offsets[k % len(offsets)]
        scale = spacing * (1 + k // len(offsets))
        px, py, pz = cx + o[0] * scale, cy + o[1] * scale, cz + o[2] * scale
        # Mantener el centroide dentro de la mitad del radio (siempre "dentro").
        norm = math.sqrt((px - cx) ** 2 + (py - cy) ** 2 + (pz - cz) ** 2)
        if norm > radius * 0.5 and norm > 0:
            f = radius * 0.5 / norm
            px, py, pz = cx + (px - cx) * f, cy + (py - cy) * f, cz + (pz - cz) * f
        out.extend(translate(enzyme_lines, (px - ex, py - ey, pz - ez)))
    return out


def write_pdb(path: str, atom_lines: Sequence[str]) -> None:
    with open(path, "w") as f:
        f.write("HEADER    Built with Packmol (double de pruebas)\n")
        for ln in atom_lines:
            f.write(ln + "\n")
        f.write("END\n")


# --------------------------------------------------------------------------- #
# Programa principal del doble
# --------------------------------------------------------------------------- #
def main(cfg: Dict[str, Any]) -> int:
    inp = sys.stdin.read()
    spec = parse_inp(inp)

    if cfg.get("sleep"):
        time.sleep(float(cfg["sleep"]))
    if cfg.get("crash"):
        sys.stdout.write("  ERROR: simulated crash\n")
        return 1

    output = spec["output"]
    fixed = [s for s in spec["structures"] if s["fixed"] is not None]
    mobile = [s for s in spec["structures"] if s["fixed"] is None]
    if len(fixed) != 1 or len(mobile) != 1 or output is None:
        sys.stdout.write("  ERROR: input not understood by the double\n")
        return 171

    capsid = fixed[0]
    enzyme = mobile[0]
    capsid_lines = read_atom_lines(capsid["file"])
    if capsid["center"] and not cfg.get("ignore_center"):
        cc = centroid(capsid_lines)
        fx, fy, fz = capsid["fixed"][:3]
        capsid_lines = translate(capsid_lines, (fx - cc[0], fy - cc[1], fz - cc[2]))

    enzyme_lines = read_atom_lines(enzyme["file"])
    n = enzyme["number"]
    sphere = enzyme["sphere"] or [0.0, 0.0, 0.0, 50.0]
    copies = place_copies(enzyme_lines, n, sphere, float(cfg.get("spacing", 4.0)))

    n_atoms = len(capsid_lines) + n * len(enzyme_lines)
    log = _HEADER.format(
        seed=spec["seed"],
        output=output,
        n_structures=len(spec["structures"]),
        tolerance=spec["tolerance"],
        n_atoms=n_atoms,
    )

    capacity = cfg.get("capacity")
    fits = capacity is None or n <= int(capacity)

    if fits:
        for loop, v in enumerate((3.970194, 0.255513), start=1):
            log += _ITERATION.format(loop=loop, violation=v, output=output)
        log += _SUCCESS.format(output=output, violation=float(cfg.get("final_violation", 0.0)))
        body = capsid_lines if cfg.get("mode") == "capsid_only" else capsid_lines + copies
        write_pdb(output, body)
        sys.stdout.write(log)
        return 0

    for loop, v in enumerate((9.812345, 7.430001), start=1):
        log += _ITERATION.format(loop=loop, violation=v, output=output)
    log += _FAILURE.format(output=output)
    write_pdb(output + "_FORCED", capsid_lines + copies)
    if cfg.get("write_partial_output", True):
        write_pdb(output, capsid_lines + copies)
    sys.stdout.write(log)
    return int(cfg.get("fail_exit_code", 173))


def install_double(directory, **cfg: Any) -> str:
    """Escribe un ejecutable que corre este doble con ``cfg`` y devuelve su ruta."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    script = directory / "packmol_double"
    script.write_text(
        f"#!{sys.executable}\n"
        "import json, sys\n"
        f"sys.path.insert(0, {str(TESTS_DIR)!r})\n"
        "from packmol_double import main\n"
        f"sys.exit(main(json.loads({json.dumps(cfg)!r})))\n"
    )
    os.chmod(script, 0o755)
    return str(script)


if __name__ == "__main__":  # pragma: no cover - uso manual
    sys.exit(main(json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}))
