#!/bin/bash

# Script Interactivo de Configuración de Simulaciones MD con SIRAH Coarse-Grained
# Genera archivos de entrada personalizados basados en las preferencias del usuario

echo "======================================================="
echo "  Configuración de Simulaciones MD SIRAH Coarse-Grained"
echo "======================================================="
echo ""

# Función para validar números positivos
validate_positive() {
    local value=$1
    if [[ $value =~ ^[0-9]+\.?[0-9]*$ ]] && (( $(echo "$value > 0" | bc -l) )); then
        return 0
    else
        return 1
    fi
}

# Función para validar enteros
validate_integer() {
    local value=$1
    if [[ $value =~ ^[0-9]+$ ]]; then
        return 0
    else
        return 1
    fi
}

# Temperatura
echo "1. CONFIGURACIÓN DE TEMPERATURA"
echo "-------------------------------"
echo "La temperatura controla la energía cinética de las partículas en su simulación."
echo "Valores comunes:"
echo "  • 300K (27°C): Temperatura ambiente, estándar para la mayoría de simulaciones"
echo "  • 310K (37°C): Temperatura fisiológica (cuerpo humano)"
echo "  • 277K (4°C): Condiciones de almacenamiento en frío"
echo "  • 323K (50°C): Temperatura elevada para muestreo mejorado"
echo ""
while true; do
    read -p "Temperatura objetivo (K) [predeterminado: 300]: " TEMP
    TEMP=${TEMP:-300}
    if validate_positive "$TEMP"; then
        break
    else
        echo "Error: Por favor ingrese un número positivo para la temperatura"
    fi
done

# Parámetros de Minimización
echo ""
echo "2. PARÁMETROS DE MINIMIZACIÓN"
echo "----------------------------"
echo "La minimización de energía elimina contactos malos y conformaciones de alta energía"
echo "antes de iniciar la simulación MD. Esto previene caídas del sistema."
echo ""
echo "Ciclos máximos: Número de pasos de optimización para encontrar el mínimo de energía."
echo "Más ciclos = mejor relajación pero mayor tiempo de cómputo."
echo ""
while true; do
    read -p "Ciclos máximos de minimización [predeterminado: 5000]: " MAXCYC
    MAXCYC=${MAXCYC:-5000}
    if validate_integer "$MAXCYC"; then
        break
    else
        echo "Error: Por favor ingrese un entero positivo"
    fi
done

echo ""
echo "Peso de restricción: Fuerza aplicada para mantener ciertos átomos en su lugar durante"
echo "la minimización. Valores mayores = restricciones más fuertes."
echo "  • 2.4 kcal/mol·Å²: Estándar para SIRAH coarse-grained"
echo "  • 5.0 kcal/mol·Å²: Restricciones fuertes para sistemas inestables"
echo "  • 1.0 kcal/mol·Å²: Restricciones débiles para sistemas flexibles"
echo ""
while true; do
    read -p "Peso inicial de restricción (kcal/mol·Å²) [predeterminado: 2.4]: " REST_WEIGHT_INIT
    REST_WEIGHT_INIT=${REST_WEIGHT_INIT:-2.4}
    if validate_positive "$REST_WEIGHT_INIT"; then
        break
    else
        echo "Error: Por favor ingrese un número positivo"
    fi
done

# Parámetros de Equilibración
echo ""
echo "3. PARÁMETROS DE EQUILIBRACIÓN"
echo "-----------------------------"
echo "La equilibración adapta gradualmente el sistema a las condiciones de simulación."
echo "La equilibración en dos fases asegura dinámicas estables:"
echo ""
echo "Fase 1: Equilibración restringida - toda la proteína mantenida en su lugar"
echo "        mientras el solvente e iones se adaptan. Previene deformación de la proteína."
echo "  • 5 ns: Estándar para proteínas pequeñas-medianas"
echo "  • 10 ns: Recomendado para complejos grandes como cápsides"
echo ""
while true; do
    read -p "Tiempo de equilibración 1 (ns) [predeterminado: 5]: " EQ1_TIME
    EQ1_TIME=${EQ1_TIME:-5}
    if validate_positive "$EQ1_TIME"; then
        break
    else
        echo "Error: Por favor ingrese un número positivo"
    fi
done

