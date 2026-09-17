# Asegúrate de estar en .../mutacionesnuevas/
for dir in mutants/mut_*; do
  [ -d "$dir" ] || continue                              # Solo directorios válidos
  mkdir -p "$dir/scripts"                                # Crea subcarpeta scripts si no existe
  cp -r scripts/* "$dir/scripts/"                        # Copia el contenido dentro de scripts/
done
