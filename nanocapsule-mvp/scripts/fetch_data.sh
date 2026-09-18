#!/usr/bin/env bash
# fetch_data.sh — descarga las estructuras pesadas que NO viajan en el repo.
#
# La biblioteca por defecto (BMV, CCMV, MS2, QB + enzimas) SÍ está commiteada y el Studio
# arranca sin esto. Pero la cápside P22 (RCSB 5UU5) pesa >100 MB y está gitignoreada, así
# que Pac-Pore / el empaquetado con P22 necesitan bajarla con este script.
#
# Uso:   ./scripts/fetch_data.sh            (desde nanocapsule-mvp/)
# Requiere: curl o wget.
set -euo pipefail

# Directorio del Studio (padre de scripts/), para que funcione desde cualquier cwd.
STUDIO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CAPSIDES="$STUDIO_DIR/Input/Capsides"

# Estructuras pesadas: "carpeta destino : PDB ID". Añade más aquí si hace falta.
STRUCTURES=(
  "P22_5UU5:5UU5"
)

download() {  # $1 = url, $2 = destino
  if command -v curl >/dev/null 2>&1; then
    curl -fSL "$1" -o "$2"
  elif command -v wget >/dev/null 2>&1; then
    wget -O "$2" "$1"
  else
    echo "ERROR: se necesita curl o wget." >&2; exit 1
  fi
}

for entry in "${STRUCTURES[@]}"; do
  folder="${entry%%:*}"; pdbid="${entry##*:}"
  dest_dir="$CAPSIDES/$folder"
  dest="$dest_dir/capside.pdb"

  if [ -f "$dest" ]; then
    echo "✓ $folder ya existe ($dest) — se omite."
    continue
  fi

  mkdir -p "$dest_dir"
  echo "↓ Descargando $pdbid (ensamblaje biológico) → $dest ..."
  # Ensamblaje biológico 1 (cápside completa), comprimido; si falla, unidad asimétrica.
  if download "https://files.rcsb.org/download/${pdbid}.pdb1.gz" "$dest.gz"; then
    gunzip -f "$dest.gz"
  else
    echo "  (ensamblaje no disponible; bajando unidad asimétrica ${pdbid}.pdb)"
    download "https://files.rcsb.org/download/${pdbid}.pdb" "$dest"
  fi
  echo "✓ $folder listo."
done

echo "Hecho. Estructuras pesadas en $CAPSIDES/."
