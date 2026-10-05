# Poromania v1.2 — protein pore analysis and molecular docking

Engine of **gate 1 ("does it get through?")** of [VLP Studio](../README.md). An automated
pipeline that identifies the residues lining a capsid pore, generates mutants of those
positions systematically, measures the resulting pore geometry with HOLE2, and docks a
substrate into every variant so that pore radius can be correlated with binding affinity.

> **Status: the pipeline runs end to end, but its only committed result is not valid and the
> pipeline is not reproducible as committed.** An independent audit (2026-10-04) found that
> the one pore profile in this repository, `mutants/mut_129HIS_132GLY/` (minimum radius
> 1.92 Å), was measured on a structure that is **byte-identical to the wild type**
> (`cmp mutants/WT.pdb mutants/mut_129HIS_132GLY/receptor.pdb` → identical; positions 129 and
> 132 are still SER and VAL in all five subunits), with the HOLE seed point **7.59 Å off the
> pentamer's symmetry axis** and the axis vector **19.3° off**, so the constriction it reports
> lies 11.8 Å from the real pore axis. That 1.92 Å value must not be cited as a mutant result
> or as the pore radius. See *Audit findings* below and the `INVALIDO.md` file in that
> mutant's directory. Dead code is also present (`pore_analyzer_backup.py`, `test_*.pml`, a
> hand-duplicated HOLE runner inside each `mutants/*/scripts/`); note that `1run_hole_old.sh`
> is **not** merely dead code: it is the version that validated the channel (see below).

The Studio consumes this engine directly: it reads `modelos/` and `mutants/*/hole/` through
`paths.POROMANIA_DIR`. Note that the Studio also **reimplements** part of this science in
Python (`src/services/pore.py`) — the same logic therefore exists in two places and can
diverge. See the architectural note in [the Studio README](../nanocapsule-mvp/README.md).

## What it does

**Pore identification.** Loads a capsid pore structure, computes a pore centre from CA atoms
of the user-selected residues, and uses an expandable probe sphere to select the residues
lining the pore by radial distance. Equivalent positions are detected across all protein
chains so that mutations stay symmetric. Works either through the PyMOL GUI or from the
terminal. **Known defect:** the centre is the mean of the selected CA atoms of *one*
subunit (`pore_analyzer.py:415-442` keeps only the first match of `resi + chain`, which is
ambiguous when subunits share a chain ID), and the axis is the 4.4 Å chord from the first CA
to that centroid (`:485-497`). On the committed run this put the HOLE seed 7.59 Å off the
symmetry axis and the axis 19.3° off. The Studio's `_pore_axis` (second-moment tensor) gets
the pentamer axis exactly and is the implementation to converge on.

**Systematic mutagenesis.** A PyMOL script applies each mutation set simultaneously to every
chain and writes one `mutants/mut_*/` directory per variant, each with its own `receptor.pdb`
and its own copy of the analysis scripts, so variants can be processed independently and in
parallel. Mutations can be random (exploratory) or specified by hand (hypothesis-driven).
**Known defect:** nothing checks that the mutation was applied. The committed mutant was not
mutated (see *Status*), and the pipeline carried on and produced a profile for it.

**Quantitative HOLE2 analysis.** Runs HOLE2 on every mutant with the same `cpoint`, `cvect`,
`sample 0.2` and `endrad 10`, and produces a pore radius profile, the minimum radius and the
location of the constriction, plus plots. **Known defects:** the HOLE deck sets no `rseed`
(the committed `hole_out.txt` records a clock-chosen seed, 2093611), so two runs on the same
input need not agree; the parsers drop every point with radius ≤ 0.5 Å, so an occluded pore
is reported as open; and the current `scripts/1run_hole.sh` lost the channel-validation
check that `1run_hole_old.sh:118-151` had (constriction farther than 5 Å from the declared
centre → warning). On the committed run that distance is 10.18 Å.

