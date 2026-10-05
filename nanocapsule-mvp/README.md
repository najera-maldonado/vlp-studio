# VLP Studio (`nanocapsule-mvp`)

The **Studio** is the web front end of [VLP Studio](../README.md): a Flask application with
an integrated 3D viewer (NGL) that drives the enzyme-in-capsid packing engine and the
Pac-Pore analysis engine, and presents the four gates of the design funnel as five tabs.

> **Status (v0.1.0).** The directory name `nanocapsule-mvp` is historical; this is the live
> Studio. Two gates have real engines wired in and two are illustrative — see *Status per
> tab*. **The two real engines run, but their headline numbers are not yet validated** (see
> *Audit findings* below). The Studio is a **single-user local research server**: it is not
> hardened, authenticated or queued for multi-user or internet-facing deployment.

## Status per tab

| Tab | What it does | Status |
|-----|--------------|--------|
| **LIBRARY** | Capsid and enzyme catalogue with computed geometry (radius, chains, residues) | Real. Caveat: the cached internal radius (`radio_interno.txt`) is a single global file attributed to BMV by name; computing another capsid's radius overwrites it |
| **STUDIO 3D** | Packmol packing of enzymes inside the capsid, multi-replica, with 3D preview | Engine runs, **capacity still under review**. The acceptance criterion was repaired on 2026-10-05 (reads the real Packmol line, counts the enzyme copies placed, rejects forced output, fixed seeds, geometric check that every enzyme lies inside the capsid; see *Audit findings*). No run with a real Packmol binary has been made since (PK-1), and `best` (maximum over replicas) is still the headline statistic (decision DC-6). The "substrate around the capsid" builder and the MD input preparer generate geometry and input files but **do not run** the simulation |
| **PAC-PORE** | HOLE pore profile on the symmetry axis, substrate cross-section (RDKit), mutant screening (PyMOL), docking (Vina) and radius/affinity correlation | Engine runs end to end with the correct axis on the pentamer (0.00° error). **Not yet validated**: the automatic residue screen yields one residue on `poro5fold` (all five subunits share chain `A`), the axis is ill-conditioned on the trimeric models (~6° error), mutagenesis is not verified after it runs, and failures in the screen are swallowed. The quick sketch `/api/pore/profile` is an analytic placeholder; `_AXIS_MIN` stores values with no committed measurement behind them |
| **DE-IMMUNISATION** | Epitope display | **Illustrative**: a static dictionary (`_DEIMMUNO`). No real predictor is wired in. Labelled as illustrative in the interface |
| **MD ANALYSIS** | RMSD/RMSF-style curves | **Illustrative**: synthetic curves (`math.sin`). Their captions ("RMSD final 2.8 Å", "SASA ~41.893 Å²", "heat1 → 17.666 K · el fallo real", `source: packmanreplicas1/1_2`) are **not measurements**: no `mdout`, trajectory or `.dat` exists in the repository. The real engine ([PackMan](../PackMan.v.1.2)) has never been run |

## Audit findings (2026-10-04) and repairs (2026-10-05)

Two independent audits of the packing engine and one of the pore engine, run with a Packmol
test double and with geometric checks on the committed files, found the following. Each item
is reproducible from the repository at commit `40f4b03`; the full list with evidence is in
[`CORRECCIONES_DOCUMENTACION.md`](../CORRECCIONES_DOCUMENTACION.md) and the repair plan is
[`HOJA_DE_RUTA.md`](../HOJA_DE_RUTA.md). **On 2026-10-05 the packing engine was repaired**
(`REPARACION_PACKING.md`, roadmap tasks PK-2…PK-5); each item says what its state is now.

