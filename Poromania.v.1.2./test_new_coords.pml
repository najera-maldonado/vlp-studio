# Test del nuevo sistema de coordenadas
# Generado para probar el cálculo: primer residuo → promedio

# Cargar proteína original
load poronatural.pdb, WT
save mutants/WT.pdb, WT

python
from pathlib import Path
from pymol import cmd, stored
import shutil

# Configuración
chains = ['A', 'B']
selected_positions = ['129']
base_dir = Path("mutants")
base_dir.mkdir(exist_ok=True)

# Funciones para calcular centro y vector del poro automaticamente
def calculate_pore_center_for_structure(structure_name):
    import numpy as np

    stored.coords = []
    coord_info = []  # Para almacenar coordenadas con información de residuo

    # Obtener coordenadas de CA de los residuos seleccionados de manera ordenada
    for pos in sorted(selected_positions, key=int):  # Ordenar por número de residuo
        for chain in chains:
            selection = f"name CA and resi {pos} and chain {chain} and {structure_name}"
            stored.temp_coords = []
            cmd.iterate_state(1, selection, "stored.temp_coords.append([x,y,z])")
            if stored.temp_coords:
                coord = stored.temp_coords[0]  # Primer (y único) resultado
                stored.coords.append(coord)
                coord_info.append({'pos': pos, 'chain': chain, 'coord': coord})

    if stored.coords:
        coords = np.array(stored.coords)

        # Primer residuo: coordenada del primer residuo encontrado (menor número)
        first_residue_coord = np.array(coord_info[0]['coord'])

        # Promedio: centro de masa de todos los residuos seleccionados
        center_avg = np.mean(coords, axis=0)

        return first_residue_coord, center_avg
    return [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]

def calculate_pore_vector(first_residue_coord, center_avg):
    # Calcula el vector del eje del poro: primer residuo → promedio
    import numpy as np

    # Vector del primer residuo al centro promedio (eje del poro)
    vector = center_avg - first_residue_coord

    # Normalizar el vector
    norm = np.linalg.norm(vector)
    if norm > 0:
        vector = vector / norm

    return vector

# Lista de mutantes a generar
mutants_data = [{'129': 'ALA'}]

print(f"Generando {len(mutants_data)} mutantes...")

for idx, mutations in enumerate(mutants_data, 1):
    # Crear nombre del mutante
    mut_parts = [f"{pos}{aa}" for pos, aa in sorted(mutations.items())]
    tag = "mut_" + "_".join(mut_parts)

    cmd.create(tag, 'WT')

    # Aplicar mutaciones en todas las cadenas
    for chain in chains:
        for pos, aa in mutations.items():
            if aa == "DEL":
                cmd.remove(f"/{tag}//{chain}/{pos}/")
                print(f"  Deleción: cadena {chain} posición {pos}")
            else:
                cmd.wizard('mutagenesis')
                w = cmd.get_wizard()
                w.set_mode(aa)
                w.do_select(f"/{tag}//{chain}/{pos}/")
                w.apply()
                cmd.set_wizard()
                print(f"  Mutación: cadena {chain} posición {pos} → {aa}")

    cmd.rebuild()

    # Calcular centro específico para este mutante DESPUÉS de aplicar mutaciones
    first_residue_coord, center_avg = calculate_pore_center_for_structure(tag)

    # Calcular vector de dirección del poro (primer residuo → promedio)
    pore_vector = calculate_pore_vector(first_residue_coord, center_avg)

    # Crear directorio para el mutante
    dest = base_dir / tag
    dest.mkdir(parents=True, exist_ok=True)

    # Guardar coordenadas del primer residuo
    first_coord_file = dest / "first_residue_coord.txt"
    with open(first_coord_file, 'w') as f:
        f.write(f"{first_residue_coord[0]:.2f} {first_residue_coord[1]:.2f} {first_residue_coord[2]:.2f}")

    # Guardar coordenadas del centro del poro (usar centro promedio)
    pore_center_file = dest / "pore_center.txt"
    with open(pore_center_file, 'w') as f:
        f.write(f"{center_avg[0]:.2f} {center_avg[1]:.2f} {center_avg[2]:.2f}")

    # Guardar vector de dirección del poro
    pore_vector_file = dest / "pore_vector.txt"
    with open(pore_vector_file, 'w') as f:
        f.write(f"{pore_vector[0]:.2f} {pore_vector[1]:.2f} {pore_vector[2]:.2f}")

    # Guardar las posiciones seleccionadas para referencia
    selected_pos_file = dest / "selected_positions.txt"
    with open(selected_pos_file, 'w') as f:
        f.write(','.join(map(str, selected_positions)))

    print(f"  Primer residuo: [{first_residue_coord[0]:.2f}, {first_residue_coord[1]:.2f}, {first_residue_coord[2]:.2f}]")
    print(f"  Centro promedio: [{center_avg[0]:.2f}, {center_avg[1]:.2f}, {center_avg[2]:.2f}]")
    print(f"  Vector calculado: [{pore_vector[0]:.2f}, {pore_vector[1]:.2f}, {pore_vector[2]:.2f}]")

    # Guardar estructura
    tmp_pdb = base_dir / f"{tag}.pdb"
    cmd.save(tmp_pdb.as_posix(), tag)
    shutil.move(tmp_pdb, dest / "receptor.pdb")

    cmd.delete(tag)
    print(f"{idx}/{len(mutants_data)} → {dest}")

print("¡Mutantes generados exitosamente!")
python end
quit