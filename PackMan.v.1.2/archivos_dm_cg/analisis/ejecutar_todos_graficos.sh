#!/bin/bash
# Script para ejecutar todos los gráficos de análisis individual

echo "================================================================================"
echo "EJECUTANDO TODOS LOS GRÁFICOS DE ANÁLISIS"
echo "================================================================================"

# Configuración inicial: Preguntar número de residuos para RMSF
echo "🔧 CONFIGURACIÓN INICIAL:"
echo "Para el análisis de comparación RMSF, necesito saber cuántos residuos tiene cada enzima."
echo ""
while true; do
    read -p "¿Cuántos residuos tiene cada enzima? " RESIDUOS_POR_ENZIMA
    if [[ "$RESIDUOS_POR_ENZIMA" =~ ^[0-9]+$ ]] && [ "$RESIDUOS_POR_ENZIMA" -ge 50 ] && [ "$RESIDUOS_POR_ENZIMA" -le 2000 ]; then
        break
    else
        echo "❌ Ingrese un número entre 50 y 2000 residuos"
    fi
done

echo "✅ Configurado: $RESIDUOS_POR_ENZIMA residuos por enzima"
echo ""

# Configuración de zonas de interés
echo "🎯 ZONAS DE INTERÉS (SITIOS CATALÍTICOS):"
echo "Para marcar regiones importantes (sitios activos, regiones catalíticas, etc.) en los gráficos RMSF."
echo ""

while true; do
    read -p "¿Cuántas zonas de interés quieres marcar? (0 para ninguna): " NUM_ZONAS
    if [[ "$NUM_ZONAS" =~ ^[0-9]+$ ]] && [ "$NUM_ZONAS" -ge 0 ]; then
        break
    else
        echo "❌ Ingrese un número mayor o igual a 0"
    fi
done

ZONAS_PARAMETRO=""
if [ "$NUM_ZONAS" -gt 0 ]; then
    ZONAS_ARRAY=()
    for ((i=1; i<=NUM_ZONAS; i++)); do
        echo ""
        echo "Zona $i:"

        while true; do
            read -p "  Nombre de la zona (ej: Sitio_Activo, Region_Catalitica): " ZONE_NAME
            if [ -n "$ZONE_NAME" ]; then
                break
            else
                echo "❌ Ingrese un nombre válido"
            fi
        done

        while true; do
            read -p "  Rango de residuos para '$ZONE_NAME' (ej: 150-180): " ZONE_RANGE
            if [[ "$ZONE_RANGE" =~ ^[0-9]+-[0-9]+$ ]]; then
                START=$(echo $ZONE_RANGE | cut -d'-' -f1)
                END=$(echo $ZONE_RANGE | cut -d'-' -f2)
                if [ "$START" -le "$END" ] && [ "$START" -ge 1 ] && [ "$END" -le "$RESIDUOS_POR_ENZIMA" ]; then
                    ZONAS_ARRAY+=("${ZONE_NAME}:${ZONE_RANGE}")
                    echo "  ✅ Zona '$ZONE_NAME': residuos $ZONE_RANGE"
                    break
                else
                    echo "❌ El rango debe estar entre 1 y $RESIDUOS_POR_ENZIMA, y inicio ≤ fin"
                fi
            else
                echo "❌ Use formato: inicio-fin (ej: 150-180)"
            fi
        done
    done

    # Crear parámetro para script Python
    ZONAS_PARAMETRO=$(IFS=,; echo "${ZONAS_ARRAY[*]}")
    echo ""
    echo "✅ Configuradas $NUM_ZONAS zonas de interés:"
    for zona in "${ZONAS_ARRAY[@]}"; do
        echo "   - $zona"
    done
else
    echo "✅ Sin zonas de interés"
fi

echo "================================================================================"
echo ""

# Paso 1: Copiar scripts de grafiqueo si no están
echo "📋 PASO 1: VERIFICANDO Y COPIANDO SCRIPTS DE GRAFIQUEO..."
if [ ! -f "analisis_individual/enzimas/enzima1/rmsd/plot_rmsd.py" ]; then
    echo "   📁 Scripts no encontrados, copiando..."
    bash copiar_scripts_grafiqueo.sh
    echo ""
else
    echo "   ✅ Scripts ya están copiados"
    echo ""
fi

# Contadores
GRAFICOS_EXITOSOS=0
GRAFICOS_ERROR=0

# Función para ejecutar gráfico con manejo de errores
ejecutar_grafico() {
    local directorio=$1
    local script=$2
    local descripcion=$3

    echo "📊 $descripcion..."
    cd "$directorio"
    python3 "$script" > /dev/null 2>&1
    local resultado=$?

    if [ $resultado -eq 0 ]; then
        echo "   ✅ Gráfico generado exitosamente"
        ((GRAFICOS_EXITOSOS++))
    else
        echo "   ❌ Error al generar gráfico"
        ((GRAFICOS_ERROR++))
    fi

    # Regresar al directorio original
    cd - > /dev/null
    return $resultado
}

