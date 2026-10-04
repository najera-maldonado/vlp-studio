#!/usr/bin/env python3
"""Auditoría empírica (solo lectura) de las conversiones coarse-grained SIRAH del repo.

Acompaña a AUDITORIA_SUSTRATO_Y_CG.md. Lee los PDB commiteados y las librerías SIRAH
que ya viajan en PackMan.v.1.2 y reporta: beads por residuo contra amino.lib, beads
derivados de hidrógenos (BPG/BPE), registros TER, distancias entre residuos consecutivos,
carga neta, geometría del empaquetado de GYE y el mapeo manual del GYE.

Uso (desde la raíz del repo, requiere numpy):
    python3 herramientas/auditoria_cg.py            # secciones 1-5 (~1 min)
    python3 herramientas/auditoria_cg.py 1 2        # solo las secciones indicadas
Secciones: 1 cápside CG de sustratinaitor · 2 correspondencia con capside.pdb de PackMan ·
3 salida de Packmol 3J7L-GYE.pdb · 4 ligando GYE · 5 PDB de la ruta PackMan.
No modifica ningún archivo.
"""
import re, sys, os
from collections import Counter, defaultdict, OrderedDict
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIRAH = f"{ROOT}/PackMan.v.1.2/archivos_dm_cg/sirah_x2.3_24-07.amber"
CG = f"{ROOT}/sustratinaitor/1_capside/3J7L_cg.pdb"
PACKED = f"{ROOT}/sustratinaitor/3_empaquetado_packmol/3J7L-GYE.pdb"
GYE_AA = f"{ROOT}/sustratinaitor/2_ligando_GYE/GYE.pdb"
GYE_CG = f"{ROOT}/sustratinaitor/2_ligando_GYE/GYE_cg_manual.pdb"
PM = f"{ROOT}/PackMan.v.1.2/archivos_dm_cg/empaquetador"
CAPS_AA = f"{PM}/capside.pdb"
CAPS_REC = f"{PM}/capside_recentrada.pdb"
ENZ_AA = f"{PM}/enzima.pdb"
ENZ_REC = f"{PM}/enzima_recentrada.pdb"
PM_PACKED = f"{PM}/capside_1enzimas_20260324_212620.pdb"

AA2CG = {"ALA":"sA","GLY":"sG","ARG":"sR","ASN":"sN","ASP":"sD","CYS":"sC","GLN":"sQ","GLU":"sE",
         "HIS":"sHe","HIE":"sHe","HID":"sHd","HIP":"sHp","ILE":"sI","LEU":"sL","LYS":"sK","MET":"sM",
         "PHE":"sF","PRO":"sP","SER":"sS","THR":"sT","TRP":"sW","TYR":"sY","VAL":"sV"}

SECTIONS = set(sys.argv[1:]) or {"1","2","3","4","5"}
def hr(t):
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)
def want(k):
    return k in SECTIONS

# ---------------------------------------------------------------- SIRAH libs
def parse_lib(path):
    """Devuelve {res: [(bead, type, charge), ...]} de un .lib de LEaP."""
    out = OrderedDict()
    cur = None
    with open(path) as fh:
        for line in fh:
            m = re.match(r"!entry\.(\S+)\.unit\.atoms table", line)
            if m:
                cur = m.group(1); out[cur] = []; continue
            if line.startswith("!entry"):
                cur = None; continue
            if cur is not None and line.strip():
                parts = line.split()
                out[cur].append((parts[0].strip('"'), parts[1].strip('"'), float(parts[-1])))
    return out

LIB = parse_lib(f"{SIRAH}/amino.lib")
LIBN = parse_lib(f"{SIRAH}/amino.n.lib")
LIBC = parse_lib(f"{SIRAH}/amino.c.lib")
EXPECTED = {r: [a[0] for a in atoms] for r, atoms in LIB.items()}
CHARGE = {r: round(sum(a[2] for a in atoms), 3) for r, atoms in LIB.items()}
CHARGE_N = {r: round(sum(a[2] for a in atoms), 3) for r, atoms in LIBN.items()}
CHARGE_C = {r: round(sum(a[2] for a in atoms), 3) for r, atoms in LIBC.items()}

hr("0. Referencia SIRAH amino.lib: beads esperados por residuo (y carga)")
for r in EXPECTED:
    print(f"  {r:4s} n={len(EXPECTED[r])}  q={CHARGE[r]:+.2f}  beads={' '.join(EXPECTED[r])}")