echo ""
echo "Fase 2: Equilibración relajada - solo esqueleto restringido"
echo "        permite que cadenas laterales y bucles se muevan libremente."
echo "  • 25 ns: Estándar para simulaciones coarse-grained"
echo "  • 50 ns: Para sistemas muy grandes o complejos"
echo ""
while true; do
    read -p "Tiempo de equilibración 2 (ns) [predeterminado: 25]: " EQ2_TIME
    EQ2_TIME=${EQ2_TIME:-25}
    if validate_positive "$EQ2_TIME"; then
        break
    else
        echo "Error: Por favor ingrese un número positivo"
    fi
done

echo ""
echo "Peso final de restricción: Restricciones más débiles para la equilibración fase 2."
echo "  • 0.24 kcal/mol·Å²: Estándar para SIRAH (10x más débil que el inicial)"
echo "  • 0.1 kcal/mol·Å²: Restricciones muy débiles"
echo "  • 0.5 kcal/mol·Å²: Restricciones más fuertes para sistemas inestables"
echo ""
while true; do
    read -p "Peso final de restricción (kcal/mol·Å²) [predeterminado: 0.24]: " REST_WEIGHT_FINAL
    REST_WEIGHT_FINAL=${REST_WEIGHT_FINAL:-0.24}
    if validate_positive "$REST_WEIGHT_FINAL"; then
        break
    else
        echo "Error: Por favor ingrese un número positivo"
    fi
done

# Parámetros de Producción
echo ""
echo "4. PARÁMETROS DE PRODUCCIÓN"
echo "--------------------------"
echo "Simulación de producción: Los datos reales de simulación que analizará."
echo "Sin restricciones - el sistema evoluciona libremente bajo fuerzas físicas."
echo ""
echo "La duración depende de su pregunta de investigación:"
echo "  • 100 ns: Estándar para dinámicas y estabilidad de proteínas"
echo "  • 500 ns: Cambios conformacionales y eventos de unión"
echo "  • 1000 ns (1 μs): Procesos lentos, transiciones alostéricas"
echo "  • 10 ns: Simulaciones de prueba rápidas o sistemas muy grandes"
echo ""
echo "Nota: SIRAH coarse-grained permite escalas de tiempo 4x más largas que all-atom"
echo ""
while true; do
    read -p "Tiempo de producción (ns) [predeterminado: 100]: " PROD_TIME
    PROD_TIME=${PROD_TIME:-100}
    if validate_positive "$PROD_TIME"; then
        break
    else
        echo "Error: Por favor ingrese un número positivo"
    fi
done

# Acoplamiento de presión
echo ""
echo "5. ACOPLAMIENTO DE PRESIÓN"
echo "-------------------------"
echo "Controla cómo responde la caja de simulación a la presión:"
echo ""
echo "1) NPT (Isotérmico-Isobárico): Temperatura y presión constantes"
echo "   • El volumen de la caja puede cambiar para mantener presión de 1 atm"
echo "   • Imita condiciones experimentales (más realista)"
echo "   • Recomendado para la mayoría de simulaciones biológicas"
echo ""
echo "2) NVT (Canónico): Temperatura y volumen constantes"
echo "   • Tamaño de caja fijo, la presión puede fluctuar"
echo "   • Útil para cálculos de densidad o sistemas confinados"
echo "   • Menos común para simulaciones de proteínas"
echo ""
while true; do
    read -p "Elija acoplamiento de presión [1-2, predeterminado: 1]: " PRESSURE_OPT
    PRESSURE_OPT=${PRESSURE_OPT:-1}
    if [[ "$PRESSURE_OPT" == "1" || "$PRESSURE_OPT" == "2" ]]; then
        break
    else
        echo "Error: Por favor elija 1 o 2"
    fi
done

# Frecuencia de salida
echo ""
echo "6. CONFIGURACIÓN DE SALIDA"
echo "-------------------------"
echo "Qué tan frecuentemente guardar instantáneas de simulación en archivos de trayectoria."
echo "Balance entre resolución de datos y tamaño de archivo:"
echo ""
echo "  • 100 ps (5000 pasos): Estándar para análisis, buena resolución temporal"
echo "  • 200 ps (10000 pasos): Archivos menores, adecuado para la mayoría de análisis"
echo "  • 50 ps (2500 pasos): Alta resolución para dinámicas detalladas"
echo "  • 500 ps (25000 pasos): Sistemas muy grandes, solo análisis básico"
echo ""
echo "Nota: Los archivos de trayectoria pueden volverse muy grandes con altas frecuencias"
echo ""
while true; do
    read -p "Frecuencia de salida (ps) [predeterminado: 100]: " OUTPUT_FREQ
    OUTPUT_FREQ=${OUTPUT_FREQ:-100}
    if validate_positive "$OUTPUT_FREQ"; then
        break
    else
        echo "Error: Por favor ingrese un número positivo"
    fi
