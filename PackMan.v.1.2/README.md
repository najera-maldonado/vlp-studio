# PackMan v1.2 — coarse-grained molecular dynamics

Engine of **gate 4 ("does it survive?")** of [VLP Studio](../README.md). PackMan prepares an
enzyme-inside-capsid system for **coarse-grained molecular dynamics with the SIRAH force
field**: packing, conversion to coarse-grained resolution, system building with LEaP, then
minimisation, equilibration and production.

> **Status: the MD has never been run, and it cannot run as committed.** An independent
> audit (2026-10-04, `AUDITORIA_MD.md` on branch `claude/audit-packman-dynamics-engine-52svym`)
> found that:
>
> - **The committed inputs are stubs, not a protocol.** The three SIRAH stages
>   `eq1_WT4.in`, `eq2_WT4.in` and `prod_md_WT4.in` each have `nstlim = 500` at
>   `dt = 0.020` ps, i.e. **10 ps each**, although their title lines read "15ns",
>   "35ns" and "0.01ns (fast test)". The whole 13-file sequence totals **≈ 240 ps**; the
>   equivalent SIRAH reference protocol (`tutorial/5`) totals ≈ 1.03 µs. No 15 ns or 35 ns
>   simulation has been run or can be produced from these files.
>   `grep -H nstlim archivos_dm_cg/*.in` shows it.
> - **Eight of the thirteen inputs are all-atom** (`heat1..6`, `density_eq`, `final_eq`:
>   `dt = 0.002`, SHAKE, `cut = 9`, `gamma_ln = 2`, restraint mask `@CA,C,N,O`) applied to
>   a SIRAH topology in which those atom names do not exist, so the mask selects 0 beads.
> - **The automated path builds an invalid topology.** `run_maestro.sh:58-62` feeds
>   `cgconv.pl` the packed PDB "skipping pdb2pqr": that file has **0 hydrogens** (SIRAH
>   maps the SER/THR/CYS/TRP side-chain beads from `HG`/`HG1`/`HE1`, so 3 866 beads would
>   be missing) and **0 `TER` records** (the capsid enters with 180, PyMOL centring leaves
>   3, Packmol leaves 0), so tLeaP would chain 181 molecules into one.
>   `grep -c '^TER' archivos_dm_cg/empaquetador/*.pdb` shows 180 / 3 / 0.
> - **Nothing is reproducible.** `ig = -1` in every input and no `mdout`, `leap.log`,
>   `prmtop` or trajectory is committed. The MD figures shown in the Studio ("RMSD 2.8 Å",
>   "SASA 41 893 Å²", "heat1 → 17 666 K") are synthetic curves in
>   `nanocapsule-mvp/src/services/md.py`, not output of this engine.
>
> Only the packing stage has evidence of execution (one run, n = 1 enzyme). Running the MD
> requires AMBER and a GPU. This engine is **not publishable as science**, and until the
> repair plan below is executed it is not an executable protocol either. The correct
> coarse-grained recipe already exists in the repository:
> `sustratinaitor/1_capside/3J7L_cg.pdb` (`pdb2pqr --ff=AMBER` → `cgconv.pl` on the capsid
> alone, with `TER`) is a valid SIRAH conversion, reproducible byte for byte.

## Pipeline

