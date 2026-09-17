#!/bin/bash

# Variables de entrada
PDBFILE="receptor.pdb"
VDWFILE="scripts/vdwradii.lib"

# Leer coordenadas del centro del poro calculado automáticamente
if [ -f "pore_center.txt" ]; then
    CPOINT=$(cat pore_center.txt | tr -d '\n')
    echo "📍 Usando centro del poro calculado: $CPOINT"
else
    CPOINT="0.0 0.0 0.0"
    echo "⚠️  No se encontró pore_center.txt, usando centro por defecto: $CPOINT"
fi

# Leer vector del eje del poro calculado automáticamente
if [ -f "pore_vector.txt" ]; then
    CVECT=$(cat pore_vector.txt | tr -d '\n')
    echo "📐 Usando vector del poro calculado: $CVECT"
else
    CVECT="0 0 1"
    echo "⚠️  No se encontró pore_vector.txt, usando vector por defecto: $CVECT"
fi

# Carpeta de salida
OUTDIR="hole/resultados"
mkdir -p "$OUTDIR"

# Archivos de salida
SPHERES="$OUTDIR/hole_spheres.pdb"
RAWOUT="$OUTDIR/hole_out.txt"

# Ejecutar HOLE2 con parámetros calculados automáticamente
echo "🔧 Ejecutando HOLE2..."
rm -f "$RAWOUT" "$SPHERES"

hole <<EOF > "$RAWOUT"
coord  $PDBFILE
radius $VDWFILE
cpoint $CPOINT
cvect  $CVECT
sphpdb $SPHERES
endrad 10.0
sample 0.2
gmacro
quit
EOF

# Verificar si HOLE2 completó exitosamente
if [ -f "$RAWOUT" ] && grep -q "normal completion" "$RAWOUT"; then
    echo "✅ HOLE2 completado exitosamente"

    # Extraer información del poro
    if [ -f "$RAWOUT" ]; then
        MIN_RAD=$(grep -i "minimum radius" "$RAWOUT" | head -1 | awk '{print $NF}' | sed 's/angstroms\.//')
        if [ -n "$MIN_RAD" ]; then
            echo "📏 Radio mínimo encontrado: ${MIN_RAD} Å"
        fi
    fi
else
    echo "❌ HOLE2 falló o no completó correctamente"
    if [ -f "$RAWOUT" ]; then
        echo "Últimas líneas del output:"
        tail -10 "$RAWOUT"
    fi
fi