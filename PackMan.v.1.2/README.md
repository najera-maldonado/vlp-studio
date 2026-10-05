# PackMan v1.3 — coarse-grained molecular dynamics

Engine of **gate 4 ("does it survive?")** of [VLP Studio](../README.md). PackMan prepares an
enzyme-inside-capsid system for **coarse-grained molecular dynamics with the SIRAH force
field**: packing, conversion to coarse-grained resolution, system building with LEaP, then
minimisation, equilibration and production.

> **Status (2026-10-05, v1.3.0): the MD has never been run.** No `mdout`, `leap.log`,
> `prmtop` or trajectory is committed, and the MD figures shown in the Studio ("RMSD 2.8 Å",
> "SASA 41 893 Å²", "heat1 → 17 666 K") are synthetic curves in
> `nanocapsule-mvp/src/services/md.py`, not output of this engine. **No 15 ns or 35 ns
> simulation has ever existed**: the inputs committed before v1.3.0 carried those titles over
> `nstlim = 500` stubs (10 ps each, ≈ 240 ps for the whole 13-file sequence; see
> `AUDITORIA_MD.md`, MD-01).
>
> What v1.3.0 repaired (closes the author's decision `CIENCIA-3`; audit items MD-01, MD-04,
> MD-05, MD-06, MD-08…MD-11, MD-14, MD-18):
>
> - The eight all-atom inputs (`heat1..6`, `density_eq`, `final_eq`: `dt = 0.002`, SHAKE,
>   `cut = 9`, `gamma_ln = 2`, restraint mask `@CA,C,N,O` that selects 0 SIRAH beads) are
>   **deleted**. SIRAH has no heating ramp for proteins: `eq1` starts from 0 K under Langevin.
> - The five remaining inputs are copied line by line from `sirah_x2.3_24-07.amber/tutorial/5`
>   with real durations (`eq1` 5 ns, `eq2` 25 ns, production 10 ns per chunk) and titles that
>   state exactly what they simulate. Positional restraints follow the reference (`em1` 2.4 on
>   `@GN,GO`; `eq1` 2.4 on the whole solute; `eq2` 0.24 on `@GN,GO`); before, `ntr = 0`.
> - `configurar_simulacion.sh` is **removed**: its `eq1` restrained the solvent too
>   (`':*&!@H='`), used `gamma_ln = 5` and left the all-atom files for `run_MD.sh` to execute.
>   The five static `.in` files are the only source of truth.
> - `run_MD.sh` is rewritten as a resumable five-stage driver with fixed seeds per stage
>   (`SEMILLAS.txt`) and a `DRY_RUN=1` mode; `prod-q_gpu.bsub` launches it instead of a bare
>   `pmemd.cuda` on a system no script generated.
> - `verificar_protocolo_md.py` (stdlib only, no AMBER) compares every `.in` parameter by
>   parameter with its SIRAH reference and fails on any undeclared deviation; it **runs in CI**.
>
> What is still broken as committed (audit of 2026-10-04, `AUDITORIA_MD.md`; tasks MD-1…MD-5,
> MD-7, MD-8 in `HOJA_DE_RUTA.md`): the **system preparation**. The automated path
> (`run_maestro.sh`) feeds `cgconv.pl` a packed PDB with **0 hydrogens** (SIRAH maps the
> SER/THR/CYS/TRP side-chain beads from `HG`/`HG1`/`HE1`, so ≈ 3 866 beads would be missing)
> and **0 `TER` records** (the capsid enters with 180; packing leaves 0), so tLeaP would chain
> 181 molecules into one; `convert_to_cg.sh` runs `pdb2pqr` first but aborts on Packmol's
> hexadecimal serials; `gensystem.leap` adds only neutralising ions, has no disulfide bonds and
> a 12 Å buffer. **The repaired protocol therefore has no valid topology to run on yet.** The
> correct coarse-grained recipe already exists in the repository:
> `sustratinaitor/1_capside/3J7L_cg.pdb` (`pdb2pqr --ff=AMBER` → `cgconv.pl` on the capsid
> alone, with `TER`) is a valid SIRAH conversion, reproducible byte for byte.
>
> Only the packing stage has evidence of execution (one run, n = 1 enzyme). Running the MD
> requires AMBER and a GPU. This engine is **not publishable as science**.

## Pipeline

