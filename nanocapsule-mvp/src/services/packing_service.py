"""
Capa de aplicación (casos de uso) para el diseño de nanocápsulas.

Esta es la frontera limpia entre los adaptadores de entrada (Flask, un futuro
CLI, tests) y el dominio (Capsid, Cargo, ParallelPacker). Ningún adaptador debe
hablar con el dominio directamente: todos pasan por aquí.

Ventajas:
- Sin dependencia de Flask -> se puede llamar desde un script o un test.
- Sin rutas relativas -> usa src.core.paths.
- Un único lugar donde vive cada caso de uso.
"""

from __future__ import annotations

import datetime
import math
import random
import string
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.core import paths
from src.core.config import ConfigManager
from src.io.structure_fetcher import StructureFetcher

# Una sola instancia de configuración y fetcher para todo el proceso.
_config = ConfigManager()
_fetcher = StructureFetcher(str(paths.INPUT_DIR))


# --------------------------------------------------------------------------- #
# Biblioteca de estructuras
# --------------------------------------------------------------------------- #
def list_library() -> Dict[str, Any]:
    """Devuelve las cápsides y enzimas disponibles."""
    capsides = _fetcher.list_available_capsides()
    enzymes = _fetcher.list_available_enzymes()
    return {
        "capsides": capsides,
        "enzymes": enzymes,
        "total_combinations": len(capsides) * len(enzymes),
    }


# Rol/uso de cada enzima (por código PDB). Honesto: solo GCase es terapéutica;
# el resto son proteínas modelo/reporteras que hay realmente en la biblioteca.
_ENZYME_ROLE = {
    "1OGS": {"enfermedad": "Gaucher", "rol": "terapéutica"},
    "1ED8": {"enfermedad": "—", "rol": "enzima modelo"},
    "4EUL": {"enfermedad": "—", "rol": "reporter fluorescente"},
    "1LCI": {"enfermedad": "—", "rol": "reporter bioluminiscente"},
}

_T_NUMBER = {3: "T=3", 4: "T=4", 7: "T=7"}

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


# --------------------------------------------------------------------------- #
# Pac-Pore · perfil del poro (ILUSTRATIVO — listo para portar HOLE a Python)
# --------------------------------------------------------------------------- #
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
            name = sph.parent.name[len("hole_"):]
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
    w, vec = np.linalg.eigh(a.T @ a)          # w ascendente
    # El par de valores propios más cercano define el plano; el otro es el eje.
    if abs(w[1] - w[0]) < abs(w[2] - w[1]):
        axis = vec[:, 2]                       # w0≈w1 (plano) → eje = mayor (prolato)
    else:
        axis = vec[:, 0]                       # w1≈w2 (plano) → eje = menor (oblato)
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
    proc = subprocess.run(["hole"], input=hole_input, cwd=str(workdir),
                          capture_output=True, text=True, timeout=180)
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
    return {"structure": structure_key, "channel_id": "run:" + workdir.name,
            "illustrative": False, "source": "HOLE (calculado ahora)", **d}


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
                lines.append(f"w.set_mode('{aa}'); w.do_select('/{tag}//{ch}/{pos}/'); w.apply(); cmd.set_wizard()")
        lines.append("cmd.rebuild()")
        lines.append(f"cmd.save(r'{outdir}/{tag}.pdb','{tag}')")
        lines.append(f"cmd.delete('{tag}')")
    script = outdir / "_mutgen.py"
    script.write_text("\n".join(lines))
    subprocess.run(["pymol", "-cq", str(script)], capture_output=True, text=True, timeout=400)


_AA3 = {"ALA", "ARG", "ASN", "ASP", "CYS", "GLN", "GLU", "GLY", "HIS", "ILE",
        "LEU", "LYS", "MET", "PHE", "PRO", "SER", "THR", "TRP", "TYR", "VAL"}


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
        library.append({"name": "m_" + "_".join(pos[:2]) + "G", "muts": {p: "GLY" for p in pos[:2]}})
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
            results.append({
                "name": mut["name"],
                "mutations": ", ".join(f"{p}{aa[0]}" for p, aa in mut["muts"].items()),
                "pore_min": pmin,
                "delta": round(pmin - wt["pore_min"], 2),
                "passes": (substrate_radius is not None and pmin >= substrate_radius),
                "channel_id": "cribado:" + structure_key.replace("/", "__") + "/" + mut["name"],
            })
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
    subprocess.run(["obabel", str(pdb_path), "-O", str(h), "-p", "7.4", "-h", "--errorlevel", "1"],
                   capture_output=True, timeout=180)
    subprocess.run(["obabel", str(h), "-O", str(out_pdbqt), "-xr", "--partialcharge", "gasteiger", "--errorlevel", "1"],
                   capture_output=True, timeout=180)
    if not out_pdbqt.exists() or out_pdbqt.stat().st_size == 0:
        raise RuntimeError("No se pudo preparar el receptor (obabel)")


