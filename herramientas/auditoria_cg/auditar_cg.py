#!/usr/bin/env python3
"""
Auditoria empirica de las conversiones a grano grueso (SIRAH) de VLP Studio.

Compara la ruta de PackMan (empaquetar -> convertir) con la de sustratinaitor
(convertir -> empaquetar) midiendo sobre los PDB reales del repositorio:

  A. Beads por residuo frente al mapa oficial `sirah_prot.map`.
  B. Beads que SIRAH deriva de un hidrogeno (BPG en CYS/SER/THR, BPE en TRP):
     su presencia prueba que la estructura de partida estaba protonada.
  C. Registros TER y numero de subunidades.
  D. Distancias entre residuos consecutivos, dentro de una subunidad y a traves
     de las fronteras, para detectar encadenamiento covalente espurio.
  E. Seriales de atomo invalidos (hexadecimales por desbordamiento del campo).
  F. Reparto espacial del sustrato GYE respecto a la cascara de la capside.

Uso:
    python3 herramientas/auditoria_cg/auditar_cg.py [raiz_del_repo]

Dependencias: numpy. `scipy` es opcional (acelera la seccion F).
Licencia: AGPLv3 o posterior, como el resto del codigo propio del repositorio.
"""
from __future__ import annotations

import collections
import os
import re
import sys

import numpy as np

try:
    from scipy.spatial import cKDTree
except ImportError:  # pragma: no cover
    cKDTree = None

# --------------------------------------------------------------------------
# Rutas relativas a la raiz del repositorio
# --------------------------------------------------------------------------

MAPA_SIRAH = ("PackMan.v.1.2/archivos_dm_cg/sirah_x2.3_24-07.amber/"
              "tools/CGCONV/maps/sirah_prot.map")
CAPSIDE_CG = "sustratinaitor/1_capside/3J7L_cg.pdb"
CAPSIDE_AA = "PackMan.v.1.2/archivos_dm_cg/empaquetador/capside.pdb"
ENZIMA_AA = "PackMan.v.1.2/archivos_dm_cg/empaquetador/enzima.pdb"
PACKMAN_OUT = ("PackMan.v.1.2/archivos_dm_cg/empaquetador/"
               "capside_1enzimas_20260324_212620.pdb")
SUSTRATO_OUT = "sustratinaitor/3_empaquetado_packmol/3J7L-GYE.pdb"
GYE_AA = "sustratinaitor/2_ligando_GYE/GYE.pdb"
GYE_CG = "sustratinaitor/2_ligando_GYE/GYE_cg_manual.pdb"

ES_HIDROGENO = re.compile(r"^(\d?H|H)")


# --------------------------------------------------------------------------
# Lectura de PDB tolerante: las salidas de cgconv.pl y de Packmol no traen
# occupancy/bfactor/element, la columna chainID puede ir en blanco y los
# seriales pueden ser hexadecimales.
# --------------------------------------------------------------------------


def leer_pdb(ruta):
    nombres, resnombres, cadenas, resnums, icodes = [], [], [], [], []
    xs, ys, zs = [], [], []
    seriales_invalidos = 0
    primer_serial_invalido = None
    ter_tras_atomo = []
    n_ter = n_end = n_model = n_conect = n_atomos = 0

    with open(ruta, "r", errors="replace") as fh:
        for linea in fh:
            reg = linea[:6]
            if reg.startswith(("ATOM", "HETATM")):
                serial = linea[6:11].strip()
                if serial and not serial.lstrip("-").isdigit():
                    seriales_invalidos += 1
                    if primer_serial_invalido is None:
                        primer_serial_invalido = (n_atomos + 1, serial)
                nombres.append(linea[12:16].strip())
                resnombres.append(linea[17:20].strip())
                cadenas.append(linea[21:22])
                resnums.append(linea[22:26].strip())
                icodes.append(linea[26:27])
                xs.append(float(linea[30:38]))
                ys.append(float(linea[38:46]))
                zs.append(float(linea[46:54]))
                n_atomos += 1
            elif reg.startswith("TER"):
                n_ter += 1
                ter_tras_atomo.append(n_atomos - 1)
            elif reg.startswith("END"):
                n_end += 1
            elif reg.startswith("MODEL"):
                n_model += 1
            elif reg.startswith("CONECT"):
                n_conect += 1

    return {
        "ruta": ruta,
        "nombre": np.array(nombres),
        "resnombre": np.array(resnombres),
        "cadena": np.array(cadenas),
        "resnum": np.array(resnums),
        "icode": np.array(icodes),
        "xyz": np.column_stack([np.array(xs, float), np.array(ys, float),
                                np.array(zs, float)]),
        "n_atomos": n_atomos,
        "n_ter": n_ter,
        "n_end": n_end,
        "n_model": n_model,
        "n_conect": n_conect,
        "ter_tras_atomo": np.array(ter_tras_atomo, dtype=int),
        "seriales_invalidos": seriales_invalidos,
        "primer_serial_invalido": primer_serial_invalido,
    }


