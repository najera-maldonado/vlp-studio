# PackMan v1.2 — coarse-grained molecular dynamics

Engine of **gate 4 ("does it survive?")** of [VLP Studio](../README.md). PackMan prepares an
enzyme-inside-capsid system for **coarse-grained molecular dynamics with the SIRAH force
field** and defines the complete MD protocol: packing, conversion to coarse-grained
resolution, system building with LEaP, then minimisation, heating, equilibration and
production.

> **Status: the scripts and the protocol are complete; the MD itself has never been run.**
> There are no trajectories and no analysis `.dat` files in the repository. Only the packing
> stage has evidence of execution. Running it requires AMBER and the SIRAH force field,
> neither of which is included. This engine is publishable as *software*; it is **not yet
> publishable as science**, because the simulation it describes has not been executed or
> validated. The MD ANALYSIS tab in the Studio therefore shows illustrative curves, not
> results from this engine.

## Pipeline

1. **Packing** (`archivos_dm_cg/empaquetador/`). `1calcula_radio_interno.py` computes the
   capsid's internal radius; `2Empaquetador_Manual.py` places a chosen number of enzymes
   inside it, and `2Empaquetador_Maximo.py` packs as many as fit. Both write a combined
   capsid-plus-enzymes PDB. This is the one stage with execution evidence.
2. **Conversion to coarse-grained** (`convert_to_cg.sh`). Maps the all-atom system onto
   SIRAH coarse-grained beads. Usage: `./convert_to_cg.sh N_ENZYMES`.
3. **System building** (`gensystem.leap`). LEaP builds the solvated, ionised system and
   writes the topology and coordinate files.
4. **MD protocol** (the `.in` files). Minimisation (`em1_WT4`, `em2_WT4`), gradual heating
   in six stages (`heat1_0to50` through `heat6_250to300`), equilibration (`eq1_WT4`,
   `eq2_WT4`, `density_eq`, `final_eq`) and production (`prod_md_WT4`). Intended to run on
   `pmemd.cuda`; `prod-q_gpu.bsub` is an example GPU batch submission script.
5. **Analysis** (`archivos_dm_cg/analisis/`). cpptraj-based characterisation of the capsid
   and of each enzyme, plus plotting scripts for RMSD, radius of gyration, RMSF and SASA,
   and a cross-comparison of different enzymes in the same capsid. This subsystem produces
   exactly the two-column `(frame, value)` `.dat` files that the Studio's MD ANALYSIS tab
   knows how to read, which is how the real engine will replace the illustrative curves.

### Orchestration

| Script | Role |
|--------|------|
| `configurar_simulacion.sh` | Interactive configurator: generates the run's `.in` files |
| `setup_universal_md.sh`, `setup_1_1o.sh` | Set up a simulation directory |
| `run_maestro.sh` | Full workflow driver |
| `copy_md_files.sh` | Copy the MD input files into a run directory |
| `fix_pdb_serial.py` | Fix PDB atom serial numbering before LEaP |
| `archivos_dm_cg/run_MD.sh` | Runs the staged MD protocol |

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

# 3. Configure the simulation (generates the .in files for this system)
./configurar_simulacion.sh

# 4. Build the system and run the staged protocol
./setup_universal_md.sh
./run_maestro.sh                           # minimisation -> heating -> equilibration -> production

# 5. Analyse the trajectory
cd archivos_dm_cg/analisis
./ejecutar_todo_paralelo_progreso.sh       # cpptraj characterisation, in parallel
./ejecutar_todos_graficos.sh               # RMSD / RMSF / SASA / Rg plots
```

The `.dat` files produced in step 5 are what the Studio's MD ANALYSIS tab is designed to
read; wiring them in is a pending task, not a finished feature.

## Reproducibility notes and open decisions

Two things must be settled before any production run is trustworthy. Both are deliberately
left to the author's scientific judgement rather than patched; they are tracked as
`CIENCIA-3` and `CIENCIA-2` in [`ESTADO.md`](../ESTADO.md) §4b.

- **Heating protocol (`CIENCIA-3`).** The static `heat*.in` files are written for all-atom
  dynamics (`dt = 0.002` ps, SHAKE, mask `@CA,C,N,O`) but would be applied to a coarse-grained
  SIRAH topology, which needs a different timestep and bead masks (`dt = 0.020` ps,
  `@GN,GO`). `configurar_simulacion.sh` already generates correct coarse-grained inputs. The
  decision is which protocol to adopt, after which the static files should be retired.
- **Resolution consistency (`CIENCIA-2`).** The related [`sustratinaitor`](../sustratinaitor)
  stage currently mixes coarse-grained and all-atom components. Any system that combines
  both engines must resolve that first.

The authoritative statement of what has and has not been executed is `ESTADO.md`. Do not
treat any MD number from this project as validated until the simulation has actually been
run and checked.

## Additional documentation

- `diagrama_archivos_dm.md` — detailed file-by-file map of the MD inputs (Spanish).
- `texto_tesis_archivos_dm.md` — prose description of the protocol, written for a thesis
  chapter (Spanish).
- `CHANGELOG.md` and `VERSION` — independent versioning of this engine (v1.2.0).

## Contributing and support

Issues and pull requests go to the monorepo:
<https://github.com/najera-maldonado/vlp-studio/issues>. See
[`CONTRIBUTING.md`](../CONTRIBUTING.md). Project boundary: AMBER and the SIRAH force field
are **called**, never forked or rewritten.

## License

Part of VLP Studio, under **GNU AGPLv3 or later**. See [`LICENSE`](../LICENSE) and
[`THIRD_PARTY.md`](../THIRD_PARTY.md). Copyright (C) 2026 najera-maldonado.
