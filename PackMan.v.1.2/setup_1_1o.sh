#!/bin/bash

# Script para configurar MD específicamente para directorio 1_1o
# Copia archivos de archivos_dm_cg a 1_1o con naming universal

TARGET_DIR="./1_1o"
SOURCE_DIR="./archivos_dm_cg"
N_ENZIMAS="1"

# Verificar que existe el directorio fuente
if [ ! -d "$SOURCE_DIR" ]; then
    echo "Error: No existe el directorio $SOURCE_DIR"
    exit 1
fi

# Crear directorio si no existe
mkdir -p "$TARGET_DIR"

echo "Configurando MD para directorio $TARGET_DIR..."

# Copiar archivos base de MD (.in files)
cp "$SOURCE_DIR"/*.in "$TARGET_DIR/"
cp "$SOURCE_DIR"/*.bsub "$TARGET_DIR/" 2>/dev/null

# Copiar directorio SIRAH si no existe
if [ ! -d "$TARGET_DIR/sirah_x2.3_24-07.amber" ]; then
    cp -r "$SOURCE_DIR/sirah_x2.3_24-07.amber" "$TARGET_DIR/"
fi

# Generar gensystem.leap personalizado para 1_1o
sed "s/NENZIMAS/$N_ENZIMAS/g" "$SOURCE_DIR/gensystem_template.leap" > "$TARGET_DIR/gensystem.leap"

# Generar run_MD.sh personalizado para 1_1o
sed "s/NENZIMAS/$N_ENZIMAS/g" "$SOURCE_DIR/run_MD_template.sh" > "$TARGET_DIR/run_MD.sh"
chmod +x "$TARGET_DIR/run_MD.sh"

echo "✓ Configurado $TARGET_DIR con $N_ENZIMAS enzimas"
echo "  - gensystem.leap: capside-$N_ENZIMAS-cg.pdb → capside-$N_ENZIMAS-cg-WAT.*"
echo "  - run_MD.sh: usa archivos capside-$N_ENZIMAS-cg-WAT.*"
echo ""
echo "Configuración completada. Para este directorio:"
echo ""
echo "1. Generar archivo CG (protocolo SIRAH de 2 pasos):"
echo "   pdb2pqr --ff=AMBER capside_${N_ENZIMAS}enzimas_*.pdb capside-$N_ENZIMAS.pqr"
echo "   ./sirah_x2.3_24-07.amber/tools/CGCONV/cgconv.pl -i capside-$N_ENZIMAS.pqr -o capside-$N_ENZIMAS-cg.pdb"
echo "   (busca archivos como capside_1enzimas_20251010_105614.pdb)"
echo ""
echo "2. Ejecutar LEaP:"
echo "   tleap -f gensystem.leap"
echo ""
echo "3. Ejecutar simulación:"
echo "   bash run_MD.sh"
echo ""
echo "Flujo completo (protocolo SIRAH):"
echo "  capside_${N_ENZIMAS}enzimas_YYYYMMDD_HHMMSS.pdb → pdb2pqr → capside-$N_ENZIMAS.pqr → cgconv.pl → capside-$N_ENZIMAS-cg.pdb → LEaP → MD"