1. **Packing** (`archivos_dm_cg/empaquetador/`). `1calcula_radio_interno.py` computes the
   capsid's internal radius; `2Empaquetador_Manual.py` places a chosen number of enzymes
   inside it (with the radius **hard-coded to 90 Å** at line 14, ignoring
   `radio_interno.txt`), and `2Empaquetador_Maximo.py` packs as many as fit (its acceptance
   regex looks for a line Packmol never writes, the same defect as the Studio's packer).
   Both write a combined capsid-plus-enzymes PDB **without `TER` records** and with
   hexadecimal serials above atom 99 999. This is the one stage with execution evidence:
   one run, 1 enzyme, 2026-03-24, Packmol 20.14.3, "Initial approximation is a solution".
2. **Conversion to coarse-grained.** Two routes exist and neither works on the packed file:
   `run_maestro.sh` calls `cgconv.pl` directly on a PDB with no hydrogens and no `TER`
   (invalid topology, see *Status*); `convert_to_cg.sh` runs `pdb2pqr` first, which aborts
   on Packmol's hexadecimal serials and on the 60 repeated `chain A, residue 41…` blocks.
   The working recipe is to protonate and convert **each component separately** (capsid
   with its 180 `TER`, enzyme with `CYX` for its two disulfides) and pack afterwards.
3. **System building** (`gensystem.leap`). LEaP builds the solvated system. As committed it
   adds **only neutralising NaW** (`addIonsRand protein NaW 0`), not the 0.15 M NaCl its
   comment promises; uses a 12 Å buffer (the SIRAH tutorial and `sustratinaitor` use 20 Å);
   has no `bond` for the enzyme's disulfides; and sets `PBradii mbondi3`, meaningless for
   beads.
4. **MD inputs** (the `.in` files). As committed: minimisation (`em1_WT4`, `em2_WT4`,
   without the restraints the SIRAH protocol applies), six all-atom heating stages
   (`heat1_0to50` … `heat6_250to300`), two all-atom equilibrations (`density_eq`,
   `final_eq`), and three SIRAH stages that are **10 ps stubs** (`eq1_WT4`, `eq2_WT4`,
   `prod_md_WT4`, with `ntr = 0`). `prod-q_gpu.bsub` references a system
   (`capside-3_cg-WAT`) that no committed script generates. The audit's recommendation
   (CIENCIA-3) is to delete the eight all-atom files and use the five stages of SIRAH
   `tutorial/5` with fixed `ig` seeds.
5. **Analysis** (`archivos_dm_cg/analisis/`). cpptraj-based characterisation of the capsid
   and of each enzyme, plus plotting scripts for RMSD, radius of gyration, RMSF and SASA.
   It produces the two-column `(frame, value)` `.dat` files that the Studio's MD ANALYSIS
   tab is designed to read. Known defects: residue masks are built from PDB `resSeq`
   instead of topology indices (the enzyme is never analysed), RMSF is computed without a
   prior `rms` fit, `surf` (LCPO) has no parameters for beads, and the plotting scripts
   hard-code 0.1 ns per frame. None of this has run, because there is no trajectory.

### Orchestration

| Script | Role | Known state |
|--------|------|-------------|
| `configurar_simulacion.sh` | Interactive configurator: regenerates `em1/em2/eq1/eq2/prod` | Its `eq1` restrains the whole system including solvent (`':*&!@H='`: no SIRAH bead starts with H) and uses `gamma_ln = 5`; it does not remove the eight all-atom files, which `run_MD.sh` keeps executing. It is **not** "the correct inputs" as earlier documentation said |
| `setup_universal_md.sh`, `setup_1_1o.sh` | Set up a simulation directory | Reference `gensystem_template.leap` and `run_MD_template.sh`, which **do not exist**; they create empty files and report success |
| `run_maestro.sh` | Full workflow driver | Skips `pdb2pqr`; picks the packed PDB with lexicographic `ls | head -1` (the committed March file, not a new one); calls `analisis/ejecutar_analisis_cpptraj.sh`, which **does not exist** |
| `copy_md_files.sh` | Copy the MD input files into a run directory | — |
| `fix_pdb_serial.py` | Renumber PDB atom serials before LEaP | Shifts every column by one from atom 100 000 (`{atom_serial:5d}` yields 6 characters); no script invokes it |
| `archivos_dm_cg/run_MD.sh` | Runs the 13-stage sequence | Seven stages write to the same default `mdcrd`; "continues with available inputs" when one is missing |

## Requirements

- **AMBER** (`pmemd.cuda` for production, `tleap` for system building), or an equivalent
  engine able to run the `.in` files. A CUDA GPU is the practical bottleneck for production.
- **The SIRAH force field** — not included; it carries its own licence. See
  [`THIRD_PARTY.md`](../THIRD_PARTY.md) and <http://www.sirahff.com/>. A bundled copy of the
  parameter directory layout is referenced as `archivos_dm_cg/sirah_x2.3_24-07.amber`.
- **cpptraj** (ships with AmberTools) for the analysis stage.
- Python 3 with numpy and matplotlib for the plotting scripts.

Nothing in this engine is installed by the Studio's `requirements.lock`: it runs outside the
web application, on whatever cluster or workstation has AMBER and a GPU.

## Usage

```bash
# 1. Pack enzymes inside the capsid (run from archivos_dm_cg/empaquetador/)
python3 1calcula_radio_interno.py
python3 2Empaquetador_Manual.py            # or 2Empaquetador_Maximo.py

# 2. Convert the packed system to coarse-grained SIRAH
./convert_to_cg.sh 1                       # argument: number of enzymes
#    -> as committed, pdb2pqr aborts on the packed PDB (hex serials); see Pipeline step 2

# 3. Configure the simulation (regenerates em1/em2/eq1/eq2/prod only)
./configurar_simulacion.sh

# 4. Build the system and run the staged sequence
./setup_universal_md.sh                    # -> references templates that do not exist
./run_maestro.sh                           # -> skips pdb2pqr; final analysis step calls a missing script

# 5. Analyse the trajectory
cd archivos_dm_cg/analisis
./ejecutar_todo_paralelo_progreso.sh       # cpptraj characterisation, in parallel
./ejecutar_todos_graficos.sh               # RMSD / RMSF / SASA / Rg plots
```

These are the commands the scripts expose; **the sequence does not currently complete**
(see *Orchestration*). The `.dat` files of step 5 are what the Studio's MD ANALYSIS tab is
designed to read; wiring them in is a pending task, not a finished feature.

## Repair plan and open decisions

The consolidated plan is `HOJA_DE_RUTA.md` (branch `claude/consolidate-audit-roadmap-k82rek`),
tasks MD-1 to MD-10, with the literal content of the five corrected `.in` files in
`PLAN_REPARACION_MD.md` (branch `claude/packman-repair-plan-9c287t`). In order: confirm the
defects locally with AmberTools (MD-1); protonate capsid and enzyme separately with
`pdb2pqr --ff=AMBER --ffout=AMBER` (MD-2); pack preserving hydrogens and re-inserting `TER`
(MD-3); `cgconv.pl` on the correct file with automatic CG validation (MD-4); fix
`gensystem.leap` (MD-5); replace the 13 inputs by the five SIRAH stages with fixed seeds
(MD-6); a 1 000-step GPU smoke run (MD-7) **before** any production (MD-8).

Two scientific decisions remain the author's, tracked as `CIENCIA-3` and `CIENCIA-2` in
[`ESTADO.md`](../ESTADO.md) §4b. The audits now give a concrete recommendation for each, and
neither needs an MD run to be decided:

- **Protocol (`CIENCIA-3`).** Recommended: delete `heat1..6`, `density_eq` and `final_eq`
  and adopt the five stages of SIRAH `tutorial/5` (em1 → em2 → eq1 → eq2 → md; SIRAH starts
  `eq1` from 0 K under NPT with Langevin, without a heating ramp), `gamma_ln = 50`, 300 K,
  restraints 2.4 → 0.24 kcal·mol⁻¹·Å⁻² on `@GN,GO`, fixed `ig` per stage, ≥ 100 ns in
  10 ns chunks. `configurar_simulacion.sh` is **not** a drop-in replacement (see
  *Orchestration*).
- **Resolution consistency (`CIENCIA-2`).** Recommended: keep the substrate out of the
  coarse-grained MD; gate 4 runs capsid + enzyme in SIRAH, and substrate physics is done
  all-atom in small systems. See the [`sustratinaitor`](../sustratinaitor) README.

The authoritative statement of what has and has not been executed is `ESTADO.md`. Do not
treat any MD number from this project as validated: none exists.

## Additional documentation

- `diagrama_archivos_dm.md` — file-by-file map of the MD inputs (Spanish). **Describes the
  intended design, not the committed state**: it lists a `ReplicaExtra/` directory that does
  not exist and calls `prod_md_WT4.in` "production" (it is a 10 ps test stub).
- `texto_tesis_archivos_dm.md` — prose description of the protocol, written for a thesis
  chapter (Spanish). Same caveat: it describes equilibration and production stages that
  have never been run and a `ReplicaExtra` hierarchy that is not in the repository.
- `CHANGELOG.md` and `VERSION` — independent versioning of this engine (v1.2.0).

## Contributing and support

Issues and pull requests go to the monorepo:
<https://github.com/najera-maldonado/vlp-studio/issues>. See
[`CONTRIBUTING.md`](../CONTRIBUTING.md). Project boundary: AMBER and the SIRAH force field
are **called**, never forked or rewritten.

## License

Part of VLP Studio, under **GNU AGPLv3 or later**. See [`LICENSE`](../LICENSE) and
[`THIRD_PARTY.md`](../THIRD_PARTY.md). Copyright (C) 2026 najera-maldonado.