def _prep_ligand_pdbqt(smiles: str, out_pdbqt: Path):
    import subprocess
    subprocess.run(["obabel", f"-:{smiles}", "-O", str(out_pdbqt), "--gen3d", "-p", "7.4",
                    "--partialcharge", "gasteiger", "--errorlevel", "1"],
                   capture_output=True, timeout=180)
    if not out_pdbqt.exists() or out_pdbqt.stat().st_size == 0:
        raise RuntimeError("No se pudo preparar el ligando desde el SMILES")


def _vina_affinity(receptor_pdbqt: Path, ligand_pdbqt: Path, center, size: int, workdir: Path) -> float:
    import subprocess
    out = workdir / "dock_out.pdbqt"
    subprocess.run(["vina", "--receptor", str(receptor_pdbqt), "--ligand", str(ligand_pdbqt),
                    "--center_x", f"{center[0]:.3f}", "--center_y", f"{center[1]:.3f}", "--center_z", f"{center[2]:.3f}",
                    "--size_x", str(size), "--size_y", str(size), "--size_z", str(size),
                    "--exhaustiveness", "8", "--seed", "1", "--out", str(out)],
                   capture_output=True, text=True, timeout=400)
    if out.exists():
        for line in out.read_text().split("\n"):
            if line.startswith("REMARK VINA RESULT"):
                return float(line.split()[3])           # mejor afinidad (kcal/mol)
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
    entries = [{"name": "WT", "pore_min": scr["wt_min"], "pdb": wt_model,
                "spheres": paths.OUTPUT_DIR / "hole_runs" / key / "hole_spheres.pdb", "passes": None}]
    for m in scr["mutants"][:4]:                       # WT + top 4 mutantes (acota el tiempo)
        entries.append({"name": m["name"], "pore_min": m["pore_min"],
                        "pdb": crib / (m["name"] + ".pdb"),
                        "spheres": crib / ("hole_" + m["name"]) / "hole_spheres.pdb",
                        "passes": m["passes"]})

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
            results.append({"name": e["name"], "pore_min": e["pore_min"],
                            "affinity": aff, "passes": e["passes"]})
        except Exception:
            continue

    corr = _pearson([r["pore_min"] for r in results], [r["affinity"] for r in results])
    return {"structure": structure_key, "smiles": smiles, "section": section,
            "points": results, "correlation": corr}


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

    from rdkit import Chem                # import perezoso
    from rdkit.Chem import AllChem
    import numpy as np

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
    xyz = np.array([[conf.GetAtomPosition(i).x, conf.GetAtomPosition(i).y, conf.GetAtomPosition(i).z]
                    for i in range(mol.GetNumAtoms())])
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

    mouth = 4.7                         # radio en la boca del canal
    half = n_points // 2
    width = (n_points / 6.0) ** 2       # anchura de la gaussiana

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


# --------------------------------------------------------------------------- #
# De-inmunización · mapa ΔMHC vs ΔΔG (ILUSTRATIVO — puerta "fuera")
# --------------------------------------------------------------------------- #
# Cada mutante: dmhc (X, negativo = silencia el epítopo) y ddg (Y, negativo =
# estabiliza la cápside). DIANA = cuadrante inferior-izquierdo (silencia + estabiliza).
# Ancla real: Bing 2024 · R312Q (mutación de-inmunizante validada en AAV).
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


# --------------------------------------------------------------------------- #
# Análisis MD · curvas de ejemplo (ILUSTRATIVO — puerta 4 "sobrevive")
# Portar: sustituir cada `points` por los .dat reales de PackMan (frame, valor).
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


# --------------------------------------------------------------------------- #
# Radio interno
# --------------------------------------------------------------------------- #
def calculate_radius(capsid_name: str, save: bool = True) -> float:
    """Calcula el radio interno de una cápside vía PyMOL (dominio)."""
    from src.core.capsid import Capsid  # import perezoso: PyMOL es pesado

    path = structure_path("capside", capsid_name)
    if not path.exists():
        raise FileNotFoundError(f"Cápside no encontrada: {capsid_name}")

    capsid = Capsid(str(path))
    return capsid.calculate_internal_radius(save_to_file=save)