**Docking from SMILES.** Converts a SMILES string to an optimised 3D structure with RDKit,
protonates and converts it with Open Babel, and docks it into every mutant with idock. It
handles large, flexible ligands — glucosylceramide, the Gaucher substrate, has 125 atoms. The
result is a comparison of binding affinities across variants. **Known defects:** idock runs
without a seed and with `threads = $(nproc)`, so results are not reproducible; the Studio
uses AutoDock Vina (`--seed 1`) instead, and idock and Vina scores are **not comparable**;
`smiles_docking_pipeline.py` reports the first line of `poses.txt` as the best score, which
is not always the minimum.

**Figures.** Electrostatic surface images (APBS) and automatically assembled comparative
triptychs.

## Installation

```bash
# PyMOL (visualisation and mutagenesis)
conda install -c conda-forge pymol        # or: sudo apt-get install pymol

# RDKit (SMILES processing)
conda install -c conda-forge rdkit        # or: pip install rdkit

# Open Babel (chemical format conversion, protonation)
sudo apt-get install openbabel

# Python analysis packages
pip install pandas matplotlib numpy
```

Two engines must be obtained separately because their licences do not allow
redistribution; see [`THIRD_PARTY.md`](../THIRD_PARTY.md):

- **HOLE2** — pore geometry. <https://www.holeprogram.org/> (academic, non-commercial).
  Must be on `PATH`, together with `vdwradii.lib` (shipped here in `scripts/`).