1. **Packing** (`archivos_dm_cg/empaquetador/`). `1calcula_radio_interno.py` computes the
   capsid's internal radius; `2Empaquetador_Manual.py` places a chosen number of enzymes
   inside it (with the radius **hard-coded to 90 Å** at line 14, ignoring
   `radio_interno.txt`), and `2Empaquetador_Maximo.py` packs as many as fit (its acceptance
   regex looks for a line Packmol never writes, the defect the Studio's packer had until its
   own repair of 2026-10-05). Both write a combined capsid-plus-enzymes PDB **without `TER`
   records** and with hexadecimal serials above atom 99 999. This is the one stage with
   execution evidence: one run, 1 enzyme, 2026-03-24, Packmol 20.14.3, "Initial approximation
   is a solution".
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
4. **MD protocol** (five `.in` files, pattern `sirah_x2.3_24-07.amber/tutorial/5`):

   | Stage | File | Simulates | Positional restraint |
   |---|---|---|---|
   | Minimisation 1 | `em1_WT4.in` | 5 000 cycles | 2.4 kcal·mol⁻¹·Å⁻² on `@GN,GO` |
   | Minimisation 2 | `em2_WT4.in` | 5 000 cycles | none |
   | Equilibration 1 (NPT, 0 → 300 K) | `eq1_WT4.in` | 5 ns | 2.4 on the whole solute (`!:WT4,NaW,ClW`) |
   | Equilibration 2 (NPT) | `eq2_WT4.in` | 25 ns | 0.24 on `@GN,GO` |
   | Production (NPT) | `prod_md_WT4.in` | 10 ns per chunk; `run_MD.sh` chains `NCHUNKS` (10 → 100 ns) | none |

   All stages: `dt = 20 fs`, `cut = 12 Å`, no SHAKE, Langevin `gamma_ln = 50`, 300 K,
   `chngmask = 0`, `skinnb = 5`. There is no heating stage: SIRAH starts `eq1` from 0 K
   under Langevin, as in the official tutorial. Declared deviations from the reference
   (fixed `ig` seeds, `skinnb`, the enzyme-count-independent `eq1` mask, 10 ns production
   chunks) are listed in `verificar_protocolo_md.py`; changing a `.in` means changing that
   list in the same commit.
5. **Analysis** (`archivos_dm_cg/analisis/`). cpptraj-based characterisation of the capsid
   and of each enzyme, plus plotting scripts for RMSD, radius of gyration, RMSF and SASA.
   It produces the two-column `(frame, value)` `.dat` files that the Studio's MD ANALYSIS
   tab is designed to read. Known defects (MD-9): residue masks are built from PDB `resSeq`
   instead of topology indices (the enzyme is never analysed), RMSF is computed without a
   prior `rms` fit, `surf` (LCPO) has no parameters for beads, and the plotting scripts
   hard-code 0.1 ns per frame. None of this has run, because there is no trajectory.

### Orchestration

| Script | Role | Known state |
|--------|------|-------------|
| `archivos_dm_cg/run_MD.sh` | Runs the five SIRAH stages (`em1 → em2 → eq1 → eq2 → prod` in chunks) | Rewritten in v1.3.0: resumable, `eq1` restarts from `em2`, one `ig` per stage written to `SEMILLAS.txt`, `DRY_RUN=1` prints the command chain without AMBER (CI checks it) |
| `verificar_protocolo_md.py` | Static check of the five `.in` files against SIRAH `tutorial/5` | New in v1.3.0; runs in CI (`engines` job) |
| `archivos_dm_cg/prod-q_gpu.bsub` | LSF launcher | Now launches `run_MD.sh`; resubmitting after a queue cut resumes from the pending stage |
| `setup_universal_md.sh`, `setup_1_1o.sh` | Set up a simulation directory | Reference `gensystem_template.leap` and `run_MD_template.sh`, which **do not exist**; they create empty files and report success |
| `run_maestro.sh` | Full workflow driver | Skips `pdb2pqr`; picks the packed PDB with lexicographic `ls \| head -1` (the committed March file, not a new one); calls `analisis/ejecutar_analisis_cpptraj.sh`, which **does not exist** |
| `copy_md_files.sh` | Copy the MD input files into a run directory | Copies the five `.in` files |
| `fix_pdb_serial.py` | Renumber PDB atom serials before LEaP | Shifts every column by one from atom 100 000 (`{atom_serial:5d}` yields 6 characters); no script invokes it |
| `configurar_simulacion.sh` | (removed in v1.3.0) | Generated an `eq1` that restrained the solvent and did not remove the all-atom inputs |

## Requirements

- **AMBER** (`pmemd.cuda` for production, `tleap` for system building), or an equivalent
  engine able to run the `.in` files. A CUDA GPU is the practical bottleneck for production.
- **The SIRAH force field** — it carries its own licence. See
  [`THIRD_PARTY.md`](../THIRD_PARTY.md) and <http://www.sirahff.com/>. The repository
  currently versions a copy of the SIRAH 2.3 distribution under
  `archivos_dm_cg/sirah_x2.3_24-07.amber` (decision DC-5 in `HOJA_DE_RUTA.md` is open:
  keep and declare it, or remove it and download it in `fetch_data.sh`).
- **cpptraj** (ships with AmberTools) for the analysis stage.
- Python 3 with numpy and matplotlib for the plotting scripts.

Nothing in this engine is installed by the Studio's `requirements.lock`: it runs outside the
web application, on whatever cluster or workstation has AMBER and a GPU.

