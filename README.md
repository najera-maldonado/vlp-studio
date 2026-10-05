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
> consolidating all audit findings is [`HOJA_DE_RUTA.md`](HOJA_DE_RUTA.md); its §0 states
> what has been repaired and what has not. On 2026-10-05 the audit reports, the roadmap and
> two repairs — the packing engine (`nanocapsule-mvp/REPARACION_PACKING.md`) and the PackMan
> MD protocol (PackMan v1.3.0) — were merged into `main`.

## The four-gate funnel

| Gate | Question | Engine | Status |
|------|----------|--------|--------|
| **1 · Through** | Does the substrate fit through the capsid pore? | HOLE2 + mutant screening (PyMOL) + docking (Vina) — [Poromania](Poromania.v.1.2.) | Engine runs end to end; **result under review**. The only committed pore profile was measured on an unmutated structure with the HOLE seed point 7.6 Å off the symmetry axis, so it does not describe the pore it is filed under |
| **2 · Inside** | Does the enzyme pack inside the capsid? | Packmol + PyMOL — [Studio](nanocapsule-mvp) | Engine runs; **capacity number still under review**. The acceptance criterion was repaired on 2026-10-05 (it now reads the real Packmol log line, counts the enzyme copies actually placed, rejects forced output, uses fixed seeds and is covered by 39 engine tests with a Packmol double). No run with a real Packmol binary has been made since the repair, and no committed multi-replica result exists |
| **3 · Outside** | Can the enzyme be de-immunised? | (real engine pending; illustrative today) | Illustrative |
| **4 · Survives** | Does the assembly hold up under molecular dynamics? | Coarse-grained SIRAH MD — [PackMan](PackMan.v.1.2) | **MD never run.** The five-stage SIRAH protocol was repaired on 2026-10-05 (PackMan v1.3.0: 5 ns + 25 ns + 10 ns per production chunk, checked against the SIRAH reference in CI). **No 15 ns or 35 ns simulation ever existed**: those were titles on 10 ps stubs. The system-preparation path still builds an invalid topology (no hydrogens, no `TER` records), so the protocol cannot yet run end to end |

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
  protocol for the enzyme-inside-capsid system. `v1.3.0`
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
- **Continuous integration:** GitHub Actions runs lint, the Studio test suite, a
  `compileall` pass over the other three engines and the static check of PackMan's MD
  inputs against the SIRAH reference on every push and pull request
  ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)).
- **What the tests cover:** 17 smoke tests; 5 golden tests that freeze the substrate
  cross-section calculation of gate 1 (`substrate_section`, RDKit); and, since 2026-10-05,
  39 tests of the packing engine and runner that exercise the real Python code against a
  Packmol double emitting the strings of the two real Packmol logs in the repository. There
  is still **no golden test of the packing radius** (task PK-6), and no test runs a real
  Packmol binary in CI (one marked test does so where Packmol is installed).
- **Packing seeds are fixed by default since 2026-10-05:** replica *i* uses
  `engines.packmol.seed_base + i` (1234567 by default), `use_random_seeds: true` switches to
  recorded random seeds, and every seed is written to `metadata.json` and `report.txt`. Two
  caveats remain: the Packmol timeout can still turn "fits" into "timeout" on a slower
  machine (now recorded as such, no longer counted as "does not fit"), and the repaired
  criterion has not yet been exercised against a real Packmol binary (task PK-1).
- **Heavy input data:** the default structure library travels in the repository; the large
  P22 capsid is fetched on demand with `nanocapsule-mvp/scripts/fetch_data.sh`.

## Testing

```bash
cd nanocapsule-mvp
python -m pytest -q      # 60 fast tests (+1 skipped without a real Packmol); no heavy engines
```

The smoke and golden tests validate wiring and the gate 1 cross-section; the engine tests
validate the packing engine's acceptance criterion, centring, seeds and statistics against a
Packmol double. Nothing in CI validates the pore engine or runs a real binary.

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
