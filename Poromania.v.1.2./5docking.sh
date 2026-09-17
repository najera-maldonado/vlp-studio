#!/bin/bash
set -euo pipefail

# === CONFIG ===
MARGIN="${MARGIN:-6}"     # margen extra al radio mínimo de HOLE
MINBOX="${MINBOX:-24}"    # caja mínima
BOX="${BOX:-30}"          # caja por defecto si no hay HOLE
THREADS="$(nproc || echo 8)"
MAXCONF="${MAXCONF:-500}" # conformaciones por iDock

# === util ===
have() { command -v "$1" >/dev/null 2>&1; }

dock_one() {
  local M="mutants/$1"
  local D="$M/docking"
  local HS="$M/hole/resultados/hole_spheres.pdb"

  echo "🔄 $(basename "$M")"
  mkdir -p "$D/Results" "$D/ligands"

  # Receptor
  if [[ ! -s "$M/receptor.pdbqt" ]]; then
    if [[ -s "$M/receptor.pdb" ]]; then
      if have prepare_receptor4.py; then
        prepare_receptor4.py -r "$M/receptor.pdb" -o "$M/receptor.pdbqt" -A checkhydrogens -U nphs_lps_waters_nonstdres || true
      fi
      if [[ ! -s "$M/receptor.pdbqt" ]]; then
        local SRC="$M/receptor.pdb"
        if have pdb4amber; then
          pdb4amber -i "$M/receptor.pdb" -o "$M/receptor_fix.pdb" --reduce || cp "$M/receptor.pdb" "$M/receptor_fix.pdb"
          SRC="$M/receptor_fix.pdb"
        fi
        obabel "$SRC" -O "$M/receptorH.pdb" -p 7.4 -h --errorlevel 1
        obabel "$M/receptorH.pdb" -O "$M/receptor.pdbqt" --partialcharge gasteiger --errorlevel 1
      fi
    else
      echo "   ❌ Falta $M/receptor.pdb y no hay .pdbqt"; return
    fi
  fi
  cp -f "$M/receptor.pdbqt" "$D/receptor.pdbqt" || { echo "   ❌ No pude copiar receptor"; return; }

  # Centro/size
  if [[ -s "$HS" ]]; then
    read CX CY CZ RMIN < <(awk '($1=="ATOM"||$1=="HETATM"){r=$10+0; if(r>0 && (min==""||r<min)){min=r; x=$7;y=$8;z=$9}} END{if(min=="") min=5; printf "%.3f %.3f %.3f %.3f\n", x,y,z,min}' "$HS")
    L=$(awk -v r="$RMIN" -v m="$MARGIN" 'BEGIN{printf("%.1f", 2*(r+m))}')
    if awk -v l="$L" -v mb="$MINBOX" 'BEGIN{exit !(l<mb)}'; then L="$MINBOX"; fi
    echo "   📐 HOLE center=($CX,$CY,$CZ) r_min=$RMIN Å → size=${L} Å"
  else
    read CX CY CZ < <(awk '($1=="ATOM"||$1=="HETATM"){x+=$7;y+=$8;z+=$9;n++} END{if(n>0) printf "%.3f %.3f %.3f\n", x/n,y/n,z/n; else print "0 0 0"}' "$D/receptor.pdbqt")
    L="$BOX"
    echo "   ⚠️ Sin HOLE; barycenter=($CX,$CY,$CZ) → size=${L} Å"
  fi

  # idock.conf
  cat > "$D/idock.conf" <<EOF
receptor = receptor.pdbqt
input_folder = ligands
output_folder = Results
center_x = ${CX}
center_y = ${CY}
center_z = ${CZ}
size_x = ${L}
size_y = ${L}
size_z = ${L}
threads = ${THREADS}
max_conformations = ${MAXCONF}
EOF

  # correr iDock (NO tumbar todo si falla)
  cp -f ligand.pdbqt "$D/ligands/"
  ( set +e; cd "$D"; idock --config idock.conf > "../$(basename "$M").log" 2>&1; rc=$?; exit 0 )
  if [[ ! -s "$D/Results/ligand.pdbqt" ]]; then
    echo "   ⚠️ Sin pose. Revisa $(basename "$M").log"; return
  fi
  echo "   ✅ Pose generada"

  # convertir a PDB (opcional)
  have obabel && obabel "$D/Results/ligand.pdbqt" -O "$D/Results/ligand.pdb" >/dev/null 2>&1 || true

  # scores
  awk 'BEGIN{IGNORECASE=1; pose=0; have_model=0}
       /^MODEL[[:space:]]*/ {pose=$2+0; have_model=1; next}
       /^REMARK/ {
         if (match($0, /PREDICTED BY IDOCK:[[:space:]]*(-?[0-9]+(\.[0-9]+)?)/, a)) {
           if (!have_model) { pose++ }
           printf "%d\t%s\n", pose, a[1];
           have_model=0; next
         }
         if (match($0, /(-?[0-9]+(\.[0-9]+)?)\s*K?CAL\/MOL/i, b)) {
           if (!have_model) { pose++ }
           printf "%d\t%s\n", pose, b[1];
           have_model=0;
         }
       }' "$D/Results/ligand.pdbqt" | sort -n > "$D/Results/poses.txt"
  echo "   📄 Scores → $D/Results/poses.txt"

  # mejor pose y top10
  mkdir -p "$D/estructuras" "$D/estructuras/top10"
  read BESTPOSE BESTSCORE < <(awk 'BEGIN{bestp=-1; best=1e9} {if(NF>=2){p=$1+0;s=$2+0;if(s<best){best=s;bestp=p}}} END{printf "%d %.3f", bestp, best}' "$D/Results/poses.txt")
  if [[ "${BESTPOSE:-0}" -gt 0 ]]; then
    awk -v keep="$BESTPOSE" 'BEGIN{m=0; on=0}
      /^MODEL[[:space:]]*/ {m=$2+0; on=(m==keep); if(on) print; next}
      on { print }
      /^ENDMDL/ { if(on){print; exit} }' "$D/Results/ligand.pdbqt" > "$D/estructuras/ligand_best_${BESTSCORE}.pdbqt"
    have obabel && obabel "$D/estructuras/ligand_best_${BESTSCORE}.pdbqt" -O "$D/estructuras/ligand_best_${BESTSCORE}.pdb" >/dev/null 2>&1 || true
    echo "   🏆 Mejor pose: #$BESTPOSE (${BESTSCORE} kcal/mol)"
  fi
  head -n 10 "$D/Results/poses.txt" | awk '{print $1}' | while read -r k; do
    awk -v keep="$k" 'BEGIN{m=0; on=0}
      /^MODEL[[:space:]]*/ {m=$2+0; on=(m==keep); if(on) print; next}
      on { print }
      /^ENDMDL/ { if(on){print; exit} }' "$D/Results/ligand.pdbqt" > "$D/estructuras/top10/pose_${k}.pdbqt"
    have obabel && obabel "$D/estructuras/top10/pose_${k}.pdbqt" -O "$D/estructuras/top10/pose_${k}.pdb" >/dev/null 2>&1 || true
  done
}

# === correr para TODOS los mut_* ===
shopt -s nullglob
found_any=0
for d in mutants/mut_*; do
  [[ -d "$d" ]] || continue
  dock_one "$(basename "$d")" || true   # <— esto impide que set -e mate el loop
done

if [[ "$found_any" -eq 0 ]]; then
  echo "❌ No encontré carpetas mutants/mut_* aquí."
  exit 1
fi

echo "✅ Terminado."