def bloques_residuo(pdb):
    """Indices (inicio, fin) de cada residuo. Un TER siempre corta residuo."""
    n = pdb["n_atomos"]
    if n == 0:
        return np.array([], int), np.array([], int)
    clave = np.char.add(
        np.char.add(np.char.add(pdb["resnombre"], "|"), pdb["cadena"]),
        np.char.add(np.char.add("|", pdb["resnum"]), np.char.add("|", pdb["icode"])),
    )
    nuevo = np.empty(n, bool)
    nuevo[0] = True
    nuevo[1:] = clave[1:] != clave[:-1]
    if pdb["ter_tras_atomo"].size:
        corte = pdb["ter_tras_atomo"] + 1
        nuevo[corte[(corte > 0) & (corte < n)]] = True
    inicios = np.flatnonzero(nuevo)
    return inicios, np.append(inicios[1:], n)


def bloques_cadena(pdb):
    """Segmentos moleculares: cortados por TER y por cambio de chainID."""
    n = pdb["n_atomos"]
    if n == 0:
        return []
    cortes = set()
    for a in pdb["ter_tras_atomo"]:
        if 0 <= a < n - 1:
            cortes.add(int(a) + 1)
    cad = pdb["cadena"]
    for i in range(1, n):
        if cad[i] != cad[i - 1]:
            cortes.add(i)
    lim = [0] + sorted(cortes) + [n]
    return [(lim[i], lim[i + 1]) for i in range(len(lim) - 1)]


def fronteras_por_numeracion(pdb, inicios):
    """Fronteras de subunidad deducidas del reinicio de la numeracion.

    Es la unica senal que queda en un PDB al que Packmol le quito los TER.
    """
    nums = []
    for v in pdb["resnum"][inicios]:
        nums.append(int(v) if v.lstrip("-").isdigit() else -(10 ** 9))
    nums = np.array(nums)
    return np.flatnonzero(nums[1:] <= nums[:-1]) + 1


def coord(pdb, ini, fin, nombre):
    idx = np.flatnonzero(pdb["nombre"][ini:fin] == nombre)
    return pdb["xyz"][ini + idx[0]] if idx.size else None


# --------------------------------------------------------------------------
# Mapa SIRAH
# --------------------------------------------------------------------------


def leer_mapa_sirah(ruta):
    entradas, actual = {}, None
    with open(ruta) as fh:
        for linea in fh:
            s = linea.split("#")[0].strip()
            if not s:
                continue
            if s.startswith(">"):
                actual = {"cgname": None, "allname": [], "beads": [], "desde_h": []}
                continue
            if actual is None:
                continue
            p = s.split()
            if p[0] == "CGNAME":
                actual["cgname"] = p[1]
                entradas[p[1]] = actual
            elif p[0] == "ALLNAME":
                actual["allname"] = p[1:]
            elif p[0] == "MAP":
                flecha = p.index("=>")
                fuentes, bead = p[1:flecha], p[flecha + 1]
                actual["beads"].append(bead)
                if all(ES_HIDROGENO.match(a) for a in fuentes):
                    actual["desde_h"].append((bead, fuentes))
    return entradas