## Usage

```bash
# 0. Check that the committed protocol still matches the SIRAH reference (no AMBER needed)
python3 verificar_protocolo_md.py -v

# 1. Pack enzymes inside the capsid (run from archivos_dm_cg/empaquetador/)
python3 1calcula_radio_interno.py
python3 2Empaquetador_Manual.py            # or 2Empaquetador_Maximo.py

# 2. Convert the packed system to coarse-grained SIRAH
./convert_to_cg.sh 1                       # argument: number of enzymes
#    -> as committed, pdb2pqr aborts on the packed PDB (hex serials); see Pipeline step 2

# 3. Build the system (gensystem.leap) and run the five stages
cd archivos_dm_cg
DRY_RUN=1 bash run_MD.sh                   # prints the pmemd command chain, runs nothing
NCHUNKS=10 bash run_MD.sh cuda             # em1 -> em2 -> eq1 (5 ns) -> eq2 (25 ns) -> 10 x 10 ns
#    or on an LSF cluster: bsub < prod-q_gpu.bsub

# 4. Analyse the trajectory
cd analisis
./ejecutar_todo_paralelo_progreso.sh       # cpptraj characterisation, in parallel
./ejecutar_todos_graficos.sh               # RMSD / RMSF / SASA / Rg plots
```

Step 3 is now a coherent protocol; **steps 1–2 do not yet produce a valid topology for it**
(see *Status*). The `.dat` files of step 4 are what the Studio's MD ANALYSIS tab is designed
to read; wiring them in is a pending task, not a finished feature.

## Reproducibility notes

- Seeds are fixed per stage: `ig = 100001` (`eq1`), `100002` (`eq2`), `100100 + k` for
  production chunk `k`. `run_MD.sh` records them in `SEMILLAS.txt`.
- Production length is set with `NCHUNKS` (10 ns chunks; 10 by default → 100 ns).
- `verificar_protocolo_md.py` fails if any `.in` diverges from the SIRAH reference outside
  its declared deviation list, if a title disagrees with `nstlim · dt`, if an all-atom marker
  reappears, or if `run_MD.sh` (in `DRY_RUN`) breaks the `-c`/`-ref` chain.

## Repair plan and open decisions

The consolidated plan is `HOJA_DE_RUTA.md`, tasks MD-1 to MD-10, with the diagnosis in
`AUDITORIA_MD.md` and the step-by-step plan in `PLAN_REPARACION_MD.md`. Done: **MD-6** (the
five SIRAH inputs, fixed seeds, driver, static verifier — this release). Still to do, in
order: confirm the preparation defects locally with AmberTools (MD-1); protonate capsid and
enzyme separately with `pdb2pqr --ff=AMBER --ffout=AMBER` (MD-2); pack preserving hydrogens
and re-inserting `TER` (MD-3); `cgconv.pl` on the correct file with automatic CG validation
(MD-4); fix `gensystem.leap` (MD-5); a 1 000-step GPU smoke run (MD-7) **before** any
production (MD-8); repair the analysis masks (MD-9); remove the synthetic MD curves from the
Studio (MD-10).

Scientific decisions, tracked in [`ESTADO.md`](../ESTADO.md) §4b:

- **Protocol (`CIENCIA-3`) — closed** by v1.3.0 following the audits' recommendation: no
  heating ramp, the five stages of SIRAH `tutorial/5`, `gamma_ln = 50`, 300 K, restraints
  2.4 → 0.24 kcal·mol⁻¹·Å⁻² on `@GN,GO`, fixed `ig` per stage, ≥ 100 ns in 10 ns chunks.
- **Resolution consistency (`CIENCIA-2`) — open**, the author's. Recommended: keep the
  substrate out of the coarse-grained MD; gate 4 runs capsid + enzyme in SIRAH, and substrate
  physics is done all-atom in small systems. See the [`sustratinaitor`](../sustratinaitor)
  README.

The authoritative statement of what has and has not been executed is `ESTADO.md`. Do not
treat any MD number from this project as validated: none exists.

## Additional documentation

- `CHANGELOG.md` / `VERSION` — engine versioning (v1.3.0).
- `diagrama_archivos_dm.md` — file layout of the engine (updated for the five-stage protocol).
- `texto_tesis_archivos_dm.md` — prose description from the thesis (historical; carries a
  banner about what was never run).

## Contributing and support

Issues and pull requests go to the monorepo:
<https://github.com/najera-maldonado/vlp-studio/issues>. See
[`CONTRIBUTING.md`](../CONTRIBUTING.md). Project boundary: AMBER and the SIRAH force field
are **called**, never forked or rewritten.

## License

Part of VLP Studio, under **GNU AGPLv3 or later**. See [`LICENSE`](../LICENSE) and
[`THIRD_PARTY.md`](../THIRD_PARTY.md). Copyright (C) 2026 najera-maldonado.