print("  Terminos (ejemplo): nK q=%+.2f  cR q=%+.2f  nA q=%+.2f cA q=%+.2f" %
      (CHARGE_N.get("nK", float("nan")), CHARGE_C.get("cR", float("nan")),
       CHARGE_N.get("nA", float("nan")), CHARGE_C.get("cA", float("nan"))))
# beads que provienen de hidrogenos segun sirah_prot.map
H_BEADS = {"sS":"BPG","sT":"BPG","sC":"BPG","sW":"BPE"}

# ---------------------------------------------------------------- PDB parser
class PDB:
    def __init__(self, path, resname_width=4):
        self.path = path
        names, resn, chain, resi, icode, xyz, elem, seg = [], [], [], [], [], [], [], []
        self.n_ter = 0; self.n_end = 0; self.hex_serials = 0
        self.ter_after_atom = []   # indice de atomo (0-based) tras el cual hay TER
        self.other = Counter()
        n = 0
        with open(path) as fh:
            for line in fh:
                rec = line[:6]
                if rec.startswith("ATOM") or rec.startswith("HETATM"):
                    s = line[6:11]
                    if not s.strip().isdigit():
                        self.hex_serials += 1
                    names.append(line[12:16].strip())
                    resn.append(line[17:17 + resname_width].strip())
                    chain.append(line[21])
                    rs = line[22:26]
                    if not rs.strip().lstrip('-').isdigit():
                        m = re.search(r"(-?\d+)", line[21:27]); rs = m.group(1) if m else "0"
                        self.malformed = getattr(self, 'malformed', 0) + 1
                    resi.append(int(rs))
                    icode.append(line[26])
                    xyz.append((float(line[30:38]), float(line[38:46]), float(line[46:54])))
                    elem.append(line[76:78].strip() if len(line) >= 78 else "")
                    seg.append(line[72:76].strip() if len(line) >= 76 else "")
                    n += 1
                elif rec.startswith("TER"):
                    self.n_ter += 1; self.ter_after_atom.append(n - 1)
                elif rec.startswith("END") and not rec.startswith("ENDMDL"):
                    self.n_end += 1
                else:
                    self.other[rec.strip()] += 1
        self.name = np.array(names); self.resn = np.array(resn); self.chain = np.array(chain)
        self.resi = np.array(resi); self.icode = np.array(icode); self.xyz = np.array(xyz)
        self.elem = np.array(elem); self.seg = np.array(seg)
        self.n = n
        # segmentos delimitados por TER
        self.segment = np.zeros(n, dtype=int)
        cuts = sorted(set(i for i in self.ter_after_atom if 0 <= i < n - 1))
        for c in cuts:
            self.segment[c + 1:] += 1
        # residuos: cambio de (segment, chain, resi, icode, resn)
        key = np.array([f"{s}|{c}|{r}|{i}|{rn}" for s, c, r, i, rn in
                        zip(self.segment, self.chain, self.resi, self.icode, self.resn)])
        change = np.ones(n, dtype=bool); change[1:] = key[1:] != key[:-1]
        self.res_start = np.flatnonzero(change)
        self.res_end = np.append(self.res_start[1:], n)
        self.nres = len(self.res_start)
        self.res_name = self.resn[self.res_start]
        self.res_num = self.resi[self.res_start]
        self.res_seg = self.segment[self.res_start]
        self.res_chain = self.chain[self.res_start]

    def summary(self, label):
        hr(f"{label}: {os.path.relpath(self.path, ROOT)}")
        print(f"  atomos={self.n}  residuos={self.nres}  TER={self.n_ter}  END={self.n_end}  "
              f"segmentos(TER)={self.segment.max() + 1}  seriales_no_decimales={self.hex_serials}")
        if self.other:
            print(f"  otros registros: {dict(self.other)}")
        el = Counter(self.elem[self.elem != ""])
        if el:
            print(f"  elementos (col 77-78): {dict(el)}")
        hcount = int(np.sum([nm.startswith("H") and not nm.startswith("HG") and not nm.startswith("HE")
                              and not nm.startswith("HD") and not nm.startswith("HZ") and not nm.startswith("HH")
                              for nm in self.name]))
        n_h_like = int(np.sum([bool(re.match(r"^[0-9]?H", nm)) for nm in self.name]))
        print(f"  nombres de atomo que parecen hidrogeno (^[0-9]?H): {n_h_like}")
        print(f"  chain IDs: {dict(Counter(self.chain))}")
        return self

    def residue_atoms(self, k):
        return self.name[self.res_start[k]:self.res_end[k]]

    def residue_xyz_of(self, k, atom):
        sl = slice(self.res_start[k], self.res_end[k])
        idx = np.flatnonzero(self.name[sl] == atom)
        if len(idx) == 0:
            return None
        return self.xyz[sl][idx[0]]

