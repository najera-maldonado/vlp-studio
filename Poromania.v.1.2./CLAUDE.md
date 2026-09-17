# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a comprehensive automated pipeline for protein pore analysis, systematic mutagenesis, and molecular docking from SMILES codes. The project combines PyMOL for 3D visualization and mutagenesis, HOLE2 for quantitative pore geometry analysis, RDKit for ligand generation from SMILES, and automated docking workflows for comparative binding analysis.

## Common Commands

### Quick Start Pipeline
- `python visualize_pore.py` - Launch interactive pore analysis (GUI or terminal mode)
- `python automated_test.py` - Run automated analysis with default parameters (9Å radius, 5 random mutations)
- `python smiles_docking_pipeline.py 'SMILES_CODE' --ligand-name NAME` - Complete SMILES to docking pipeline

### Complete Analysis Workflow
- `pymol -cq 1crear_mutantes.pml` - Generate all mutant structures from pore analysis results
- `./2cargarsuperficies.sh` - Generate molecular surfaces for visualization
- `./3copiar_scripts.sh` - Copy analysis scripts to mutant directories (optional)
- `./4generarhole.sh` - Execute parallel HOLE2 analysis across all mutants
- `./5docking.sh` - Run molecular docking (requires ligand.pdbqt)
- `./5imagenescargasporo.sh` - Generate electrostatic surface visualizations
- `./6generador_triptico.sh` - Create publication-ready comparative figures

### Pipeline Automation
- `./clickaqui.sh` - Execute complete pipeline (steps 1-7 except docking)

### Individual Analysis Components
- `python pore_analyzer.py --gui` - Direct PyMOL GUI mode for interactive pore analysis
- `./scripts/clickautomatico.sh` - Execute HOLE analysis for individual mutant (run from mutant directory)
- `python ./scripts/1run_hole.sh` - Manual HOLE2 execution with predefined coordinates
- `python ./scripts/2out_tsv.py` - Convert HOLE2 raw output to structured TSV
- `python ./scripts/3analizar_hole.py` - Generate pore profiles and calculate constriction metrics

### SMILES and Ligand Processing
- `python generate_ligand_from_smiles.py 'SMILES' -o filename.pdbqt` - Convert SMILES to 3D PDBQT format
- `python test_smiles_example.py` - Test common drug molecules (aspirin, ibuprofen, caffeine)

## Project Architecture

### Three-Stage Analysis Pipeline

The pipeline implements a systematic approach to protein pore analysis through three distinct stages:

1. **Interactive Pore Discovery** (`pore_analyzer.py`, `visualize_pore.py`):
   - Loads `poronatural.pdb` and calculates geometric pore center from CA atoms
   - Creates expandable probe spheres for interactive pore-lining residue identification
   - Automatically detects common positions across all protein chains for symmetric analysis
   - Generates mutation specifications (random or manual) for systematic mutagenesis
   - Supports both GUI (PyMOL) and terminal-based interaction modes

2. **Systematic Mutant Generation** (`1crear_mutantes.pml`):
   - PyMOL script applies mutations simultaneously across all protein chains (A, B, C)
   - Creates individual `mutants/mut_*/` directories with `receptor.pdb` for each variant
   - Automatically copies analysis pipeline scripts for independent processing
   - Maintains structural symmetry through coordinated multi-chain mutagenesis

3. **Parallel Quantitative Analysis** (`4generarhole.sh`, `scripts/`):
   - Executes HOLE2 across all mutants using consistent parameters (cpoint: 219.21, 171.38, 312.96)
   - Generates quantitative pore profiles identifying constriction zones and minimum radii
   - Produces publication-ready plots with automated narrow region detection
   - Supports molecular docking integration for binding affinity correlation studies

### SMILES-to-Docking Integration

The pipeline includes a complete small molecule processing workflow:

- **Ligand Generation** (`generate_ligand_from_smiles.py`): Converts SMILES codes to optimized 3D structures with RDKit, handles complex molecules (e.g., glucosylceramide with 125 atoms), applies pH-specific protonation states
- **Automated Docking** (`smiles_docking_pipeline.py`): Integrates ligand generation with multi-mutant docking analysis, provides comprehensive binding affinity comparison across all generated mutants
- **Results Integration**: Correlates pore geometry metrics (HOLE2) with binding scores for structure-function analysis

### Directory Structure and Data Flow

```
Poromania/
├── poronatural.pdb                    # Input protein structure
├── Core analysis scripts
│   ├── pore_analyzer.py              # Interactive pore analysis
│   ├── visualize_pore.py             # Analysis launcher
│   ├── generate_ligand_from_smiles.py # SMILES processing
│   └── smiles_docking_pipeline.py    # Complete pipeline
├── Pipeline automation
│   ├── 1crear_mutantes.pml           # Mutant generation
│   ├── 2-6*.sh                       # Analysis stages
│   └── clickaqui.sh                  # Complete automation
├── mutants/                          # Generated during analysis
│   ├── WT.pdb                        # Wild-type reference
│   └── mut_*/                        # Individual mutant analysis
│       ├── receptor.pdb              # Mutant structure
│       ├── scripts/                  # Copied analysis tools
│       ├── hole/resultados/          # HOLE2 quantitative results
│       │   ├── hole_profile.tsv      # Pore geometry data
│       │   └── perfil_*.png          # Visualization plots
│       └── docking/                  # Binding analysis results
│           ├── Results/poses.txt     # Binding affinity scores
│           └── estructuras/          # 3D binding poses
└── scripts/                          # Base analysis components
    ├── 1run_hole.sh                  # HOLE2 execution
    ├── 2out_tsv.py                   # Data format conversion
    ├── 3analizar_hole.py             # Profile analysis
    ├── clickautomatico.sh            # Individual automation
    └── vdwradii.lib                  # HOLE2 parameters
```

### Key Dependencies and Environment

- **HOLE2**: Must be available in PATH with `vdwradii.lib` for van der Waals radius calculations
- **PyMOL**: Required for protein visualization, mutagenesis, and 3D manipulation
- **RDKit**: Chemical informatics library for SMILES processing and 3D structure generation
- **OpenBabel/iDock**: For molecular format conversion and docking calculations
- **Python packages**: pandas, matplotlib, numpy for data analysis and publication-quality plotting

### Fixed Analysis Parameters

The pipeline uses pre-configured parameters optimized for the target protein structure:
- **Pore center coordinates**: (219.21, 171.38, 312.96) - automatically calculated from geometric center
- **Multi-chain architecture**: Designed for symmetric proteins with chains A, B, C
- **HOLE2 vector**: Pre-determined for consistent pore axis analysis across all mutants

### Mutation Strategy and Analysis

The system implements a comprehensive mutagenesis approach:
- **Distance-based selection**: Identifies pore-lining residues using user-defined sphere radius
- **Symmetric mutations**: Ensures mutations are applied to equivalent positions across all protein chains
- **Flexible modes**: Supports both random exploration and hypothesis-driven manual mutation selection
- **Quantitative comparison**: Enables systematic structure-function correlation analysis

### Development Notes

When modifying analysis scripts:
- Maintain compatibility with the three-chain protein architecture (A, B, C)
- Preserve HOLE2 parameter consistency across mutants for valid comparison
- Follow the established mutants/ directory structure for proper pipeline integration
- Ensure SMILES processing handles complex molecules and maintains stereochemistry
- Test with provided example molecules (aspirin, ibuprofen, caffeine, glucosylceramida) before production use