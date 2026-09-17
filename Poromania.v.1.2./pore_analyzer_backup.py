#!/usr/bin/env python3
"""
PyMOL Pore Analyzer
Analiza poros de proteína con una esfera interactiva que crece desde el centro
"""

import pymol
from pymol import cmd, stored
import numpy as np
import random
import os
from pathlib import Path

def load_and_center_protein(pdb_file):
    """
    Carga la proteína y la centra en el origen
    """
    cmd.load(pdb_file, "protein")
    cmd.center("protein")
    cmd.zoom("protein")
    cmd.show("cartoon", "protein")
    cmd.color("white", "protein")
    print(f"Proteína cargada: {pdb_file}")

def find_pore_center(selection="protein"):
    """
    Encuentra el centro geométrico del poro de la proteína
    """
    # Obtener coordenadas de todos los átomos CA
    stored.coords = []
    cmd.iterate_state(1, f"{selection} and name CA", "stored.coords.append([x,y,z])")

    if not stored.coords:
        print("Error: No se encontraron átomos CA")
        return None

    coords = np.array(stored.coords)
    center = np.mean(coords, axis=0)

    # Crear pseudoátomo en el centro
    cmd.pseudoatom("pore_center", pos=center.tolist())
    cmd.show("spheres", "pore_center")
    cmd.color("red", "pore_center")

    print(f"Centro del poro calculado: ({center[0]:.2f}, {center[1]:.2f}, {center[2]:.2f})")
    return center

def create_probe_sphere(center, radius=1.0):
    """
    Crea una esfera de prueba en el centro del poro
    """
    cmd.delete("probe_sphere")

    # Crear esfera usando pseudoátomo con radio específico
    cmd.pseudoatom("probe_sphere", pos=center.tolist())
    cmd.show("spheres", "probe_sphere")
    cmd.set("sphere_scale", radius, "probe_sphere")
    cmd.color("blue", "probe_sphere")
    cmd.set("sphere_transparency", 0.3, "probe_sphere")

    print(f"Esfera creada con radio: {radius:.2f} Å")

def find_pore_residues(center, radius):
    """
    Encuentra residuos que están dentro de la esfera de radio especificado
    """
    # Crear selección de átomos dentro del radio
    cmd.select("pore_atoms", f"protein within {radius} of pore_center")

    # Obtener residuos únicos
    stored.residues = []
    cmd.iterate("pore_atoms", "stored.residues.append((chain, resi, resn))")

    # Eliminar duplicados y ordenar
    unique_residues = sorted(list(set(stored.residues)))

    # Colorear residuos del poro
    cmd.color("yellow", "pore_atoms")
    cmd.show("sticks", "pore_atoms")

    return unique_residues

def get_common_pore_positions(residues):
    """
    Encuentra posiciones que están presentes en todas las cadenas disponibles
    """
    # Obtener todas las cadenas disponibles
    stored.chains = []
    cmd.iterate("protein", "stored.chains.append(chain)")
    available_chains = sorted(list(set(stored.chains)))

    # Agrupar residuos por posición
    positions_by_chain = {}
    for chain, resi, resn in residues:
        if chain not in positions_by_chain:
            positions_by_chain[chain] = set()
        positions_by_chain[chain].add(int(resi))

    # Encontrar posiciones comunes a todas las cadenas
    if not positions_by_chain:
        return [], available_chains

    common_positions = set.intersection(*positions_by_chain.values())

    # Obtener información completa de las posiciones comunes
    common_residues = []
    for chain in available_chains:
        for pos in sorted(common_positions):
            for ch, resi, resn in residues:
                if ch == chain and int(resi) == pos:
                    common_residues.append((ch, resi, resn))
                    break

    return sorted(common_residues), available_chains

def print_common_pore_positions(common_residues, available_chains):
    """
    Muestra las posiciones comunes en todas las cadenas
    """
    if not common_residues:
        print("\nNo se encontraron posiciones comunes en todas las cadenas")
        return

    # Agrupar por posición
    by_position = {}
    for chain, resi, resn in common_residues:
        pos = int(resi)
        if pos not in by_position:
            by_position[pos] = []
        by_position[pos].append((chain, resn))

    print(f"\nCadenas disponibles: {', '.join(available_chains)}")
    print("\n" + "="*70)
    print("POSICIONES DEL PORO PRESENTES EN TODAS LAS CADENAS")
    print("="*70)
    print("Posición | Residuos por cadena")
    print("-"*70)

    for pos in sorted(by_position.keys()):
        chain_info = " | ".join([f"{chain}:{resn}" for chain, resn in sorted(by_position[pos])])
        print(f"   {pos:>3}   | {chain_info}")

    print("="*70)
    print(f"Total de posiciones comunes: {len(by_position)}")

    return list(by_position.keys())

def print_pore_residues(residues):
    """
    Imprime la lista de residuos que forman el poro
    """
    print("\n" + "="*60)
    print(f"RESIDUOS QUE FORMAN EL PORO ({len(residues)} residuos)")
    print("="*60)
    print("Cadena | Número | Tipo")
    print("-"*60)

    for chain, resi, resn in residues:
        print(f"   {chain}   |   {resi:>4}  | {resn}")

    print("="*60)
    print(f"Total de residuos en el poro: {len(residues)}")