def consecutive_distances(p, atom="CA", partner=None, same_segment=True, label=""):
    """Distancias entre atom(i) y atom(i+1) (o partner(i+1)) de residuos consecutivos
    en el archivo. Devuelve arrays d_same (mismo segmento TER) y d_cross (cruzan TER)."""
    pos = np.full((p.nres, 3), np.nan)
    pos2 = np.full((p.nres, 3), np.nan)
    for k in range(p.nres):
        a = p.residue_xyz_of(k, atom)
        if a is not None: pos[k] = a
        b = p.residue_xyz_of(k, partner or atom)
        if b is not None: pos2[k] = b
    d = np.linalg.norm(pos2[1:] - pos[:-1], axis=1)
    same = p.res_seg[1:] == p.res_seg[:-1]
    return d[same], d[~same], d, same

def report_consecutive(p, atom, partner=None, thr_hi=4.5, thr_lo=2.5, tag=""):
    d_same, d_cross, d, same = consecutive_distances(p, atom, partner)
    ok = ~np.isnan(d_same)
    ds = d_same[ok]
    pair = f"{atom}(i)-{partner or atom}(i+1)"
    print(f"  {tag}{pair} dentro de un mismo segmento TER: n={len(ds)} "
          f"media={ds.mean():.3f} sd={ds.std():.3f} min={ds.min():.3f} max={ds.max():.3f} "
          f"| >{thr_hi}A: {int((ds > thr_hi).sum())}  <{thr_lo}A: {int((ds < thr_lo).sum())}")
    if len(d_cross):
        dc = d_cross[~np.isnan(d_cross)]
        print(f"  {tag}{pair} cruzando un TER (no se enlazan): n={len(dc)} "
              f"min={dc.min():.1f} media={dc.mean():.1f} max={dc.max():.1f}")
    # saltos de numeracion dentro de un segmento
    jumps = np.flatnonzero(same & (np.diff(p.res_num) != 1))
    return ds, jumps, d, same

# ======================================================================
if not (want("1") or want("2") or want("3")): pass
hr("1. CAPSIDE CG DE SUSTRATINAITOR  (3J7L_cg.pdb)")
cg = PDB(CG).summary("1a. Resumen")
nseg = cg.segment.max() + 1
res_per_seg = Counter(cg.res_seg)
print(f"  residuos por segmento: {dict(Counter(res_per_seg.values()))}  (valor: n_segmentos)")
rng = [(cg.res_num[cg.res_seg == s].min(), cg.res_num[cg.res_seg == s].max()) for s in range(nseg)]
print(f"  rangos de numeracion por segmento (unicos): {sorted(set(rng))}")

print("\n1b. Beads por residuo vs amino.lib")
bad = Counter(); good = Counter(); detail = defaultdict(Counter)
for k in range(cg.nres):
    rn = cg.res_name[k]; atoms = list(cg.residue_atoms(k))
    exp = EXPECTED.get(rn)
    if exp is None:
        bad[rn] += 1; detail[rn]["sin_lib"] += 1; continue
    if sorted(atoms) == sorted(exp):
        good[rn] += 1
    else:
        bad[rn] += 1
        detail[rn][f"obs={'/'.join(atoms)} exp={'/'.join(exp)}"] += 1
print(f"  {'res':5s} {'n_res':>6s} {'beads/res':>9s} {'esperado':>8s} {'coincide':>8s} {'falla':>6s}")
for rn in sorted(set(cg.res_name)):
    n_res = int((cg.res_name == rn).sum())
    nb = int((cg.resn == rn).sum()) / n_res
    print(f"  {rn:5s} {n_res:6d} {nb:9.2f} {len(EXPECTED.get(rn, [])):8d} {good[rn]:8d} {bad[rn]:6d}")
print(f"  TOTAL residuos={cg.nres} coinciden={sum(good.values())} fallan={sum(bad.values())}")
for rn, c in detail.items():
    for k2, v in c.items():
        print(f"    {rn}: {v}x {k2}")
