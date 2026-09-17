#!/usr/bin/env bash

# Sal del script si algo falla
set -euo pipefail
shopt -s nullglob

command -v montage >/dev/null || { echo "❌ Falta ImageMagick (montage)"; exit 1; }
command -v convert  >/dev/null || { echo "❌ Falta ImageMagick (convert)"; exit 1; }

base_dir="mutants"
out_dir="imagenes"
mkdir -p "$out_dir"

for mut_dir in "$base_dir"/mut_*; do
    mut_name=$(basename "$mut_dir")
    echo "📦 Procesando $mut_name"

    ext_img=$(find "$mut_dir" -path '*/cargas_apbs/snap/*_ext.png' | head -n1)
    int_img=$(find "$mut_dir" -path '*/cargas_apbs/snap/*_int.png' | head -n1)
    hole_img=$(find "$mut_dir/hole/resultados" -iname "perfil_*.png" | head -n1)


    if [[ -z $ext_img || -z $int_img || -z $hole_img ]]; then
        echo "⚠️  Faltan imágenes para $mut_name. Se omite."
        continue
    fi

    # Carpeta del mutante
    out_mut_dir="${out_dir}/${mut_name}"
    mkdir -p "$out_mut_dir"

    # Etiqueta las imágenes: "Cara externa" y "Cara interna"
    labeled_ext="${out_mut_dir}/ext_labeled.png"
    labeled_int="${out_mut_dir}/int_labeled.png"

# Más espacio (80 px) y letras más grandes (36 pt)
convert "$ext_img" -gravity south -splice 0x80 \
    -background white -fill black -font DejaVu-Sans -pointsize 36 \
    -annotate +0+20 "Cara externa" "$labeled_ext"

convert "$int_img" -gravity south -splice 0x80 \
    -background white -fill black -font DejaVu-Sans -pointsize 36 \
    -annotate +0+20 "Cara interna" "$labeled_int"

    # Une ext + int verticalmente
    # ─── Escala ext/int al 80% de la altura de la gráfica y las centra ───
    graf_h=$(identify -format %h "$hole_img")              # altura total de la gráfica
    target=$(( graf_h * 80 / 100 ))                        # 80%

    ext_scaled="${out_mut_dir}/ext_scaled.png"
    int_scaled="${out_mut_dir}/int_scaled.png"

    # Redimensiona y extiende a la misma altura que la gráfica, centrando
    convert "$labeled_ext" -resize x${target} \
           -background white -gravity center -extent x${graf_h} \
           "$ext_scaled"

    convert "$labeled_int" -resize x${target} \
           -background white -gravity center -extent x${graf_h} \
           "$int_scaled"

    # Apila EXT arriba de INT
    surf_img="${out_mut_dir}/surf.png"
    montage "$ext_scaled" "$int_scaled" \
            -tile 1x2 -geometry +0+0 -background white \
            "$surf_img"

    # Borra temporales
    rm "$ext_scaled" "$int_scaled"


    # Tríptico final (surf izquierda + HOLE derecha)
    # ─── Escalar la gráfica HOLE a la misma altura que surf + montar tríptico ───
    graf_h=$(identify -format %h "$surf_img")               # altura del surf (y del hole deseada)
    hole_scaled="${out_mut_dir}/hole_scaled.png"

    # Ajusta la altura de la gráfica al alto de surf_img
    convert "$hole_img" -resize x${graf_h} "$hole_scaled"

    # Monta surf (izq) + gráfica escalada (der)
    triptico_img="${out_mut_dir}/${mut_name}_triptico.png"
    montage "$surf_img" "$hole_scaled" \
            -tile 2x1 -geometry +0+0 -background white \
            "$triptico_img"

    # Limpieza
    rm "$hole_scaled"


    echo "✅ Tríptico generado en: $triptico_img"
done

echo "🎉 Todos los trípticos organizados en: $out_dir/<mutante>/"

