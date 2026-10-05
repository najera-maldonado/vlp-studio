#!/usr/bin/env bash
# Reproduce, sobre un extracto pequeno del repositorio, la receta de conversion
# a grano grueso que produjo `sustratinaitor/1_capside/3J7L_cg.pdb`, y la
# contrasta con la variante sin protonar.
#
# Demuestra tres cosas:
#   1. pdb2pqr anade los hidrogenos de los que SIRAH deriva los beads BPG/BPE.
#   2. pdb2pqr reconstruye los TER aunque la entrada no los traiga.
#   3. cgconv.pl propaga esos TER al fichero CG.
#
# Requisitos: perl, python3, pdb2pqr (`pip install pdb2pqr`).
# Uso: herramientas/auditoria_cg/reproducir_receta.sh [directorio_de_trabajo]
set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TRABAJO="${1:-$(mktemp -d)}"
mkdir -p "$TRABAJO"

CGCONV="$RAIZ/PackMan.v.1.2/archivos_dm_cg/sirah_x2.3_24-07.amber/tools/CGCONV/cgconv.pl"
EMPAQUETADO="$RAIZ/PackMan.v.1.2/archivos_dm_cg/empaquetador/capside_1enzimas_20260324_212620.pdb"

echo "raiz del repositorio: $RAIZ"
echo "directorio de trabajo: $TRABAJO"

# ---------------------------------------------------------------------------
# Extrae las primeras 20 subunidades del PDB ya empaquetado por Packmol.
# Ese fichero no tiene TER y, a partir del atomo 100000, sus seriales son
# hexadecimales; nos quedamos por debajo de ese umbral a proposito.
# ---------------------------------------------------------------------------
python3 - "$EMPAQUETADO" "$TRABAJO/extracto.pdb" <<'PY'
import sys
origen, destino = sys.argv[1], sys.argv[2]
lineas = [l for l in open(origen) if l.startswith("ATOM")]
cortes, previo = [0], None
for i, l in enumerate(lineas):
    n = l[22:26].strip()
    if previo is not None and n != previo and int(n) <= int(previo):
        cortes.append(i)
    previo = n
with open(destino, "w") as fh:
    fh.writelines(lineas[cortes[0]:cortes[20]])
    fh.write("END\n")
print(f"extracto: 20 subunidades, {cortes[20]} atomos, 0 TER")
PY

# ---------------------------------------------------------------------------
# Ruta A (la de sustratinaitor): protonar con pdb2pqr y luego mapear a CG.
# ---------------------------------------------------------------------------
echo
echo "--- Ruta A: pdb2pqr --ff=AMBER  ->  cgconv.pl"
pdb2pqr30 --ff=AMBER "$TRABAJO/extracto.pdb" "$TRABAJO/extracto.pqr" > "$TRABAJO/pdb2pqr.log" 2>&1
perl "$CGCONV" -i "$TRABAJO/extracto.pqr" -o "$TRABAJO/extracto_cg.pdb" > "$TRABAJO/cgconv_A.log" 2>&1

# ---------------------------------------------------------------------------
# Ruta B (saltarse pdb2pqr): mapear a CG directamente desde el PDB sin H.
# ---------------------------------------------------------------------------
echo "--- Ruta B: cgconv.pl directamente sobre el PDB sin hidrogenos"
perl "$CGCONV" -i "$TRABAJO/extracto.pdb" -o "$TRABAJO/extracto_cg_sinH.pdb" > "$TRABAJO/cgconv_B.log" 2>&1

# ---------------------------------------------------------------------------
python3 - "$TRABAJO" "$RAIZ/sustratinaitor/1_capside/3J7L_cg.pdb" <<'PY'
import collections
import sys

trabajo, referencia = sys.argv[1], sys.argv[2]


def mirar(ruta):
    beads, ter = collections.Counter(), 0
    for l in open(ruta):
        if l.startswith("ATOM"):
            beads[l[12:16].strip()] += 1
        elif l.startswith("TER"):
            ter += 1
    return beads, ter


print()
print(f"{'fichero':<34} {'beads':>8} {'TER':>5} {'BPG':>6} {'BPE':>6}")
filas = [
    ("A  pdb2pqr -> cgconv", f"{trabajo}/extracto_cg.pdb"),
    ("B  cgconv directo (sin H)", f"{trabajo}/extracto_cg_sinH.pdb"),
    ("   referencia sustratinaitor", referencia),
]
for etiqueta, ruta in filas:
    b, t = mirar(ruta)
    print(f"{etiqueta:<34} {sum(b.values()):>8} {t:>5} "
          f"{b.get('BPG', 0):>6} {b.get('BPE', 0):>6}")

# Comparacion bead a bead de la primera subunidad contra la referencia.
def subunidades(ruta):
    out, cur = [], []
    for l in open(ruta):
        if l.startswith("ATOM"):
            cur.append(l)
        elif l.startswith("TER") and cur:
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


a = subunidades(f"{trabajo}/extracto_cg.pdb")[0]
r = subunidades(referencia)[0]
print()
print(f"subunidad 1: reproducida={len(a)} beads, referencia={len(r)} beads")
print("secuencia de nombres de bead identica:",
      [l[12:16] for l in a] == [l[12:16] for l in r])
print("resname+chainID+resSeq identicos     :",
      [l[17:26] for l in a] == [l[17:26] for l in r])
PY

echo
echo "Resultados en: $TRABAJO"