print("  Beads que SIRAH deriva de HIDROGENOS (BPG<-HG, BPE<-HE1):")
for rn, b in H_BEADS.items():
    n_res = int((cg.res_name == rn).sum())
    have = sum(1 for k in range(cg.nres) if cg.res_name[k] == rn and b in cg.residue_atoms(k))
    print(f"    {rn}: {have}/{n_res} residuos tienen {b}")
his = {rn: int((cg.res_name == rn).sum()) for rn in ("sHe", "sHd", "sHp")}
print(f"  Variantes de histidina: {his}")

print("\n1c. Distancias entre residuos consecutivos")
ds_gc, jumps, d_all, same_all = report_consecutive(cg, "GC")
report_consecutive(cg, "GO", "GN", thr_hi=3.5, thr_lo=1.5)
print(f"  saltos de numeracion (resi(i+1)-resi(i) != 1) dentro de un segmento: {len(jumps)}")
print(f"  histograma GC-GC (A): " + ", ".join(
    f"[{a:.1f},{b:.1f}):{int(((ds_gc >= a) & (ds_gc < b)).sum())}" for a, b in
    [(2.5, 3.0), (3.0, 3.5), (3.5, 4.0), (4.0, 4.5), (4.5, 6.0), (6.0, 99)]))
# cis-prolina? GC-GC ~2.9-3.0 en cis
print("\n1d. Carga neta estimada con cargas de amino.lib (termini con amino.n/c.lib)")
q = 0.0; qdet = Counter()
for s in range(nseg):
    idx = np.flatnonzero(cg.res_seg == s)
    for j, k in enumerate(idx):
        rn = cg.res_name[k]
        if j == 0: qq = CHARGE_N.get("n" + rn[1:], CHARGE[rn])
        elif j == len(idx) - 1: qq = CHARGE_C.get("c" + rn[1:], CHARGE[rn])
        else: qq = CHARGE[rn]
        q += qq; qdet[rn] += qq
print(f"  carga total capside CG = {q:+.1f} e  (por tipo: " +
      ", ".join(f"{k}:{v:+.0f}" for k, v in sorted(qdet.items()) if abs(v) > 0.5) + ")")
print(f"  por cadena: {q / nseg:+.2f} e  -> 'addIonsRand NaW 0' {'NO puede neutralizar (carga positiva, hacen falta ClW)' if q > 0 else 'anade NaW hasta neutralizar'}")

# ======================================================================
hr("2. CORRESPONDENCIA CON LA CAPSIDE ALL-ATOM DE PACKMAN (capside.pdb)")
aa = PDB(CAPS_AA, resname_width=3).summary("2a. Resumen capside.pdb")
print(f"  residuos por segmento: {dict(Counter(Counter(aa.res_seg).values()))}")
seqs_aa = ["".join(f"{AA2CG.get(r,'?')}," for r in aa.res_name[aa.res_seg == s]) for s in range(aa.segment.max() + 1)]
seqs_cg = ["".join(f"{r}," for r in cg.res_name[cg.res_seg == s]) for s in range(nseg)]
print(f"  secuencias (tras mapear AA->SIRAH) identicas segmento a segmento: {seqs_aa == seqs_cg}")
print(f"  secuencias unicas en AA: {len(set(seqs_aa))}  en CG: {len(set(seqs_cg))}")
# coordenadas: GC == CA, GN == N, GO == O ?
def coords_of(p, atom):
    out = np.full((p.nres, 3), np.nan)
    for k in range(p.nres):
        a = p.residue_xyz_of(k, atom)
        if a is not None: out[k] = a
    return out
