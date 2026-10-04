# VLP Studio (`nanocapsule-mvp`)

The **Studio** is the web front end of [VLP Studio](../README.md): a Flask application with
an integrated 3D viewer (NGL) that drives the enzyme-in-capsid packing engine and the
Pac-Pore analysis engine, and presents the four gates of the design funnel as five tabs.

> **Status (v0.1.0).** The directory name `nanocapsule-mvp` is historical; this is the live
> Studio. Two gates are real and two are illustrative — see *Status per tab*. The Studio is
> a **single-user local research server**: it is not hardened, authenticated or queued for
> multi-user or internet-facing deployment.

## Status per tab

| Tab | What it does | Status |
|-----|--------------|--------|
| **LIBRARY** | Capsid and enzyme catalogue with computed geometry (radius, chains, residues) | Real |
| **STUDIO 3D** | Packmol packing of enzymes inside the capsid, multi-replica, with 3D preview | Real. The "substrate around the capsid" builder and the MD input preparer generate real geometry and real input files but **do not run** the simulation |
| **PAC-PORE** | HOLE pore profile on the symmetry axis, substrate cross-section (RDKit), mutant screening (PyMOL), docking (Vina) and radius/affinity correlation | **Real, end to end** — the most mature part. One exception: the quick radius-versus-axis sketch (`/api/pore/profile`) is an analytic placeholder and says so in its own response; the real measurement is `/api/pore/run_hole` |
| **DE-IMMUNISATION** | Epitope display | **Illustrative**: a static dictionary (`_DEIMMUNO`). No real predictor is wired in. Labelled as illustrative in the interface |
| **MD ANALYSIS** | RMSD/RMSF-style curves | **Illustrative**: synthetic curves. The real engine ([PackMan](../PackMan.v.1.2)) exists, but its MD has never been run, so there are no trajectories to read |

## Architecture

```
nanocapsule-mvp/
├── src/
│   ├── core/                    # Domain layer
│   │   ├── capsid.py            # Capsid handling, internal-radius calculation (PyMOL)
│   │   ├── cargo.py             # Enzyme preparation and centring
│   │   ├── config.py            # Centralised YAML configuration
│   │   ├── experiment_manager.py / experiment_runner.py   # Multi-replica experiments
│   │   └── paths.py             # Single source of truth for paths, incl. the Poromania bridge
│   ├── services/                # One module per gate (the science orchestration)
│   │   ├── packing_service.py   # Facade: re-exports the public service API
│   │   ├── common.py            # Shared helpers and subprocess infrastructure
│   │   ├── library.py           # LIBRARY tab
│   │   ├── packing.py           # STUDIO 3D tab
│   │   ├── pore.py              # PAC-PORE tab (HOLE, screening, docking, cross-section)
│   │   ├── deimmuno.py          # DE-IMMUNISATION tab (illustrative)
│   │   └── md.py                # MD ANALYSIS tab (illustrative) + MD input preparation
│   ├── io/structure_fetcher.py  # Structure library access
│   ├── packing/parallel_packer.py
│   └── web/
│       ├── app.py               # Thin HTTP adapter: routes only, no science
│       ├── templates/studio.html
│       └── static/js/           # One module per tab
├── config/default.yaml          # All tunable parameters
├── Input/{Capsides,Enzimas}/    # Structure library (ships with the repository)
├── Output/                      # Generated structures and experiments
├── scripts/fetch_data.sh        # Downloads the heavy structures that are not in git
└── tests/                       # Smoke tests + scientific golden test
```

The layering is deliberate: `app.py` is a thin HTTP adapter, all orchestration lives in
`services/`, and the domain logic lives in `core/`. Adding a gate means adding a module in
`services/` and re-exporting it from the facade.

**Known architectural overlap:** the Studio reimplemented in Python the pore/screening/
docking logic that also lives in Poromania (`pore_analyzer.py` and the shell scripts). Both
work, but the same science exists in two places and can diverge. Any correction has to be
made deliberately on one side.

## Installation

Full instructions, including how to supply the non-redistributable engines, are in
[`docs/installation.md`](../docs/installation.md). In short:

```bash
# Docker (recommended, reproducible)
docker compose build && docker compose up -d     # http://localhost:5000

# Local
pip install -r requirements.lock
sudo apt-get install packmol pymol openbabel autodock-vina
FLASK_DEBUG=0 python3 src/web/app.py             # http://localhost:5000
```

Verify with `curl http://localhost:5000/api/health`, which reports which engines and Python
dependencies are actually present.

### External engines

The Studio **invokes** these as external processes; it does not redistribute them.

