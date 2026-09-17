#!/bin/bash

# Script universal para copiar archivos de MD coarse-grained a directorios #N_#N
# Basado en archivos del 26 de agosto en ../archivos_dm_cg

SOURCE_DIR="./archivos_dm_cg"

# Verificar que existe el directorio fuente
if [ ! -d "$SOURCE_DIR" ]; then
    echo "Error: No existe el directorio $SOURCE_DIR"
    exit 1
fi

# Buscar todos los directorios con patrón #N_#N
TARGET_DIRS=$(find . -maxdepth 1 -type d -name "*_*" | grep -E '\./[0-9]+_[0-9]+')

if [ -z "$TARGET_DIRS" ]; then
    echo "No se encontraron directorios con patrón #N_#N"
    exit 1
fi

echo "Copiando archivos MD de $SOURCE_DIR a directorios objetivo..."

for dir in $TARGET_DIRS; do
    echo "Procesando: $dir"

    # Copiar archivos de MD
    cp "$SOURCE_DIR"/*.in "$dir/"
    cp "$SOURCE_DIR"/run_MD.sh "$dir/"
    cp "$SOURCE_DIR"/*.bsub "$dir/" 2>/dev/null

    # Copiar directorio SIRAH si no existe
    if [ ! -d "$dir/sirah_x2.3_24-07.amber" ]; then
        cp -r "$SOURCE_DIR/sirah_x2.3_24-07.amber" "$dir/"
    fi

    # Crear gensystem.leap universal (se modificará después)
    cp "$SOURCE_DIR/gensystem.leap" "$dir/"

    echo "  ✓ Archivos copiados a $dir"
done

echo ""
echo "Archivos copiados:"
echo "  - em1_WT4.in, em2_WT4.in (minimización)"
echo "  - eq1_WT4.in, eq2_WT4.in (equilibración)"
echo "  - prod_md_WT4.in (producción)"
echo "  - run_MD.sh (script principal)"
echo "  - gensystem.leap (configuración LEaP)"
echo "  - sirah_x2.3_24-07.amber/ (campo de fuerza)"
echo ""
echo "IMPORTANTE: Modificar gensystem.leap en cada directorio para usar:"
echo "  - Archivo PDB correcto: capside-#N_#N-cg.pdb"
echo "  - Nombres de salida apropiados"