if aa.nres == cg.nres:
    for a_at, c_at in (("CA", "GC"), ("N", "GN"), ("O", "GO")):
        d = np.linalg.norm(coords_of(aa, a_at) - coords_of(cg, c_at), axis=1)
        print(f"  |{a_at}(AA) - {c_at}(CG)|: max={np.nanmax(d):.4f} A  media={np.nanmean(d):.4f}  (n={np.sum(~np.isnan(d))})")
    # side-chain mapping check for a few
    for rn_aa, pairs in (("LYS", [("CG", "BCG"), ("CE", "BCE")]), ("ARG", [("CZ", "BCZ"), ("NH1", "BNN1")]),
                         ("SER", [("OG", "BOG")]), ("TRP", [("NE1", "BNE"), ("CZ2", "BCZ")])):
        ks = np.flatnonzero(aa.res_name == rn_aa)
        for a_at, c_at in pairs:
            d = [np.linalg.norm(aa.residue_xyz_of(k, a_at) - cg.residue_xyz_of(k, c_at)) for k in ks
                 if aa.residue_xyz_of(k, a_at) is not None and cg.residue_xyz_of(k, c_at) is not None]
            d = np.array(d)
            print(f"  {rn_aa} {a_at}->{c_at}: max dev {d.max():.4f} A (n={len(d)}); residuos con dev>0.05 A: {int((d>0.05).sum())}")
    # desviaciones por tipo de residuo (busca huella de 'debump' de pdb2pqr)
    moved = Counter(); tot = Counter()
    for k in range(aa.nres):
        rn = cg.res_name[k]; tot[rn] += 1
        sl_cg = slice(cg.res_start[k], cg.res_end[k]); sl_aa = slice(aa.res_start[k], aa.res_end[k])
        dev = 0.0
        for nm, x in zip(cg.name[sl_cg], cg.xyz[sl_cg]):
            if nm in ("BPG", "BPE"): continue
            dmin = np.linalg.norm(aa.xyz[sl_aa] - x, axis=1).min()
            dev = max(dev, dmin)
        if dev > 0.05: moved[rn] += 1
    print(f"  residuos cuyos beads (sin BPG/BPE) NO coinciden con ningun atomo pesado del AA (dev>0.05 A): {sum(moved.values())} de {aa.nres} -> por tipo {dict(moved)}")
    movedk = [k for k in range(aa.nres) if cg.res_name[k]=="sR"]
    # which chains / which residue numbers moved
    mv = []
    for k in range(aa.nres):
        if cg.res_name[k] != "sR": continue
        sl_cg = slice(cg.res_start[k], cg.res_end[k]); sl_aa = slice(aa.res_start[k], aa.res_end[k])
        dev = max(np.linalg.norm(aa.xyz[sl_aa] - x, axis=1).min() for x in cg.xyz[sl_cg])
        if dev > 0.05: mv.append((int(cg.res_seg[k]), int(cg.res_num[k])))
    print(f"  ARG movidas: {len(mv)}; numeros de residuo implicados: {sorted(set(n for _, n in mv))}; segmentos implicados: {len(set(s for s, _ in mv))}")
    # cis peptides
    short = np.flatnonzero((d_all < 3.2) & same_all)
    print(f"  pares GC-GC < 3.2 A (peptido cis): {len(short)}; residuo i+1 = {dict(Counter(cg.res_name[short + 1]))}; numeros = {sorted(set(int(x) for x in cg.res_num[short + 1]))}")
    # BPG position vs OG (should be ~1 A: it is the hydroxyl H)
    ks = np.flatnonzero(cg.res_name == "sS")
    d = [np.linalg.norm(cg.residue_xyz_of(k, "BOG") - cg.residue_xyz_of(k, "BPG")) for k in ks]
    print(f"  sS: |BOG-BPG| media={np.mean(d):.3f} A min={np.min(d):.3f} max={np.max(d):.3f}  (O-H covalente ~0.96 A => bead puesto sobre un H real)")
    ks = np.flatnonzero(cg.res_name == "sW")
    d = [np.linalg.norm(cg.residue_xyz_of(k, "BNE") - cg.residue_xyz_of(k, "BPE")) for k in ks]
    print(f"  sW: |BNE-BPE| media={np.mean(d):.3f} A  (N-H ~1.01 A)")
    ks = np.flatnonzero(cg.res_name == "sC")
    d = [np.linalg.norm(cg.residue_xyz_of(k, "BSG") - cg.residue_xyz_of(k, "BPG")) for k in ks]
    print(f"  sC: |BSG-BPG| media={np.mean(d):.3f} A  (S-H ~1.34 A)")
print("  AA capside.pdb: distancias CA-CA consecutivas")
report_consecutive(aa, "CA", tag="  ")
n_H_aa = int(np.sum(aa.elem == "H"))
print(f"  hidrogenos en capside.pdb: {n_H_aa}  (la CG tiene beads BPG/BPE => la entrada a cgconv NO fue este archivo tal cual)")