| Engine | Gate / use | Install | Licence | In the Docker image? |
|--------|------------|---------|---------|----------------------|
| Packmol | Packing | `apt install packmol` | free (MIT-like) | Yes |
| PyMOL (open source) | Geometry, mutagenesis | `apt install pymol` | permissive | Yes |
| Open Babel (`obabel`) | Ligand preparation | `apt install openbabel` | GPL-2.0 | Yes |
| AutoDock Vina (`vina`) | Docking | `apt install autodock-vina` | Apache-2.0 | Yes |
| RDKit | SMILES, 3D geometry | pip (in the lock file) | BSD-3-Clause | Yes |
| **HOLE** | Pac-Pore profile | manual (Oxford) | academic, **not redistributable** | No — you supply it |
| **idock** | Alternative docking | manual | check terms | No — you supply it |
| **GROMACS** (`gmx`) | Gate 4 MD | `apt`/manual | LGPL-2.1 | No |

HOLE and idock are not baked into the image because their academic licences do not permit
redistribution. Without HOLE the Pac-Pore gate does not run; without GROMACS and SIRAH gate
4 does not run. The rest of the Studio (packing, Vina docking, cross-sections) works without
them. See [`THIRD_PARTY.md`](../THIRD_PARTY.md).

## Usage

A gate-by-gate walkthrough with concrete commands and payloads is in
[`docs/usage.md`](../docs/usage.md). The short version:

1. Put capsids in `Input/Capsides/<NAME>/capside.pdb` and enzymes in
   `Input/Enzimas/<NAME>/enzima.pdb` (the repository already ships BMV, CCMV, MS2 and QB
   capsids plus four enzymes, including glucocerebrosidase `GCase_1OGS`).
2. Start the server and open <http://localhost:5000>.
3. Pick a capsid and an enzyme in **LIBRARY**, pack them in **STUDIO 3D**, then analyse the
   pore in **PAC-PORE**.

## REST API

All endpoints return JSON unless stated otherwise. Errors return
`{"error": "<message>"}` with status 400, 404 or 500.

### Health and pages

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/` | Studio interface |
| GET | `/classic` | Legacy NGL viewer. **Deprecated**: still functional, no longer linked |
| GET | `/api/health` | `{"status":"ok","engines":{...},"deps":{...}}` — which binaries and Python modules are present |

### Library

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/library/capsides` | Available capsids |
| GET | `/api/library/enzymes` | Available enzymes |
| GET | `/api/library/combinations` | Valid capsid/enzyme pairs |
| GET | `/api/library/detail` | Computed detail (radius, chains, residues) for the catalogue |

### Gate 1 — Pac-Pore

| Method | Endpoint | Body / query | Purpose |
|--------|----------|--------------|---------|
| GET | `/api/pore/config` | — | Pore analysis configuration |
| POST | `/api/pore/profile` | `{"capsid": …, "axis": "3-fold"}` | Quick radius-versus-axis sketch. **Illustrative** (an analytic Gaussian constriction) and flagged as `"illustrative": true` in the response. Use `/api/pore/run_hole` for a real profile |
| GET | `/api/pore/channels` | — | Precomputed channels available from Poromania |
| GET | `/api/pore/channel` | `?id=…` | Channel geometry as plain text (for the viewer) |
| GET | `/api/pore/structures` | — | Structures that HOLE can be run on |
| POST | `/api/pore/run_hole` | `{"structure": "BMV/poronatural"}` | **Runs HOLE for real** on a Poromania model and returns the measured profile (`"illustrative": false`) |
| POST | `/api/pore/screen` | `{"structure": …, "substrate_radius": …}` | Screen pore mutants against a substrate radius |
| POST | `/api/pore/mutant` | `{"structure": …, "mutations": …}` | Build and evaluate one specific mutant |
| POST | `/api/pore/dock` | `{"structure": …, "smiles": …}` | Dock a substrate and correlate affinity with pore radius |
| POST | `/api/pore/section` | `{"smiles": …}` | Minimum cross-section radius of a substrate (RDKit) |

### Gate 2 — packing

| Method | Endpoint | Body | Purpose |
|--------|----------|------|---------|
| POST | `/api/capsid/radius` | `{"capsid": …}` | Internal radius via PyMOL (cached) |
| POST | `/api/experiment/run` | `{"capsid": …, "enzyme": …, "n_replicas": …, "run_packing": false}` | With `run_packing=false` it only confirms parameters; with `true` it runs the multi-replica Packmol experiment and returns best/mean/stdev/median/worst |
| POST | `/api/preview/enzymes` | `{"capsid": …, "enzyme": …, "n_enzymes": 10, "radius": 50.0, "save_file": false}` | Geometry preview without running Packmol. Returns a PDB as **plain text**, not JSON |
| POST | `/api/preview/substrate` | `{"capsid": …, "n": 60, "smiles": …, "save_file": false}` | Substrate shell preview (RDKit). Returns a PDB as **plain text** |

