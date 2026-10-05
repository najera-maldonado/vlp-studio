#!/bin/bash
#
# run_MD.sh — protocolo SIRAH de 5 etapas para sistemas capside-*-cg-WAT
#
#   em1 (min, esqueleto restringido) -> em2 (min libre)
#   -> eq1 (5 ns NPT, todo el soluto restringido 2.4)
#   -> eq2 (25 ns NPT, esqueleto GN,GO restringido 0.24)
#   -> prod (NCHUNKS trozos de 10 ns, reiniciables; 10 trozos = 100 ns)
#
# Patron: sirah_x2.3_24-07.amber/tutorial/5 (proteina en WT4). Los .in se
# validan estaticamente con ../verificar_protocolo_md.py; no editar a mano
# sin volver a correr el verificador.
#
# Uso: run_MD.sh [engine] [system_name] [topology_file]
#   engine        : 'cuda' (pmemd.cuda, por defecto) o 'sander'
#   system_name   : nombre base (autodetectado de capside-*-cg-WAT.prmtop)
#   topology_file : por defecto system_name.prmtop
#
# Variables de entorno:
#   NCHUNKS=10    numero de trozos de produccion de 10 ns (10 -> 100 ns)
#   DRY_RUN=1     imprime los comandos sin ejecutar ni exigir archivos
#   MD_EXE=...    fuerza el ejecutable (p. ej. MD_EXE=pmemd.cuda.MPI)
#
# Reanudable: una etapa cuyo mdout ya termina en "Total wall time" y cuyo
# .ncrst existe se salta. Las semillas (ig) de cada etapa quedan en SEMILLAS.txt.

set -u