def generate_mutants_interactive(common_positions, available_chains):
    """
    Interfaz interactiva para generar mutantes
    """
    if not common_positions:
        print("No hay posiciones comunes para mutar")
        return

    print("\n" + "="*60)
    print("GENERADOR DE MUTANTES")
    print("="*60)

    # Preguntar número de mutantes
    while True:
        try:
            num_mutants = int(input("¿Cuántos mutantes quiere generar? "))
            if num_mutants > 0:
                break
            print("Debe ser un número mayor que 0")
        except ValueError:
            print("Ingrese un número válido")

    # Preguntar tipo de mutación
    print("\nTipo de mutación:")
    print("1. Manual (usted elige las mutaciones)")
    print("2. Aleatoria (se generan automáticamente)")

    while True:
        choice = input("Seleccione opción (1 o 2): ").strip()
        if choice in ['1', '2']:
            break
        print("Seleccione 1 o 2")

    # Lista de aminoácidos disponibles
    all_aa = ['ALA','ARG','ASN','ASP','CYS','GLN','GLU','GLY','HIS','ILE',
              'LEU','LYS','MET','PHE','PRO','SER','THR','TRP','TYR','VAL','DEL']

    if choice == '1':
        generate_manual_mutants(num_mutants, common_positions, available_chains, all_aa)
    else:
        generate_random_mutants(num_mutants, common_positions, available_chains, all_aa)

def generate_manual_mutants(num_mutants, common_positions, available_chains, all_aa):
    """
    Genera mutantes con selección manual
    """
    print(f"\nPosiciones disponibles: {common_positions}")
    print(f"Aminoácidos disponibles: {', '.join(all_aa)}")
    print("(DEL = deleción)")

    mutants = []
    for i in range(num_mutants):
        print(f"\n--- Mutante {i+1} ---")
        mutations = {}

        while True:
            try:
                num_muts = int(input("¿Cuántas mutaciones para este mutante? "))
                if 0 < num_muts <= len(common_positions):
                    break
                print(f"Debe ser entre 1 y {len(common_positions)}")
            except ValueError:
                print("Ingrese un número válido")

        for j in range(num_muts):
            while True:
                try:
                    pos = int(input(f"Posición {j+1} a mutar: "))
                    if pos in common_positions and pos not in mutations:
                        break
                    elif pos in mutations:
                        print("Ya seleccionó esta posición")
                    else:
                        print(f"Posición debe estar en: {common_positions}")
                except ValueError:
                    print("Ingrese un número válido")

            while True:
                aa = input(f"Aminoácido para posición {pos}: ").upper().strip()
                if aa in all_aa:
                    mutations[pos] = aa
                    break
                print(f"Aminoácido debe estar en: {all_aa}")

        mutants.append(mutations)
        print(f"Mutante {i+1}: {mutations}")

    create_mutant_files(mutants, available_chains)

def generate_random_mutants(num_mutants, common_positions, available_chains, all_aa):
    """
    Genera mutantes aleatorios
    """
    while True:
        try:
            muts_per_mutant = int(input("¿Cuántas mutaciones por mutante? "))
            if 0 < muts_per_mutant <= len(common_positions):
                break
            print(f"Debe ser entre 1 y {len(common_positions)}")
        except ValueError:
            print("Ingrese un número válido")

    # Establecer semilla para reproducibilidad
    random.seed(42)

    mutants = []
    print(f"\nGenerando {num_mutants} mutantes aleatorios...")

    for i in range(num_mutants):
        # Seleccionar posiciones aleatorias
        selected_positions = random.sample(common_positions, muts_per_mutant)

        # Asignar aminoácidos aleatorios
        mutations = {}
        for pos in selected_positions:
            mutations[pos] = random.choice(all_aa)

        mutants.append(mutations)
        print(f"Mutante {i+1}: {mutations}")

    create_mutant_files(mutants, available_chains)

def create_mutant_files(mutants, available_chains):
    """
    Crea archivos .pml para generar los mutantes
    """
    # Crear directorio para mutantes
    mutants_dir = Path("mutants")
    mutants_dir.mkdir(exist_ok=True)

    # Crear script principal
    script_content = generate_pymol_script(mutants, available_chains)

    script_file = "1crear_mutantes.pml"
    with open(script_file, 'w') as f:
        f.write(script_content)

    print(f"\n✓ Archivo generado: {script_file}")
    print(f"✓ Directorio creado: {mutants_dir}")
    print(f"\nPara ejecutar: pymol -cq {script_file}")