- **Acceptance criterion never fires.** `src/packing/parallel_packer.py:35,192` searches the
  Packmol log for `Maximum distance violation:`; Packmol writes `Maximum violation of target
  distance:`. Against both real Packmol logs committed in this repository the regex has zero
  matches, so `packing.max_violation_threshold` had no effect. **Fixed:** the parser reads
  `Maximum violation of target distance:` (last value in the log), requires `Success!`, and
  rejects `ENDED WITHOUT PERFECT PACKING` and `<output>_FORCED` even when Packmol exits 0.
- **Fallback is blind to the enzymes.** On no match, `parallel_packer.py:303` accepts any output
  with ≥ 10 000 atom lines. The library capsids have 168 480 to 216 780 atoms. With a Packmol
  double that places zero enzymes, the engine reported 100 enzymes, σ = 0.00, 2/2 replicas.
  **Fixed:** the line-count fallback is gone; the output must contain exactly
  `capsid + N × enzyme` atom lines, and every enzyme centroid must lie inside the packing
  sphere of the output file. The same double now yields `status: failed`.
- **`n_packed` is assumed, not counted**; `best` is a maximum over replicas shown as the
  headline number. **Partly fixed:** placed copies are counted (`n_enzymes_found`),
  `n_replicas_at_best` is reported, σ is `null` with fewer than two accepted replicas, and
  reaching the search ceiling (100) is flagged as a warning. `best` remains the headline
  statistic until the author takes decision DC-6.
- **Seeds were random in production.** `experiment_runner.py:160` called
  `run_parallel_replicas` without `seed_base`; `parallel_packer.py:118` then uses
  `random.randint`. `engines.packmol.seed_base`, `use_random_seeds`, `engines.packmol.timeout`
  and `packing.collision_margin` in `config/default.yaml` were read by no module
  (`timeout=90` and `collision_margin = 2.0` were hard-coded). **Fixed:** all of them, plus
  the new `engines.packmol.max_workers` and `experiments.n_replicas`, are read from the YAML;
  replica *i* uses `seed_base + i` and every seed is recorded.
- **Silent 90 Å fallback.** `capsid.py` returns 90.0 Å when PyMOL is missing, when the search
  loop exhausts at 199 Å (P22 would hit this) or on any exception, and `/api/capsid/radius`
  labels it "calculado". For BMV the true value rounds to the same 90, so no committed result
  shows whether PyMOL ever ran. **Partly fixed:** `Capsid.radius_source` records
  `"calculated"` or `"default"` and `ExperimentRunner` refuses to run an experiment on the
  default value (pass `internal_radius` explicitly instead); `/api/capsid/radius` itself
  still returns 90.0 labelled as computed (remainder of PK-3).
- **Delivered PDB loses structure.** Centring with PyMOL collapses the capsid's 180 `TER`
  records to 3; Packmol writes 0 and emits hexadecimal serials above atom 99 999. The output is
  not consumable by tLeaP (gate 4) without repair. **Partly fixed:** centring is now pure
  Python, keeps the 180 `TER` and writes into the experiment directory instead of `Input/`;
  Packmol still writes 0 `TER` and hexadecimal serials (roadmap task T1).
- **No test covered this engine.** `tests/test_golden_science.py` tests `substrate_section`
  (gate 1); coverage of `capsid.py`, `parallel_packer.py`, `experiment_runner.py` and
  `experiment_manager.py` was zero, and the 22 tests passed with all of the above present.
  **Fixed:** 39 engine and runner tests with a Packmol double
  (`tests/test_packing_engine.py`, `tests/test_experiment_runner.py`; 28 of them fail against
  the old code) run in CI. There is still no golden test of the radius (PK-6).