- **idock** — the docking engine used by the shell pipeline. Check its terms before use.
  (The Studio's own Pac-Pore tab uses AutoDock Vina instead, which *is* redistributable.)

APBS is needed only for the electrostatic surface figures.

Verify the installation:

```bash
python -c "import pymol, rdkit, pandas; print('Python dependencies OK')"
which hole  && echo "HOLE2 available"
which idock && echo "idock available"
which obabel && echo "Open Babel available"
```

System requirements: Linux or macOS, Python 3.8+, 8 GB RAM minimum (16 GB recommended for
whole-capsid structures), about 5 GB of free disk for mutant output.

## Usage

### Step 0 — pore analysis and mutant specification

```bash
python visualize_pore.py        # launcher: offers PyMOL GUI or terminal mode
python run_pore_analysis.py     # runs the analyser directly through PyMOL
```

In the interactive prompt you give a probe radius (typically 5–15 Å), which selects the
pore-lining residues, then ask for mutants, choose random or manual mode, and give the
number of mutants and mutations per mutant. The result is the mutation specification that
step 1 consumes.

### Step 1 — generate the mutants

```bash
pymol -cq 1crear_mutantes.pml
# writes mutants/mut_*/receptor.pdb plus per-mutant scripts
```

### Steps 2–4 — structural analysis

```bash
./2cargarsuperficies.sh     # molecular surfaces
./3copiar_scripts.sh        # distribute the analysis scripts (optional)
./4generarhole.sh           # HOLE2 across all mutants, in parallel
```

Per-mutant results land in `mutants/mut_*/hole/resultados/`: `hole_profile.tsv` with the
quantitative profile and `perfil_*.png` with the plot.

### Step 5 — docking

```bash
# From SMILES (recommended): generates the ligand and docks it everywhere
python smiles_docking_pipeline.py 'SMILES_CODE' --ligand-name NAME

# Or in two steps
python generate_ligand_from_smiles.py 'SMILES_CODE' -o my_ligand.pdbqt
cp my_ligand.pdbqt ligand.pdbqt    # 5docking.sh reads ./ligand.pdbqt
./5docking.sh
```

Worked example with the Gaucher substrate, glucosylceramide:

```bash
python smiles_docking_pipeline.py \
  'CCCCCCCCCCCCCCC(C(=O)N[C@@H](CO[C@H]1[C@@H]([C@H]([C@@H]([C@H](O1)CO)O)O)O)[C@@H](/C=C/CC/C=C/CCCCCCCCC)O)O' \
  --ligand-name glucosylceramide
```

Smaller molecules are useful for a quick check that the toolchain works:

```bash
python test_smiles_example.py                                           # lists examples
python smiles_docking_pipeline.py 'CC(=O)OC1=CC=CC=C1C(=O)O' --ligand-name aspirin
```

Affinity scores appear in `mutants/*/docking/Results/poses.txt`, and the best poses in
`mutants/*/docking/estructuras/`.

### Steps 6–7 — figures

```bash
./5imagenescargasporo.sh    # APBS electrostatic surface images
./6generador_triptico.sh    # comparative triptychs
```

## Repository layout

```
Poromania.v.1.2./
├── poronatural.pdb                 # Structure loaded by 1crear_mutantes.pml. NOTE: this is the
│                                   # CCMV trimer (3574 atoms, chains A/B/C, identical to
│                                   # modelos/CCMV/poronatural.pdb), NOT the structure that produced
│                                   # the committed result (which is modelos/BMV/poro5fold.pdb
│                                   # centred: 5735 atoms, chains A/B). The script's
│                                   # `chains = ['A','B']` only makes sense for poro5fold.
├── modelos/                        # Capsid models consumed by the Studio
│   ├── BMV/                        # capside.pdb, poronatural.pdb, poro3fold, poro5fold
│   └── CCMV/
├── pore_analyzer.py                # Interactive pore analyser
├── visualize_pore.py               # Launcher (GUI or terminal)
├── run_pore_analysis.py            # Direct runner
├── generate_ligand_from_smiles.py  # SMILES -> 3D -> PDBQT
├── smiles_docking_pipeline.py      # SMILES -> ligand -> docking, end to end
├── center_structures.py            # Structure centring helper
├── 1crear_mutantes.pml             # Mutant generation (PyMOL)
├── 2cargarsuperficies.sh           # Molecular surfaces
├── 3copiar_scripts.sh              # Script distribution
├── 4generarhole.sh                 # Parallel HOLE2
├── 5docking.sh                     # Docking (idock)
├── 5imagenescargasporo.sh          # APBS images
├── 6generador_triptico.sh          # Comparative figures
├── mutants/                        # Output, one directory per variant
│   ├── WT.pdb                      # Wild-type reference (= modelos/BMV/poro5fold.pdb centred)
│   └── mut_*/                      # Only mut_129HIS_132GLY is committed, and it is INVALID:
│       │                           # its receptor.pdb is byte-identical to WT.pdb (see INVALIDO.md)
│       ├── receptor.pdb            # Mutant structure
│       ├── pore_center.txt, pore_vector.txt, selected_positions.txt
│       ├── hole/resultados/        # hole_profile.tsv, perfil_*.png
│       ├── cargas_apbs/            # Electrostatics
│       └── docking/                # Results/poses.txt, estructuras/
└── scripts/                        # Base analysis components
    ├── 1run_hole.sh                # HOLE2 execution
    ├── 2out_tsv.py                 # Raw HOLE output -> TSV
    ├── 3analizar_hole.py           # Profile analysis and constriction metrics
    ├── clickautomatico.sh          # Per-mutant automation
    └── vdwradii.lib                # HOLE2 van der Waals radii
```

## Parameters and formats

| Parameter | Meaning | Typical values |
|-----------|---------|----------------|
| probe radius | Radius used to select pore-lining residues | 5–15 Å |
| number of mutants | Variants to generate | 5–20 |
| mutations per mutant | Substitutions per variant | 1–5 |
| pH | Protonation state for ligand preparation | 7.4 (physiological) |
| max conformations | Docking poses to keep | 100–1000 |

Inputs: protein structures in PDB format, ligands as SMILES strings. Outputs: structures
(PDB, PDBQT), data (TSV), figures (PNG).

### Fixed parameters (important limitation)

The pipeline was tuned for one target structure, and some parameters are hard-coded rather
than derived from the input:

- The pore centre and the HOLE axis vector are written per mutant
  (`pore_center.txt`, `pore_vector.txt`). Using the same values across mutants is what makes
  variants comparable, **provided the values are right**: on the committed run they are not
  (centre 7.59 Å off axis, vector 19.3° off; see *Audit findings*).
- The mutagenesis script assumes the target's chain architecture, and `resi + chain` does not
  identify a residue on `poro5fold`, where the five subunits all carry chain `A` and differ
  only in `segi`.
- The pore axis is defined in four places in the codebase (`pore_analyzer.py`,
  `1run_hole.sh`, `1run_hole_old.sh`, Studio `pore.py`); see `ESTADO.md` §4.

Keeping HOLE2 parameters identical across mutants is a requirement, not a convenience: a
profile computed on a different axis is not comparable with the others.

## Audit findings (2026-10-04)

From `AUDITORIA_PORO.md` (branch `claude/audit-poro-engine-giea7e`), all reproducible without
HOLE or PyMOL; the consolidated repair plan is `HOJA_DE_RUTA.md` (branch
`claude/consolidate-audit-roadmap-k82rek`), tasks PO-1 to PO-11.

| ID | Finding | Check it yourself |
|----|---------|-------------------|
| PORO-01 | The committed "mutant" is the wild type: `mut_129HIS_132GLY/receptor.pdb` ≡ `WT.pdb`; residues 129/132 are SER/VAL in all 5 subunits | `cmp mutants/WT.pdb mutants/mut_129HIS_132GLY/receptor.pdb` |
| PORO-02 | The result cannot be regenerated from the committed inputs: `1crear_mutantes.pml` loads `poronatural.pdb` (CCMV trimer), but `WT.pdb` is `modelos/BMV/poro5fold.pdb` centred | `grep -c ^ATOM poronatural.pdb mutants/WT.pdb modelos/BMV/poro5fold.pdb` → 3574 / 5735 / 5735 |
| PORO-03 | HOLE seed point 7.59 Å off the C5 axis, axis vector 19.29° off, constriction traced 11.76 Å off axis | script in the audit, §3.3 |
| PORO-04 | Channel validation existed in `1run_hole_old.sh:118-151` and is absent from the live `1run_hole.sh` | `diff scripts/1run_hole.sh scripts/1run_hole_old.sh` |
| PORO-05 | No `rseed` in the HOLE deck | `grep rseed scripts/1run_hole.sh` → nothing |
| PORO-10 | `radio > 0.5` filter in `2out_tsv.py:22` hides occlusion (93 of 268 sphere records are ≤ 0.5 Å) | `awk` over `hole_spheres.pdb` |
| PORO-12 | `1run_hole.sh:55` never prints the minimum radius (`$NF` is `angstroms.`) | run the line on `hole_out.txt` |
| PORO-14 | idock without seed; `threads=$(nproc)`; idock vs Vina not comparable | `5docking.sh:56-72` |
| PORO-17 | `CLAUDE.md` here documents a `cpoint (219.21, 171.38, 312.96)` that matches no committed run, and cites `automated_test.py` / `clickaqui.sh`, which do not exist | `ls` |

The audit also notes what is right and should be kept: the shared `scripts/vdwradii.lib`,
the Studio's `rseed 1`, both profile parsers agreeing on the committed file (1.915 Å at
z = −15.382), and `substrate_section` in the Studio as the pattern to imitate.