### Gates 3 and 4 (illustrative) and MD preparation

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/deimmuno/data` | Epitope data — **static dictionary, illustrative** |
| GET | `/api/md/examples` | Example MD curves — **synthetic, illustrative** |
| GET | `/api/md/box` | `?capsid=…` — simulation box dimensions for a capsid (real geometry) |
| POST | `/api/md/prepare` | `{"capsid": …, "n_substrate": 40, "smiles": …}` — writes real MD input files; **does not run the simulation** |

### Structures, files and downloads

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/structure/<type>/<name>` | Structure metadata |
| GET | `/api/file/<type>/<name>` | Raw structure file |
| GET | `/api/result/pdb` | Last generated packed structure |
| GET | `/api/files/generated` | List generated files |
| POST | `/api/files/cleanup` | Delete temporary files |
| GET | `/api/download/single/<filename>` | Download one file |
| POST | `/api/download/experiment-zip` | `{"capsid": …, "enzyme": …}` — ZIP of every generated structure for that pair plus the input structures |

## Configuration

Every tunable parameter lives in `config/default.yaml`; nothing scientific is hard-coded in
the routes. The values that matter most:

| Key | Default | Meaning |
|-----|---------|---------|
| `packing.internal_radius_default` | 90.0 Å | Fallback radius when PyMOL cannot compute one |
| `packing.collision_margin` | 2.0 Å | Subtracted from the internal radius before packing |
| `packing.exclusion_radius` | 5.0 Å | Minimum distance between packed enzymes |
| `packing.tolerance` | 2.0 Å | Packmol tolerance |
| `packing.max_violation_threshold` | 0.10 Å | Above this, a replica counts as a collision |
| `engines.packmol.seed_base` | 1234567 | Seed base; replica *n* uses `seed_base + n`, which makes packing reproducible |
| `engines.packmol.timeout` | 300 s | Packmol timeout |
| `experiments.n_replicas` | 10 | Replicas per experiment |
| `web.port` / `web.host` | 5000 / 0.0.0.0 | Flask bind address |

`engines.packmol.use_random_seeds: false` is what keeps experiments reproducible; setting it
to `true` trades reproducibility for independent sampling.

## Testing

```bash
python -m pytest -q
```

22 fast tests: 17 smoke tests (the app boots, every route is wired, service functions return
the expected shape) and 5 golden tests that freeze known numerical results of the substrate
cross-section calculation, so a scientific regression is caught even when nothing crashes.

The suite deliberately **does not** exercise the slow binary engines (HOLE, PyMOL, Vina,
Packmol): it validates wiring and shape, not scientific validity. Both jobs run in CI.

## Reproducibility notes

- `requirements.lock` pins exact versions, including transitive ones; Docker and CI install
  from it. `requirements.txt` holds the human-readable direct dependencies. Regenerate the
  lock with `pip-compile --strip-extras requirements.txt`.
- Packing is geometric and deterministic under a fixed seed base, which makes it the most
  trustworthy numerical output in the project.
- `scripts/fetch_data.sh` downloads the heavy P22 capsid (RCSB 5UU5) that is excluded from
  git, so a fresh clone can be brought to a complete state.

## Known limitations

Recorded honestly rather than hidden; the authoritative list is [`ESTADO.md`](../ESTADO.md).

- Gates 3 and 4 are illustrative in the interface; their real engines are not wired in.
- Gate 4's MD has never been run, so there are no trajectories or analysis data.
- Three open scientific decisions (`CIENCIA-1/2/3` in `ESTADO.md` §4b) are deliberately
  unresolved pending the author's judgement and an MD run: the ±1 Å internal-radius margin,
  the coarse-grained vs all-atom resolution in `sustratinaitor`, and PackMan's heating
  protocol.
- The internal radius is only cached for some capsids; others fall back to 90 Å.
- Single-user server: no authentication, no job queue, no sandboxing of subprocess inputs.

## License

GNU AGPLv3 or later — strong copyleft that also covers use as a network service. See
[`LICENSE`](../LICENSE) and [`THIRD_PARTY.md`](../THIRD_PARTY.md). Copyright (C) 2026
najera-maldonado.
