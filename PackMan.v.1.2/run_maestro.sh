#!/bin/bash

# Script maestro para ejecutar workflow completo de MD con SIRAH
# Automáticamente procesa directorios 1_2 y 1_4

# set -e  # No salir si hay error (continuar con siguientes directorios)

echo "🚀 Iniciando workflow maestro MD-SIRAH..."

# Directorios objetivo - detecta automáticamente carpetas #N_#N
DIRS=($(ls -d [0-9]*_[0-9]* 2>/dev/null | sort))

for DIR in "${DIRS[@]}"; do
    echo ""
    echo "==============================================="
    echo "🔄 Procesando directorio: $DIR"
    echo "==============================================="

    # Extraer número de enzimas del nombre del directorio (#N_#N → tomar el segundo número)
    N_ENZIMAS=$(echo $DIR | cut -d'_' -f2)
    echo "📊 Número de enzimas detectado: $N_ENZIMAS"

    # Crear directorio si no existe
    mkdir -p "$DIR"

    # Copiar todo el contenido de archivos_dm_cg al directorio
    echo "📁 Copiando archivos base desde archivos_dm_cg..."
    cp -r archivos_dm_cg/* "$DIR/"

    # Entrar al directorio
    cd "$DIR"

    echo "🔧 Paso 1: Calculando radio interno de cápside..."
    cd empaquetador
    pymol -cq 1calcula_radio_interno.py

    echo "📦 Paso 2: Empaquetando $N_ENZIMAS enzimas..."
    echo "$N_ENZIMAS" | pymol -cq 2Empaquetador_Manual.py

    # Copiar archivo generado con nombre correcto
    GENERATED_FILE=$(ls capside_${N_ENZIMAS}enzimas_*.pdb | head -1)
    cp "$GENERATED_FILE" "../capside_${N_ENZIMAS}enzimas_$(date +%Y%m%d_%H%M%S).pdb"
    echo "✅ Archivo copiado: capside_${N_ENZIMAS}enzimas_*.pdb"

    cd ..

    echo "🧬 Paso 3: Conversión directa a coarse-grained con SIRAH..."
    # Buscar archivo de entrada
    INPUT_FILE=$(ls capside_${N_ENZIMAS}enzimas_*.pdb 2>/dev/null | head -1)
    if [ -z "$INPUT_FILE" ]; then
        echo "❌ Error: No se encontró archivo capside_${N_ENZIMAS}enzimas_*.pdb"
        cd ..
        continue
    fi

    echo "📂 Archivo encontrado: $INPUT_FILE"

    # Conversión directa PDB a CG usando cgconv.pl de SIRAH (salta pdb2pqr)
    echo "🔄 Convirtiendo directamente a coarse-grained con cgconv.pl..."
    # Dar permisos de ejecución y ejecutar
    chmod +x ./sirah_x2.3_24-07.amber/tools/CGCONV/cgconv.pl
    perl ./sirah_x2.3_24-07.amber/tools/CGCONV/cgconv.pl -i "$INPUT_FILE" -o "capside-${DIR}-cg.pdb"

    echo "⚙️ Paso 4: Preparando sistema con tleap..."
    if bash setup_universal.sh; then
        echo "✅ tLeap completado exitosamente"

        echo "🏃 Paso 5: Ejecutando simulaciones MD..."
        if bash run_MD.sh; then
            echo "✅ Simulaciones MD completadas"

            echo "📈 Paso 6: Ejecutando análisis..."
            cd analisis
            if bash ejecutar_analisis_cpptraj.sh; then
                echo "✅ Análisis completado"
            else
                echo "⚠️ Análisis falló, pero continuando..."
            fi
            cd ..
        else
            echo "⚠️ Simulaciones MD fallaron (posiblemente falta pmemd.cuda), pero continuando..."
        fi
    else
        echo "❌ tLeap falló para $DIR, saltando a siguiente directorio..."
    fi

    echo "✅ Procesamiento de directorio $DIR completado!"

    # Volver al directorio principal
    cd ..
done

echo ""
echo "🎉 ¡Workflow maestro completado para todos los directorios!"
echo "📊 Resultados disponibles en:"
for DIR in "${DIRS[@]}"; do
    echo "   - $DIR/ (configuración con $(echo $DIR | cut -d'_' -f2) enzimas)"
done