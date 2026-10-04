# Poromania v1.2 — protein pore analysis and molecular docking

Engine of **gate 1 ("does it get through?")** of [VLP Studio](../README.md). An automated
pipeline that identifies the residues lining a capsid pore, generates mutants of those
positions systematically, measures the resulting pore geometry with HOLE2, and docks a
substrate into every variant so that pore radius can be correlated with binding affinity.

> **Status:** this is the **most mature engine in the project — real and end to end.** The
> pore profile, the mutant screen and the docking all run on real structures and produce
> real numbers. Two caveats are recorded honestly: the pipeline carries known dead code
> (`pore_analyzer_backup.py`, `1run_hole_old.sh`, `test_*.pml`, a hand-duplicated HOLE
> runner inside each `mutants/*/scripts/`), and the analysis parameters are **tuned for the
> target structure**, not auto-detected for arbitrary input (see *Fixed parameters*).

The Studio consumes this engine directly: it reads `modelos/` and `mutants/*/hole/` through
`paths.POROMANIA_DIR`. Note that the Studio also **reimplements** part of this science in
Python (`src/services/pore.py`) — the same logic therefore exists in two places and can
diverge. See the architectural note in [the Studio README](../nanocapsule-mvp/README.md).

## What it does

**Pore identification.** Loads a capsid pore structure, computes the geometric pore centre
from CA atoms, and uses an expandable probe sphere to select the residues lining the pore by
radial distance. Equivalent positions are detected across all protein chains so that
mutations stay symmetric. Works either through the PyMOL GUI or from the terminal.

**Systematic mutagenesis.** A PyMOL script applies each mutation set simultaneously to every
chain and writes one `mutants/mut_*/` directory per variant, each with its own `receptor.pdb`
and its own copy of the analysis scripts, so variants can be processed independently and in
parallel. Mutations can be random (exploratory) or specified by hand (hypothesis-driven).

**Quantitative HOLE2 analysis.** Runs HOLE2 on every mutant with identical parameters, which
is what makes the variants comparable, and produces a pore radius profile, the minimum radius
and the location of the constriction, plus publication-quality plots.

**Docking from SMILES.** Converts a SMILES string to an optimised 3D structure with RDKit,
protonates and converts it with Open Babel, and docks it into every mutant. It handles
large, flexible ligands — glucosylceramide, the Gaucher substrate, has 125 atoms. The result
is a comparison of binding affinities across variants, which can be correlated against the
HOLE2 geometry.

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
├── poronatural.pdb                 # Reference pore structure
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
│   ├── WT.pdb                      # Wild-type reference
│   └── mut_*/
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

- The pore centre and the HOLE axis vector are fixed per mutant
  (`pore_center.txt`, `pore_vector.txt`), which is exactly what makes variants comparable
  but means a new structure needs them re-derived.
- The mutagenesis script assumes the target's chain architecture.
- The pore axis is currently defined in more than one place in the codebase; see the dead
  code note at the top and `ESTADO.md` §4.

Keeping HOLE2 parameters identical across mutants is a requirement, not a convenience: a
profile computed on a different axis is not comparable with the others.

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