- **Only one real Packmol run of capsid + enzyme exists** in the repository
  (`PackMan.v.1.2/.../log_packmol_1enzimas_20260324_212620.txt`, n = 1, "Initial approximation
  is a solution. Nothing to do."). There is no committed multi-replica result and no committed
  evidence for a "6 enzymes" capacity. **Still true after the repair:** the repaired criterion
  has not been exercised against a real Packmol binary (PK-1; `pytest -m engine` does it
  where Packmol is installed).

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
| POST | `/api/capsid/radius` | `{"capsid": …}` | Internal radius via PyMOL (cached). **Caveat:** returns 90.0 Å labelled as computed when PyMOL is absent, when the search exhausts, or on any error (audit P-11) |
| POST | `/api/experiment/run` | `{"capsid": …, "enzyme": …, "n_replicas": …, "run_packing": false, "internal_radius": null}` | With `run_packing=false` it only confirms parameters; with `true` it runs the multi-replica Packmol experiment and returns best/mean/stdev/median/worst plus `seeds`, `warnings`, `rejection_reasons`, `n_replicas_at_best` and `radius_source`. An experiment with no accepted replica returns `status: "failed"` and `error`. `internal_radius` bypasses PyMOL explicitly (the UI does not send it). **Caveat:** `best_result` is a maximum over replicas (DC-6) and the repaired criterion has not been validated against a real Packmol run (PK-1) |
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

The tunable parameters live in `config/default.yaml`. The audit of 2026-10-04 found that
five of them were not read by the code; the repair of 2026-10-05 (PK-4) made
`ExperimentRunner.packing_parameters()` the single point of reading. The "Effective" column
says what happens today:

| Key | Default | Meaning | Effective today |
|-----|---------|---------|-----------------|
| `packing.internal_radius_default` | 90.0 Å | Fallback radius when PyMOL cannot compute one | Still returned by `/api/capsid/radius` labelled as computed (P-11), but `ExperimentRunner` **refuses** to pack on it: pass `internal_radius` explicitly |
| `packing.collision_margin` | 2.0 Å | Subtracted from the internal radius before packing | Read; the effective sphere is stored as `run_config.packing_radius` |
| `packing.exclusion_radius` | 5.0 Å | Per-atom `radius` of the enzyme in the Packmol input (Packmol enforces the *sum* of radii: 10 Å between enzymes, 6 Å enzyme–capsid) | Read. The capacity depends strongly on this knob; its value is an open scientific decision (P-13, DC-B in `REPARACION_PACKING.md`) |
| `packing.tolerance` | 2.0 Å | Packmol tolerance | Read |
| `packing.max_violation_threshold` | 0.10 Å | A run whose last `Maximum violation of target distance:` exceeds this is rejected | Read and applied. Whether 0.10 Å is the right threshold is the author's (DC-D) |
| `packing.min_lines_threshold` | (removed) | Old "≥ 10 000 lines" fallback | **Removed**: the capsid alone satisfied it |
| `engines.packmol.seed_base` | 1234567 | Replica *i* uses `seed_base + i`; retry *k* adds `1000·k` | Read; seeds recorded in `metadata.json` and `report.txt` |
| `engines.packmol.use_random_seeds` | false | `true` draws recorded random seeds instead | Read |
| `engines.packmol.timeout` | 300 s | Packmol timeout per run | Read; a timeout is recorded as rejection cause `timeout`, no longer counted as "does not fit" |
| `engines.packmol.max_workers` | null | Simultaneous Packmol processes (null = min(cores, 7)) | Read; more workers with a fixed timeout can turn "fits" into "timeout" |
| `experiments.n_replicas` | 10 | Replicas per experiment | Read (the old hard-coded 7 is gone) |
| `web.port` / `web.host` | 5000 / 0.0.0.0 | Flask bind address | Read |

The effective parameters of every run (`run_config`) are written to `summary/statistics.json`
and printed in `report.txt`.

## Testing

```bash
python -m pytest -q
```

60 fast tests plus one that is skipped unless a real Packmol is installed: 17 smoke tests
(the app boots, every route is wired, service functions return the expected shape), 5 golden
tests that freeze known numerical results of the substrate cross-section calculation
(`substrate_section`, gate 1), and 39 tests of the packing engine and runner
(`tests/test_packing_engine.py`, `tests/test_experiment_runner.py`) that run the real Python
code against a Packmol double (`tests/packmol_double.py`) emitting the strings of the two real
Packmol logs committed as fixtures: acceptance criterion, `_FORCED`/exit-code combinations,
enzyme counting, centring with `TER` preserved, seeds, timeouts and statistics.

What the suite does **not** cover, stated plainly: no test runs a real Packmol or PyMOL in CI
(`pytest -m engine` checks the installed Packmol's log vocabulary where it exists); there is no
golden test of the internal radius (PK-6); and the gate 1 golden value is the semi-axis of
atomic *centres* without van der Waals radii, which underestimates the physical cross-section
by a factor of about 1.8 to 2.2 (audit G-03). The suite deliberately does not exercise the
slow binary engines (HOLE, PyMOL, Vina, Packmol): it validates the Python side, not the
binaries. Both jobs run in CI.

## Reproducibility notes

- `requirements.lock` pins exact versions, including transitive ones; Docker and CI install
  from it. `requirements.txt` holds the human-readable direct dependencies. Regenerate the
  lock with `pip-compile --strip-extras requirements.txt`.
- Packing seeds are fixed by default since 2026-10-05 (`seed_base + replica`, see
  *Configuration*), so two invocations with the same configuration send Packmol the same
  input. Two caveats: a Packmol timeout on a slower machine is recorded as a rejection, so the
  accepted set can still differ between machines; and reproducibility has been verified only
  with the test double, not yet with a real Packmol binary (PK-1).
- `scripts/fetch_data.sh` downloads the heavy P22 capsid (RCSB 5UU5) that is excluded from
  git, so a fresh clone can be brought to a complete state.

## Known limitations

Recorded honestly rather than hidden; the authoritative list is [`ESTADO.md`](../ESTADO.md)
and the audit items above.

- Gates 3 and 4 are illustrative in the interface; their real engines are not wired in.
- Gate 4's MD has never been run, so there are no trajectories or analysis data. The MD tab's
  numeric captions are synthetic anchors, not results.
- The packing capacity number is not validated. The acceptance criterion, counting, seeds
  and statistics were repaired on 2026-10-05 (see *Audit findings*), but no experiment has
  been run with a real Packmol since, `best` is still the headline statistic (DC-6) and the
  internal-radius definition is still open (CIENCIA-1). Geometric bounds put GCase in BMV
  between ~6 and ~20 copies.
- The pore screen does not work on the pentamer model (`poro5fold`) and the pore axis is
  ill-conditioned on the trimer models; neither case raises an error.
- Two open scientific decisions (`CIENCIA-1` and `CIENCIA-2` in `ESTADO.md` §4b) remain the
  author's to take. The audits recommend: subtract the 1 Å margin, or better, redefine the
  radius as `d_min − r_vdW` (CIENCIA-1); take the substrate out of the coarse-grained MD
  (CIENCIA-2). `CIENCIA-3` (PackMan's protocol) was closed on 2026-10-05 by adopting the
  five-stage SIRAH tutorial protocol. Further packing-specific decisions (exclusion radius,
  headline statistic, violation threshold) are listed in `REPARACION_PACKING.md` §3.
- The internal radius is only cached for one capsid, in a single global file; others fall
  back to 90 Å without telling the caller.
- Experiments are written to `Output/<capsid>/<enzyme>` without a timestamp and overwrite
  each other. (Centring no longer writes into the versioned `Input/` tree; three enzyme
  inputs were overwritten in place before the repair and `GCase_1OGS` has no `.original`
  backup, audit P-17.)
- Single-user server: no authentication, no job queue, no sandboxing of subprocess inputs.

## License

GNU AGPLv3 or later — strong copyleft that also covers use as a network service. See
[`LICENSE`](../LICENSE) and [`THIRD_PARTY.md`](../THIRD_PARTY.md). Copyright (C) 2026
najera-maldonado.
