#!/usr/bin/env bash
# Salud del proyecto VLP Studio — chequeo de un vistazo (sin tocar nada).
# Lo usa el pane "salud" del tablero zellij. Correr: bash herramientas/salud.sh
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1

ok(){ printf '  \033[32m✓\033[0m %s\n' "$1"; }
no(){ printf '  \033[31m✗\033[0m %s\n' "$1"; }

echo "── Binarios científicos ─────────────────"
for t in hole vina idock obabel pymol packmol; do
  if command -v "$t" >/dev/null 2>&1; then ok "$t"; else no "$t (falta)"; fi
done

echo "── Python ───────────────────────────────"
for m in rdkit flask numpy yaml; do
  if python3 -c "import $m" 2>/dev/null; then ok "$m"; else no "$m (falta)"; fi
done

echo "── ¿El Studio importa? ──────────────────"
if ( cd nanocapsule-mvp && python3 -c "import sys; sys.path.insert(0,'src'); from services import packing_service" 2>/dev/null ); then
  ok "packing_service importa"
else
  no "packing_service NO importa (revisar deps/rutas)"
fi

echo "── Git ──────────────────────────────────"
branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?')"
dirty="$(git status --porcelain 2>/dev/null | wc -l)"
printf '  rama %s · %s cambios sin commitear\n' "$branch" "$dirty"
git log --oneline -3 2>/dev/null | sed 's/^/  · /'

echo "── Tests de humo (pytest) ───────────────"
if python3 -c "import pytest" 2>/dev/null; then
  res="$( cd nanocapsule-mvp && python3 -m pytest -q 2>/dev/null | tail -1 )"
  case "$res" in
    *passed*) ok "$res" ;;
    *) no "${res:-sin salida}" ;;
  esac
else
  no "pytest no instalado (pip install pytest)"
fi

echo
echo "── Plan (ESTADO.md §6) ──────────────────"
grep -E '^\| \*\*VLP-0' ESTADO.md 2>/dev/null | sed -E 's/\| \*\*(VLP-0[0-9])\*\* \| (.) \|.*/  \2 \1/' || echo "  (ESTADO.md no encontrado)"