# ======================================================================
hr("3. SALIDA DE PACKMOL DE SUSTRATINAITOR (3J7L-GYE.pdb)")
pk = PDB(PACKED).summary("3a. Resumen")
is_cap = pk.resn != "GYE"
n_cap = int(is_cap.sum()); n_gye = int((~is_cap).sum())
print(f"  atomos capside={n_cap}  atomos GYE={n_gye} = {n_gye // 144} copias x 144")
shift = pk.xyz[:n_cap] - cg.xyz
print(f"  capside = 3J7L_cg desplazada por {shift.mean(axis=0).round(3)}; dispersion del desplazamiento (max) = {np.abs(shift - shift.mean(axis=0)).max():.3f} A")
print(f"  centroide capside empaquetada: {pk.xyz[:n_cap].mean(axis=0).round(3)}")
print(f"  nombres/numeros de residuo de la capside preservados: {bool(np.all(pk.resn[:n_cap] == cg.resn) and np.all(pk.resi[:n_cap] == cg.resi))}")
print(f"  numeracion GYE: resi min={pk.resi[~is_cap].min()} max={pk.resi[~is_cap].max()}; chain GYE={set(pk.chain[~is_cap])}")
# Enlaces espurios que crearia tleap sin TER: pares consecutivos de residuos en el mismo segmento con GC-GC > 4.5
pos = coords_of(pk, "GC")
d = np.linalg.norm(pos[1:] - pos[:-1], axis=1)
same = pk.res_seg[1:] == pk.res_seg[:-1]
capres = np.flatnonzero(pk.res_name != "GYE")
dd = d[: len(capres) - 1]
print(f"  pares de residuos de capside consecutivos SIN TER entre ellos con GC-GC > 4.5 A: {int((dd > 4.5).sum())}  "
      f"(= enlaces peptidicos espurios que tleap intentaria crear; distancia media de esos 'enlaces' = {dd[dd > 4.5].mean():.1f} A, max={dd[dd > 4.5].max():.1f} A)")
print(f"  en 3J7L_cg.pdb (con sus 180 TER) ese numero es: {int((d_all[same_all] > 4.5).sum())}")

if not want("3"):
    print("  (3b omitido)")
else:
  print("\n3b. Geometria: donde quedaron las 200 GYE")
  cap_xyz = pk.xyz[:n_cap]; gye_xyz = pk.xyz[n_cap:].reshape(200, 144, 3)
  center = cap_xyz.mean(axis=0)
  r_cap = np.linalg.norm(cap_xyz - center, axis=1)
  pct = np.percentile(r_cap, [0, 1, 5, 50, 95, 99, 100])
  print(f"  radio de los beads de la capside desde su centroide (A): min={pct[0]:.1f} p1={pct[1]:.1f} p5={pct[2]:.1f} mediana={pct[3]:.1f} p95={pct[4]:.1f} p99={pct[5]:.1f} max={pct[6]:.1f}")
  print(f"  extension cartesiana capside: x[{cap_xyz[:,0].min():.1f},{cap_xyz[:,0].max():.1f}] y[{cap_xyz[:,1].min():.1f},{cap_xyz[:,1].max():.1f}] z[{cap_xyz[:,2].min():.1f},{cap_xyz[:,2].max():.1f}]  (caja Packmol: +-150.3/147.2/152.0)")
  # histogram of r_cap to find shell
  hist, edges = np.histogram(r_cap, bins=np.arange(0, 160, 5))
  print("  perfil radial de beads (bin 5 A): " + " ".join(f"{int(e)}:{h}" for e, h in zip(edges[:-1], hist) if h))
  r_in = np.percentile(r_cap, 1); r_out = np.percentile(r_cap, 99)
  gye_com = gye_xyz.mean(axis=1)
  r_gye = np.linalg.norm(gye_com - center, axis=1)
  r_gye_atoms = np.linalg.norm(gye_xyz - center, axis=2)
  inside = r_gye < r_in; shell = (r_gye >= r_in) & (r_gye <= r_out); outside = r_gye > r_out
  print(f"  radio del COM de cada GYE: min={r_gye.min():.1f} mediana={np.median(r_gye):.1f} max={r_gye.max():.1f}")
  print(f"  usando capa de la capside [p1={r_in:.1f}, p99={r_out:.1f}] A: GYE en el LUMEN={inside.sum()}  en la CAPA/poros={shell.sum()}  FUERA={outside.sum()}")
  allin = (r_gye_atoms.max(axis=1) < r_in).sum(); allout = (r_gye_atoms.min(axis=1) > r_out).sum()
  print(f"  GYE con TODOS sus atomos en el lumen: {allin}; con todos fuera: {allout}; a caballo: {200 - allin - allout}")
  print(f"  histograma radial de COM GYE (bin 20 A): " + " ".join(
      f"[{a}-{a+20}):{int(((r_gye >= a) & (r_gye < a + 20)).sum())}" for a in range(0, 280, 20)))
  # distancias minimas GYE-capside (filtrado radial) y GYE-GYE
  min_cap = np.zeros(200)
  for i in range(200):
      rr = r_gye_atoms[i]
      sel = (r_cap > rr.min() - 25) & (r_cap < rr.max() + 25)
      if not sel.any():
          min_cap[i] = np.inf; continue
      sub = cap_xyz[sel]
      dmin = np.inf
      for j in range(0, 144, 48):
          blk = gye_xyz[i, j:j + 48]
          dm = np.sqrt(((blk[:, None, :] - sub[None, :, :]) ** 2).sum(-1)).min()
          dmin = min(dmin, dm)
      min_cap[i] = dmin
  print(f"  distancia minima atomo(GYE)-bead(capside): min={min_cap.min():.2f} A mediana={np.median(min_cap):.2f} max={min_cap.max():.1f}  (tolerance Packmol 2.0)")
  print(f"  GYE a <= 4 A de la capside (contacto): {(min_cap <= 4).sum()}; a > 20 A: {(min_cap > 20).sum()}")
  # GYE-GYE
  com_d = np.linalg.norm(gye_com[:, None] - gye_com[None], axis=2); np.fill_diagonal(com_d, np.inf)
  print(f"  distancia COM-COM minima entre GYE: {com_d.min():.1f} A; vecino mas cercano mediana: {np.median(com_d.min(axis=1)):.1f} A")
  # volume / concentration
  box_v = 2 * 150.336 * 2 * 147.174 * 2 * 151.982
  sphere_v = 4 / 3 * np.pi * r_out ** 3; lumen_v = 4 / 3 * np.pi * r_in ** 3
  print(f"  volumen caja={box_v/1e6:.2f}e6 A^3; esfera externa capside={sphere_v/1e6:.2f}e6; lumen={lumen_v/1e6:.2f}e6; caja fuera de la esfera={(box_v - sphere_v)/1e6:.2f}e6 (= {100*(box_v-sphere_v)/box_v:.0f}% de la caja)")
  mol_per_A3_to_M = 1e27 / 6.022e23
  print(f"  concentracion nominal de GYE en la caja: {200 / box_v * mol_per_A3_to_M * 1e3:.1f} mM; en el lumen (si todas dentro): {200 / lumen_v * mol_per_A3_to_M * 1e3:.1f} mM")
  # box check
  print(f"  atomos GYE fuera de la caja declarada: {int(((np.abs(gye_xyz[:,:,0]) > 150.336) | (np.abs(gye_xyz[:,:,1]) > 147.174) | (np.abs(gye_xyz[:,:,2]) > 151.982)).sum())}")