# --------------------------------------------------------------------------- #
# Preview rápido (colocación aleatoria, sin Packmol) — antes vivía en app.py
# --------------------------------------------------------------------------- #
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


def _random_positions(n: int, radius: float, min_distance: float) -> List[List[float]]:
    """Posiciones aleatorias uniformes dentro de una esfera, con distancia mínima."""
    effective_radius = radius * 0.8  # margen para que las enzimas no toquen la pared
    positions: List[List[float]] = []
    max_attempts = 1000

    for i in range(n):
        placed = False
        for _ in range(max_attempts):
            x, y, z = (random.uniform(-1, 1) for _ in range(3))
            if x * x + y * y + z * z > 1:
                continue
            candidate = [x * effective_radius, y * effective_radius, z * effective_radius]
            if all(
                math.dist(candidate, p) >= min_distance for p in positions
            ):
                positions.append(candidate)
                placed = True
                break
        if not placed:
            # No cupo respetando distancia: colocar en la superficie efectiva.
            x, y, z = (random.uniform(-1, 1) for _ in range(3))
            norm = math.sqrt(x * x + y * y + z * z) or 1.0
            positions.append(
                [x / norm * effective_radius, y / norm * effective_radius, z / norm * effective_radius]
            )
    return positions


def preview(
    capsid_name: str,
    enzyme_name: str,
    n_enzymes: int = 10,
    radius: float = 50.0,
    save_file: bool = False,
) -> Dict[str, Any]:
    """
    Genera un PDB combinado (cápside + N enzimas colocadas al azar) al instante.

    Devuelve un dict con el contenido del PDB, el nombre de archivo y, si se pidió,
    la ruta guardada. Es una vista previa: no ejecuta Packmol.
    """
    capsid_path = structure_path("capside", capsid_name)
    enzyme_path = structure_path("enzima", enzyme_name)
    if not capsid_path.exists() or not enzyme_path.exists():
        raise FileNotFoundError("Cápside o enzima no encontrada")

    capsid_content = capsid_path.read_text()
    enzyme_content = enzyme_path.read_text()

    min_distance = _config.get("packing.exclusion_radius", 10.0)
    positions = _random_positions(n_enzymes, radius, min_distance)

    # La cápside no está centrada en el origen: desplazo las enzimas a su
    # centroide para que queden realmente DENTRO de la cápside.
    cx, cy, cz = _pdb_centroid(capsid_content)
    positions = [[p[0] + cx, p[1] + cy, p[2] + cz] for p in positions]

    # La enzima tampoco está centrada en su origen: resto su propio centroide
    # para que cada copia caiga EXACTAMENTE en su posición asignada (si no, el
    # cúmulo entero se desplaza — el bug que se veía con GCase).
    ex, ey, ez = _pdb_centroid(enzyme_content)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines: List[str] = [
        f"HEADER    NANOCAPSULE GENERATED PDB                       {timestamp}",
        f"TITLE     {capsid_name} WITH {n_enzymes} {enzyme_name} ENZYMES",
        "REMARK    Generated by Nanocapsule MVP (preview service)",
        f"REMARK    Capsid: {capsid_name}",
        f"REMARK    Enzyme: {enzyme_name}",
        f"REMARK    Number of enzymes: {n_enzymes}",
        f"REMARK    Internal radius used: {radius:.1f} A",
        "",
        capsid_content,
    ]

    chain_ids = list(string.ascii_uppercase) + [
        f"{a}{b}" for a in string.ascii_uppercase for b in string.ascii_uppercase
    ]
    atom_counter = 10000

    for i, pos in enumerate(positions):
        lines.append(f"\nMODEL     {i + 1}")
        chain_id = chain_ids[i % len(chain_ids)][0]
        for line in enzyme_content.split("\n"):
            if line.startswith(("ATOM", "HETATM")):
                x = float(line[30:38]) if len(line) > 38 else 0.0
                y = float(line[38:46]) if len(line) > 46 else 0.0
                z = float(line[46:54]) if len(line) > 54 else 0.0
                new_line = (
                    line[:6]
                    + f"{atom_counter:5d}"
                    + line[11:21]
                    + chain_id
                    + line[22:30]
                    + f"{x - ex + pos[0]:8.3f}{y - ey + pos[1]:8.3f}{z - ez + pos[2]:8.3f}"
                    + (line[54:] if len(line) > 54 else "")
                )
                lines.append(new_line)
                atom_counter += 1
            elif line.strip():
                lines.append(line)
        lines.append("ENDMDL")

    lines.append("END")
    content = "\n".join(lines)

    timestamp_short = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{capsid_name}_{n_enzymes}enzimas_{enzyme_name}_{timestamp_short}.pdb"

    saved_path: Optional[Path] = None
    if save_file:
        paths.ensure_output_dirs()
        saved_path = paths.GENERATED_DIR / filename
        saved_path.write_text(content)

    return {
        "content": content,
        "filename": filename,
        "saved_path": str(saved_path) if saved_path else None,
        "n_enzymes": n_enzymes,
        "radius": radius,
    }


