#!/bin/bash

# Script para convertir PDB all-atom a coarse-grained usando protocolo SIRAH
# Uso: ./convert_to_cg.sh N_ENZIMAS

if [ "$#" -ne 1 ]; then
    echo "Uso: $0 N_ENZIMAS"
    echo "Ejemplo: $0 1"
    exit 1
fi

N_ENZIMAS=$1

# Buscar archivo de entrada con patrón capside_Nenzimas_*.pdb
INPUT_FILE=$(ls capside_${N_ENZIMAS}enzimas_*.pdb 2>/dev/null | head -1)

if [ -z "$INPUT_FILE" ]; then
    echo "Error: No se encontró archivo capside_${N_ENZIMAS}enzimas_*.pdb"
    exit 1
fi

echo "Archivo encontrado: $INPUT_FILE"
echo "Convirtiendo a coarse-grained usando protocolo SIRAH..."

# Paso 1: PDB a PQR usando AMBER force field
echo "Paso 1: Generando archivo PQR..."
pdb2pqr --ff=AMBER "$INPUT_FILE" capside-${N_ENZIMAS}.pqr

if [ $? -ne 0 ]; then
    echo "Error en pdb2pqr"
    exit 1
fi

# Paso 2: PQR a CG usando cgconv.pl de SIRAH
echo "Paso 2: Convirtiendo a coarse-grained..."
./sirah_x2.3_24-07.amber/tools/CGCONV/cgconv.pl -i capside-${N_ENZIMAS}.pqr -o capside-${N_ENZIMAS}-cg.pdb

if [ $? -ne 0 ]; then
    echo "Error en cgconv.pl"
    exit 1
fi

echo "✓ Conversión completada:"
echo "  Input:  $INPUT_FILE"
echo "  PQR:    capside-${N_ENZIMAS}.pqr"
echo "  CG:     capside-${N_ENZIMAS}-cg.pdb"
echo ""
echo "Siguiente paso: tleap -f gensystem.leap"