#!/bin/bash
# Ejecutor PARALELO con MONITOREO DE PROGRESO EN TIEMPO REAL
# Muestra el progreso de cada enzima y cápside individualmente

NCPUS=$(nproc)
echo "================================================================================"
echo "EJECUTANDO ANÁLISIS EN PARALELO CON MONITOREO DE PROGRESO"
echo "Núcleos disponibles: $NCPUS"
echo "================================================================================"

# Verificar directorios
if [ ! -d "analisis_individual" ]; then
    echo "❌ Error: No existe el directorio analisis_individual"
    exit 1
fi

# Crear directorio temporal para archivos de estado
TEMP_DIR="/tmp/cpptraj_progress_$$"
mkdir -p "$TEMP_DIR"

# Función para ejecutar análisis con monitoreo
ejecutar_con_progreso() {
    local tipo=$1
    local directorio=$2
    local enzima_name=$3
    local job_id=$4

    local log_file="${TEMP_DIR}/${enzima_name}_${tipo}.log"
    local status_file="${TEMP_DIR}/${enzima_name}_${tipo}.status"
    local progress_file="${TEMP_DIR}/${enzima_name}_${tipo}.progress"

    echo "INICIANDO" > "$status_file"
    echo "0" > "$progress_file"

    cd "$directorio"

    # Ejecutar cpptraj con output a log
    cpptraj -i "${tipo}.cpptraj" > "$log_file" 2>&1 &
    local cpptraj_pid=$!

    # Monitorear progreso en background
    (
        while kill -0 $cpptraj_pid 2>/dev/null; do
            # Extraer último porcentaje del log
            if [ -f "$log_file" ]; then
                # Buscar líneas con porcentajes: "10% 20% 30%..." o "Complete"
                local ultimo_porcentaje=$(grep -o '[0-9]\+%\|Complete' "$log_file" | tail -1)
                if [ -n "$ultimo_porcentaje" ]; then
                    if [ "$ultimo_porcentaje" = "Complete" ]; then
                        echo "100" > "$progress_file"
                    else
                        echo "${ultimo_porcentaje%\%}" > "$progress_file"
                    fi
                fi
            fi
            sleep 0.5
        done

        wait $cpptraj_pid
        local resultado=$?

        if [ $resultado -eq 0 ]; then
            echo "COMPLETADO" > "$status_file"
            echo "100" > "$progress_file"
        else
            echo "ERROR" > "$status_file"
            echo "-1" > "$progress_file"
        fi
    ) &

    cd - > /dev/null
    wait $cpptraj_pid
    return $?
}

# Preparar lista de trabajos
TRABAJOS=()
declare -A JOB_INFO

# Detectar enzimas
ENZIMAS=$(find analisis_individual/enzimas -maxdepth 1 -type d -name "enzima*" | sort)
NUM_ENZIMAS=$(echo "$ENZIMAS" | wc -l)

echo "🧬 Preparando $NUM_ENZIMAS enzimas..."

JOB_ID=1
for enzima_dir in $ENZIMAS; do
    if [ -d "$enzima_dir" ]; then
        enzima_name=$(basename "$enzima_dir")

        for tipo in rmsf sasa rmsd; do
            if [ -d "${enzima_dir}/${tipo}" ]; then
                TRABAJOS+=("$tipo ${enzima_dir}/${tipo} ${enzima_name} $JOB_ID")
                JOB_INFO["${enzima_name}_${tipo}"]="$JOB_ID"
                ((JOB_ID++))
            fi
        done
    fi
done

# Agregar cápside
if [ -d "analisis_individual/capside/ryg" ]; then
    TRABAJOS+=("ryg analisis_individual/capside/ryg capside $JOB_ID")
    JOB_INFO["capside_ryg"]="$JOB_ID"
    ((JOB_ID++))
fi

if [ -d "analisis_individual/capside/rmsd" ]; then
    TRABAJOS+=("rmsd analisis_individual/capside/rmsd capside $JOB_ID")
    JOB_INFO["capside_rmsd"]="$JOB_ID"
    ((JOB_ID++))
fi

echo "📋 Total trabajos: ${#TRABAJOS[@]}"
echo ""

# Ejecutar trabajos en paralelo
echo "🚀 INICIANDO ANÁLISIS PARALELO..."
echo "================================================================================"

TRABAJOS_ACTIVOS=0
declare -a PIDS_ACTIVOS

for trabajo in "${TRABAJOS[@]}"; do
    # Parsear trabajo
    IFS=' ' read -r tipo directorio enzima_name job_id <<< "$trabajo"

    # Esperar si tenemos el máximo de trabajos
    while [ $TRABAJOS_ACTIVOS -ge $NCPUS ]; do
        # Verificar trabajos terminados
        for i in "${!PIDS_ACTIVOS[@]}"; do
            if ! kill -0 "${PIDS_ACTIVOS[i]}" 2>/dev/null; then
                unset PIDS_ACTIVOS[i]
                ((TRABAJOS_ACTIVOS--))
            fi
        done
        PIDS_ACTIVOS=("${PIDS_ACTIVOS[@]}")  # Reindexar array
        sleep 0.1
    done

    # Ejecutar nuevo trabajo
    ejecutar_con_progreso "$tipo" "$directorio" "$enzima_name" "$job_id" &
    PIDS_ACTIVOS+=($!)
    ((TRABAJOS_ACTIVOS++))

    echo "🔄 Iniciado: $enzima_name $tipo [Job $job_id]"
    sleep 0.1
