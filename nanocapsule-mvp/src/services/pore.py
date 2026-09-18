"""
Puerta "A través" · Pac-Pore.

Perfil del poro (HOLE con eje de simetría exacto + rseed), sección de sustrato por
SMILES (RDKit), canal 3D, cribado de mutantes (PyMOL + HOLE), y docking (Vina) +
correlación radio-de-poro vs afinidad. Motor real de punta a punta, sobre los modelos
de la carpeta hermana Poromania (paths.POROMANIA_DIR).
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.core import paths
from src.services.common import _pdb_centroid

# --- Pac-Pore (puerta "a través") ---------------------------------------- #
# Sustratos con su radio de sección mínima (Å). Valores de literatura del
# diseño — ILUSTRATIVOS hasta portar el cálculo real.
_SUBSTRATES = [
    {"name": "Glucosilceramida", "disease": "Gaucher", "radius": 4.4},
    {"name": "Globotriaosilceramida", "disease": "Fabry", "radius": 4.6},
    {"name": "4-MU-β-glucopiranósido", "disease": "ensayo", "radius": 3.5},
    {"name": "Glucógeno (frag)", "disease": "Pompe", "radius": 5.1},
]

_PORE_AXES = ["3-fold · trímero", "5-fold · pentámero", "2-fold · dímero"]

# Radio mínimo ilustrativo del poro nativo (Å) por eje de simetría.
_AXIS_MIN = {"3-fold": 1.9, "5-fold": 3.2, "2-fold": 2.6}


def pore_config() -> Dict[str, Any]:
    """Ejes de simetría y sustratos disponibles para la puerta 'a través'."""
    return {"axes": _PORE_AXES, "substrates": _SUBSTRATES}


def pore_channels() -> Dict[str, Any]:
    """Canales HOLE disponibles (hole_spheres.pdb): de Poromania + los que generemos."""
    base = paths.POROMANIA_DIR
    channels = []
    if base.exists():
        for sph in sorted(base.glob("mutants/*/hole/resultados/hole_spheres.pdb")):
            channels.append({"id": sph.parents[2].name, "path": str(sph)})
    runs = paths.OUTPUT_DIR / "hole_runs"
    if runs.exists():
        for sph in sorted(runs.glob("*/hole_spheres.pdb")):
            channels.append({"id": "run:" + sph.parent.name, "path": str(sph)})
    crib = paths.OUTPUT_DIR / "cribado"
    if crib.exists():
        for sph in sorted(crib.glob("*/hole_*/hole_spheres.pdb")):
            key = sph.parents[1].name
            name = sph.parent.name[len("hole_") :]
            channels.append({"id": "cribado:" + key + "/" + name, "path": str(sph)})
    return {"channels": channels}


def hole_structures() -> Dict[str, Any]:
    """Estructuras de poro de Poromania sobre las que podemos correr HOLE."""
    base = paths.POROMANIA_DIR / "modelos"
    structures = []
    if base.exists():
        for pdb in sorted(base.glob("*/poro*.pdb")):
            structures.append({"key": f"{pdb.parent.name}/{pdb.stem}"})
    return {"structures": structures}


def _pore_axis(pdb_text: str, center: List[float]) -> List[float]:
    """Eje de simetría del poro (exacto para simetría Cn).

    Para un poro con simetría rotacional (3-fold, 5-fold…) el tensor de inercia
    tiene dos valores propios iguales (el plano) y uno distinto (el eje). El eje
    del poro es el eigenvector del valor propio DISTINTO — no el de mayor varianza
    (ese suele caer en el plano y hace que HOLE se escape del canal).
    """
    import numpy as np

    pts = []
    for line in pdb_text.split("\n"):
        if line.startswith(("ATOM", "HETATM")) and len(line) >= 54:
            try:
                pts.append([float(line[30:38]), float(line[38:46]), float(line[46:54])])
            except ValueError:
                continue
    a = np.array(pts) - np.array(center)
    w, vec = np.linalg.eigh(a.T @ a)  # w ascendente
    # El par de valores propios más cercano define el plano; el otro es el eje.
    if abs(w[1] - w[0]) < abs(w[2] - w[1]):
        axis = vec[:, 2]  # w0≈w1 (plano) → eje = mayor (prolato)
    else:
        axis = vec[:, 0]  # w1≈w2 (plano) → eje = menor (oblato)
    return [float(axis[0]), float(axis[1]), float(axis[2])]


def _parse_hole_profile(out_text: str):
    """Extrae (Z, Radio) del texto crudo de HOLE (misma lógica que 2out_tsv.py)."""
    zs, rs = [], []
    for line in out_text.splitlines():
        if line.strip().startswith("#") or "RADIUS" in line:
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        try:
            z, r = float(parts[0]), float(parts[1])
        except ValueError:
            continue
        if r > 0.5:
            zs.append(z)
            rs.append(r)
    return zs, rs


def _hole_on(receptor_pdb: Path, workdir: Path) -> Dict[str, Any]:
    """Motor: corre HOLE sobre un PDB (eje de simetría + rseed) y devuelve el perfil."""
    import shutil
    import subprocess

    workdir.mkdir(parents=True, exist_ok=True)
    shutil.copy(receptor_pdb, workdir / "receptor.pdb")
    shutil.copy(paths.POROMANIA_DIR / "scripts" / "vdwradii.lib", workdir / "vdwradii.lib")

    text = Path(receptor_pdb).read_text()
    c = _pdb_centroid(text)
    ax = _pore_axis(text, c)
    hole_input = (
        "coord receptor.pdb\n"
        "radius vdwradii.lib\n"
        f"cpoint {c[0]:.3f} {c[1]:.3f} {c[2]:.3f}\n"
        f"cvect {ax[0]:.4f} {ax[1]:.4f} {ax[2]:.4f}\n"
        "sphpdb hole_spheres.pdb\n"
        "endrad 10.0\n"
        "sample 0.25\n"
        "rseed 1\n"
    )
    proc = subprocess.run(
        ["hole"], input=hole_input, cwd=str(workdir), capture_output=True, text=True, timeout=180
    )
    (workdir / "hole_out.txt").write_text(proc.stdout)

    zs, rs = _parse_hole_profile(proc.stdout)
    if len(rs) < 30:
        raise RuntimeError("HOLE no trazó un canal válido (resultado degenerado)")
    mi = min(range(len(rs)), key=lambda i: rs[i])
    z0 = zs[mi]
    return {
        "positions": [round(z - z0, 2) for z in zs],
        "radius": [round(r, 3) for r in rs],
        "pore_min": round(rs[mi], 2),
        "min_index": mi,
        "n_points": len(rs),
        "axis": [round(v, 3) for v in ax],
    }


def run_hole(structure_key: str) -> Dict[str, Any]:
    """Corre HOLE de verdad sobre una estructura de poro de Poromania."""
    if not structure_key or ".." in structure_key:
        raise ValueError("Estructura inválida")
    pdb = (paths.POROMANIA_DIR / "modelos" / structure_key).with_suffix(".pdb")
    if not pdb.exists():
        raise FileNotFoundError(f"Estructura no encontrada: {structure_key}")
    workdir = paths.OUTPUT_DIR / "hole_runs" / structure_key.replace("/", "__")
    d = _hole_on(pdb, workdir)
    return {
        "structure": structure_key,
        "channel_id": "run:" + workdir.name,
        "illustrative": False,
        "source": "HOLE (calculado ahora)",
        **d,
    }


# --------------------------------------------------------------------------- #
# Cribado de mutantes: abrir el poro para que pase el sustrato
# --------------------------------------------------------------------------- #
def _chain_ids(pdb_text: str) -> List[str]:
    seen = []
    for line in pdb_text.split("\n"):
        if line.startswith("ATOM") and len(line) > 21:
            ch = line[21]
            if ch not in seen:
                seen.append(ch)
    return seen


def _constriction_point(spheres_pdb: Path):
    """Coordenada de la esfera de menor radio POSITIVO (la constricción real)."""
    import numpy as np

    best = None
    for line in spheres_pdb.read_text().split("\n"):
        if line.startswith(("ATOM", "HETATM")) and len(line) >= 66:
            try:
                r = float(line[60:66])
                xyz = [float(line[30:38]), float(line[38:46]), float(line[46:54])]
            except ValueError:
                continue
            if r > 0.5 and (best is None or r < best[0]):
                best = (r, np.array(xyz))
    return best[1] if best else None


def _pore_residues(pdb_text: str, constriction, chains: List[str], n: int = 3):
    """Residuos que revisten el poro: CA comunes a todas las cadenas, cerca de la constricción."""
    import numpy as np

    res = {}
    for line in pdb_text.split("\n"):
        if line.startswith("ATOM") and line[12:16].strip() == "CA":
            ch = line[21]
            try:
                ri = int(line[22:26])
                p = np.array([float(line[30:38]), float(line[38:46]), float(line[46:54])])
            except ValueError:
                continue
            d = float(np.linalg.norm(p - constriction))
            e = res.setdefault(ri, {"resn": line[17:20].strip(), "chains": set(), "mind": 1e9})
            e["chains"].add(ch)
            e["mind"] = min(e["mind"], d)
    common = [(ri, v) for ri, v in res.items() if len(v["chains"]) >= len(chains)]
    common.sort(key=lambda x: x[1]["mind"])
    return [{"pos": ri, "resn": v["resn"], "dist": round(v["mind"], 1)} for ri, v in common[:n]]


def _generate_mutants(wt_pdb: Path, chains: List[str], library: List[Dict], outdir: Path):
    """Genera los PDB de todos los mutantes en UNA llamada a PyMOL (mutagenesis wizard)."""
    import subprocess

    lines = ["from pymol import cmd", f"cmd.load(r'{wt_pdb}','WT')"]
    for mut in library:
        tag = mut["name"]
        lines.append(f"cmd.create('{tag}','WT')")
        for ch in chains:
            for pos, aa in mut["muts"].items():
                lines.append("cmd.wizard('mutagenesis'); w=cmd.get_wizard()")
                lines.append(
                    f"w.set_mode('{aa}'); w.do_select('/{tag}//{ch}/{pos}/'); w.apply(); cmd.set_wizard()"
                )
        lines.append("cmd.rebuild()")
        lines.append(f"cmd.save(r'{outdir}/{tag}.pdb','{tag}')")
        lines.append(f"cmd.delete('{tag}')")
    script = outdir / "_mutgen.py"
    script.write_text("\n".join(lines))
    subprocess.run(["pymol", "-cq", str(script)], capture_output=True, text=True, timeout=400)


_AA3 = {
    "ALA",
    "ARG",
    "ASN",
    "ASP",
    "CYS",
    "GLN",
    "GLU",
    "GLY",
    "HIS",
    "ILE",
    "LEU",
    "LYS",
    "MET",
    "PHE",
    "PRO",
    "SER",
    "THR",
    "TRP",
    "TYR",
    "VAL",
}


def evaluate_mutant(structure_key: str, mutations: Dict[str, str]) -> Dict[str, Any]:
    """Cribado MANUAL: evalúa un mutante concreto (posición→aminoácido) con HOLE."""
    if not structure_key or ".." in structure_key:
        raise ValueError("Estructura inválida")
    wt_pdb = (paths.POROMANIA_DIR / "modelos" / structure_key).with_suffix(".pdb")
    if not wt_pdb.exists():
        raise FileNotFoundError(f"Estructura no encontrada: {structure_key}")

    muts = {}
    for pos, aa in (mutations or {}).items():
        aa = str(aa).upper().strip()
        if aa not in _AA3:
            raise ValueError(f"Aminoácido inválido: {aa} (usa código de 3 letras, p.ej. GLY, TRP)")
        muts[str(pos).strip()] = aa
    if not muts:
        raise ValueError("Indica al menos una mutación (posición:aminoácido)")

    chains = _chain_ids(wt_pdb.read_text())
    name = "man_" + "_".join(f"{p}{aa[0]}" for p, aa in sorted(muts.items()))
    mutdir = paths.OUTPUT_DIR / "cribado" / structure_key.replace("/", "__")
    mutdir.mkdir(parents=True, exist_ok=True)
    _generate_mutants(wt_pdb, chains, [{"name": name, "muts": muts}], mutdir)

    pdb = mutdir / f"{name}.pdb"
    if not pdb.exists():
        raise RuntimeError("PyMOL no generó el mutante (¿posición o cadena inexistente?)")
    d = _hole_on(pdb, mutdir / ("hole_" + name))

    wt_min = None
    wt_out = paths.OUTPUT_DIR / "hole_runs" / structure_key.replace("/", "__") / "hole_out.txt"
    if wt_out.exists():
        _, rs = _parse_hole_profile(wt_out.read_text())
        if rs:
            wt_min = round(min(rs), 2)

    return {
        "name": name,
        "mutations": ", ".join(f"{p}{aa}" for p, aa in muts.items()),
        "pore_min": d["pore_min"],
        "delta": round(d["pore_min"] - wt_min, 2) if wt_min is not None else None,
        "channel_id": "cribado:" + structure_key.replace("/", "__") + "/" + name,
    }


def screen_mutants(structure_key: str, substrate_radius: Optional[float] = None) -> Dict[str, Any]:
    """Cribado real: muta los residuos del poro a AAs pequeños, corre HOLE y rankea."""
    if not structure_key or ".." in structure_key:
        raise ValueError("Estructura inválida")
    wt_pdb = (paths.POROMANIA_DIR / "modelos" / structure_key).with_suffix(".pdb")
    if not wt_pdb.exists():
        raise FileNotFoundError(f"Estructura no encontrada: {structure_key}")

    # 1) WT + constricción + residuos del poro
    wt = run_hole(structure_key)
    wt_workdir = paths.OUTPUT_DIR / "hole_runs" / structure_key.replace("/", "__")
    constriction = _constriction_point(wt_workdir / "hole_spheres.pdb")
    text = wt_pdb.read_text()
    chains = _chain_ids(text)
    residues = _pore_residues(text, constriction, chains, n=3)
    pos = [str(r["pos"]) for r in residues]

    # 2) librería de mutantes (progresiva: abrir el poro a GLY/ALA)
    library = []
    for i in range(len(pos)):
        library.append({"name": f"m_{pos[i]}G", "muts": {pos[i]: "GLY"}})
    if len(pos) >= 2:
        library.append(
            {"name": "m_" + "_".join(pos[:2]) + "G", "muts": {p: "GLY" for p in pos[:2]}}
        )
    if len(pos) >= 3:
        library.append({"name": "m_" + "_".join(pos) + "G", "muts": {p: "GLY" for p in pos}})
        library.append({"name": "m_" + "_".join(pos) + "A", "muts": {p: "ALA" for p in pos}})

    # 3) generar todos los mutantes en una llamada a PyMOL
    mutdir = paths.OUTPUT_DIR / "cribado" / structure_key.replace("/", "__")
    mutdir.mkdir(parents=True, exist_ok=True)
    _generate_mutants(wt_pdb, chains, library, mutdir)

    # 4) HOLE en cada mutante
    results = []
    for mut in library:
        pdb = mutdir / f"{mut['name']}.pdb"
        if not pdb.exists():
            continue
        try:
            d = _hole_on(pdb, mutdir / ("hole_" + mut["name"]))
            pmin = d["pore_min"]
            results.append(
                {
                    "name": mut["name"],
                    "mutations": ", ".join(f"{p}{aa[0]}" for p, aa in mut["muts"].items()),
                    "pore_min": pmin,
                    "delta": round(pmin - wt["pore_min"], 2),
                    "passes": (substrate_radius is not None and pmin >= substrate_radius),
                    "channel_id": "cribado:" + structure_key.replace("/", "__") + "/" + mut["name"],
                }
            )
        except Exception:
            continue

    results.sort(key=lambda r: r["pore_min"], reverse=True)
    return {
        "structure": structure_key,
        "wt_min": wt["pore_min"],
        "substrate_radius": substrate_radius,
        "pore_residues": residues,
        "mutants": results,
    }


# --------------------------------------------------------------------------- #
# Docking (vina) + correlación radio de poro vs afinidad
# --------------------------------------------------------------------------- #
def _prep_receptor_pdbqt(pdb_path: Path, out_pdbqt: Path):
    import subprocess

    h = out_pdbqt.with_name(out_pdbqt.stem + "_H.pdb")
    subprocess.run(
        ["obabel", str(pdb_path), "-O", str(h), "-p", "7.4", "-h", "--errorlevel", "1"],
        capture_output=True,
        timeout=180,
    )
    subprocess.run(
        [
            "obabel",
            str(h),
            "-O",
            str(out_pdbqt),
            "-xr",
            "--partialcharge",
            "gasteiger",
            "--errorlevel",
            "1",
        ],
        capture_output=True,
        timeout=180,
    )
    if not out_pdbqt.exists() or out_pdbqt.stat().st_size == 0:
        raise RuntimeError("No se pudo preparar el receptor (obabel)")


def _prep_ligand_pdbqt(smiles: str, out_pdbqt: Path):
    import subprocess

    subprocess.run(
        [
            "obabel",
            f"-:{smiles}",
            "-O",
            str(out_pdbqt),
            "--gen3d",
            "-p",
            "7.4",
            "--partialcharge",
            "gasteiger",
            "--errorlevel",
            "1",
        ],
        capture_output=True,
        timeout=180,
    )
    if not out_pdbqt.exists() or out_pdbqt.stat().st_size == 0:
        raise RuntimeError("No se pudo preparar el ligando desde el SMILES")


def _vina_affinity(
    receptor_pdbqt: Path, ligand_pdbqt: Path, center, size: int, workdir: Path
) -> float:
    import subprocess

    out = workdir / "dock_out.pdbqt"
    subprocess.run(
        [
            "vina",
            "--receptor",
            str(receptor_pdbqt),
            "--ligand",
            str(ligand_pdbqt),
            "--center_x",
            f"{center[0]:.3f}",
            "--center_y",
            f"{center[1]:.3f}",
            "--center_z",
            f"{center[2]:.3f}",
            "--size_x",
            str(size),
            "--size_y",
            str(size),
            "--size_z",
            str(size),
            "--exhaustiveness",
            "8",
            "--seed",
            "1",
            "--out",
            str(out),
        ],
        capture_output=True,
        text=True,
        timeout=400,
    )
    if out.exists():
        for line in out.read_text().split("\n"):
            if line.startswith("REMARK VINA RESULT"):
                return float(line.split()[3])  # mejor afinidad (kcal/mol)
    raise RuntimeError("vina no devolvió afinidad")


def _pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = sum((x - mx) ** 2 for x in xs) ** 0.5
    dy = sum((y - my) ** 2 for y in ys) ** 0.5
    return round(num / (dx * dy), 3) if dx and dy else None


def dock_correlate(structure_key: str, smiles: str) -> Dict[str, Any]:
    """Dockea el sustrato (SMILES) en WT + mutantes del cribado y correlaciona
    radio de poro vs afinidad de unión (vina)."""
    smiles = (smiles or "").strip()
    if not smiles:
        raise ValueError("Falta el SMILES del sustrato para el docking")

    section = substrate_section(smiles)
    scr = screen_mutants(structure_key, substrate_radius=section)
    key = structure_key.replace("/", "__")
    crib = paths.OUTPUT_DIR / "cribado" / key
    dockdir = paths.OUTPUT_DIR / "docking" / key
    dockdir.mkdir(parents=True, exist_ok=True)

    lig = dockdir / "ligand.pdbqt"
    _prep_ligand_pdbqt(smiles, lig)

    wt_model = (paths.POROMANIA_DIR / "modelos" / structure_key).with_suffix(".pdb")
    entries = [
        {
            "name": "WT",
            "pore_min": scr["wt_min"],
            "pdb": wt_model,
            "spheres": paths.OUTPUT_DIR / "hole_runs" / key / "hole_spheres.pdb",
            "passes": None,
        }
    ]
    for m in scr["mutants"][:4]:  # WT + top 4 mutantes (acota el tiempo)
        entries.append(
            {
                "name": m["name"],
                "pore_min": m["pore_min"],
                "pdb": crib / (m["name"] + ".pdb"),
                "spheres": crib / ("hole_" + m["name"]) / "hole_spheres.pdb",
                "passes": m["passes"],
            }
        )

    results = []
    for e in entries:
        try:
            rec = dockdir / (e["name"] + "_receptor.pdbqt")
            if not rec.exists():
                _prep_receptor_pdbqt(e["pdb"], rec)
            center = _constriction_point(e["spheres"])
            size = max(24, int(round(2 * (e["pore_min"] + 6))))
            wd = dockdir / ("dock_" + e["name"])
            wd.mkdir(exist_ok=True)
            aff = _vina_affinity(rec, lig, center, size, wd)
            results.append(
                {
                    "name": e["name"],
                    "pore_min": e["pore_min"],
                    "affinity": aff,
                    "passes": e["passes"],
                }
            )
        except Exception:
            continue

    corr = _pearson([r["pore_min"] for r in results], [r["affinity"] for r in results])
    return {
        "structure": structure_key,
        "smiles": smiles,
        "section": section,
        "points": results,
        "correlation": corr,
    }


def pore_channel_content(structure_id: str) -> str:
    """Contenido del hole_spheres.pdb de una estructura (radio del canal en B-factor)."""
    for ch in pore_channels()["channels"]:
        if ch["id"] == structure_id:
            return Path(ch["path"]).read_text()
    raise FileNotFoundError(f"Canal no encontrado: {structure_id}")


def substrate_section(smiles: str) -> Optional[float]:
    """Radio de sección mínima (Å) de un sustrato desde su SMILES (RDKit + PCA).

    Genera la geometría 3D, la orienta por sus ejes principales y toma el menor
    semieje: es el radio del canal más estrecho por el que la molécula podría pasar.
    """
    smiles = (smiles or "").strip()
    if not smiles:
        return None

    import numpy as np
    from rdkit import Chem  # import perezoso
    from rdkit.Chem import AllChem

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"SMILES inválido: {smiles}")
    mol = Chem.AddHs(mol)
    params = AllChem.ETKDGv3()
    params.randomSeed = 42
    params.useRandomCoords = True
    params.maxIterations = 2000
    if AllChem.EmbedMolecule(mol, params) != 0:
        if AllChem.EmbedMolecule(mol, useRandomCoords=True, randomSeed=7, maxIterations=2000) != 0:
            raise ValueError("No se pudo generar la geometría 3D del SMILES")
    try:
        AllChem.MMFFOptimizeMolecule(mol, maxIters=500)
    except Exception:
        pass

    conf = mol.GetConformer()
    xyz = np.array(
        [
            [conf.GetAtomPosition(i).x, conf.GetAtomPosition(i).y, conf.GetAtomPosition(i).z]
            for i in range(mol.GetNumAtoms())
        ]
    )
    xyz -= xyz.mean(axis=0)
    _, _, vt = np.linalg.svd(xyz, full_matrices=False)
    ext = xyz @ vt.T
    half_extents = (ext.max(axis=0) - ext.min(axis=0)) / 2.0
    return round(float(sorted(half_extents)[0]), 2)


def pore_profile(capsid_name: str, axis: str, n_points: int = 61) -> Dict[str, Any]:
    """
    Perfil radio-vs-eje del canal. HOY es ilustrativo: una constricción
    gaussiana centrada. Para hacerlo real, basta sustituir el cuerpo por la
    salida de HOLE (o una sonda que crece por el eje) manteniendo esta forma
    de retorno; el frontend no cambia.
    """
    key = (axis or "3-fold").split(" ")[0]
    pore_min = _AXIS_MIN.get(key, 2.0)
    # Pequeño desplazamiento determinista por cápside para que varíe.
    offset = (sum(ord(c) for c in (capsid_name or "")) % 7) * 0.05
    pore_min = round(pore_min + offset, 2)

    mouth = 4.7  # radio en la boca del canal
    half = n_points // 2
    width = (n_points / 6.0) ** 2  # anchura de la gaussiana

    positions: List[int] = []
    radius: List[float] = []
    for i in range(n_points):
        x = i - half
        r = mouth - (mouth - pore_min) * math.exp(-(x * x) / width)
        positions.append(x)
        radius.append(round(r, 2))

    return {
        "capsid": capsid_name,
        "axis": axis,
        "positions": positions,
        "radius": radius,
        "pore_min": pore_min,
        "mouth": mouth,
        "min_index": half,
        "illustrative": True,
    }