# --------------------------------------------------------------------------
# Informes
# --------------------------------------------------------------------------


def titulo(t):
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)


def resumen(pdb, raiz):
    inicios, fines = bloques_residuo(pdb)
    segs = bloques_cadena(pdb)
    cadenas = sorted({c if c.strip() else "(blanco)" for c in pdb["cadena"]})
    n_h = int(sum(1 for n in pdb["nombre"] if ES_HIDROGENO.match(n)))
    print(f"  fichero            : {os.path.relpath(pdb['ruta'], raiz)}")
    print(f"  atomos / beads     : {pdb['n_atomos']}")
    print(f"  residuos           : {len(inicios)}")
    print(f"  registros TER      : {pdb['n_ter']}")
    print(f"  segmentos (TER+cad): {len(segs)}")
    print(f"  chainIDs           : {cadenas}")
    print(f"  hidrogenos explic. : {n_h}")
    if pdb["seriales_invalidos"]:
        at, val = pdb["primer_serial_invalido"]
        print(f"  !! seriales no decimales: {pdb['seriales_invalidos']} "
              f"(primero en el atomo {at}: {val!r}) -> desbordamiento del campo "
              f"de 5 columnas")
    return inicios, fines, segs


def beads_por_residuo(pdb, sirah, etiqueta):
    inicios, fines = bloques_residuo(pdb)
    conteo = collections.defaultdict(collections.Counter)
    vistos = collections.defaultdict(set)
    for i, f in zip(inicios, fines):
        rn = pdb["resnombre"][i]
        conteo[rn][f - i] += 1
        vistos[rn] |= set(pdb["nombre"][i:f].tolist())
    print(f"\n{etiqueta}: beads por residuo frente a sirah_prot.map")
    print(f"  {'resCG':>6} {'n_res':>7} {'beads':>7} {'esperado':>9}  incidencia")
    discrepancias = 0
    for rn in sorted(conteo):
        c = conteo[rn]
        esp = len(sirah[rn]["beads"]) if rn in sirah else None
        obs = ", ".join(f"{k}" for k in sorted(c))
        nota = ""
        if esp is not None:
            falta = sorted(set(sirah[rn]["beads"]) - vistos[rn])
            extra = sorted(vistos[rn] - set(sirah[rn]["beads"]))
            if falta:
                nota += "FALTA " + ",".join(falta) + " "
            if extra:
                nota += "EXTRA " + ",".join(extra)
            if falta or extra:
                discrepancias += 1
        print(f"  {rn:>6} {sum(c.values()):>7} {obs:>7} {str(esp):>9}  {nota}")
    print(f"  -> tipos de residuo con discrepancia: {discrepancias}")
    return discrepancias


def beads_desde_hidrogeno(pdb, sirah):
    print("\nBeads que el mapa oficial deriva de un HIDROGENO:")
    inicios, fines = bloques_residuo(pdb)
    rn_res = pdb["resnombre"][inicios]
    total_presentes = 0
    for cg, ent in sorted(sirah.items()):
        for bead, fuentes in ent["desde_h"]:
            n_res = int((rn_res == cg).sum())
            if n_res == 0:
                continue
            presentes = sum(
                1 for i, f in zip(inicios, fines)
                if pdb["resnombre"][i] == cg and bead in set(pdb["nombre"][i:f].tolist())
            )
            total_presentes += presentes
            estado = "OK" if presentes == n_res else "<-- AUSENTE"
            print(f"  {cg:>4} ({'/'.join(ent['allname']):<8}) {bead:<4} "
                  f"<- {'|'.join(fuentes):<10} {presentes:>5}/{n_res:<5} {estado}")
    print(f"  -> beads derivados de hidrogeno presentes en total: {total_presentes}")
    return total_presentes


