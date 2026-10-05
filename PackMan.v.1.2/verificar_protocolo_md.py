#!/usr/bin/env python3
"""Verificación estática del protocolo MD de PackMan contra la referencia SIRAH.

Aquí no hay AMBER, así que lo único que se puede garantizar es que los `.in`
commiteados dicen lo que deben decir. Este script compara cada archivo de
`archivos_dm_cg/` parámetro por parámetro con el `.in` oficial de SIRAH que le
sirve de patrón (`sirah_x2.3_24-07.amber/tutorial/5/`, proteína en WT4) y falla
si divergen en algo que no esté en la lista explícita de desvíos permitidos.

Comprobaciones:
  1. Inventario: exactamente las 5 etapas SIRAH; ninguna etapa all-atom residual.
  2. Parámetro por parámetro: todo lo que fija la referencia debe estar con el
     mismo valor; no puede haber parámetros extra. Los únicos desvíos admitidos
     son los de DESVIOS_PERMITIDOS, con el valor exacto que ahí se declara.
  3. Marcadores all-atom prohibidos (dt=2 fs, SHAKE, cut=9, @CA,C,N,O, ...).
  4. Los títulos dicen la verdad: la duración en ns del título = nstlim*dt.
  5. Las máscaras usan nombres que existen en las librerías SIRAH.
  6. run_MD.sh orquesta esas 5 etapas y nada más, con la cadena -c/-ref correcta
     (se comprueba con DRY_RUN=1, sin AMBER).

Uso:  python3 verificar_protocolo_md.py [-v]      (código de salida 0 = todo bien)
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
DM = RAIZ / "archivos_dm_cg"
SIRAH = DM / "sirah_x2.3_24-07.amber"
REF = SIRAH / "tutorial" / "5"

# Etapa -> (archivo propio, archivo de referencia SIRAH)
ETAPAS = {
    "em1": ("em1_WT4.in", "em1_WT4.in"),
    "em2": ("em2_WT4.in", "em2_WT4.in"),
    "eq1": ("eq1_WT4.in", "eq1_WT4.in"),
    "eq2": ("eq2_WT4.in", "eq2_WT4.in"),
    "prod": ("prod_md_WT4.in", "md_WT4.in"),
}

# Único lugar donde se admite divergir de la referencia. Cada entrada es
# (grupo, parámetro) -> valor exacto que debe tener nuestro archivo. Si la
# referencia también define el parámetro, el nuestro puede diferir solo así;
# si no lo define, es la única adición permitida. Motivo de cada desvío:
#   ig       : semilla fija y distinta por etapa (reproducibilidad; la referencia
#              usa -1 y aquí no hay mdout que la rescate). Producción: 100100+k
#              por trozo, lo fija run_MD.sh; el commiteado es el trozo 1.
#   skinnb   : tutorial/7/heat_Prot-Lip.in:27, "avoid skinnb errors in GPU code";
#              el sistema tiene ~400 k partículas.
#   eq1 mask : la referencia restringe ':1-46' (toda la crambina). El equivalente
#              para N enzimas sin depender del número de residuos es "todo lo que
#              no sea solvente ni iones".
#   prod nstlim: 1 µs de la referencia -> trozos reiniciables de 10 ns; el número
#              de trozos (NCHUNKS, 10 por defecto = 100 ns) lo pone run_MD.sh.
DESVIOS_PERMITIDOS = {
    "eq1": {
        ("cntrl", "ig"): 100001,
        ("cntrl", "restraintmask"): "!:WT4,NaW,ClW",
        ("ewald", "skinnb"): 5,
    },
    "eq2": {
        ("cntrl", "ig"): 100002,
        ("ewald", "skinnb"): 5,
    },
    "prod": {
        ("cntrl", "ig"): 100101,
        ("cntrl", "nstlim"): 500000,
        ("ewald", "skinnb"): 5,
    },
}

# Herencia all-atom que no puede volver a aparecer (auditoría MD-04/MD-05/MD-14).
PROHIBIDOS = [
    (("cntrl", "dt"), lambda v: v is not None and abs(v - 0.020) > 1e-9, "dt distinto de 20 fs"),
    (("cntrl", "ntc"), lambda v: v not in (None, 1), "SHAKE (ntc>1) sobre beads SIRAH"),
    (("cntrl", "ntf"), lambda v: v not in (None, 1), "SHAKE (ntf>1) sobre beads SIRAH"),
    (("cntrl", "cut"), lambda v: v is not None and abs(v - 12.0) > 1e-9, "cutoff distinto de 12 A"),
    (("cntrl", "gamma_ln"), lambda v: v is not None and abs(v - 50.0) > 1e-9, "gamma_ln distinto de 50"),
    (("cntrl", "barostat"), lambda v: v is not None, "barostat explícito (no está en ningún .in SIRAH)"),
    (("cntrl", "nmropt"), lambda v: v is not None, "rampa nmropt (etapa heat all-atom)"),
    (("cntrl", "restraintmask"), lambda v: v is not None and re.search(r"@[^']*\b(CA|C|N|O)\b", v) is not None,
     "máscara con nombres de átomo all-atom (CA, C, N, O)"),
]

ETAPAS_ALLATOM = ("heat", "density_eq", "final_eq")

# Lo que dice el protocolo sobre restricciones (auditoría MD-06), por etapa.
RESTRICCIONES = {
    "em1": (1, 2.4, "@GN,GO"),
    "em2": (None, None, None),  # la referencia no define ntr -> sin restricción
    "eq1": (1, 2.4, "!:WT4,NaW,ClW"),
    "eq2": (1, 0.24, "@GN,GO"),
    "prod": (0, None, None),
}

CADENA_ESPERADA = [
    # etiqueta, input, -c, -ref ("" = sin -ref)
    ("em1", "em1_WT4.in", "{N}.ncrst", "{N}.ncrst"),
    ("em2", "em2_WT4.in", "{N}_em1.ncrst", ""),
    ("eq1", "eq1_WT4.in", "{N}_em2.ncrst", "{N}_em2.ncrst"),
    ("eq2", "eq2_WT4.in", "{N}_eq1.ncrst", "{N}_eq1.ncrst"),
    ("prod_k01", "prod_md_WT4_k01.in", "{N}_eq2.ncrst", ""),
    ("prod_k02", "prod_md_WT4_k02.in", "{N}_prod_k01.ncrst", ""),
]


# --------------------------------------------------------------------------
# Parser mínimo de namelist AMBER
# --------------------------------------------------------------------------
def _valor(txt: str):
    txt = txt.strip()
    if len(txt) >= 2 and txt[0] == txt[-1] and txt[0] in "'\"":
        return txt[1:-1]
    try:
        return int(txt)
    except ValueError:
        pass
    try:
        return float(txt)
    except ValueError:
        return txt


def _sin_comentario(ln: str) -> str:
    """Quita un comentario '!' solo si está fuera de comillas (las máscaras
    negadas empiezan por '!')."""
    comilla = None
    for i, ch in enumerate(ln):
        if comilla:
            if ch == comilla:
                comilla = None
        elif ch in "'\"":
            comilla = ch
        elif ch == "!":
            return ln[:i]
    return ln


def parsear_in(ruta: Path) -> tuple[str, dict[str, dict[str, object]]]:
    """Devuelve (título, {grupo: {param: valor}}). Entiende &grp ... &end o /,
    comentarios con '!', y pares 'k = v' separados por comas o saltos de línea."""
    lineas = ruta.read_text(encoding="utf-8", errors="replace").splitlines()
    titulo = lineas[0] if lineas else ""
    grupos: dict[str, dict[str, object]] = {}
    actual = None
    cuerpo: list[str] = []

    def cerrar():
        nonlocal actual, cuerpo
        if actual is None:
            return
        texto = " ".join(cuerpo)
        d = grupos.setdefault(actual, {})
        for m in re.finditer(r"([A-Za-z_][A-Za-z0-9_]*)\s*=\s*('[^']*'|\"[^\"]*\"|[^,\s]+)", texto):
            k = m.group(1).lower()
            if k in d:
                raise ValueError(f"{ruta.name}: parámetro repetido {k} en &{actual}")
            d[k] = _valor(m.group(2))
        actual, cuerpo = None, []

    for ln in lineas[1:]:
        s = _sin_comentario(ln).strip()
        if not s:
            continue
        if s.startswith("&"):
            if s.lower() == "&end":
                cerrar()
                continue
            if actual is not None:
                cerrar()
            nombre, _, resto = s[1:].partition(" ")
            actual = nombre.lower()
            cuerpo = [resto] if resto else []
            # grupo de una sola línea: &wt type='TEMP0' ... /
            if actual != "cntrl" and resto.rstrip().endswith("/"):
                cuerpo = [resto.rstrip()[:-1]]
                cerrar()
            continue
        if s == "/":
            cerrar()
            continue
        if actual is not None:
            cuerpo.append(s)
    cerrar()
    return titulo, grupos


def igual(a, b) -> bool:
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a) - float(b)) < 1e-9
    return a == b


def fmt(v) -> str:
    return repr(v) if isinstance(v, str) else str(v)


# --------------------------------------------------------------------------
# Comprobaciones
# --------------------------------------------------------------------------
class Informe:
    def __init__(self, verbose: bool):
        self.fallos: list[str] = []
        self.verbose = verbose

    def ok(self, msg: str):
        if self.verbose:
            print(f"  ok   {msg}")

    def fallo(self, msg: str):
        self.fallos.append(msg)
        print(f"  FALLO {msg}")


def comprobar_inventario(inf: Informe):
    print("[1] Inventario de archivos .in")
    presentes = sorted(p.name for p in DM.glob("*.in"))
    esperados = sorted(a for a, _ in ETAPAS.values())
    for extra in set(presentes) - set(esperados):
        if extra.startswith(ETAPAS_ALLATOM):
            inf.fallo(f"{extra}: etapa all-atom residual; el protocolo SIRAH no la tiene")
        elif re.fullmatch(r"prod_md_WT4_k\d+\.in", extra):
            inf.fallo(f"{extra}: trozo de producción generado por run_MD.sh; no se commitea")
        else:
            inf.fallo(f"{extra}: archivo .in fuera del protocolo (no hay referencia contra la que verificarlo)")
    for falta in set(esperados) - set(presentes):
        inf.fallo(f"{falta}: falta")
    if set(presentes) == set(esperados):
        inf.ok(f"exactamente las 5 etapas: {', '.join(esperados)}")
    for _, ref in ETAPAS.values():
        if not (REF / ref).is_file():
            inf.fallo(f"referencia SIRAH ausente: {REF / ref}")


def comprobar_parametros(inf: Informe, etapa: str, propio: dict, ref: dict):
    permitidos = DESVIOS_PERMITIDOS.get(etapa, {})
    claves_ref = {(g, k) for g, d in ref.items() for k in d}
    claves_mio = {(g, k) for g, d in propio.items() for k in d}

    for g, k in sorted(claves_ref):
        vr = ref[g][k]
        if (g, k) not in claves_mio:
            inf.fallo(f"{etapa}: &{g} {k} = {fmt(vr)} está en la referencia y falta aquí")
            continue
        vm = propio[g][k]
        if (g, k) in permitidos:
            if not igual(vm, permitidos[(g, k)]):
                inf.fallo(f"{etapa}: &{g} {k} = {fmt(vm)}; el desvío permitido es exactamente {fmt(permitidos[(g, k)])}")
            else:
                inf.ok(f"{etapa}: &{g} {k} = {fmt(vm)} (desvío documentado; referencia {fmt(vr)})")
        elif not igual(vm, vr):
            inf.fallo(f"{etapa}: &{g} {k} = {fmt(vm)} diverge de la referencia SIRAH ({fmt(vr)})")
        else:
            inf.ok(f"{etapa}: &{g} {k} = {fmt(vm)}")

    for g, k in sorted(claves_mio - claves_ref):
        vm = propio[g][k]
        if (g, k) in permitidos:
            if igual(vm, permitidos[(g, k)]):
                inf.ok(f"{etapa}: &{g} {k} = {fmt(vm)} (adición documentada)")
            else:
                inf.fallo(f"{etapa}: &{g} {k} = {fmt(vm)}; la adición permitida es exactamente {fmt(permitidos[(g, k)])}")
        else:
            inf.fallo(f"{etapa}: &{g} {k} = {fmt(vm)} no está en la referencia SIRAH ni en los desvíos permitidos")

    for g in propio:
        if g not in ref:
            inf.fallo(f"{etapa}: grupo &{g} no existe en la referencia")


def comprobar_prohibidos(inf: Informe, etapa: str, propio: dict):
    for (g, k), es_malo, motivo in PROHIBIDOS:
        v = propio.get(g, {}).get(k)
        if es_malo(v):
            inf.fallo(f"{etapa}: &{g} {k} = {fmt(v)}: {motivo}")


def comprobar_restricciones(inf: Informe, etapa: str, propio: dict):
    ntr, wt, mask = RESTRICCIONES[etapa]
    c = propio.get("cntrl", {})
    if ntr is None:
        if "ntr" in c and c["ntr"] != 0:
            inf.fallo(f"{etapa}: ntr = {c['ntr']} pero la etapa debe ir sin restricciones")
        return
    if c.get("ntr") != ntr:
        inf.fallo(f"{etapa}: ntr = {fmt(c.get('ntr'))}, esperado {ntr}")
    if ntr == 1:
        if not igual(c.get("restraint_wt"), wt):
            inf.fallo(f"{etapa}: restraint_wt = {fmt(c.get('restraint_wt'))}, esperado {wt}")
        if c.get("restraintmask") != mask:
            inf.fallo(f"{etapa}: restraintmask = {fmt(c.get('restraintmask'))}, esperado {mask!r}")
        else:
            inf.ok(f"{etapa}: restricción {wt} kcal/mol/A2 sobre {mask!r}")
    else:
        inf.ok(f"{etapa}: sin restricciones (ntr = 0)")


def duracion_ns(propio: dict) -> float | None:
    c = propio.get("cntrl", {})
    if c.get("imin") == 1:
        return None
    try:
        return float(c["nstlim"]) * float(c["dt"]) / 1000.0
    except (KeyError, TypeError, ValueError):
        return None


def comprobar_titulo(inf: Informe, etapa: str, titulo: str, propio: dict):
    if len(titulo) > 80:
        inf.fallo(f"{etapa}: título de {len(titulo)} caracteres; AMBER lee 80")
    if not titulo.isascii():
        inf.fallo(f"{etapa}: título con caracteres no ASCII (riesgo de truncado en Fortran)")
    ns = duracion_ns(propio)
    anunciados = [float(x.replace(",", ".")) for x in re.findall(r"(\d+(?:[.,]\d+)?)\s*ns\b", titulo)]
    if ns is None:
        if anunciados:
            inf.fallo(f"{etapa}: el título anuncia ns pero es una minimización")
        elif "minimizacion" not in titulo.lower() and "minimización" not in titulo.lower():
            inf.fallo(f"{etapa}: el título de una minimización debe decirlo: {titulo!r}")
        else:
            inf.ok(f"{etapa}: título de minimización: {titulo!r}")
        return
    if not anunciados:
        inf.fallo(f"{etapa}: el título no dice cuánto simula (nstlim*dt = {ns:g} ns): {titulo!r}")
    elif abs(anunciados[0] - ns) > 1e-6:
        inf.fallo(f"{etapa}: el título anuncia {anunciados[0]:g} ns pero nstlim*dt = {ns:g} ns")
    else:
        inf.ok(f"{etapa}: título {anunciados[0]:g} ns == nstlim*dt {ns:g} ns")


def nombres_sirah() -> tuple[set[str], set[str]]:
    """(residuos, átomos) definidos en las librerías que carga leaprc.sirah."""
    residuos: set[str] = set()
    atomos: set[str] = set()
    libs = [p for p in SIRAH.glob("*.lib")]
    for lib in libs:
        for ln in lib.read_text(encoding="utf-8", errors="replace").splitlines():
            m = re.match(r"!entry\.(\S+)\.unit\.atoms\s+table", ln)
            if m:
                residuos.add(m.group(1))
            m = re.match(r'\s*"([^"]+)"\s+"([^"]+)"\s+0\s+1\s+\d+\s+\d+\s+-?\d+\s+-?[\d.]+', ln)
            if m:
                atomos.add(m.group(1))
    return residuos, atomos


def comprobar_mascaras(inf: Informe, etapa: str, propio: dict, residuos: set[str], atomos: set[str]):
    mask = propio.get("cntrl", {}).get("restraintmask")
    if not isinstance(mask, str):
        return
    for sel in re.findall(r"@([A-Za-z0-9,*=]+)", mask):
        for nombre in sel.split(","):
            if nombre and "*" not in nombre and "=" not in nombre and nombre not in atomos:
                inf.fallo(f"{etapa}: la máscara {mask!r} usa el bead '{nombre}', que no existe en SIRAH")
    for sel in re.findall(r":([A-Za-z0-9,*=]+)", mask):
        for nombre in sel.split(","):
            if nombre and not nombre.isdigit() and "*" not in nombre and nombre not in residuos:
                inf.fallo(f"{etapa}: la máscara {mask!r} usa el residuo '{nombre}', que no existe en SIRAH")
    inf.ok(f"{etapa}: nombres de {mask!r} existen en las librerías SIRAH")


def comprobar_run_md(inf: Informe):
    print("[6] run_MD.sh")
    script = DM / "run_MD.sh"
    texto = script.read_text(encoding="utf-8")
    for malo in ETAPAS_ALLATOM:
        if malo in texto:
            inf.fallo(f"run_MD.sh menciona la etapa all-atom '{malo}'")
    for propio, _ in ETAPAS.values():
        if propio not in texto:
            inf.fallo(f"run_MD.sh no menciona {propio}")
    r = subprocess.run(["bash", "-n", str(script)], capture_output=True, text=True)
    if r.returncode != 0:
        inf.fallo(f"bash -n run_MD.sh: {r.stderr.strip()}")
        return
    env = dict(os.environ, DRY_RUN="1", NCHUNKS="2")
    r = subprocess.run(["bash", str(script), "cuda", "SYS"], cwd=DM, capture_output=True, text=True, env=env)
    if r.returncode != 0:
        inf.fallo(f"DRY_RUN=1 run_MD.sh falló: {r.stderr.strip() or r.stdout.strip()}")
        return
    cmds = [ln.strip() for ln in r.stdout.splitlines() if ln.strip().startswith("pmemd.cuda ")]
    if len(cmds) != len(CADENA_ESPERADA):
        inf.fallo(f"run_MD.sh lanza {len(cmds)} comandos con NCHUNKS=2; se esperaban {len(CADENA_ESPERADA)}")
    for cmd, (label, inp, c, ref) in zip(cmds, CADENA_ESPERADA):
        tok = cmd.split()
        def arg(flag):
            return tok[tok.index(flag) + 1] if flag in tok else ""
        c, ref = c.format(N="SYS"), ref.format(N="SYS")
        if arg("-i") != inp or arg("-c") != c or arg("-ref") != ref:
            inf.fallo(f"run_MD.sh etapa {label}: -i {arg('-i')} -c {arg('-c')} -ref {arg('-ref') or '(ninguno)'}; "
                      f"esperado -i {inp} -c {c} -ref {ref or '(ninguno)'}")
        else:
            inf.ok(f"run_MD.sh etapa {label}: -i {inp} -c {c}" + (f" -ref {ref}" if ref else ""))
        if label.startswith("prod") and arg("-ref"):
            inf.fallo(f"run_MD.sh etapa {label}: producción con -ref (ntr = 0, no debe llevarlo)")
    semillas = re.findall(r"\[semilla\] (prod_k\d+) .*ig = (\d+)", r.stdout)
    if [s for s, _ in semillas] != ["prod_k01", "prod_k02"] or [int(i) for _, i in semillas] != [100101, 100102]:
        inf.fallo(f"run_MD.sh: semillas de producción {semillas}; esperado 100100+k por trozo")
    else:
        inf.ok("run_MD.sh: ig = 100100+k por trozo de producción")

    bsub = DM / "prod-q_gpu.bsub"
    if bsub.is_file():
        tb = bsub.read_text(encoding="utf-8")
        if "run_MD.sh" not in tb:
            inf.fallo("prod-q_gpu.bsub no lanza run_MD.sh (ruta manual sin protocolo)")
        if re.search(r"capside-\d", tb):
            inf.fallo("prod-q_gpu.bsub tiene un nombre de sistema fijo que ningún script genera")


def main(argv: list[str]) -> int:
    verbose = "-v" in argv
    inf = Informe(verbose)
    comprobar_inventario(inf)
    residuos, atomos = nombres_sirah()
    if not {"GN", "GO", "GC"} <= atomos or not {"WT4", "NaW", "ClW"} <= residuos:
        inf.fallo(f"no se pudieron leer los nombres SIRAH de {SIRAH} (beads={len(atomos)}, residuos={len(residuos)})")

    print("[2-5] Parámetros, marcadores all-atom, restricciones, títulos y máscaras")
    total_ns = 0.0
    filas = []
    for etapa, (propio_n, ref_n) in ETAPAS.items():
        rp, rr = DM / propio_n, REF / ref_n
        if not rp.is_file() or not rr.is_file():
            continue
        try:
            titulo, propio = parsear_in(rp)
            _, ref = parsear_in(rr)
        except ValueError as e:
            inf.fallo(str(e))
            continue
        comprobar_parametros(inf, etapa, propio, ref)
        comprobar_prohibidos(inf, etapa, propio)
        comprobar_restricciones(inf, etapa, propio)
        comprobar_titulo(inf, etapa, titulo, propio)
        comprobar_mascaras(inf, etapa, propio, residuos, atomos)
        ns = duracion_ns(propio)
        c = propio.get("cntrl", {})
        filas.append((propio_n, c.get("nstlim", "-"), c.get("dt", "-"), ns, titulo))
        if ns:
            total_ns += ns

    comprobar_run_md(inf)

    print()
    print(f"{'archivo':<16}{'nstlim':>10}{'dt(ps)':>8}{'ns':>8}  título")
    for n, nst, dt, ns, t in filas:
        print(f"{n:<16}{str(nst):>10}{str(dt):>8}{(f'{ns:g}' if ns else '-'):>8}  {t}")
    print(f"Total con un trozo de producción: {total_ns:g} ns; con 10 trozos (run_MD.sh por defecto): {total_ns + 90:g} ns")
    print()
    if inf.fallos:
        print(f"FALLA: {len(inf.fallos)} divergencia(s) respecto a la referencia SIRAH.")
        return 1
    print("OK: el protocolo coincide con la referencia SIRAH salvo los desvíos documentados.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
