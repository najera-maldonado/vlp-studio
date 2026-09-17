#!/usr/bin/env bash
# correrhole.sh – ejecuta el pipeline desde scripts/ en cada mutante

set -e
set -u
set -o pipefail

BASE="mutants"

for dir in "${BASE}"/mut_*; do
    [ -d "$dir" ] || continue

    (
      cd "$dir" || exit 1

      # Verifica que scripts/ existe y contiene el script esperado
      if [ -x scripts/clickautomatico.sh ]; then
          chmod +x scripts/*.sh || true
          ./scripts/clickautomatico.sh
      else
          echo "⚠️  No se encontró scripts/clickautomatico.sh en $dir"
      fi
    )

    echo "✅ Terminado $dir"
done

echo "🏁 Todos los mutantes finalizados desde scripts/"