show_usage() {
    sed -n '2,27p' "$0" | sed 's/^# \{0,1\}//'
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    show_usage
    exit 0
fi

ENGINE=${1:-cuda}
NCHUNKS=${NCHUNKS:-10}
DRY_RUN=${DRY_RUN:-0}
INPUTS=(em1_WT4.in em2_WT4.in eq1_WT4.in eq2_WT4.in prod_md_WT4.in)

auto_detect_system() {
    local detected=( $(ls capside-*-cg-WAT.prmtop 2>/dev/null) )
    if [ ${#detected[@]} -eq 0 ]; then
        echo "No se encontro ningun capside-*-cg-WAT.prmtop en el directorio actual" >&2
        return 1
    elif [ ${#detected[@]} -gt 1 ]; then
        echo "Hay varios capside-*-cg-WAT.prmtop; indica el sistema como 2o argumento:" >&2
        printf '  %s\n' "${detected[@]}" >&2
        return 1
    fi
    echo "${detected[0]%.prmtop}"
}

if [ -n "${2:-}" ]; then
    NAME="$2"
elif [ "$DRY_RUN" = "1" ]; then
    NAME="capside-DRY-cg-WAT"
else
    NAME=$(auto_detect_system) || exit 1
    echo "Sistema autodetectado: $NAME"
fi
PRMTOP=${3:-${NAME}.prmtop}

if [ -z "${MD_EXE:-}" ]; then
    case "$ENGINE" in
        cuda)   MD_EXE="pmemd.cuda" ;;
        sander) MD_EXE="sander" ;;
        *) echo "Error: engine debe ser 'cuda' o 'sander' (recibido: $ENGINE)"; exit 1 ;;
    esac
fi
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"

# ---------- validacion de archivos (se omite en DRY_RUN) ----------
COORD_FILE="${NAME}.ncrst"
if [ "$DRY_RUN" != "1" ]; then
    if [ ! -f "$PRMTOP" ]; then
        echo "Error: no existe la topologia $PRMTOP"; exit 1
    fi
    if [ ! -f "$COORD_FILE" ]; then
        for ext in rst rst7 inpcrd; do
            [ -f "${NAME}.${ext}" ] && COORD_FILE="${NAME}.${ext}" && break
        done
        [ -f "$COORD_FILE" ] || { echo "Error: no existen coordenadas iniciales ${NAME}.ncrst"; exit 1; }
    fi
    for f in "${INPUTS[@]}"; do
        [ -f "$f" ] || { echo "Error: falta el archivo de entrada $f"; exit 1; }
    done
fi

echo "Protocolo SIRAH (em1 -> em2 -> eq1 5 ns -> eq2 25 ns -> prod ${NCHUNKS} x 10 ns)"
echo "  Motor:       $MD_EXE"
echo "  Sistema:     $NAME"
echo "  Topologia:   $PRMTOP"
echo "  Coordenadas: $COORD_FILE"
[ "$DRY_RUN" = "1" ] && echo "  (DRY_RUN: solo se imprimen los comandos)"
echo ""

# ---------- utilidades ----------
stage_done() {   # stage_done <out> <ncrst>
    [ -f "$1" ] && [ -f "$2" ] && grep -q "Total wall time" "$1"
}

leer_ig() {      # leer_ig <archivo.in>  -> valor de ig
    sed -nE 's/.*[[:space:]]ig[[:space:]]*=[[:space:]]*(-?[0-9]+).*/\1/p' "$1" | head -1
}

anotar_semilla() {  # anotar_semilla <etapa> <input> <ig>
    if [ "$DRY_RUN" = "1" ]; then
        echo "  [semilla] $1 ($2): ig = $3"
    else
        printf '%s\t%s\t%s\n' "$1" "$2" "$3" >> SEMILLAS.txt
    fi
}

run_stage() {    # run_stage <etiqueta> <input> <coords> <ref|-> <traj|->
    local label=$1 input=$2 coords=$3 ref=$4 traj=$5
    local out="${NAME}_${label}.out" rst="${NAME}_${label}.ncrst"
    local cmd=( "$MD_EXE" -O -i "$input" -p "$PRMTOP" -c "$coords" )
    [ "$ref" != "-" ]  && cmd+=( -ref "$ref" )
    cmd+=( -o "$out" -r "$rst" )
    [ "$traj" != "-" ] && cmd+=( -x "$traj" )

    echo "=== Etapa $label ==="
    if [ "$DRY_RUN" = "1" ]; then
        echo "  ${cmd[*]}"
        return 0
    fi
    if stage_done "$out" "$rst"; then
        echo "  ya completada ($out termina en 'Total wall time'); se salta"
        return 0
    fi
    "${cmd[@]}" || { echo "Error en la etapa $label (ver $out)"; exit 1; }
    echo "  completada"
}

# ---------- 1-2: minimizaciones ----------
run_stage em1 em1_WT4.in "$COORD_FILE"      "$COORD_FILE"      -
run_stage em2 em2_WT4.in "${NAME}_em1.ncrst" -                 -

# ---------- 3-4: equilibracion NPT con restricciones (2.4 -> 0.24) ----------
if [ "$DRY_RUN" != "1" ]; then
    [ -f SEMILLAS.txt ] || printf 'etapa\tinput\tig\n' > SEMILLAS.txt
    anotar_semilla eq1 eq1_WT4.in "$(leer_ig eq1_WT4.in)"
    anotar_semilla eq2 eq2_WT4.in "$(leer_ig eq2_WT4.in)"
fi
run_stage eq1 eq1_WT4.in "${NAME}_em2.ncrst" "${NAME}_em2.ncrst" "${NAME}_eq1.nc"
run_stage eq2 eq2_WT4.in "${NAME}_eq1.ncrst" "${NAME}_eq1.ncrst" "${NAME}_eq2.nc"

# ---------- 5: produccion en trozos de 10 ns, semilla distinta por trozo ----------
# Con irest=1 y Langevin cada trozo vuelve a sembrar el generador; por eso cada
# trozo lleva un ig propio (100100 + k) y queda anotado en SEMILLAS.txt.
prev="${NAME}_eq2.ncrst"
for (( k=1; k<=NCHUNKS; k++ )); do
    kk=$(printf '%02d' "$k")
    ig=$((100100 + k))
    input="prod_md_WT4_k${kk}.in"
    if [ "$DRY_RUN" = "1" ]; then
        echo "  [gen] $input <- prod_md_WT4.in con ig = $ig"
    else
        sed -E "s/^([[:space:]]*.*[[:space:]]ig[[:space:]]*=[[:space:]]*)-?[0-9]+,/\1${ig},/" prod_md_WT4.in > "$input"
        [ "$(leer_ig "$input")" = "$ig" ] || { echo "Error: no se pudo fijar ig=$ig en $input"; exit 1; }
    fi
    anotar_semilla "prod_k${kk}" "$input" "$ig"
    run_stage "prod_k${kk}" "$input" "$prev" - "${NAME}_prod_k${kk}.nc"
    prev="${NAME}_prod_k${kk}.ncrst"
done

echo ""
echo "=== Protocolo completo ==="
echo "  Minimizacion:  ${NAME}_em1.out, ${NAME}_em2.out"
echo "  Equilibracion: ${NAME}_eq1.{out,nc} (5 ns), ${NAME}_eq2.{out,nc} (25 ns)"
echo "  Produccion:    ${NAME}_prod_k01..k$(printf '%02d' "$NCHUNKS").{out,nc} ($((NCHUNKS * 10)) ns)"
echo "  Semillas:      SEMILLAS.txt"
echo "  Coordenadas finales: $prev"
