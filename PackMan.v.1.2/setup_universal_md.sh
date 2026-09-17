#!/bin/bash

# Script para configurar MD universal en directorios #N_#N
# Genera archivos personalizados para cada directorio

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

echo "Configurando MD universal para directorios #N_#N..."

for dir in $TARGET_DIRS; do
    dir_name=$(basename "$dir")
    echo "Procesando: $dir (nombre: $dir_name)"

    # Crear directorio si no existe
    mkdir -p "$dir"

    # Copiar archivos base de MD (.in files)
    cp "$SOURCE_DIR"/*.in "$dir/"
    cp "$SOURCE_DIR"/*.bsub "$dir/" 2>/dev/null

    # Copiar directorio SIRAH si no existe
    if [ ! -d "$dir/sirah_x2.3_24-07.amber" ]; then
        cp -r "$SOURCE_DIR/sirah_x2.3_24-07.amber" "$dir/"
    fi

    # Generar gensystem.leap personalizado
    sed "s/DIRNAME/$dir_name/g" "$SOURCE_DIR/gensystem_template.leap" > "$dir/gensystem.leap"

    # Generar run_MD.sh personalizado
    sed "s/DIRNAME/$dir_name/g" "$SOURCE_DIR/run_MD_template.sh" > "$dir/run_MD.sh"

    # Verificar que la substitución funcionó
    if grep -q "DIRNAME" "$dir/gensystem.leap"; then
        echo "  ⚠️ Advertencia: substitución de template falló en $dir/gensystem.leap"
        # Forzar substitución manual
        sed -i "s/DIRNAME/$dir_name/g" "$dir/gensystem.leap"
    fi

    if grep -q "DIRNAME" "$dir/run_MD.sh"; then
        echo "  ⚠️ Advertencia: substitución de template falló en $dir/run_MD.sh"
        # Forzar substitución manual
        sed -i "s/DIRNAME/$dir_name/g" "$dir/run_MD.sh"
    fi
    chmod +x "$dir/run_MD.sh"

    echo "  ✓ Configurado $dir con nombre: $dir_name"
    echo "    - gensystem.leap: capside-$dir_name-cg.pdb → capside-$dir_name-cg-WAT.*"
    echo "    - run_MD.sh: usa archivos capside-$dir_name-cg-WAT.*"
done

echo ""
echo "Configuración completada. Para cada directorio:"
echo ""
echo "1. Generar archivo CG:"
echo "   pdb4amber -i capside_#Nenzimas.pdb -o capside-#N_#N-cg.pdb"
echo ""
echo "2. Ejecutar LEaP:"
echo "   tleap -f gensystem.leap"
echo ""
echo "3. Ejecutar simulación:"
echo "   bash run_MD.sh"
echo ""
echo "Flujo completo:"
echo "  capside_#Nenzimas.pdb → capside-#N_#N-cg.pdb → LEaP → MD"