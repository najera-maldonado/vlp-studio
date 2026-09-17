# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Nanocapsule Designer MVP - A professional system for designing and packaging therapeutic enzymes in viral capsids through computational optimization. This is a molecular packing simulation system that uses Packmol for optimization and PyMOL for geometric calculations.

## Common Development Commands

### Installation and Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Or use setup.py for development
python setup.py develop

# Install system dependencies (required)
sudo apt-get install packmol        # Linux
brew install packmol                # macOS

# Install PyMOL (required)
conda install -c schrodinger pymol-open-source
# or
sudo apt-get install pymol
```

### Running the Web Server
```bash
cd src/web
python app.py
# Server runs on http://localhost:5000 (port 5001 in README is outdated)
```

### Running Tests
```bash
# Currently tests are standalone scripts (not using pytest yet)
# Located in _temp_backup/ directory - no active tests in main codebase
# To implement tests, use pytest framework as configured in requirements.txt
pytest tests/  # When tests are properly implemented
```

### Linting and Formatting
```bash
# Code formatting with black
black src/

# Linting with flake8
flake8 src/
```

## High-Level Architecture

### Core System Flow
1. **Structure Input**: Capsid and enzyme PDB files from `Input/` directories
2. **Preprocessing**: PyMOL calculates internal capsid radius and centers structures
3. **Packing Optimization**: Packmol iteratively places enzymes inside capsid with collision avoidance
4. **Multi-Replica Execution**: 7-10 parallel runs with different seeds to find optimal packing
5. **Result Selection**: Best replica (most enzymes packed) is selected automatically
6. **Visualization**: NGL.js renders 3D structures in web browser with interactive controls

### Key Architecture Components

#### Core Business Logic (`src/core/`)
- **capsid.py**: Manages viral capsid structures, calculates internal radius using PyMOL collision detection
- **cargo.py**: Handles enzyme preparation, centering, and validation
- **config.py**: Centralized YAML configuration management (loads from `config/default.yaml`)
- **experiment_manager.py**: Orchestrates multi-replica experiments (default 7-10 replicas)
- **experiment_runner.py**: Executes individual packing experiments with Packmol

#### Packing Engine (`src/packing/`)
- **parallel_packer.py**: Parallel processing of multiple packing attempts
- Uses exclusion radius (5-10Å in config) between enzymes to prevent collisions
- Implements iterative optimization to find maximum packing density

#### Web Interface (`src/web/`)
- **app.py**: Flask server with REST API (MUST run on port 5000)
- **templates/index.html**: Interactive 3D visualization using NGL.js library
- Provides real-time visualization controls (transparency, clipping, rotation)

#### I/O Management (`src/io/`)
- **structure_fetcher.py**: Manages structure library from Input/Capsides and Input/Enzimas
- Handles PDB file reading, validation, and preparation

### Configuration System
All parameters externalized in `config/default.yaml`:
- **Packing parameters**: radii, tolerances, thresholds (exclusion_radius: 5.0Å, tolerance: 2.0Å)
- **Engine settings**: Packmol timeout (300s), PyMOL headless mode
- **Experiment settings**: n_replicas (10), output paths
- **Web server**: port (5000), CORS settings

### Critical Implementation Details

#### Internal Radius Calculation
PyMOL-based calculation with specific order:
1. Center capsid at origin using center_of_mass
2. Create expanding pseudoatom to detect collision
3. **Subtract 1Å safety margin** from collision radius (not add)
4. Store in `radio_interno.txt` for caching

#### Multi-Replica System
- Runs 7-10 replicas with different random seeds (configurable)
- Each replica in `Output/Experiments/[timestamp]/replica_[N]/`
- Automatic selection of best result (most enzymes successfully packed)
- Parallel execution for performance

#### Packing Validation Thresholds
- Max distance violation: 0.10Å (configurable)
- Exclusion radius between enzymes: 5.0Å (configurable)
- Packmol tolerance: 2.0Å
- Min output lines for valid result: 10000

## API Endpoints

- `GET /api/structures` - List all available structures
- `GET /api/library/capsides` - List available capsids
- `GET /api/library/enzymes` - List available enzymes
- `GET /api/radius/{capsid}` - Calculate internal radius
- `POST /api/generate_pdb` - Generate single packed structure
- `POST /api/experiment/run` - Run full experiment with replicas
- `GET /api/download/{exp_id}` - Download results as ZIP

## File Organization

```
Input/
├── Capsides/       # Viral capsids (MS2, CCMV, BMV, QB)
└── Enzimas/        # Therapeutic enzymes

Output/
├── Experiments/    # Multi-replica experiment results
├── Generated_PDBs/ # Final packed structures
└── test_*/         # Test experiment results

config/
└── default.yaml    # All configuration parameters
```

## Development Status

### Working Features
- Multi-replica packing system
- Web visualization with NGL.js
- PyMOL radius calculation
- Packmol integration
- Configuration management

### In Progress (per DEVELOPMENT_PLAN.md)
- Creating pytest test suite
- Docker containerization
- CLI with argument parsing
- SQLite experiment history
- Progress bars for long operations

### Known Limitations
- Tests are placeholder scripts in `_temp_backup/`
- No CLI entry point despite setup.py configuration
- Flask debug mode disabled in production
- Temporary file cleanup could be improved