def distancias_consecutivas(pdb, etiqueta, par=("GO", "GN"), usar_numeracion=False):
    """Distancia del enlace que tLeaP inferiria entre residuos consecutivos."""
    a_nom, b_nom = par
    inicios, fines = bloques_residuo(pdb)
    if usar_numeracion:
        frontera = set(fronteras_por_numeracion(pdb, inicios).tolist())
    else:
        frontera = {int(np.searchsorted(inicios, a0, side="left"))
                    for a0, _ in bloques_cadena(pdb)}
    dentro, cruce = [], []
    for i in range(1, len(inicios)):
        a = coord(pdb, inicios[i - 1], fines[i - 1], a_nom)
        b = coord(pdb, inicios[i], fines[i], b_nom)
        if a is None or b is None:
            continue
        (cruce if i in frontera else dentro).append(float(np.linalg.norm(a - b)))
    dentro, cruce = np.array(dentro), np.array(cruce)
    print(f"\n{etiqueta}: distancia {a_nom}(i)-{b_nom}(i+1)")
    for v, tag in ((dentro, "dentro de subunidad"), (cruce, "en la frontera")):
        if v.size:
            print(f"  {tag:<22}: n={v.size:>6} min={v.min():7.2f} "
                  f"mediana={np.median(v):7.2f} max={v.max():8.2f} A")
        else:
            print(f"  {tag:<22}: (ninguna)")
    if cruce.size:
        print(f"  fronteras con d < 3 A (enlace plausible): "
              f"{int((cruce < 3.0).sum())}/{cruce.size}")
    if dentro.size:
        print(f"  huecos internos d > 5 A (residuos no resueltos): "
              f"{int((dentro > 5.0).sum())}/{dentro.size}")
    return dentro, cruce


def geometria_ligando_cg(ruta):
    pdb = leer_pdb(ruta)
    nombres, xyz = pdb["nombre"], pdb["xyz"]
    print(f"  beads: {len(nombres)} -> {list(nombres)}")
    dup = [n for n, c in collections.Counter(nombres.tolist()).items() if c > 1]
    print(f"  nombres de bead DUPLICADOS en el mismo residuo: {dup or 'ninguno'}")
    primera = next(l for l in open(ruta) if l.startswith("ATOM"))
    print(f"  campo resSeq (cols 23-26): {primera[22:26]!r} "
          f"{'(NO numerico: formato PDB invalido)' if not primera[22:26].strip().isdigit() else ''}")
    print(f"  campo element (cols 77-78): {primera[76:78]!r}")
    d = np.linalg.norm(xyz[1:] - xyz[:-1], axis=1)
    largos = int((d > 5.0).sum())
    print(f"  distancias entre beads consecutivos: min={d.min():.2f} "
          f"mediana={np.median(d):.2f} max={d.max():.2f} A")
    print(f"  pares consecutivos a mas de 5 A (inviable como enlace SIRAH): "
          f"{largos}/{d.size}")
    idx = {n: k for k, n in enumerate(nombres)}
    for a, b in (("BCE", "BF1"), ("BCE", "BF6")):
        if a in idx and b in idx:
            print(f"  d({a},{b}) = {np.linalg.norm(xyz[idx[a]] - xyz[idx[b]]):.2f} A")


