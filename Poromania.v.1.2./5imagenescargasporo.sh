#!/usr/bin/env bash
# Ejecuta foto_poro.pml en cada carpeta cargas_apbs de los mutantes
# Autor: Lucio el Incansable

set -euo pipefail

PML="foto_poro.pml"
BASE="mutants"

[[ -f "$PML" ]] || { echo "❌ No se encontró $PML"; exit 1; }

for dir in "$BASE"/mut_*/cargas_apbs; do
  if [[ ! -d "$dir" ]]; then
    echo "⏩ $dir no existe, se omite."
    continue
  fi

  pqr=("$dir"/*.pqr)
  dx=("$dir"/*_pot-PE0.dx)

  if [[ ! -f "${pqr[0]}" || ! -f "${dx[0]}" ]]; then
    echo "⚠️  Sin .pqr o .dx en $dir, se omite."
    continue
  fi

  echo "📸 Procesando $(basename "$(dirname "$dir")")"

  cp "$PML" "$dir/"
  (cd "$dir" && pymol -cq foto_poro.pml || echo "❌ Error en $dir")
done

echo "✅ Terminado: imágenes generadas en cada snap/"
