# sustratinaitor — substrate placement around the capsid

Builds the substrate **glucosylceramide (residue code GYE)**, the molecule that accumulates
in Gaucher disease, and distributes 200 copies of it around the **3J7L** capsid (3J7L is the
**BMV** capsid, 149/149 residues identical to the Studio's `BMV_IJS9`) to produce a starting
configuration for a coarse-grained molecular dynamics simulation. It complements
[gate 4](../README.md) by supplying the capsid-plus-substrate system that
[PackMan](../PackMan.v.1.2) would then simulate.

> **Status: stages 1–3 ran, stage 4 has not run and cannot run as committed.** The packed
> system (`3J7L-GYE.pdb`: the coarse-grained capsid plus 200 GYE copies) exists with its
> Packmol log (converged, violation 0.000, seed 1234567). Solvation, ionisation and the MD
> itself have **not** been executed. Two independent audits of this engine (2026-10-04,
> `AUDITORIA_SUSTRATO_Y_CG.md` on branches `claude/audit-sirah-coarse-grain-conversion-e9h0rt`
> and `claude/audit-coarse-grained-conversion-rfst1e`) found:
>
> - **The capsid conversion is correct** and reproducible byte for byte
>   (`pdb2pqr --ff=AMBER` → `cgconv.pl`; 180 `TER`, all BPG/BPE beads present). It is the
>   reference recipe PackMan should copy.
> - **The packed output is not usable downstream**: `3J7L-GYE.pdb` has **0 `TER` records**
>   (the capsid input has 180) and hexadecimal atom serials above 99 999, so tLeaP would
>   chain the subunits and `pdb2pqr` aborts on it.
> - **The packed GYE is all-atom (144 atoms) under a coarse-grained protocol** (`dt = 20 fs`,
>   no SHAKE): 17 800 explicit hydrogens at 20 fs are not integrable, and there are no
>   GAFF2 × SIRAH cross parameters. The "CG" `GYE_cg_manual.pdb` has **no topology and no
>   coarse-grained geometry** (beads placed on individual atoms 1.4 Å apart, bead names that
>   collide with the protein backbone, no `.lib`); it is not a starting point.
> - **Stage 4 cannot start**: `gensystem.leap` writes `3J7L-GYE_cg.prmtop` and `run_MD.sh`
>   looks for `3J7L-GYE_cg-WAT.prmtop`; the four `.in` files, the SIRAH bundle and
>   `GYE.mol2`/`.frcmod` are not in the stage-4 directory; there is no production stage and
>   no `set -e`, so the script would launch all stages and exit 0 regardless.
> - 40 of the 200 GYE copies have their centre of mass **inside the capsid lumen**, 36 in the
>   shell and 124 outside; 18 are entirely inside. The box, not a shell, decides where they go.
>
> The generic SIRAH force field parameter files are deliberately **not** included here. The
> open decision `CIENCIA-2` is described under *Resolution mismatch* below, with the audits'
> recommendation.

The full file-by-file account, including the Packmol log analysis, is in
[`EXPLICACION.md`](EXPLICACION.md) (Spanish).

## Stages

### `1_capside/` — the capsid

`3J7L_cg.pdb`: the 3J7L capsid already converted to coarse-grained SIRAH representation,
roughly 131,820 beads. It is held **fixed** during packing.

### `2_ligando_GYE/` — building the substrate

Glucosylceramide had no predefined coarse-grained parameters in SIRAH, so it was built in
three steps:

1. **Manual coarse-grained sketch** (`GYE_cg_manual.pdb`,
   `README_conversion_gye_cg.md`). SIRAH's automatic converter (`cgconv.pl`) failed for GYE
   for lack of parameters, so a 17-bead partition was drawn by hand — 4 for the glucose head
   (GC/GO), 2 linkers (BGL/BCE), 5 along the sphingosine chain (BC1–BCT) and 6 for the fatty
   acid (BF1–BF6). **Correction (audit 2026-10-04):** contrary to what
   `README_conversion_gye_cg.md` states, the bead coordinates are **not** centres of mass of
   atom groups (they sit on individual atoms, 1.4 Å apart) and the file is **not** compatible
   with SIRAH topology generation (no `.lib`, bead names `GC`/`GO` collide with the protein
   backbone, invalid `resSeq`, a 39 Å `BCT–BF1` gap). It is a partition sketch, not a
   coarse-grained model, and was never used by any later stage.
2. **Chemical parametrisation** with antechamber, GAFF2 and AM1-BCC (`sqm.in`, `sqm.out`,
   `ATOMTYPE.INF`, `ANTECHAMBER_AC.AC`, `ANTECHAMBER_AM1BCC.AC`). This yields `GYE.mol2`
   (structure plus partial charges) and `GYE.frcmod` (the bond, angle and dihedral
   parameters missing from stock GAFF2).
3. **Loading into tLEaP** (`convert.leap`, `GYE.log`): loads `GYE.mol2` and `GYE.frcmod`
   against `leaprc.gaff2` and saves the unit as `GYE.off` (a reusable library) and `GYE.pdb`
   (the coordinates that Packmol actually consumes).

### `3_empaquetado_packmol/` — placing the substrate around the capsid

There is no sophisticated geometric shell algorithm here, and the method is worth stating
plainly: a box the size of the capsid is defined, the capsid is **fixed at the centre**, and
Packmol is asked to fit N copies of the ligand into that box without clashing with the fixed
capsid atoms.

```
structure 3J7L_cg.pdb
  number 1
  center
  fixed 0. 0. 0. 0. 0. 0.
end structure

structure GYE.pdb
  number 200
  inside box -150.336 -147.174 -151.982 150.336 147.174 151.982
end structure
```

The box half-widths (about 150 × 147 × 152 Å) roughly match the maximum radius of the
centred capsid (~142 Å), so the box just wraps the volume the capsid occupies. Packmol
optimises the positions and orientations of the 200 GYE molecules with a 2.0 Å tolerance,
filling whatever free space exists — outside the capsid and inside its cavity alike,
wherever there is room. The result is therefore a **packed distribution, not an explicit
shell**, bounded by the capsid's own geometry and the chosen box size.

Outputs: `3J7L-GYE.pdb` (capsid plus 200 GYE, no water or ions yet; **0 `TER` records and
hexadecimal serials from atom 100 000**, to be normalised before any use) and the logs
`packmol_run.log` (complete: `Success!`, maximum violation 0.000, seed 1234567) and
`packmol.log` (truncated mid-optimisation; the complete one is `packmol_run.log`).

Measured on the committed file: capsid centroid at the origin, inner/outer radius
89.5/142.6 Å; GYE centres of mass in lumen / shell / outside = 40 / 36 / 124. If the
question is pore crossing (gate 1), the lumen should be excluded (`outside sphere 0 0 0
143`); if it is encapsulated substrate, use `inside sphere` with the internal radius.

### `4_ensamblaje_y_simulacion/` — assembly and simulation (not run, not runnable as is)

- `gensystem.leap`: a tLEaP script that loads `3J7L-GYE.pdb` together with the SIRAH force
  field (not included) and GAFF2, solvates with coarse-grained WT4 water in a truncated
  octahedral box (20 Å buffer), adds **neutralising NaW only** (`addIonsRand protein NaW 0`;
  the "0.15 M" in its comment is not implemented), and writes `3J7L-GYE_cg.prmtop` /
  `3J7L-GYE_cg.ncrst`.
- `run_MD.sh`: minimisation and equilibration (em1 → em2 → eq1 → eq2) for `pmemd.cuda`.
  It expects `3J7L-GYE_cg-WAT.prmtop`, a name `gensystem.leap` never writes; the `.in`
  files it calls are not in this directory; there is no production stage; without `set -e`
  every stage is launched regardless and the script exits 0.

Neither has been executed.

## Requirements

- **Packmol** — packing. `apt install packmol` or <https://m3g.github.io/packmol/>.
- **AmberTools** — `antechamber`, `sqm`, `tleap` for parametrisation and system building.
- **AMBER** (`pmemd.cuda`) and a CUDA GPU for stage 4.
- **The SIRAH force field** — not included; its own licence applies. See
  [`THIRD_PARTY.md`](../THIRD_PARTY.md) and <http://www.sirahff.com/>.

## Usage

Stages 2–3 are reproducible from the files in this directory (stage 1's recipe is
`pdb2pqr --ff=AMBER capside.pdb` → `cgconv.pl`, verified to reproduce `3J7L_cg.pdb` byte for
byte; stage 4 does not run, see above):

```bash
# 2. Parametrise the ligand (from 2_ligando_GYE/)
antechamber -i GYE.pdb -fi pdb -o GYE.mol2 -fo mol2 -c bcc -at gaff2
parmchk2 -i GYE.mol2 -f mol2 -o GYE.frcmod
tleap -f convert.leap                  # writes GYE.off and GYE.pdb

# 3. Pack 200 copies around the fixed capsid (from 3_empaquetado_packmol/)
packmol < packmol_input.inp            # writes 3J7L-GYE.pdb

# 4. Solvate, ionise and simulate (NOT YET RUN — needs SIRAH + AMBER)
tleap -f gensystem.leap
./run_MD.sh
```

To change how much substrate surrounds the capsid, edit `number 200` in
`packmol_input.inp`. To use a different capsid, replace `3J7L_cg.pdb` and recompute the box
dimensions from the new structure's maximum radius.

## Resolution mismatch (`CIENCIA-2`) — read before reusing this system

The packed system is **physically inconsistent as it stands**, and this is recorded rather
than quietly fixed. Packmol packed the **all-atom** GYE structure of 144 atoms, not the
17-bead coarse-grained version: the atom count of the result
(160,620 = 131,820 + 200 × 144) confirms it, and `GYE_cg_manual.pdb` was left unused. The
resulting system therefore combines a coarse-grained capsid, an atomistic ligand and
coarse-grained water, which is not a valid SIRAH system.

The decision belongs to the author, and the audits of 2026-10-04 conclude it can be taken
now, without running anything, because the committed hybrid is ruled out by physics
(explicit hydrogens at 20 fs without SHAKE; no GAFF2 × SIRAH cross parameters; no `TER`):

- **Option A — parametrise GYE in SIRAH.** A 2–4 week sub-project (head group following the
  SIRAH glycan bead pattern, tails with `xMY`/`xPA`/`xOL` beads, charges, validation against
  an all-atom MD of GYE). `GYE_cg_manual.pdb` is **not** a usable starting point (see
  stage 2).
- **Option B — take the substrate out of the coarse-grained MD** (recommended by the audits).
  Gate 4 simulates capsid + enzyme in SIRAH (PackMan, once repaired); substrate physics
  (pore crossing, active site) is done all-atom in small systems, reusing `GYE.mol2` /
  `GYE.frcmod`, which are a correct GAFF2/AM1-BCC parametrisation. Stage 4 of this engine
  would then be retired.
- **All all-atom** for the whole capsid — not viable at this size.

Tracked as `CIENCIA-2` in [`ESTADO.md`](../ESTADO.md) §4b; tasks SU-1 to SU-3 and decision
DC-3 in `HOJA_DE_RUTA.md` (branch `claude/consolidate-audit-roadmap-k82rek`).

## Contributing and support

Issues and pull requests go to the monorepo:
<https://github.com/najera-maldonado/vlp-studio/issues>. See
[`CONTRIBUTING.md`](../CONTRIBUTING.md). Project boundary: Packmol, AmberTools and the SIRAH
force field are **called**, never forked.

## License

Part of VLP Studio, under **GNU AGPLv3 or later**. See [`LICENSE`](../LICENSE) and
[`THIRD_PARTY.md`](../THIRD_PARTY.md). Copyright (C) 2026 najera-maldonado.
