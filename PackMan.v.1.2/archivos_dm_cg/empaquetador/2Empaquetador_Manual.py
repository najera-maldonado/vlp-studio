import os
import subprocess
from datetime import datetime
from pymol import cmd
import numpy as np
import shutil

# === CONFIGURACIÓN ===
capsid_input = "capside.pdb"
enzyme_input = "enzima.pdb"  # Puede ser multicanal, multímero, etc.
capsid_pdb = "capside_recentrada.pdb"
enzyme_pdb = "enzima_recentrada.pdb"
centro = [0.0, 0.0, 0.0]
radio_interno = 90
margen_colision = 2
radio_usado = radio_interno - margen_colision
radio_exclusion = 5.0

# === PREGUNTAR CUÁNTAS ENZIMAS ===
n_enzimas = int(input("🔢 ¿Cuántas enzimas deseas empaquetar? "))

# === RECESAR Y GUARDAR ARCHIVOS CENTRADOS ===
def recentrar(input_file, output_file, obj_name):
    cmd.reinitialize()
    cmd.load(input_file, obj_name)
    coords = cmd.get_coords(obj_name)
    com = np.mean(coords, axis=0)
    cmd.alter_state(1, obj_name, f"x = x - {com[0]}")
    cmd.alter_state(1, obj_name, f"y = y - {com[1]}")
    cmd.alter_state(1, obj_name, f"z = z - {com[2]}")
    cmd.save(output_file, obj_name)
    print(f"✅ {obj_name} centrado y guardado como {output_file}")

if not os.path.exists(enzyme_pdb):
    recentrar(enzyme_input, enzyme_pdb, "enzima")

if not os.path.exists(capsid_pdb):
    recentrar(capsid_input, capsid_pdb, "capside")

# === GENERAR ARCHIVOS DE EMPAQUETAMIENTO ===
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_pdb = f"capside_{n_enzimas}enzimas_{timestamp}.pdb"
input_packmol = "packmol_tmp.inp"
logfile = f"log_packmol_{n_enzimas}enzimas_{timestamp}.txt"

def generar_input_packmol():
    texto = f"""tolerance 2.0
filetype pdb
output {output_pdb}

structure {capsid_pdb}
  number 1
  fixed {centro[0]} {centro[1]} {centro[2]} 0. 0. 0.
end structure

structure {enzyme_pdb}
  number {n_enzimas}
  inside sphere {centro[0]} {centro[1]} {centro[2]} {radio_usado}
  radius {radio_exclusion}
end structure
"""
    with open(input_packmol, 'w') as f:
        f.write(texto)

def correr_packmol():
    with open(input_packmol, 'r') as f:
        resultado = subprocess.run(["packmol"], stdin=f, capture_output=True, text=True)
    with open(logfile, 'w') as logf:
        logf.write(resultado.stdout + "\n" + resultado.stderr)
    return resultado.returncode == 0

def verificar_enzimas(pdb_file):
    with open(pdb_file, 'r') as f:
        lines = [line for line in f if line.startswith("ATOM") or line.startswith("HETATM")]
    return len(lines)

# === FUNCIONES DE SEPARACIÓN ===
def preparar_directorio(nombre):
    if os.path.exists(nombre):
        shutil.rmtree(nombre)
    os.makedirs(nombre)

def extraer_enzimas_individuales(pdb_file, n_enzimas, lineas_por_enzima, carpeta="enzimas_individuales"):
    preparar_directorio(carpeta)
    with open(pdb_file, 'r') as f:
        lines = [line for line in f if line.startswith("ATOM") or line.startswith("HETATM")]

    # Quitar líneas de la cápside (asume que es la primera estructura)
    with open(capsid_pdb, 'r') as capf:
        lines_capside = [line for line in capf if line.startswith("ATOM") or line.startswith("HETATM")]
    lines = lines[len(lines_capside):]

    for i in range(n_enzimas):
        start = i * lineas_por_enzima
        end = (i + 1) * lineas_por_enzima
        enz_lines = lines[start:end]
        outname = os.path.join(carpeta, f"enzima_{i+1}.pdb")
        with open(outname, 'w') as out:
            out.writelines(enz_lines)
        print(f"✅ enzima_{i+1}.pdb guardada en {carpeta}/")

# === EJECUCIÓN ===
print(f"\n📦 Iniciando empaquetamiento de {n_enzimas} enzimas en cápside...")
generar_input_packmol()
exito = correr_packmol()

if exito and os.path.exists(output_pdb):
    n_atom_lines = verificar_enzimas(output_pdb)
    if n_atom_lines > 10000:
        print(f"✅ Empaquetamiento exitoso. Archivo: {output_pdb} ({n_atom_lines} átomos)")
        lineas_una_enzima = verificar_enzimas(enzyme_pdb)
        extraer_enzimas_individuales(output_pdb, n_enzimas, lineas_una_enzima)
    else:
        print(f"⚠️ Packmol terminó pero el archivo parece incompleto ({n_atom_lines} átomos).")
else:
    print("❌ Falló el empaquetamiento. Revisa el archivo de log:")
    print(f"   📄 {logfile}")