# --------------------------------------------------------------------------- #
# Colocador de sustrato ALREDEDOR de la cápside (ILUSTRATIVO — como sustratinaitor)
# Coloca N copias del sustrato en una caja del tamaño de la cápside, en la
# cavidad interna y en el exterior, evitando el cascarón. Portar: sustituir por
# Packmol real (fija la cápside, empaqueta N sustratos en la caja).
# --------------------------------------------------------------------------- #
# Plantilla de un sustrato: cadena corta de ~12 beads (glucosilceramida ilustrativa).
_SUBSTRATE_TEMPLATE = [(i * 1.6, 1.2 * math.sin(i * 0.9), 0.8 * math.cos(i * 0.6)) for i in range(12)]
_ST_CX = sum(p[0] for p in _SUBSTRATE_TEMPLATE) / len(_SUBSTRATE_TEMPLATE)
_ST_CY = sum(p[1] for p in _SUBSTRATE_TEMPLATE) / len(_SUBSTRATE_TEMPLATE)
_ST_CZ = sum(p[2] for p in _SUBSTRATE_TEMPLATE) / len(_SUBSTRATE_TEMPLATE)
_SUBSTRATE_CENTERED = [(x - _ST_CX, y - _ST_CY, z - _ST_CZ) for x, y, z in _SUBSTRATE_TEMPLATE]


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


def _rot(p, ax, ay, az):
    """Rota un punto por ángulos de Euler (determinista, para variar orientación)."""
    x, y, z = p
    y, z = y * math.cos(ax) - z * math.sin(ax), y * math.sin(ax) + z * math.cos(ax)
    x, z = x * math.cos(ay) + z * math.sin(ay), -x * math.sin(ay) + z * math.cos(ay)
    x, y = x * math.cos(az) - y * math.sin(az), x * math.sin(az) + y * math.cos(az)
    return x, y, z


def _around_positions(n, center, r_inner, r_outer, box, min_distance=7.0):
    """Posiciones en la cavidad (r<r_inner) o en el exterior (r>r_outer), dentro de la caja."""
    cx, cy, cz = center
    positions: List[List[float]] = []
    attempts = 0
    while len(positions) < n and attempts < n * 300:
        attempts += 1
        x, y, z = (random.uniform(-box, box) for _ in range(3))
        r = math.sqrt(x * x + y * y + z * z)
        if r < r_inner * 0.85 or r > r_outer * 1.04:   # cavidad o fuera del cascarón
            cand = [cx + x, cy + y, cz + z]
            if all(math.dist(cand, p) >= min_distance for p in positions):
                positions.append(cand)
    return positions


# Plantilla de sustrato generada desde un SMILES (RDKit), cacheada por SMILES.
_smiles_cache: Dict[str, List] = {}


def _smiles_to_template(smiles: str) -> List:
    """SMILES → coordenadas 3D de los átomos pesados (elem, x, y, z), centradas."""
    smiles = (smiles or "").strip()
    if not smiles:
        return None
    if len(smiles) > 400:
        raise ValueError("SMILES demasiado largo")
    if smiles in _smiles_cache:
        return _smiles_cache[smiles]

    from rdkit import Chem            # import perezoso
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
    atoms = []
    for i, a in enumerate(mol.GetAtoms()):
        if a.GetSymbol() == "H":
            continue
        p = conf.GetAtomPosition(i)
        atoms.append((a.GetSymbol(), p.x, p.y, p.z))
    if not atoms:
        raise ValueError("SMILES sin átomos pesados")

    cx = sum(a[1] for a in atoms) / len(atoms)
    cy = sum(a[2] for a in atoms) / len(atoms)
    cz = sum(a[3] for a in atoms) / len(atoms)
    atoms = [(e, x - cx, y - cy, z - cz) for e, x, y, z in atoms]
    _smiles_cache[smiles] = atoms
    return atoms