# ======================================================================
if not want("4"): sys.exit(0) if not want("5") else None
hr("4. LIGANDO GYE: all-atom (GYE.pdb) vs 17 beads manuales (GYE_cg_manual.pdb)")
g_aa = PDB(GYE_AA, resname_width=3).summary("4a. GYE.pdb (lo que empaqueto Packmol)")
g_cg = PDB(GYE_CG, resname_width=3).summary("4b. GYE_cg_manual.pdb (NO usado por Packmol)")
print(f"  lineas ATOM con columna resSeq (23-26) mal formada: {getattr(g_cg, 'malformed', 0)} de {g_cg.n} (chain 'A' cae en col 23 en vez de 22 -> PDB invalido)")
heavy = np.array([not re.match(r"^H", n) for n in g_aa.name])
print(f"  GYE.pdb: {g_aa.n} atomos, {int(heavy.sum())} pesados, {int((~heavy).sum())} H. GYE_cg_manual: {g_cg.n} beads")
print(f"  mismo marco de coordenadas? centroide AA={g_aa.xyz.mean(0).round(2)} centroide CG={g_cg.xyz.mean(0).round(2)}")
print("  bead -> atomo pesado mas cercano (A) y n atomos pesados a <1.0 A / <2.0 A:")
for i in range(g_cg.n):
    d = np.linalg.norm(g_aa.xyz[heavy] - g_cg.xyz[i], axis=1)
    j = d.argmin()
    print(f"    {i+1:2d} {g_cg.name[i]:4s} nearest={g_aa.name[heavy][j]:4s} {d[j]:5.2f}  <1A:{int((d<1).sum())} <2A:{int((d<2).sum())}")