Until PO-3/PO-4/PO-7 of the repair plan are done (verified mutagenesis, a single channel
definition, and a real re-screen on `BMV/poro5fold` with provenance), **no pore radius or
mutant effect from this engine should be quoted**.

## Contributing and support

Issues and pull requests go to the monorepo:
<https://github.com/najera-maldonado/vlp-studio/issues>. See
[`CONTRIBUTING.md`](../CONTRIBUTING.md). Note the project boundary: third-party engines
(HOLE, Vina, idock, Open Babel) are **called**, never forked or rewritten.

## License

Part of VLP Studio, under **GNU AGPLv3 or later**. See [`LICENSE`](../LICENSE) and
[`THIRD_PARTY.md`](../THIRD_PARTY.md). Copyright (C) 2026 najera-maldonado.

## Citing and tool references

To cite the platform, see [`CITATION.cff`](../CITATION.cff) in the repository root; the
references for the underlying engines are collected in [`paper.bib`](../paper.bib).

- **HOLE** — Smart, O. S. *et al.* *J. Mol. Graph.* **14**, 354–360 (1996)
- **PyMOL** — Schrödinger, LLC, *The PyMOL Molecular Graphics System*
- **RDKit** — Landrum, G., *RDKit: Open-source cheminformatics*
- **AutoDock Vina** — Trott, O. and Olson, A. J. *J. Comput. Chem.* **31**, 455–461 (2010)
- **Open Babel** — O'Boyle, N. M. *et al.* *J. Cheminform.* **3**, 33 (2011)
