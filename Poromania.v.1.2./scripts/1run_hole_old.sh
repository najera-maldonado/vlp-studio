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
    echo "⚠️  No se encontró pore_vector.txt, calculando vector automáticamente..."

    # Solo si no existe pore_vector.txt, hacer el cálculo de respaldo
    if [ -f "selected_positions.txt" ]; then
        SELECTED_POS=$(cat selected_positions.txt)
        echo "🧮 Calculando eje del poro basado en residuos: $SELECTED_POS"

        # Probar vectores comunes sistemáticamente
        VECTORS=("0 0 1" "0 0 -1" "0 1 0" "0 -1 0" "1 0 0" "-1 0 0" "1 1 0" "-1 -1 0" "1 0 1" "-1 0 -1")

    for test_vector in "${VECTORS[@]}"; do
        echo "🔄 Probando vector: $test_vector"

        # Ejecutar HOLE2 con este vector
        hole <<EOF > "${RAWOUT}_temp"
coord  $PDBFILE
radius $VDWFILE
cpoint $CPOINT
cvect  $test_vector
sphpdb "${SPHERES}_temp"
endrad 10.0
sample 0.2
gmacro
quit
EOF

        # Verificar si encontró un canal válido
        if grep -q "normal completion" "${RAWOUT}_temp"; then
            # Verificar si el punto más estrecho está cerca del centro
            if [ -f "${RAWOUT}_temp" ]; then
                narrowest_line=$(grep -A1 "minimum radius" "${RAWOUT}_temp" | tail -1)
                if [ -n "$narrowest_line" ]; then
                    narrowest_coords=$(echo "$narrowest_line" | awk '{print $2, $3, $4}')
                    if [ -n "$narrowest_coords" ]; then
                        distance=$(python3 -c "
import math
narrowest = [$narrowest_coords]
center = [$CPOINT]
if len(narrowest) == 3 and len(center) == 3:
    dist = math.sqrt(sum((a-b)**2 for a,b in zip(narrowest, center)))
    print(f'{dist:.2f}')
else:
    print('999')
")
                        echo "   → Distancia al centro: ${distance}Å"
                        if (( $(echo "$distance <= 8.0" | bc -l) )); then
                            echo "✅ Vector exitoso: $test_vector (distancia: ${distance}Å)"
                            CVECT="$test_vector"
                            mv "${RAWOUT}_temp" "$RAWOUT"
                            mv "${SPHERES}_temp" "$SPHERES"
                            break
                        fi
                    fi
                fi
            fi
        fi

        echo "   ❌ Vector $test_vector falló"
        rm -f "${RAWOUT}_temp" "${SPHERES}_temp"
    done

    # Si no encontró ningún vector válido, usar el por defecto
    if [ ! -f "$RAWOUT" ]; then
        echo "⚠️  Ningún vector funcionó, usando vector por defecto: 0 0 1"
        CVECT="0 0 1"
    fi

        echo "📐 Vector del eje calculado: $CVECT"
    else
        CVECT="0 0 1"
        echo "⚠️  No se encontró selected_positions.txt, usando vector por defecto: $CVECT"
    fi
fi

# Carpeta de salida
OUTDIR="hole/resultados"
mkdir -p "$OUTDIR"

# Archivos de salida
SPHERES="$OUTDIR/hole_spheres.pdb"
RAWOUT="$OUTDIR/hole_out.txt"

# Ejecutar HOLE
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

# Validar si HOLE2 encontró el poro correcto
if [ -f "$RAWOUT" ] && [ -f "pore_center.txt" ]; then
    echo "🔍 Validando canal encontrado por HOLE2..."

    # Extraer coordenadas del punto más estrecho de HOLE2
    NARROWEST=$(grep -A1 "minimum radius" "$RAWOUT" | tail -1 | awk '{print $2, $3, $4}')

    if [ -n "$NARROWEST" ]; then
        # Leer centro calculado
        CENTER=$(cat pore_center.txt)

        # Calcular distancia entre puntos
        DISTANCE=$(python3 -c "
import math
narrowest = [$NARROWEST]
center = [$CENTER]
dist = math.sqrt(sum((a-b)**2 for a,b in zip(narrowest, center)))
print(f'{dist:.2f}')
")

        echo "📍 Centro calculado: $CENTER"
        echo "🎯 Punto más estrecho HOLE2: $NARROWEST"
        echo "📏 Distancia: ${DISTANCE}Å"

        # Validación simple
        if (( $(echo "$DISTANCE <= 5.0" | bc -l) )); then
            echo "✅ Canal detectado correctamente en el poro seleccionado"
        else
            echo "❌ HOLE2 se desvió del poro seleccionado (distancia: ${DISTANCE}Å > 5Å)"
            echo "💡 Sugerencia: Verifique los residuos seleccionados o el vector del canal"
        fi
    else
        echo "⚠️  No se pudo extraer el punto más estrecho del output de HOLE2"
    fi
else
    echo "⚠️  Validación omitida: faltan archivos necesarios"
fi