# Función especial para gráfico de comparación (permite entrada interactiva)
ejecutar_grafico_interactivo() {
    local directorio=$1
    local script=$2
    local descripcion=$3

    echo "📊 $descripcion..."
    echo "   ⚠️  Este script requiere entrada del usuario"
    cd "$directorio"
    python3 "$script"
    local resultado=$?

    if [ $resultado -eq 0 ]; then
        echo "   ✅ Gráfico generado exitosamente"
        ((GRAFICOS_EXITOSOS++))
    else
        echo "   ❌ Error al generar gráfico"
        ((GRAFICOS_ERROR++))
    fi

    # Regresar al directorio original
    cd - > /dev/null
    return $resultado
}

# Paso 2: Ejecutar gráficos de enzimas
echo "================================================================================"
echo "🧬 PASO 2: GENERANDO GRÁFICOS DE ENZIMAS"
echo "================================================================================"

ENZIMAS=$(find analisis_individual/enzimas -maxdepth 1 -type d -name "enzima*" | wc -l)
echo "Enzimas detectadas: $ENZIMAS"
echo ""

for enzima_dir in analisis_individual/enzimas/enzima*/; do
    if [ -d "$enzima_dir" ]; then
        enzima_name=$(basename "$enzima_dir")
        echo "🧬 $enzima_name:"

        # RMSD
        if [ -f "${enzima_dir}rmsd/plot_rmsd.py" ]; then
            ejecutar_grafico "${enzima_dir}rmsd" "plot_rmsd.py" "  RMSD de $enzima_name"
        fi

        # RMSF
        if [ -f "${enzima_dir}rmsf/plot_rmsf.py" ]; then
            ejecutar_grafico "${enzima_dir}rmsf" "plot_rmsf.py" "  RMSF de $enzima_name"
        fi

        # SASA
        if [ -f "${enzima_dir}sasa/plot_sasa.py" ]; then
            ejecutar_grafico "${enzima_dir}sasa" "plot_sasa.py" "  SASA de $enzima_name"
        fi

        echo ""
    fi
done

# Paso 3: Ejecutar gráficos de cápside
echo "================================================================================"
echo "🏗️ PASO 3: GENERANDO GRÁFICOS DE CÁPSIDE"
echo "================================================================================"

if [ -d "analisis_individual/capside" ]; then
    # Radio de giro
    if [ -f "analisis_individual/capside/ryg/plot_ryg.py" ]; then
        ejecutar_grafico "analisis_individual/capside/ryg" "plot_ryg.py" "Radio de giro de cápside"
    fi

    # RMSD
    if [ -f "analisis_individual/capside/rmsd/plot_rmsd.py" ]; then
        ejecutar_grafico "analisis_individual/capside/rmsd" "plot_rmsd.py" "RMSD de cápside"
    fi
else
    echo "⚠️ No se encontró directorio de cápside"
fi

echo ""

# Paso 4: Ejecutar comparación con parámetro
echo "================================================================================"
echo "📈 PASO 4: GENERANDO GRÁFICO DE COMPARACIÓN"
echo "================================================================================"

if [ -f "analisis_individual/enzimas/compara_enzimas_misma_capside.py" ]; then
    if [ -n "$ZONAS_PARAMETRO" ]; then
        echo "📊 Comparación entre enzimas (usando $RESIDUOS_POR_ENZIMA residuos, con $NUM_ZONAS zonas de interés)..."
        cd "analisis_individual/enzimas"
        python3 compara_enzimas_misma_capside.py --residues "$RESIDUOS_POR_ENZIMA" --zones "$ZONAS_PARAMETRO" > /dev/null 2>&1
        resultado=$?
        cd - > /dev/null
    else
        echo "📊 Comparación entre enzimas (usando $RESIDUOS_POR_ENZIMA residuos, sin zonas de interés)..."
        cd "analisis_individual/enzimas"
        python3 compara_enzimas_misma_capside.py --residues "$RESIDUOS_POR_ENZIMA" > /dev/null 2>&1
        resultado=$?
        cd - > /dev/null
    fi

    if [ $resultado -eq 0 ]; then
        echo "   ✅ Gráfico generado exitosamente"
        ((GRAFICOS_EXITOSOS++))
    else
        echo "   ❌ Error al generar gráfico"
        ((GRAFICOS_ERROR++))
    fi
else
    echo "⚠️ No se encontró script de comparación"
fi

echo ""

# Resumen final
echo "================================================================================"
echo "GENERACIÓN DE GRÁFICOS COMPLETADA"
echo "================================================================================"
echo "✅ Gráficos exitosos: $GRAFICOS_EXITOSOS"
echo "❌ Gráficos con errores: $GRAFICOS_ERROR"
echo ""

if [ $GRAFICOS_ERROR -eq 0 ]; then
    echo "🎉 ¡Todos los gráficos se generaron exitosamente!"
else
    echo "⚠️ Algunos gráficos tuvieron errores. Verifica los datos de entrada."
fi

echo ""
echo "📁 UBICACIÓN DE GRÁFICOS:"
echo "   - Enzimas: analisis_individual/enzimas/enzima#/{rmsd,rmsf,sasa}/"
echo "   - Cápside: analisis_individual/capside/{ryg,rmsd}/"
echo "   - Comparación: analisis_individual/enzimas/"
echo ""
echo "🔍 PARA VER ARCHIVOS GENERADOS:"
echo "   find analisis_individual -name '*.png' -o -name '*.pdf' -o -name '*.svg'"
echo ""
echo "================================================================================"