done

# Selección GPU/CPU
echo ""
echo "7. CONFIGURACIÓN COMPUTACIONAL"
echo "-----------------------------"
echo "Elija motor computacional para la simulación MD:"
echo ""
echo "1) pmemd.cuda (aceleración GPU)"
echo "   • 10-50x más rápido que CPU para la mayoría de sistemas"
echo "   • Requiere GPU NVIDIA con soporte CUDA"
echo "   • Recomendado para simulaciones de producción"
echo "   • Limitado por memoria RAM de GPU"
echo ""
echo "2) sander (CPU)"
echo "   • Más lento pero funciona en cualquier sistema"
echo "   • Útil para pruebas o cuando GPU no disponible"
echo "   • Puede usar RAM del sistema para sistemas muy grandes"
echo "   • Bueno para depuración"
echo ""
while true; do
    read -p "Elija motor [1-2, predeterminado: 1]: " ENGINE_OPT
    ENGINE_OPT=${ENGINE_OPT:-1}
    if [[ "$ENGINE_OPT" == "1" || "$ENGINE_OPT" == "2" ]]; then
        break
    else
        echo "Error: Por favor elija 1 o 2"
    fi
done

if [[ "$ENGINE_OPT" == "1" ]]; then
    echo ""
    echo "Selección de dispositivo GPU (use nvidia-smi para ver GPUs disponibles):"
    echo "  • 0: Primera GPU (más común)"
    echo "  • 1,2,3...: GPUs adicionales si están disponibles"
    echo ""
    while true; do
        read -p "ID de dispositivo GPU [predeterminado: 0]: " GPU_ID
        GPU_ID=${GPU_ID:-0}
        if validate_integer "$GPU_ID"; then
            break
        else
            echo "Error: Por favor ingrese un ID de GPU válido (entero)"
        fi
    done
fi

# Calcular pasos desde tiempos (SIRAH usa timestep de 20 fs)
EQ1_STEPS=$(echo "$EQ1_TIME * 1000000 / 20" | bc)
EQ2_STEPS=$(echo "$EQ2_TIME * 1000000 / 20" | bc)
PROD_STEPS=$(echo "$PROD_TIME * 1000000 / 20" | bc)
OUTPUT_STEPS=$(echo "$OUTPUT_FREQ * 1000 / 20" | bc)

# Establecer parámetros de presión
if [[ "$PRESSURE_OPT" == "1" ]]; then
    NTB=2
    NTP=1
    PRES0="1.0"
else
    NTB=1
    NTP=0
    PRES0=""
fi

# Establecer motor
if [[ "$ENGINE_OPT" == "1" ]]; then
    ENGINE="cuda"
    MD_EXE="pmemd.cuda"
else
    ENGINE="sander"
    MD_EXE="sander"
fi

echo ""
echo "======================================================="
echo "  GENERANDO ARCHIVOS DE ENTRADA"
echo "======================================================="

# Validar/crear directorio de destino
if [ ! -d "archivos_dm_cg" ]; then
    mkdir -p archivos_dm_cg
    echo "✓ Creado directorio archivos_dm_cg/"
fi

# Generar entrada de minimización 1
cat > "archivos_dm_cg/em1_WT4.in" << EOF
Minimización 1
&cntrl
  imin = 1,
  maxcyc = $MAXCYC, ntmin=1, ncyc = 100, ntpr = 50, ntxo=2,

  ntb = 1, ntp = 0,
  cut = 12,

  ntr = 1,
  restraint_wt=$REST_WEIGHT_INIT,
  restraintmask='@GN,GO',

&end
EOF

echo "✓ Generado archivos_dm_cg/em1_WT4.in"

# Generar entrada de minimización 2 (sin restricciones para relajación completa)
cat > "archivos_dm_cg/em2_WT4.in" << EOF
Minimización 2
&cntrl
  imin = 1,
  maxcyc = $MAXCYC, ntmin=1, ncyc = 100, ntpr = 50, ntxo=2,

  ntb = 1, ntp = 0,
  cut = 12,

