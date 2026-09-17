#!/bin/bash
set -e

# Ir mutante por mutante desde fuera de cada carpeta
for dir in mutants/mut_*; do
    echo "🔍 Procesando $dir..."

    # Verifica si receptor.pdb existe
    if [ ! -f "$dir/receptor.pdb" ]; then
        echo "❌ No se encontró receptor.pdb en $dir, se omite."
        continue
    fi

    mutante=$(basename "$dir")              # mut_83ALA_84CYS_...
    outdir="$dir/cargas_apbs"
    mkdir -p "$outdir"

    echo "🧬 Generando ${mutante}.pqr ..."
    pdb2pqr --ff=AMBER --with-ph=4.5 "$dir/receptor.pdb" "$outdir/${mutante}.pqr"

    echo "📄 Creando input APBS ..."
    cat > "$outdir/${mutante}.in" <<EOL
read
  mol pqr ${mutante}.pqr
end
elec
  mg-auto
  sdens 10.0
  dime 97 97 97
  cglen 80 80 80
  fglen 40 40 40
  cgcent mol 1
  fgcent mol 1
  mol 1
  lpbe
  bcfl sdh
  pdie 2.0
  sdie 78.54
  srfm smol
  chgm spl2
  srad 1.4
  swin 0.3
  temp 298.15
  calcenergy total
  calcforce no
  write pot dx ${mutante}_pot
end
quit
EOL

    echo "⚡ Ejecutando APBS en $dir ..."
    (cd "$outdir" && apbs "${mutante}.in" > log_apbs.txt)

    echo "✅ $mutante procesado correctamente."
done

echo "🏁 Todos los mutantes han sido procesados desde fuera del directorio."
# Copiar script de PyMOL automático
cat > "$outdir/foto_poro.pml" <<'PML'
# ---------- foto_poro.pml ----------
python
import glob
pqr = glob.glob("*.pqr")[0]
dx = glob.glob("*_pot-PE0.dx")[0]
modelo = pqr.split(".")[0]
cmd.load(pqr, "modelo")
cmd.load(dx, "pot")
python end

as surface, modelo
set transparency, 0.1
ramp_new r, pot, [-5, 0, 5]
set surface_color, r, modelo
bg_color white

python
import os
os.makedirs("snap", exist_ok=True)
cmd.set("ray_trace_mode", 1)
python end

set_view (\
0.8629038333892822, -0.41040459275245667, 0.2949010133743286,\
0.4929146468639374, 0.8122352361679077, -0.31194427609443665,\
-0.11150549352169037, 0.41453880071640015, 0.9031745791435242,\
0.0, 0.0, -82.44172668457031,\
220.40969848632812, 169.1165313720703, 316.34521484375,\
25.958553314208984, 138.92489624023438, -20.0 )
clip slab, 80
clip move, -20
refresh
python
cmd.png(f"snap/{modelo}_ext.png", dpi=300, ray=1, width=2400, height=1800)
python end

set_view (\
-0.7393578290939331, -0.6013239622116089, -0.30292075872421265,\
-0.6693006157875061, 0.7054134011268616, 0.2332986742258072,\
0.07339610159397125, 0.375236451625824, -0.9240193963050842,\
0.0, 0.0, -82.44172668457031,\
220.40969848632812, 169.1165313720703, 316.34521484375,\
25.958553314208984, 138.92489624023438, -20.0 )
clip slab, 80
clip move, -20
refresh
python
cmd.png(f"snap/{modelo}_int.png", dpi=300, ray=1, width=2400, height=1800)
python end
PML