def reparto_sustrato(pdb_mezcla, etiqueta_ligando="GYE"):
    inicios, fines = bloques_residuo(pdb_mezcla)
    rn = pdb_mezcla["resnombre"][inicios]
    idx_lig = np.flatnonzero(rn == etiqueta_ligando)
    mascara = np.ones(pdb_mezcla["n_atomos"], bool)
    for i in idx_lig:
        mascara[inicios[i]:fines[i]] = False
    capside = pdb_mezcla["xyz"][mascara]
    centro = capside.mean(axis=0)
    r_cap = np.linalg.norm(capside - centro, axis=1)
    r_int, r_ext = r_cap.min(), r_cap.max()
    print(f"  beads de capside: {capside.shape[0]}   moleculas de "
          f"{etiqueta_ligando}: {idx_lig.size}")
    print(f"  cascara de la capside: r_interno={r_int:.1f} A  r_externo={r_ext:.1f} A")

    centros, enteras_dentro = [], 0
    dmin_por_molecula = []
    arbol = cKDTree(capside) if cKDTree is not None else None
    for i in idx_lig:
        pts = pdb_mezcla["xyz"][inicios[i]:fines[i]]
        centros.append(pts.mean(axis=0))
        if np.linalg.norm(pts - centro, axis=1).max() < r_int:
            enteras_dentro += 1
        if arbol is not None:
            dmin_por_molecula.append(float(arbol.query(pts, k=1)[0].min()))
    centros = np.array(centros)
    r_lig = np.linalg.norm(centros - centro, axis=1)
    en_lumen = int((r_lig < r_int).sum())
    en_pared = int(((r_lig >= r_int) & (r_lig <= r_ext)).sum())
    fuera = int((r_lig > r_ext).sum())
    print(f"  por centro de masa -> lumen: {en_lumen}   cascara: {en_pared}   "
          f"exterior: {fuera}")
    print(f"  moleculas integramente dentro del lumen: {enteras_dentro}")
    if dmin_por_molecula:
        dm = np.array(dmin_por_molecula)
        print(f"  distancia minima ligando-capside: min={dm.min():.2f} "
              f"mediana={np.median(dm):.2f} A   (tolerancia Packmol declarada: 2.0 A)")
        print(f"  moleculas con algun atomo a < 2.0 A: {int((dm < 2.0).sum())}")
    return en_lumen, en_pared, fuera


# --------------------------------------------------------------------------


def main():
    raiz = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..")
    raiz = os.path.abspath(raiz)
    r = lambda p: os.path.join(raiz, p)  # noqa: E731

    sirah = leer_mapa_sirah(r(MAPA_SIRAH))
    desde_h = [(k, b) for k, v in sirah.items() for b, _ in v["desde_h"]]
    print(f"sirah_prot.map: {len(sirah)} residuos CG; beads derivados de "
          f"hidrogeno: {desde_h}")

    titulo("1. sustratinaitor — capside convertida a CG (1_capside/3J7L_cg.pdb)")
    cg = leer_pdb(r(CAPSIDE_CG))
    resumen(cg, raiz)
    beads_por_residuo(cg, sirah, "3J7L_cg")
    beads_desde_hidrogeno(cg, sirah)
    distancias_consecutivas(cg, "3J7L_cg", ("GO", "GN"))
    distancias_consecutivas(cg, "3J7L_cg", ("GC", "GC"))

    titulo("2. PackMan — entradas all-atom")
    for ruta in (CAPSIDE_AA, ENZIMA_AA):
        resumen(leer_pdb(r(ruta)), raiz)
        print()

    titulo("3. PackMan — salida de Packmol (entrada de convert_to_cg.sh)")
    pk = leer_pdb(r(PACKMAN_OUT))
    resumen(pk, raiz)
    distancias_consecutivas(pk, "capside_1enzimas", ("C", "N"), usar_numeracion=True)

    titulo("4. sustratinaitor — salida de Packmol (entrada de gensystem.leap)")
    sg = leer_pdb(r(SUSTRATO_OUT))
    resumen(sg, raiz)
    distancias_consecutivas(sg, "3J7L-GYE", ("GO", "GN"), usar_numeracion=True)

    titulo("5. sustratinaitor — el ligando GYE en sus dos resoluciones")
    print("  all-atom (el que Packmol empaqueto de verdad):")
    resumen(leer_pdb(r(GYE_AA)), raiz)
    print("\n  CG manual de 17 beads (construido pero NO usado):")
    geometria_ligando_cg(r(GYE_CG))

    titulo("6. Reparto espacial del sustrato alrededor de la capside")
    reparto_sustrato(sg)

    print("\nFin de la auditoria.")


if __name__ == "__main__":
    main()