&end
EOF

echo "✓ Generado archivos_dm_cg/em2_WT4.in"

# Generar entrada de equilibración 1
cat > "archivos_dm_cg/eq1_WT4.in" << EOF
SIRAH Proteína: ${EQ1_TIME}ns equilibración NPT (proteína completa)
 &cntrl
  imin = 0, ntx = 1, irest = 0,

  nstlim = $EQ1_STEPS, dt = 0.020,
  ntpr = $OUTPUT_STEPS, ntwx = $OUTPUT_STEPS, ntwr = $OUTPUT_STEPS, ioutfm=1, ntxo=2,

  ntb = $NTB, ntp = $NTP, ${PRES0:+pres0 = $PRES0,}

  ntt = 3, gamma_ln = 5.0, ig = -1,
  temp0 = $TEMP.0, tempi = 0.0,

  ntc = 1, ntf = 1,

  cut = 12.0, nrespa = 1,

  ntr = 1,
  restraint_wt=$REST_WEIGHT_INIT,
  restraintmask=':*&!@H=',  ! Todos los átomos pesados

 &end

 &ewald
  chngmask=0,
 &end
EOF

echo "✓ Generado archivos_dm_cg/eq1_WT4.in"

# Generar entrada de equilibración 2
cat > "archivos_dm_cg/eq2_WT4.in" << EOF
SIRAH Proteína: ${EQ2_TIME}ns equilibración NPT (esqueleto)
 &cntrl
  imin = 0, ntx = 1, irest = 0,

  nstlim = $EQ2_STEPS, dt = 0.020,
  ntpr = $OUTPUT_STEPS, ntwx = $OUTPUT_STEPS, ntwr = $OUTPUT_STEPS, ioutfm=1, ntxo=2,

  ntb = $NTB, ntp = $NTP, ${PRES0:+pres0 = $PRES0,}

  ntt = 3, gamma_ln = 5.0, ig = -1,
  temp0 = $TEMP.0, tempi = $TEMP.0,

  ntc = 1, ntf = 1,

  cut = 12.0, nrespa = 1,

  ntr = 1,
  restraint_wt=$REST_WEIGHT_FINAL,
  restraintmask='@GN,GO',  ! Solo beads backbone SIRAH

 &end

 &ewald
  chngmask=0,
 &end
EOF

echo "✓ Generado archivos_dm_cg/eq2_WT4.in"

# Generar entrada de producción
cat > "archivos_dm_cg/prod_md_WT4.in" << EOF
SIRAH Proteína: ${PROD_TIME}ns producción
 &cntrl
  imin = 0, ntx = 5, irest = 1,

  nstlim = $PROD_STEPS, dt = 0.020,
  ntpr = $OUTPUT_STEPS, ntwx = $OUTPUT_STEPS, ntwr = $OUTPUT_STEPS, ioutfm=1, ntxo=2,

  ntb = $NTB, ntp = $NTP, ${PRES0:+pres0 = $PRES0,}

  ntt = 3, gamma_ln = 5.0, ig = -1,
  temp0 = $TEMP.0, tempi = $TEMP.0,

  ntc = 1, ntf = 1,

  cut = 12.0, nrespa = 1,

  ntr = 0,

 &end

 &ewald
  chngmask=0,
 &end
EOF

echo "✓ Generado archivos_dm_cg/prod_md_WT4.in"

echo ""
echo "======================================================="
echo "  ¡CONFIGURACIÓN COMPLETA!"
echo "======================================================="
echo ""
echo "Archivos generados en archivos_dm_cg/:"
echo "  • em1_WT4.in - Minimización 1"
echo "  • em2_WT4.in - Minimización 2"
echo "  • eq1_WT4.in - Equilibración 1 (${EQ1_TIME} ns)"
echo "  • eq2_WT4.in - Equilibración 2 (${EQ2_TIME} ns)"
echo "  • prod_md_WT4.in - Producción (${PROD_TIME} ns)"
echo ""
echo "Parámetros configurados:"
echo "  • Temperatura: $TEMP K"
echo "  • Tiempo total simulación: $(echo "$EQ1_TIME + $EQ2_TIME + $PROD_TIME" | bc) ns"
echo "  • Motor: $MD_EXE"
echo "  • Ensamble: $(if [[ "$PRESSURE_OPT" == "1" ]]; then echo "NPT"; else echo "NVT"; fi)"