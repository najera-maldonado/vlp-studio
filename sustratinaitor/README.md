# sustratinaitor — substrate placement around the capsid

Builds the substrate **glucosylceramide (residue code GYE)**, the molecule that accumulates
in Gaucher disease, and distributes 200 copies of it around the **3J7L** capsid to produce
the starting configuration for a coarse-grained molecular dynamics simulation. It
complements [gate 4](../README.md) by supplying the capsid-plus-substrate system that
[PackMan](../PackMan.v.1.2) would then simulate.

> **Status: stages 1–3 are done, stage 4 has not been run.** The packed system
> (`3J7L-GYE.pdb`: the coarse-grained capsid surrounded by 200 GYE copies) exists and has
> execution logs. Solvation, ionisation and the MD itself have **not** been executed. The
> generic SIRAH force field parameter files are deliberately **not** included here: they are
> the force field's own library, not something generated for this system.
>
> **Known open issue (`CIENCIA-2`):** the packed system mixes resolutions. See
> *Resolution mismatch* below before building on it.

The full file-by-file account, including the Packmol log analysis, is in
[`EXPLICACION.md`](EXPLICACION.md) (Spanish).

## Stages

### `1_capside/` — the capsid

`3J7L_cg.pdb`: the 3J7L capsid already converted to coarse-grained SIRAH representation,
roughly 131,820 beads. It is held **fixed** during packing.

### `2_ligando_GYE/` — building the substrate

Glucosylceramide had no predefined coarse-grained parameters in SIRAH, so it was built in
three steps:

1. **Manual coarse-grained mapping** (`GYE_cg_manual.pdb`,
   `README_conversion_gye_cg.md`). SIRAH's automatic converter (`cgconv.pl`) failed for GYE
   for lack of parameters, so the molecule was mapped by hand following SIRAH conventions
   (about four carbons per bead along aliphatic chains): **17 beads** in total — 4 for the
   glucose head (GC/GO), 2 linkers (BGL/BCE), 5 along the sphingosine chain (BC1–BCT) and 6
   for the fatty acid (BF1–BF6). Each bead's coordinates come from the centre of mass of the
   corresponding all-atom group.
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

Outputs: `3J7L-GYE.pdb` (capsid plus 200 GYE, no water or ions yet) and the optimisation
logs `packmol.log` and `packmol_run.log`, in which the overlap penalty falls from about
61,000 to about 1,455 as badly oriented molecules are relocated.

### `4_ensamblaje_y_simulacion/` — assembly and simulation (not run)

- `gensystem.leap`: a tLEaP script that loads `3J7L-GYE.pdb` together with the SIRAH force
  field (not included) and GAFF2, computes the system charge, solvates with coarse-grained
  WT4 water in a truncated octahedral box, adds NaW counter-ions, and writes the final
  topology and coordinates (`3J7L-GYE_cg.prmtop`, `3J7L-GYE_cg.ncrst`).
- `run_MD.sh`: a minimisation and equilibration pipeline (em1 → em2 → eq1 → eq2) for
  `pmemd.cuda` on the solvated system.

Neither has been executed.

## Requirements

- **Packmol** — packing. `apt install packmol` or <https://m3g.github.io/packmol/>.
- **AmberTools** — `antechamber`, `sqm`, `tleap` for parametrisation and system building.
- **AMBER** (`pmemd.cuda`) and a CUDA GPU for stage 4.
- **The SIRAH force field** — not included; its own licence applies. See
  [`THIRD_PARTY.md`](../THIRD_PARTY.md) and <http://www.sirahff.com/>.

## Usage

Stages 1–3 are reproducible from the files in this directory:

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

The decision is between two options, and it belongs to the author, to be taken when the
corresponding MD is actually run:

- **All coarse-grained** — redo the packing with `GYE_cg_manual.pdb` (17 beads). Consistent
  with PackMan, but the manual coarse-grained mapping has not been validated.
- **All all-atom** — not viable for a whole capsid at this size.

Tracked as `CIENCIA-2` in [`ESTADO.md`](../ESTADO.md) §4b.

## Contributing and support

Issues and pull requests go to the monorepo:
<https://github.com/najera-maldonado/vlp-studio/issues>. See
[`CONTRIBUTING.md`](../CONTRIBUTING.md). Project boundary: Packmol, AmberTools and the SIRAH
force field are **called**, never forked.

## License

Part of VLP Studio, under **GNU AGPLv3 or later**. See [`LICENSE`](../LICENSE) and
[`THIRD_PARTY.md`](../THIRD_PARTY.md). Copyright (C) 2026 najera-maldonado.
