# VLP Studio

Computational platform for **designing virus-like particle (VLP) nanocapsules loaded with
therapeutic enzymes** (e.g. glucocerebrosidase for Gaucher disease). The design problem is
organised as a **four-filter funnel**: each gate asks whether a candidate survives one
physical criterion before it is allowed through to the next.

> **Status:** research software under early development (v0.1.0), maintained by a single
> author. The engines are wired and run, but **no scientific result in this repository is
> validated yet** (see *Status per gate* below and the audit note that follows). This is
> **not** a clinical product.

> **Audit note (2026-10-04/05).** Four independent audits of the engines, run after the
> first version of this documentation was written, found that several earlier claims were
> not supported by the code and data in the repository. The claims have been corrected
> throughout the public documentation; every correction, with its evidence, is listed in
> [`CORRECCIONES_DOCUMENTACION.md`](CORRECCIONES_DOCUMENTACION.md). The repair plan
> consolidating all audit findings lives in `HOJA_DE_RUTA.md` on the branch
> `claude/consolidate-audit-roadmap-k82rek`.

## The four-gate funnel

| Gate | Question | Engine | Status |
|------|----------|--------|--------|
| **1 · Through** | Does the substrate fit through the capsid pore? | HOLE2 + mutant screening (PyMOL) + docking (Vina) — [Poromania](Poromania.v.1.2.) | Engine runs end to end; **result under review**. The only committed pore profile was measured on an unmutated structure with the HOLE seed point 7.6 Å off the symmetry axis, so it does not describe the pore it is filed under |
| **2 · Inside** | Does the enzyme pack inside the capsid? | Packmol + PyMOL — [Studio](nanocapsule-mvp) | Engine runs; **capacity number under review**. The acceptance criterion never fires (it looks for a line Packmol does not write) and the fallback accepts the capsid alone, so the reported capacity is not yet a measurement. Seeds are random in the production path |
| **3 · Outside** | Can the enzyme be de-immunised? | (real engine pending; illustrative today) | Illustrative |
| **4 · Survives** | Does the assembly hold up under molecular dynamics? | Coarse-grained SIRAH MD — [PackMan](PackMan.v.1.2) | **MD never run, and not runnable as committed**: the automated path builds an invalid topology (no hydrogens, no `TER` records) and the committed inputs total ~240 ps, not the 15/35 ns their titles state |

The **Studio** (3D web interface) wires gates 1 and 2 together interactively. Gates 3 and 4
are represented in the interface in illustrative form while their real engines are being
connected; the interface labels them as such. The MD tab's synthetic curves carry numeric
captions ("RMSD 2.8 Å", "17 666 K") that do not come from any simulation.

## Components (engines)

A monorepo with four independently versioned engines:

- **[`nanocapsule-mvp/`](nanocapsule-mvp)** — the **Studio**: Flask application plus a 3D
  viewer (NGL) that orchestrates packing (Packmol/PyMOL) and Pac-Pore (pore profile,
  docking). `v0.1.0`
- **[`Poromania.v.1.2./`](Poromania.v.1.2.)** — pore analysis pipeline: HOLE2 +
  mutagenesis (PyMOL) + docking. `v1.2.0`
- **[`PackMan.v.1.2/`](PackMan.v.1.2)** — system preparation and coarse-grained SIRAH MD
  protocol for the enzyme-inside-capsid system. `v1.2.0`
- **[`sustratinaitor/`](sustratinaitor)** — builds the substrate and packs it around the
  capsid for MD. `v0.1.0`

## Quick start (Docker, recommended)

```bash
git clone https://github.com/najera-maldonado/vlp-studio.git
cd vlp-studio/nanocapsule-mvp
docker compose build
docker compose up -d                     # http://localhost:5000
curl http://localhost:5000/api/health    # -> {"status":"ok", "engines": {...}, "deps": {...}}
```

The image ships Packmol, PyMOL, Open Babel, AutoDock Vina and RDKit. **Pac-Pore** (gate 1)
and the **MD** (gate 4) need additional engines (HOLE, GROMACS, SIRAH) that **you must
supply yourself** under their own licences — see [`THIRD_PARTY.md`](THIRD_PARTY.md) and
[`docs/installation.md`](docs/installation.md) for how to mount them.

