#!/bin/bash
# clickautomatico.sh – corre pipeline HOLE desde carpeta scripts/

# 1. Ejecutando HOLE...
./scripts/1run_hole.sh

# 2. Convirtiendo salida a TSV...
python3 ./scripts/2out_tsv.py

# 3. Analizando perfil del canal...
python3 ./scripts/3analizar_hole.py