order = ["GC", "GO", "GC", "GO", "BGL", "BCE", "BC1", "BC2", "BC3", "BC4", "BCT", "BF1", "BF2", "BF3", "BF4", "BF5", "BF6"]
print("  distancias entre beads consecutivos segun el orden del archivo (1-2, 2-3, ...):")
dd = np.linalg.norm(np.diff(g_cg.xyz, axis=0), axis=1)
print("    " + "  ".join(f"{g_cg.name[i]}-{g_cg.name[i+1]}:{dd[i]:.2f}" for i in range(g_cg.n - 1)))
# nearest-neighbour bead distances
bd = np.linalg.norm(g_cg.xyz[:, None] - g_cg.xyz[None], axis=2); np.fill_diagonal(bd, np.inf)
print(f"  vecino mas cercano por bead: min={bd.min(axis=1).min():.2f} max={bd.min(axis=1).max():.2f} A; beads con vecino <2.0 A: {int((bd.min(axis=1) < 2.0).sum())}  (SIRAH: enlaces bead-bead tipicos 3-5 A)")
print(f"  extension del GYE all-atom: {np.linalg.norm(g_aa.xyz.max(0) - g_aa.xyz.min(0)):.1f} A (diagonal), max dist entre atomos: {max(np.linalg.norm(g_aa.xyz - g_aa.xyz[i], axis=1).max() for i in range(g_aa.n)):.1f} A")
print(f"  nombres de bead usados: {sorted(set(g_cg.name))}  -> GC/GO/BCE/BGL son nombres del backbone/lipidos SIRAH, 'GYE' no existe en ninguna .lib de SIRAH")

# ======================================================================
if not want("5"): sys.exit(0)
hr("5. RUTA PACKMAN: mismos chequeos sobre sus PDB")
rec = PDB(CAPS_REC, resname_width=3).summary("5a. capside_recentrada.pdb (salida PyMOL, entrada a Packmol)")
print("  CA-CA consecutivos:")
ds, jumps, d_rec, same_rec = report_consecutive(rec, "CA", tag="  ")
print(f"  pares consecutivos SIN TER con CA-CA > 4.5 A (= uniones espurias si se pasa asi a tleap): {int((ds > 4.5).sum())}")
print(f"  orden de atomos: primer residuo de cada segmento = {[ (rec.res_chain[rec.res_seg==s][0], rec.res_num[rec.res_seg==s][0]) for s in range(rec.segment.max()+1)]}")
print(f"  segids unicos: {len(set(rec.seg))}; chains: {dict(Counter(rec.res_chain))}")
enz = PDB(ENZ_AA, resname_width=3).summary("5b. enzima.pdb")
ds_e, jumps_e, _, _ = report_consecutive(enz, "CA", tag="  ")
print(f"  saltos de numeracion dentro de la enzima (huecos del cristal): {len(jumps_e)} -> " +
      ", ".join(f"{enz.res_num[j]}->{enz.res_num[j+1]}" for j in jumps_e))
print(f"  CA-CA > 4.5 A en la enzima: {int((ds_e > 4.5).sum())} (cada uno es un hueco que tleap 'cerraria' con un enlace largo)")
n_polarH_res = sum(int((enz.res_name == r).sum()) for r in ("SER", "THR", "CYS", "TRP"))
print(f"  residuos de la enzima cuyo bead SIRAH sale de un H (SER/THR/CYS/TRP): {n_polarH_res} de {enz.nres}; hidrogenos presentes: {int((enz.elem=='H').sum())}")
print(f"  residuos no estandar en enzima.pdb: {sorted(set(enz.res_name) - set(AA2CG))}")
pmp = PDB(PM_PACKED, resname_width=3).summary("5c. capside_1enzimas_*.pdb (salida Packmol que run_maestro.sh manda a cgconv.pl)")
ds_p, _, _, _ = report_consecutive(pmp, "CA", tag="  ")
print(f"  pares consecutivos SIN TER con CA-CA > 4.5 A: {int((ds_p > 4.5).sum())}  (capside: 180 copias + enzima => todo en un solo 'chain' para tleap)")
n_polarH_cap = sum(int((pmp.res_name == r).sum()) for r in ("SER", "THR", "CYS", "TRP"))
print(f"  residuos SER/THR/CYS/TRP en el sistema empaquetado: {n_polarH_cap} -> cgconv sin H no generaria su bead BPG/BPE; tleap los 'anadiria' en posicion arbitraria")
print(f"  seriales hexadecimales: {pmp.hex_serials} (Packmol pasa a hex por encima de 99999)")
print(f"  hidrogenos: {int((pmp.elem=='H').sum())}")
print("\nFIN")