done

echo ""
echo "⏳ MONITOREANDO PROGRESO..."
echo "================================================================================"

# Monitor de progreso en tiempo real
mostrar_progreso() {
    clear
    echo "================================================================================"
    echo "                    PROGRESO DE ANÁLISIS EN TIEMPO REAL"
    echo "================================================================================"
    echo "Núcleos usados: $NCPUS | $(date '+%H:%M:%S')"
    echo ""

    # Mostrar enzimas
    for enzima_dir in $ENZIMAS; do
        if [ -d "$enzima_dir" ]; then
            enzima_name=$(basename "$enzima_dir")
            echo "🧬 $enzima_name:"

            for tipo in rmsd rmsf sasa; do
                if [ -f "${TEMP_DIR}/${enzima_name}_${tipo}.progress" ]; then
                    local progreso=$(cat "${TEMP_DIR}/${enzima_name}_${tipo}.progress" 2>/dev/null || echo "0")
                    local status=$(cat "${TEMP_DIR}/${enzima_name}_${tipo}.status" 2>/dev/null || echo "PENDIENTE")

                    if [ "$progreso" = "-1" ]; then
                        printf "   %-6s: ❌ ERROR\n" "$tipo"
                    elif [ "$status" = "COMPLETADO" ]; then
                        printf "   %-6s: ✅ 100%%\n" "$tipo"
                    elif [ "$progreso" -gt 0 ]; then
                        local barra=$(crear_barra_progreso $progreso)
                        printf "   %-6s: %s %3s%%\n" "$tipo" "$barra" "$progreso"
                    else
                        printf "   %-6s: ⏳ Iniciando...\n" "$tipo"
                    fi
                fi
            done
            echo ""
        fi
    done

    # Mostrar cápside
    echo "🏗️ Cápside:"
    for tipo in ryg rmsd; do
        if [ -f "${TEMP_DIR}/capside_${tipo}.progress" ]; then
            local progreso=$(cat "${TEMP_DIR}/capside_${tipo}.progress" 2>/dev/null || echo "0")
            local status=$(cat "${TEMP_DIR}/capside_${tipo}.status" 2>/dev/null || echo "PENDIENTE")

            if [ "$progreso" = "-1" ]; then
                printf "   %-6s: ❌ ERROR\n" "$tipo"
            elif [ "$status" = "COMPLETADO" ]; then
                printf "   %-6s: ✅ 100%%\n" "$tipo"
            elif [ "$progreso" -gt 0 ]; then
                local barra=$(crear_barra_progreso $progreso)
                printf "   %-6s: %s %3s%%\n" "$tipo" "$barra" "$progreso"
            else
                printf "   %-6s: ⏳ Iniciando...\n" "$tipo"
            fi
        fi
    done

    echo ""
    echo "================================================================================"
}

# Función para crear barra de progreso visual
crear_barra_progreso() {
    local porcentaje=$1
    local ancho=20
    local completado=$((porcentaje * ancho / 100))
    local restante=$((ancho - completado))

    local barra="["
    for ((i=0; i<completado; i++)); do barra+="█"; done
    for ((i=0; i<restante; i++)); do barra+="░"; done
    barra+="]"

    echo "$barra"
}

# Exportar función para uso en subshells
export -f crear_barra_progreso

# Loop de monitoreo
while [ $TRABAJOS_ACTIVOS -gt 0 ]; do
    mostrar_progreso

    # Verificar trabajos terminados
    for i in "${!PIDS_ACTIVOS[@]}"; do
        if ! kill -0 "${PIDS_ACTIVOS[i]}" 2>/dev/null; then
            unset PIDS_ACTIVOS[i]
            ((TRABAJOS_ACTIVOS--))
        fi
    done
    PIDS_ACTIVOS=("${PIDS_ACTIVOS[@]}")  # Reindexar

    sleep 1
done

# Mostrar resultado final
clear
mostrar_progreso

echo ""
echo "🎉 ¡TODOS LOS ANÁLISIS COMPLETADOS!"
echo ""

# Contar resultados
EXITOSOS=0
ERRORES=0

for enzima_dir in $ENZIMAS; do
    if [ -d "$enzima_dir" ]; then
        enzima_name=$(basename "$enzima_dir")
        for tipo in rmsd rmsf sasa; do
            if [ -f "${TEMP_DIR}/${enzima_name}_${tipo}.status" ]; then
                local status=$(cat "${TEMP_DIR}/${enzima_name}_${tipo}.status")
                if [ "$status" = "COMPLETADO" ]; then
                    ((EXITOSOS++))
                else
                    ((ERRORES++))
                fi
            fi
        done
    fi
done

for tipo in ryg rmsd; do
    if [ -f "${TEMP_DIR}/capside_${tipo}.status" ]; then
        local status=$(cat "${TEMP_DIR}/capside_${tipo}.status")
        if [ "$status" = "COMPLETADO" ]; then
            ((EXITOSOS++))
        else
            ((ERRORES++))
        fi
    fi
done

echo "📊 RESUMEN FINAL:"
echo "   ✅ Exitosos: $EXITOSOS"
echo "   ❌ Errores: $ERRORES"
echo ""

if [ $ERRORES -eq 0 ]; then
    echo "🔄 SIGUIENTE PASO:"
    echo "   bash ejecutar_todos_graficos.sh"
fi

# Limpiar archivos temporales
rm -rf "$TEMP_DIR"

echo "================================================================================"