def preview_substrate(capsid_name: str, n: int = 60, smiles: str = None,
                      save_file: bool = False) -> Dict[str, Any]:
    """PDB combinado: cápside (modelo 0) + N copias de sustrato colocadas alrededor.

    Si `smiles` viene, el sustrato se genera desde ese SMILES con RDKit; si no, se
    usa la plantilla sintética simple.
    """
    capsid_path = structure_path("capside", capsid_name)
    if not capsid_path.exists():
        raise FileNotFoundError(f"Cápside no encontrada: {capsid_name}")

    # Plantilla del sustrato: (elemento, x, y, z) centrada en el origen.
    tpl = _smiles_to_template(smiles)
    if tpl is None:
        tpl = [("C", x, y, z) for x, y, z in _SUBSTRATE_CENTERED]

    capsid_content = capsid_path.read_text()
    center = _pdb_centroid(capsid_content)
    r_outer = _max_radius(capsid_content, center)
    r_inner = r_outer * 0.72          # cavidad interna aprox (ilustrativo)
    box = r_outer * 1.2               # caja del tamaño de la cápside (como sustratinaitor)

    positions = _around_positions(n, center, r_inner, r_outer, box)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines: List[str] = [
        f"HEADER    NANOCAPSULE SUBSTRATE PLACEMENT                {timestamp}",
        f"TITLE     {capsid_name} WITH {len(positions)} SUBSTRATE COPIES (AROUND)",
        f"REMARK    Sustrato: {'SMILES ' + smiles if smiles else 'plantilla simple'}",
        "",
        capsid_content,
    ]

    chain_ids = list(string.ascii_uppercase)
    atom = 20000
    for i, pos in enumerate(positions):
        lines.append(f"\nMODEL     {i + 1}")
        chain = chain_ids[i % len(chain_ids)]
        res = (i % 9999) + 1
        for j, (elem, ax, ay, az) in enumerate(tpl):
            bx, by, bz = _rot((ax, ay, az), i * 0.7, i * 1.3, i * 0.5)
            x, y, z = pos[0] + bx, pos[1] + by, pos[2] + bz
            name = (elem + str(j))[:4]
            lines.append(
                f"HETATM{atom:5d} {name:<4} LIG {chain}{res:4d}    "
                f"{x:8.3f}{y:8.3f}{z:8.3f}  1.00  0.00          {elem:>2}"
            )
            atom += 1
        lines.append("ENDMDL")
    lines.append("END")
    content = "\n".join(lines)

    saved_path: Optional[Path] = None
    if save_file:
        paths.ensure_output_dirs()
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_path = paths.GENERATED_DIR / f"{capsid_name}_sustrato_{len(positions)}_{ts}.pdb"
        saved_path.write_text(content)

    return {"content": content, "n": len(positions), "saved_path": str(saved_path) if saved_path else None}


# --------------------------------------------------------------------------- #
# Experimento real (Packmol, múltiples réplicas en paralelo)
# --------------------------------------------------------------------------- #
def run_experiment(
    capsid_name: str,
    enzyme_name: str,
    n_replicas: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Ejecuta el empaquetamiento máximo real con Packmol y múltiples réplicas.

    Bloquea hasta terminar (puede tardar minutos). En una versión escalable esto
    se movería a una cola de trabajos en background; aquí es síncrono a propósito
    para el prototipo.
    """
    from src.core.experiment_runner import ExperimentRunner

    if n_replicas is None:
        n_replicas = _config.get("experiments.n_replicas", 10)

    capsid_path = structure_path("capside", capsid_name)
    enzyme_path = structure_path("enzima", enzyme_name)
    if not capsid_path.exists() or not enzyme_path.exists():
        raise FileNotFoundError("Archivos de estructura no encontrados")

    paths.ensure_output_dirs()
    runner = ExperimentRunner(output_base_dir=str(paths.OUTPUT_DIR), config=_config)
    results = runner.run_maximum_packing(
        capsid_file=str(capsid_path),
        enzyme_file=str(enzyme_path),
        capsid_name=capsid_name,
        enzyme_name=enzyme_name,
        n_replicas=n_replicas,
    )
    return results