def generate_pymol_script(mutants, available_chains):
    """
    Genera el contenido del script PyMOL
    """
    script = f"""# 1crear_mutantes.pml
# Generado automáticamente por el analizador de poros

# Cargar proteína original
load poronatural.pdb, WT
save mutants/WT.pdb, WT

python
from pathlib import Path
from pymol import cmd
import shutil

# Configuración
chains = {available_chains}
base_dir = Path("mutants")
base_dir.mkdir(exist_ok=True)

# Lista de mutantes a generar
mutants_data = {mutants}

print(f"Generando {{len(mutants_data)}} mutantes...")

for idx, mutations in enumerate(mutants_data, 1):
    # Crear nombre del mutante
    mut_parts = [f"{{pos}}{{aa}}" for pos, aa in sorted(mutations.items())]
    tag = "mut_" + "_".join(mut_parts)

    cmd.create(tag, 'WT')

    # Aplicar mutaciones en todas las cadenas
    for chain in chains:
        for pos, aa in mutations.items():
            if aa == "DEL":
                cmd.remove(f"/{{tag}}//{{chain}}/{{pos}}/")
                print(f"  Deleción: cadena {{chain}} posición {{pos}}")
            else:
                cmd.wizard('mutagenesis')
                w = cmd.get_wizard()
                w.set_mode(aa)
                w.do_select(f"/{{tag}}//{{chain}}/{{pos}}/")
                w.apply()
                cmd.set_wizard()
                print(f"  Mutación: cadena {{chain}} posición {{pos}} → {{aa}}")

    cmd.rebuild()

    # Crear directorio para el mutante
    dest = base_dir / tag
    dest.mkdir(parents=True, exist_ok=True)

    # Guardar estructura
    tmp_pdb = base_dir / f"{{tag}}.pdb"
    cmd.save(tmp_pdb.as_posix(), tag)
    shutil.move(tmp_pdb, dest / "receptor.pdb")

    cmd.delete(tag)
    print(f"{{idx}}/{{len(mutants_data)}} → {{dest}}")

print("¡Mutantes generados exitosamente!")
python end
quit
"""
    return script

def interactive_pore_analysis():
    """
    Función principal para análisis interactivo del poro
    """
    print("\n" + "="*60)
    print("ANALIZADOR DE POROS DE PROTEÍNA")
    print("="*60)

    # Cargar proteína
    pdb_file = "poronatural.pdb"
    load_and_center_protein(pdb_file)

    # Encontrar centro del poro
    center = find_pore_center()
    if center is None:
        return

    print("\nControles:")
    print("- Ingrese un radio en Ångströms para la esfera")
    print("- Escriba 'mutantes' para generar mutantes con las posiciones seleccionadas")
    print("- Escriba 'quit' o 'salir' para terminar")
    print("- Escriba 'reset' para resetear la vista")

    current_common_positions = []
    current_chains = []

    while True:
        try:
            user_input = input("\nIngrese radio de la esfera (Å) o comando: ").strip()

            if user_input.lower() in ['quit', 'salir', 'exit']:
                print("Terminando análisis...")
                break
            elif user_input.lower() == 'reset':
                cmd.delete("probe_sphere")
                cmd.color("white", "protein")
                cmd.hide("sticks", "protein")
                cmd.show("cartoon", "protein")
                print("Vista reseteada")
                continue
            elif user_input.lower() == 'mutantes':
                if current_common_positions:
                    generate_mutants_interactive(current_common_positions, current_chains)
                else:
                    print("Primero debe analizar un radio para identificar posiciones del poro")
                continue

            radius = float(user_input)

            if radius <= 0:
                print("Error: El radio debe ser mayor que 0")
                continue

            # Crear esfera y encontrar residuos
            create_probe_sphere(center, radius)
            pore_residues = find_pore_residues(center, radius)

            # Mostrar resultados
            print_pore_residues(pore_residues)

            # Encontrar posiciones comunes en todas las cadenas
            common_residues, available_chains = get_common_pore_positions(pore_residues)
            common_positions = print_common_pore_positions(common_residues, available_chains)

            # Guardar para uso en generación de mutantes
            current_common_positions = common_positions if common_positions else []
            current_chains = available_chains

            # Crear selección nombrada para los residuos del poro
            if pore_residues:
                cmd.select("pore_residues", "pore_atoms")
                print(f"\nSelección 'pore_residues' creada con {len(pore_residues)} residuos")

            if current_common_positions:
                print(f"\nTip: Escriba 'mutantes' para generar mutantes usando las {len(current_common_positions)} posiciones comunes")

        except ValueError:
            print("Error: Ingrese un número válido para el radio")
        except KeyboardInterrupt:
            print("\nTerminando análisis...")
            break
        except Exception as e:
            print(f"Error: {e}")

def setup_pymol_view():
    """
    Configura la vista inicial de PyMOL
    """
    cmd.bg_color("white")
    cmd.set("ray_opaque_background", "off")
    cmd.set("depth_cue", "off")
    cmd.set("antialias", 2)

if __name__ == "__main__":
    import sys

    # Verificar si se quiere modo GUI
    gui_mode = len(sys.argv) > 1 and sys.argv[1] == '--gui'

    if gui_mode:
        # Modo con interfaz gráfica
        pymol.finish_launching(['pymol'])
    else:
        # Modo consola (sin ventana)
        pymol.finish_launching(['pymol', '-c'])

    # Configurar vista
    setup_pymol_view()

    # Ejecutar análisis interactivo
    interactive_pore_analysis()