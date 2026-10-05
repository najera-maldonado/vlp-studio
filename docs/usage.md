# Usage

This document walks through the platform the way it is actually meant to be used: one gate
of the funnel at a time, on the project's own case study — encapsulating **glucocerebrosidase**
(the enzyme deficient in Gaucher disease) inside a virus-like particle so that it can process
its substrate, **glucosylceramide**.

If you have not installed the platform yet, start with
[`installation.md`](installation.md).

## Contents

- [The funnel, and what is real](#the-funnel-and-what-is-real)
- [Telling real output from illustrative output](#telling-real-output-from-illustrative-output)
- [Starting the Studio](#starting-the-studio)
- [Gate 0 — the library](#gate-0--the-library)
- [Gate 1 — does the substrate get through?](#gate-1--does-the-substrate-get-through)
- [Gate 2 — does the enzyme fit inside?](#gate-2--does-the-enzyme-fit-inside)
- [Gate 3 — can the enzyme be de-immunised?](#gate-3--can-the-enzyme-be-de-immunised)
- [Gate 4 — does the assembly survive?](#gate-4--does-the-assembly-survive)
- [Where results are written](#where-results-are-written)
- [Adding your own structures](#adding-your-own-structures)
- [Reproducing a result](#reproducing-a-result)

## The funnel, and what is real

Each gate asks one physical question, and a candidate design has to survive all four. The
point of the funnel is that the cheap questions come first: there is no reason to simulate
an assembly that the substrate cannot even enter.

| Gate | Question | Where you run it | Status |
|------|----------|------------------|--------|
| 1 · Through | Does the substrate fit through the capsid pore? | Studio PAC-PORE tab, or [Poromania](../Poromania.v.1.2./README.md) directly | Engine runs end to end; result under review (see the Poromania README's audit findings) |
| 2 · Inside | Does the enzyme pack inside the capsid? | Studio STUDIO 3D tab | Engine runs; the capacity number is not yet a validated measurement (see the Studio README's audit findings) |
| 3 · Outside | Can the enzyme be de-immunised? | Studio DE-IMMUNISATION tab | Illustrative only |
| 4 · Survives | Does it hold up under molecular dynamics? | [PackMan](../PackMan.v.1.2/README.md) and [sustratinaitor](../sustratinaitor/README.md) | MD never run; committed inputs are stubs, not a runnable protocol |

Gates 1 and 2 run real engines and return numbers today, but **do not quote those numbers as
results yet**: an independent audit (2026-10-04) found that gate 2's convergence check never
fires and gate 1's only committed profile is invalid. Gate 3 is a placeholder. Gate 4 has
never been executed and cannot be from the committed files, so the Studio tab shows
example curves rather than results. The corrections, with evidence, are in
[`CORRECCIONES_DOCUMENTACION.md`](../CORRECCIONES_DOCUMENTACION.md).

## Telling real output from illustrative output

This matters enough to be a convention rather than a footnote. Every API response that is a
placeholder carries an explicit flag:

```json
{"illustrative": true, ...}
```

A real measurement carries `"illustrative": false` and a `source` field naming what produced
it, for example `"source": "HOLE (calculado ahora)"`. The interface shows the same
distinction as a label on the tab. If you are deciding whether to trust a number, check that
flag first; it is the single honest signal in the API.

The two endpoints that are easiest to confuse:

| Endpoint | What it is |
|----------|------------|
| `POST /api/pore/profile` | A fast analytic sketch of a radius-versus-axis curve, for the interface. **Illustrative.** |
| `POST /api/pore/run_hole` | Runs HOLE on a real structure and returns the measured profile. **Real.** |

## Starting the Studio

```bash
cd nanocapsule-mvp
docker compose up -d                       # or: FLASK_DEBUG=0 python3 src/web/app.py
curl http://localhost:5000/api/health
```

Open <http://localhost:5000>. The five tabs correspond to the library plus the four gates.
Everything the interface does is also available over the REST API, which is what the
examples below use, since commands are reproducible and clicks are not. The full endpoint
reference is in the [Studio README](../nanocapsule-mvp/README.md#rest-api).

Before anything else, confirm which engines you have:

```bash
curl -s http://localhost:5000/api/health | python3 -m json.tool
```

If `hole` is `false`, gate 1's real measurements will fail and only the sketch will work.

## Gate 0 — the library

The library is the catalogue of structures the platform can work with, with geometry
computed from the files themselves.

```bash
curl -s http://localhost:5000/api/library/capsides
curl -s http://localhost:5000/api/library/enzymes
curl -s http://localhost:5000/api/library/combinations     # valid capsid/enzyme pairs
curl -s http://localhost:5000/api/library/detail           # radius, chains, residues
```

The repository ships four capsids (BMV, CCMV, MS2, QB) and four enzymes. For the Gaucher
case the relevant one is `GCase_1OGS`, the crystal structure of human acid
β-glucosidase; the others (alkaline phosphatase, luciferase, EGFP) are useful controls
because they differ in size.

To add the much larger P22 capsid, which is the one used in the published VLP nanoreactor
literature, fetch it first:

```bash
./scripts/fetch_data.sh                    # downloads RCSB 5UU5
```

## Gate 1 — does the substrate get through?

The question is geometric: the narrowest point of the capsid pore has to be wider than the
narrowest cross-section of the substrate. Both sides of that comparison are measured.

### Step 1 — measure the substrate

```bash
curl -s -X POST http://localhost:5000/api/pore/section \
  -H 'Content-Type: application/json' \
  -d '{"smiles": "OCC1OC(O)C(O)C(O)C1O"}'
```

```json
{"smiles": "OCC1OC(O)C(O)C(O)C1O", "radius": 1.95}
```

RDKit embeds the molecule in 3D with a fixed seed, aligns it by principal component
analysis and reports the minimum cross-sectional radius in ångström. The seed is fixed, so
this number is reproducible; the project's golden tests pin it to 0.2 Å so that a
future change cannot move it silently.

Glucose is used here as the headgroup proxy. For the real substrate, pass the full
glucosylceramide SMILES:

```bash
curl -s -X POST http://localhost:5000/api/pore/section \
  -H 'Content-Type: application/json' \
  -d '{"smiles": "CCCCCCCCCCCCCCC(C(=O)N[C@@H](CO[C@H]1[C@@H]([C@H]([C@@H]([C@H](O1)CO)O)O)O)[C@@H](/C=C/CC/C=C/CCCCCCCCC)O)O"}'
```

### Step 2 — measure the pore

List the pore structures available from Poromania, then run HOLE on one:

```bash
curl -s http://localhost:5000/api/pore/structures
# {"structures": [{"key": "BMV/poronatural"}, {"key": "BMV/poro3fold"}, ...]}

curl -s -X POST http://localhost:5000/api/pore/run_hole \
  -H 'Content-Type: application/json' \
  -d '{"structure": "BMV/poronatural"}'
```

This is a real HOLE run. It needs `hole` on the `PATH`, takes seconds to minutes depending
on the structure, and returns the measured profile, the minimum radius, the symmetry axis it
used and a `channel_id` that the 3D viewer can load. The axis is derived from the structure
by principal component analysis rather than assumed, which was one of the harder bugs to get
right: a profile measured along the wrong axis is meaningless.

Fetch the channel geometry for visualisation with:

```bash
curl -s 'http://localhost:5000/api/pore/channel?id=run:BMV__poronatural'
```

### Step 3 — if the pore is too narrow, open it

Comparing step 1 with step 2 usually shows the native pore is too narrow. The screen then
asks which mutations widen it enough:

```bash
curl -s -X POST http://localhost:5000/api/pore/screen \
  -H 'Content-Type: application/json' \
  -d '{"structure": "BMV/poronatural", "substrate_radius": 1.95}'
```

This runs the full real pipeline: HOLE on the wild type, location of the constriction point,
identification of the three pore-lining residues nearest that point on every chain,
construction of a progressive mutant library that replaces them with glycine or alanine,
generation of all mutants in a single PyMOL call, and a HOLE run on each one. The response
ranks the mutants by resulting minimum radius and includes, for each:

| Field | Meaning |
|-------|---------|
| `mutations` | The substitutions applied, e.g. `129G, 132G` |
| `pore_min` | Minimum pore radius after mutation (Å) |
| `delta` | Change relative to the wild type (Å) |
| `passes` | Whether `pore_min >= substrate_radius`, i.e. whether this gate is survived |
| `channel_id` | Identifier to load the channel in the viewer |

`passes` is the gate's verdict. Mutations are applied symmetrically to all chains, because a
capsid pore is a symmetric assembly and mutating one chain would produce a structure that
does not exist.

To test a specific hypothesis instead of the automatic library:

```bash
curl -s -X POST http://localhost:5000/api/pore/mutant \
  -H 'Content-Type: application/json' \
  -d '{"structure": "BMV/poronatural", "mutations": {"129": "GLY", "132": "ALA"}}'
```

### Step 4 — check that a wider pore still binds the substrate

A pore wide enough to pass the substrate is useless if it no longer interacts with it, so the
last step docks the substrate into each variant and correlates affinity against radius:

```bash
curl -s -X POST http://localhost:5000/api/pore/dock \
  -H 'Content-Type: application/json' \
  -d '{"structure": "BMV/poronatural", "smiles": "OCC1OC(O)C(O)C(O)C1O"}'
```

Open Babel prepares receptor and ligand, AutoDock Vina docks, and the response includes the
per-variant affinities and a Pearson correlation between pore radius and binding affinity.
This is the slowest call in the Studio; expect minutes.

### Running gate 1 outside the Studio

The same science exists as a standalone shell pipeline in Poromania, which additionally
produces electrostatic surface figures and comparative triptychs, and which uses idock rather
than Vina. See the [Poromania README](../Poromania.v.1.2./README.md) for the full sequence.
Be aware of the overlap: the Studio reimplemented this logic in Python, so the two
implementations can diverge.

## Gate 2 — does the enzyme fit inside?

### Step 1 — compute the capsid's internal radius

```bash
curl -s -X POST http://localhost:5000/api/capsid/radius \
  -H 'Content-Type: application/json' \
  -d '{"capsid": "BMV_IJS9"}'
```

PyMOL recentres the capsid, grows a probe from the centre of mass until it collides, and
reports the usable internal radius, which is then cached. When it cannot be computed the
system falls back to `packing.internal_radius_default` (90 Å) — worth knowing, because for
several library capsids that fallback is what you are actually using.

### Step 2 — preview before committing

```bash
curl -s -X POST http://localhost:5000/api/preview/enzymes \
  -H 'Content-Type: application/json' \
  -d '{"capsid": "BMV_IJS9", "enzyme": "GCase_1OGS", "n_enzymes": 6, "radius": 50.0}' \
  -o preview.pdb
```

The preview generates real geometry without launching Packmol, so it is fast and good for
deciding how many enzymes to attempt. Unlike most endpoints it returns the structure as
plain text rather than JSON, which is why the example writes it to a file. Add
`"save_file": true` to also keep it in `Output/`.

The same exists for a substrate shell around the capsid:

```bash
curl -s -X POST http://localhost:5000/api/preview/substrate \
  -H 'Content-Type: application/json' \
  -d '{"capsid": "BMV_IJS9", "n": 60, "smiles": "OCC1OC(O)C(O)C(O)C1O"}' \
  -o substrate_preview.pdb
```

### Step 3 — configure, then run the experiment

The endpoint is deliberately two-phase: a call without `run_packing` only echoes the
parameters, so you cannot start a long run by accident.

```bash
# Dry run: confirm parameters
curl -s -X POST http://localhost:5000/api/experiment/run \
  -H 'Content-Type: application/json' \
  -d '{"capsid": "BMV_IJS9", "enzyme": "GCase_1OGS", "n_replicas": 10}'
# -> {"status": "configured", ...}

# Real run
curl -s -X POST http://localhost:5000/api/experiment/run \
  -H 'Content-Type: application/json' \
  -d '{"capsid": "BMV_IJS9", "enzyme": "GCase_1OGS", "n_replicas": 10, "run_packing": true}'
```

Packmol is stochastic, so one run is not an answer. The experiment runs *n* replicas and
reports the distribution rather than a single figure. **Seeds:** today each replica draws a
random seed (`experiment_runner.py` does not pass the configured `seed_base`); the seed used
is written to `replica_N/metadata.json`, so keep that file if you need to repeat a run.

| Field | Meaning |
|-------|---------|
| `best_result` | Most enzymes successfully packed in any replica |
| `mean`, `median`, `stdev`, `worst` | Distribution across replicas |
| `n_replicas_success` / `n_replicas_total` | How many replicas converged |
| `internal_radius` | Radius used (computed or fallback) |
| `experiment_dir`, `best_file` | Where the output was written |
| `all_results` | Per-replica detail |

Report the distribution, not just `best_result`: `best_result` is a maximum over replicas
and grows with the number of replicas you ask for.

**Read this before trusting the numbers.** The audit of 2026-10-04 found that the
convergence check does not work as the configuration implies: the code looks for the log
line `Maximum distance violation:`, which Packmol never writes (it writes `Maximum violation
of target distance:`), so `packing.max_violation_threshold` has no effect; the fallback then
accepts any output with at least 10 000 atom lines, which the capsid alone satisfies; and the
number of enzymes actually placed is never counted. With a Packmol double that places zero
enzymes the engine reported 100 enzymes, σ = 0.00. Until tasks PK-2 to PK-5 of the repair
plan are done, verify a result yourself: count the atoms of `best_packing.pdb` against
`capsid + n × enzyme`, read the real violation in the replica's Packmol log, and treat a
σ of 0.00 across replicas as a warning sign, not as convergence. `packing.exclusion_radius`
(5 Å) is a per-atom radius, so Packmol enforces 10 Å between atoms of different enzymes;
the capacity depends strongly on that choice.

Re-running the same experiment does **not** currently reproduce the same numbers, because
the seeds are random (see above). The calculation is geometric, but it is not deterministic
in the production path and it is not covered by any test; the golden test in the repository
covers the gate 1 cross-section.

### Step 4 — retrieve the structure

```bash
curl -s http://localhost:5000/api/result/pdb -o packed.pdb
curl -s http://localhost:5000/api/files/generated
curl -s -X POST http://localhost:5000/api/download/experiment-zip \
  -H 'Content-Type: application/json' \
  -d '{"capsid": "BMV_IJS9", "enzyme": "GCase_1OGS"}' -o experiment.zip
```

The packed PDB loads in the Studio's 3D viewer, with each enzyme on its own chain so it gets
its own colour, and with capsid transparency and clipping controls for looking inside.

## Gate 3 — can the enzyme be de-immunised?

```bash
curl -s http://localhost:5000/api/deimmuno/data
```

**This gate is illustrative.** The response is a static dictionary with
`"illustrative": true`, kept so that the interface can show the shape of the analysis. No
epitope predictor is wired in. Do not use it for any scientific claim.

The intended real engine has been identified — NetMHCIIpan-4.3, which is academic, not
redistributable, and would have to be supplied by the user in the same way HOLE is. Wiring
it in is future work, not a hidden feature.

## Gate 4 — does the assembly survive?

### What the Studio can do today

The Studio prepares real MD inputs, and that part works:

```bash
curl -s 'http://localhost:5000/api/md/box?capsid=BMV_IJS9'

curl -s -X POST http://localhost:5000/api/md/prepare \
  -H 'Content-Type: application/json' \
  -d '{"capsid": "BMV_IJS9", "n_substrate": 40, "smiles": "OCC1OC(O)C(O)C(O)C1O"}'
```

`md/box` returns real box dimensions computed from the structure. `md/prepare` writes real
input files for a simulation. **Neither runs a simulation.**

```bash
curl -s http://localhost:5000/api/md/examples
```

returns `"illustrative": true` with synthetic curves. The MD ANALYSIS tab is a preview of the
shape of results, not results.

### Running the actual dynamics

The real protocol lives in two engines, outside the web application, and both need AMBER,
the SIRAH force field and a CUDA GPU:

- **[PackMan](../PackMan.v.1.2/README.md)** — the enzyme-inside-capsid system: packing,
  conversion to coarse-grained, system building with LEaP, then minimisation, six-stage
  heating, equilibration and production, followed by cpptraj analysis that emits exactly the
  two-column `.dat` files the Studio tab is designed to read.
- **[sustratinaitor](../sustratinaitor/README.md)** — the capsid-plus-substrate system: 200
  copies of glucosylceramide packed around the capsid with Packmol.

Two warnings before you run anything, both recorded as deliberate open decisions rather than
patched over:

1. **PackMan's static heating files are written for all-atom dynamics** but would be applied
   to a coarse-grained topology. Use the inputs generated by `configurar_simulacion.sh`
   instead, and read `CIENCIA-3` in [`ESTADO.md`](../ESTADO.md) §4b first.
2. **sustratinaitor's packed system mixes resolutions**: Packmol packed the 144-atom
   all-atom substrate, not the 17-bead coarse-grained version, giving a coarse-grained
   capsid with an atomistic ligand in coarse-grained water. That system is not physically
   valid as it stands. See `CIENCIA-2`.

The author's own standing instruction applies here: **treat no molecular dynamics result
from this project as validated until the simulation has been run and checked.** That is why
gate 4 is presented as a protocol rather than as findings.

## Where results are written

```
nanocapsule-mvp/Output/
├── Experiments/<timestamp>/replica_<n>/   # one directory per replica, per experiment
├── Generated_PDBs/                        # packed structures
├── hole_runs/<structure>/                 # real HOLE runs: hole_spheres.pdb, profile
└── cribado/<structure>/                   # mutant screen: mutants and per-mutant HOLE runs
```

`Output/` is bind-mounted in Docker, so results survive a container rebuild. Clear temporary
files with `POST /api/files/cleanup`.

## Adding your own structures

```
Input/Capsides/<YOUR_CAPSID>/capside.pdb
Input/Enzimas/<YOUR_ENZYME>/enzima.pdb
```

The file names inside each directory are fixed (`capside.pdb`, `enzima.pdb`); the directory
name is what appears in the library. The convention in the shipped library is
`NAME_PDBID`, for example `GCase_1OGS`. Use the biological assembly rather than the
asymmetric unit for capsids: the asymmetric unit is a fragment, and packing into it is
meaningless. Structures appear in the library on the next request, with no restart needed.

For a new pore structure in gate 1, add it under `Poromania.v.1.2./modelos/<NAME>/poro*.pdb`;
it then shows up in `/api/pore/structures`.

## Reproducing a result

For a result to be reproducible, record four things: the structure files, the configuration,
the pinned environment and the seed. The platform is set up so that all four are
recoverable.

1. **Environment.** `pip install -r nanocapsule-mvp/requirements.lock`, or use the Docker
   image, which installs from the same lock file. Python 3.12.
2. **Configuration.** `config/default.yaml` holds every scientific parameter. Keep a copy of
   it alongside your results; it is a small text file and it is the difference between a
   reproducible run and a number with no provenance.
3. **Seeding.** `engines.packmol.seed_base` and `use_random_seeds` exist in the YAML but are
   **not read by the code yet** (task PK-4). Until then, the only record of a replica's seed
   is `replica_N/metadata.json`; keep it with the results. Passing `seed_base` explicitly to
   `ParallelPacker.run_parallel_replicas` from Python does give `seed_base + n` per replica.
4. **Data.** The default library is in the repository; `scripts/fetch_data.sh` recovers the
   heavy structures that are not.

Then verify the installation still behaves as expected:

```bash
cd nanocapsule-mvp && python -m pytest -q
```

The golden tests in `tests/test_golden_science.py` freeze known substrate cross-section
values (gate 1, `substrate_section`) with a 0.2 Å tolerance. Two caveats: they cover only
that function (nothing in the test suite exercises the packing engine), and the frozen value
is the semi-axis of atomic centres without van der Waals radii, about half the physical
cross-section (glucose: 1.95 Å frozen vs 3.49 Å with vdW). If those tests fail, numbers from
this installation are not comparable with previous ones; if they pass, that says nothing
about packing.
