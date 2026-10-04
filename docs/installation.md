# Installation

VLP Studio is a Linux-oriented research application. Two installation routes are supported:
**Docker**, which is reproducible and recommended, and a **local install** with pip plus
system packages, which is what you want if you already have the scientific engines on the
machine or you intend to develop the code.

Whichever route you choose, the end state is the same: a Flask server on
<http://localhost:5000> whose `/api/health` endpoint reports exactly which engines are
present, so you always know which gates of the funnel will work.

## Contents

- [Requirements](#requirements)
- [Route A — Docker](#route-a--docker-recommended)
- [Route B — local install](#route-b--local-install)
- [External engines](#external-engines)
- [Optional data download](#optional-data-download)
- [Verifying the installation](#verifying-the-installation)
- [The other three engines](#the-other-three-engines)
- [Troubleshooting](#troubleshooting)
- [Uninstalling](#uninstalling)

## Requirements

| | Minimum | Recommended |
|---|---|---|
| Operating system | Linux (Debian/Ubuntu family tested) or macOS | Linux |
| Python | 3.12 (required by `rdkit==2025.9.1`) | 3.12 |
| RAM | 8 GB | 16 GB or more for whole-capsid structures |
| Disk | 5 GB free | 20 GB if you run multi-replica experiments |
| GPU | not needed for the Studio | CUDA GPU required for gate 4 MD (PackMan) |

The Studio itself needs no GPU. Gate 4's molecular dynamics does, but that runs outside the
web application.

## Route A — Docker (recommended)

This is the reproducible route: the image installs Python dependencies from
`requirements.lock`, so the environment is pinned down to transitive dependencies.

```bash
git clone https://github.com/najera-maldonado/vlp-studio.git
cd vlp-studio/nanocapsule-mvp
docker compose build
docker compose up -d
```

The Studio is then at <http://localhost:5000>. Check it came up healthy:

```bash
docker compose ps                        # STATUS should become "healthy"
curl http://localhost:5000/api/health
```

The image is built on `python:3.12-slim` and installs, from Debian packages, the four
redistributable engines plus the runtime libraries that PyMOL and RDKit need when running
headless (`libgl1`, `libxrender1`, `libgomp1`):

| Engine in the image | Used for |
|---------------------|----------|
| Packmol | Packing enzymes inside the capsid (gate 2) |
| PyMOL (open source) | Internal radius, mutant construction |
| Open Babel (`obabel`) | Receptor and ligand preparation |
| AutoDock Vina (`vina`) | Docking (gate 1) |
| RDKit (pip) | SMILES handling, 3D geometry, substrate cross-section |

**HOLE and idock are deliberately not in the image.** Their academic licences do not permit
redistribution, so baking them into a public image would violate their terms. `/api/health`
will report them as absent, and the Pac-Pore gate will not run until you supply them — see
[External engines](#external-engines).

A second known limitation of the Docker route: the build context is only `nanocapsule-mvp/`,
so the Poromania models in the sibling directory are outside the image. If you want Pac-Pore
inside the container you must mount them.

### Mounting the engines and models you supply

Add volumes to `docker-compose.yml` under the existing `volumes:` key:

```yaml
    volumes:
      - ./Input:/app/Input
      - ./Output:/app/Output
      - ./config:/app/config
      # Engines you obtained yourself, under their own licence:
      - /path/to/your/hole:/usr/local/bin/hole:ro
      - /path/to/your/idock:/usr/local/bin/idock:ro
      - /path/to/your/gmx:/usr/local/bin/gmx:ro
      # Poromania models, so Pac-Pore can read them from inside the container:
      - ../Poromania.v.1.2.:/Poromania.v.1.2.:ro
```

Then `docker compose up -d --force-recreate` and re-check `/api/health`.

### Everyday Docker commands

```bash
docker compose logs -f        # follow the server log
docker compose restart        # restart after changing config/default.yaml
docker compose down           # stop and remove the container
```

`Input/`, `Output/` and `config/` are bind-mounted, so your structures, results and
configuration survive container rebuilds.

## Route B — local install

### 1. Clone and create a virtual environment

```bash
git clone https://github.com/najera-maldonado/vlp-studio.git
cd vlp-studio/nanocapsule-mvp
python3.12 -m venv .venv
source .venv/bin/activate
```

### 2. Install the Python dependencies

For an exact, reproducible environment, install from the lock file:

```bash
pip install --upgrade pip
pip install -r requirements.lock
```

`requirements.lock` is generated with `pip-compile` and pins every version, including
transitive dependencies. It is what Docker and CI both use, so installing from it gives you
the same environment they run.

`requirements.txt` holds the human-readable direct dependencies (Flask, Werkzeug, PyYAML,
numpy, RDKit, pytest). Use it only if you intend to change dependencies; after editing it,
regenerate the lock:

```bash
pip install pip-tools
pip-compile --strip-extras requirements.txt      # rewrites requirements.lock
```

### 3. Install the system engines

On Debian or Ubuntu:

```bash
sudo apt-get update
sudo apt-get install packmol pymol openbabel autodock-vina
```

On macOS with Homebrew, `packmol` and `open-babel` are available; PyMOL is easiest through
conda (`conda install -c conda-forge pymol-open-source`). AutoDock Vina may need to be
installed from its own release.

These four are the redistributable engines. HOLE, idock, GROMACS and SIRAH are separate; see
below.

### 4. Start the server

```bash
FLASK_DEBUG=0 python3 src/web/app.py
```

The Studio is at <http://localhost:5000>. `FLASK_DEBUG=0` is the production default and is
what you want: debug mode exposes an interactive console, and this server has no
authentication.

To change the port or bind address, edit the `web:` section of `config/default.yaml` rather
than the code.

## External engines

These are **not** installed by either route, because their licences do not allow
redistribution or they are outside the scope of the web application. The Studio invokes them
as external processes; it never incorporates them. Full licence details are in
[`THIRD_PARTY.md`](../THIRD_PARTY.md).

| Engine | Needed for | Where to get it | Licence |
|--------|-----------|-----------------|---------|
| **HOLE** | Gate 1 pore profile (Pac-Pore) | <https://www.holeprogram.org/> | academic, non-commercial, not redistributable |
| **idock** | Alternative docking in the Poromania shell pipeline | from its author | check terms before use |
| **GROMACS** | Gate 4 MD | <https://www.gromacs.org/> | LGPL-2.1 |
| **AMBER** | Gate 4 MD as PackMan is written (`pmemd.cuda`, `tleap`) | <https://ambermd.org/> | own licence |
| **SIRAH** | Coarse-grained force field for gate 4 | <http://www.sirahff.com/> | academic; check terms |
| **NetMHCIIpan** | Gate 3, if and when a real de-immunisation engine is wired in | <https://services.healthtech.dtu.dk/services/NetMHCIIpan-4.3/> | academic DTU, not redistributable |

For a local install, put each binary on your `PATH` (for example in `/usr/local/bin`) and
confirm with `which hole`. For Docker, mount them as shown above.

**What works without them:** packing (gate 2), substrate cross-section calculation, docking
with Vina, the library, and the illustrative gates 3 and 4. **What does not:** the HOLE pore
profile and the mutant screen that depends on it, and any real molecular dynamics.

HOLE also needs its van der Waals radii file. Poromania ships one at
`Poromania.v.1.2./scripts/vdwradii.lib`.

## Optional data download

The default structure library travels in the repository: four capsids (BMV, CCMV, MS2, QB)
and four enzymes, including glucocerebrosidase (`GCase_1OGS`), so the Studio runs
immediately after installation.

One structure is too large for git and is fetched on demand — the P22 capsid, RCSB entry
5UU5:

```bash
cd nanocapsule-mvp
./scripts/fetch_data.sh
```

The script downloads biological assembly 1 from RCSB into
`Input/Capsides/P22_5UU5/capside.pdb`, falling back to the asymmetric unit if the assembly
is unavailable, and skips the download if the file already exists. It needs `curl` or
`wget`.

## Verifying the installation

### 1. The health endpoint

```bash
curl http://localhost:5000/api/health
```

```json
{
  "status": "ok",
  "engines": {"packmol": true, "pymol": true, "obabel": true,
              "vina": true, "hole": false, "idock": false},
  "deps": {"rdkit": true, "numpy": true, "yaml": true, "flask": true}
}
```

`status: ok` means the application is alive. The `engines` map is a `which` lookup for each
binary and the `deps` map an import check for each Python module, so this single call tells
you which gates will work. In the example above Pac-Pore would fail, because `hole` is
false; everything else is ready.

All four `deps` must be `true`. If `rdkit` is false, the install did not complete: two gates
import it as a hard dependency.

### 2. The test suite

```bash
cd nanocapsule-mvp
python -m pytest -q
```

22 tests should pass in a couple of seconds: 17 smoke tests that boot the app and check every
route is wired and returns the expected shape, and 5 golden tests that freeze known numerical
results of the substrate cross-section calculation so a scientific regression is caught even
when nothing crashes.

The suite intentionally does **not** exercise the slow binary engines, so it passes on a
machine without HOLE, Packmol or PyMOL. It validates wiring, not scientific validity.

### 3. The interface

Open <http://localhost:5000>. The LIBRARY tab should list the four capsids and four enzymes
with computed geometry. If it does, the server, the configuration and the structure paths
are all correct.

## The other three engines

The three scientific engines are not pip packages and are not installed with the Studio.
They are run directly, from their own directories, and each README states its requirements
and its honest execution status:

| Engine | Requirements | Status |
|--------|--------------|--------|
| [Poromania](../Poromania.v.1.2./README.md) | PyMOL, RDKit, Open Babel, HOLE2, idock, pandas, matplotlib; APBS for figures | Real, end to end |
| [PackMan](../PackMan.v.1.2/README.md) | AMBER (`pmemd.cuda`, `tleap`), SIRAH, cpptraj, CUDA GPU | Protocol complete, MD never run |
| [sustratinaitor](../sustratinaitor/README.md) | Packmol, AmberTools (`antechamber`, `sqm`, `tleap`), SIRAH | Stages 1–3 done, stage 4 not run |

Continuous integration verifies that all three engines' Python parses (`compileall`), which
catches syntax breakage without needing the heavy binaries.

## Troubleshooting

**The container reports `unhealthy`.** The healthcheck polls `/api/health` with urllib. Read
the log with `docker compose logs`; the usual cause is a missing bind-mounted directory or
an occupied port 5000.

**`ModuleNotFoundError: No module named 'rdkit'`.** You installed into a different
interpreter than the one running the server, or you used Python older than 3.12.
`rdkit==2025.9.1` has no wheels for older versions. Check with
`python -c "import sys; print(sys.version)"` inside the active virtual environment.

**PyMOL fails with an OpenGL or libGL error.** PyMOL is being run headless without its
runtime libraries. Install `libgl1`, `libxrender1` and `libgomp1`; the Docker image already
does.

**Pac-Pore returns an error about HOLE.** Expected without HOLE on the `PATH`. Confirm with
`/api/health`, then install or mount it as described above.

**Packmol times out.** The default timeout is 300 s (`engines.packmol.timeout` in
`config/default.yaml`). Whole capsids with many enzymes can exceed it; raise the value or
reduce the number of replicas.

**Port 5000 is already in use.** Change the `web.port` value in `config/default.yaml` for a
local install, or the port mapping in `docker-compose.yml` for Docker.

**A packing experiment gives different results between runs.** Check
`engines.packmol.use_random_seeds` in `config/default.yaml`. It must be `false` for
reproducible packing; with `seed_base: 1234567`, replica *n* uses `seed_base + n`.

## Uninstalling

```bash
# Docker
cd vlp-studio/nanocapsule-mvp && docker compose down
docker image rm nanocapsule-mvp:latest

# Local
rm -rf vlp-studio               # the virtual environment lives inside the clone
```

Nothing is installed outside the clone and the Docker image. The engines you installed
system-wide (`packmol`, `pymol`, `openbabel`, `autodock-vina`) are removed with your package
manager if you no longer want them.