Full installation instructions, including a local pip install, are in
[`docs/installation.md`](docs/installation.md); a worked walkthrough of each gate is in
[`docs/usage.md`](docs/usage.md).

## Documentation

| Document | Contents |
|----------|----------|
| [`docs/installation.md`](docs/installation.md) | Docker and local installation, external engines, verification |
| [`docs/usage.md`](docs/usage.md) | Gate-by-gate walkthrough, REST API reference, engine pipelines |
| [`nanocapsule-mvp/README.md`](nanocapsule-mvp/README.md) | Studio architecture and API |
| [`paper.md`](paper.md) | JOSS manuscript (statement of need, software summary) |
| [`THIRD_PARTY.md`](THIRD_PARTY.md) | Third-party engines and their licences |
| [`JOSS_CHECKLIST.md`](JOSS_CHECKLIST.md) | Submission readiness and open items |

Internal working documents (`ESTADO.md`, `PENDIENTES.md`, `BITACORA.md`,
`REVISION_MOTORES.md`, `INVESTIGACION_*.md`) are the author's development log and audit
trail. They are kept in Spanish on purpose: they are a record of decisions, not
user-facing documentation. `ESTADO.md` is the authoritative map of what actually works.

## Reproducibility

- **Pinned environment:** `nanocapsule-mvp/requirements.lock` (exact versions, generated
  with `pip-compile`; Docker and CI both install from it).
- **Continuous integration:** GitHub Actions runs smoke tests, a golden test and lint on
  every push and pull request ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)).
  The golden test freezes the substrate cross-section calculation of gate 1
  (`substrate_section`, RDKit). **No test covers the packing engine** (radius, Packmol
  input, acceptance criterion, statistics or seeds).
- **Packing seeds are not yet deterministic.** `config/default.yaml` declares
  `engines.packmol.seed_base` and `use_random_seeds`, but no module reads them: the
  production path (`experiment_runner.py` → `run_parallel_replicas`) passes no seed base and
  each replica draws a random seed. The seed actually used is written to each replica's
  `metadata.json`, so a past run can be identified, but a run cannot be declared in advance
  from the configuration. Fixing this is task PK-4 of the repair plan.
- **Heavy input data:** the default structure library travels in the repository; the large
  P22 capsid is fetched on demand with `nanocapsule-mvp/scripts/fetch_data.sh`.

## Testing

```bash
cd nanocapsule-mvp
python -m pytest -q      # 22 fast tests; does not exercise the heavy engines
```

The 22 tests pass with every defect listed in the audit note above present: they validate
wiring and the gate 1 cross-section, not the packing or pore engines.

## Contributing and support

Issues and pull requests are welcome at
<https://github.com/najera-maldonado/vlp-studio/issues>. See
[`CONTRIBUTING.md`](CONTRIBUTING.md) for how to report a problem, what the test suite does
and does not cover, and the project's scope boundaries (third-party engines are *called*,
never forked).

## License

The project's own code is licensed under the **GNU Affero General Public License v3.0 or
later** (see [`LICENSE`](LICENSE)) — strong copyleft: any modified version must stay open,
**including when it is offered as a network service**. Copyright (C) 2026
najera-maldonado.

The third-party scientific engines that the Studio **invokes** keep their own licences;
some of them (HOLE, NetMHCIIpan) are not redistributable and must be supplied by the user —
details in [`THIRD_PARTY.md`](THIRD_PARTY.md). One exception to "not redistributed" must be
stated: the repository currently versions a copy of the **SIRAH 2.3** force-field
distribution (146 files under `PackMan.v.1.2/archivos_dm_cg/sirah_x2.3_24-07.amber/`,
including its GPL-licensed `tools/`). Whether to keep that bundle or replace it with a
download step is an open licensing decision (DC-5 in the repair plan).

## How to cite

See [`CITATION.cff`](CITATION.cff). A JOSS submission is in preparation; the archive DOI
and the paper reference will be added here once available.
