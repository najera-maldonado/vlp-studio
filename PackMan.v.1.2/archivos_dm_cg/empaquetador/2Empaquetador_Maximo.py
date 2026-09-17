import os
import re
import subprocess
from datetime import datetime
from pymol import cmd
import numpy as np
import shutil

# =============== CONFIG ===============
capsid_input = "capside.pdb"
enzyme_input = "enzima.pdb"
capsid_pdb = "capside_recentrada.pdb"
enzyme_pdb = "enzima_recentrada.pdb"

centro = [0.0, 0.0, 0.0]

# Intentar leer radio interno desde archivo (generado por 1calcula_radio_interno.py)
radio_interno_default = 90.0
if os.path.exists("radio_interno.txt"):
    try:
        with open("radio_interno.txt") as f:
            radio_interno = float(f.readline().strip())
    except Exception:
        radio_interno = radio_interno_default
else:
    radio_interno = radio_interno_default

margen_colision = 2.0
radio_usado = radio_interno - margen_colision
radio_exclusion = 5.0

# Parámetros Packmol
packmol_tolerance = 2.0   # la "tolerance" del input
umbral_violacion_maxima = 0.10  # Å. Si la violación máxima > a este umbral, consideramos colisión
umbral_minimo_lineas = 10000    # fallback: si el log no aporta "Maximum distance violation"

# ============= UTILIDADES I/O =============
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

def generar_input_packmol(output_pdb, n_enzimas, input_name="packmol_tmp.inp"):
    texto = f"""tolerance {packmol_tolerance}
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
    with open(input_name, 'w') as f:
        f.write(texto)

def correr_packmol(input_name, output_pdb, log_file):
    with open(input_name, 'r') as f:
        resultado = subprocess.run(["packmol"], stdin=f, capture_output=True, text=True)
    with open(log_file, 'w') as logf:
        logf.write(resultado.stdout + "\n" + resultado.stderr)
    ok = (resultado.returncode == 0 and os.path.exists(output_pdb))
    return ok

def contar_lineas_atomicas(pdb_file):
    with open(pdb_file, 'r') as f:
        return sum(1 for line in f if line.startswith("ATOM") or line.startswith("HETATM"))

# ============= PARSING DEL LOG =============
_violation_regex = re.compile(r"Maximum\s+distance\s+violation:\s*([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)")

def leer_violacion_maxima(log_file):
    """
    Retorna float con la violación máxima si se encuentra en el log.
    Si no se encuentra, retorna None.
    """
    try:
        with open(log_file, 'r') as f:
            txt = f.read()
        m = _violation_regex.search(txt)
        if m:
            return float(m.group(1))
    except Exception:
        pass
    return None

# ============= SEPARACIÓN DE ENZIMAS ============
def preparar_directorio(nombre):
    if os.path.exists(nombre):
        shutil.rmtree(nombre)
    os.makedirs(nombre)

def extraer_enzimas_individuales(pdb_file, n_enzimas, lineas_por_enzima, carpeta="enzimas_individuales"):
    preparar_directorio(carpeta)
    with open(pdb_file, 'r') as f:
        lines = [line for line in f if line.startswith("ATOM") or line.startswith("HETATM")]

    # Quitar líneas de la cápside (se asume primera estructura en el PDB final)
    with open(capsid_pdb, 'r') as capf:
        caps_lines = [line for line in capf if line.startswith("ATOM") or line.startswith("HETATM")]
    lines = lines[len(caps_lines):]

    for i in range(n_enzimas):
        start = i * lineas_por_enzima
        end = (i + 1) * lineas_por_enzima
        enz_lines = lines[start:end]
        outname = os.path.join(carpeta, f"enzima_{i+1}.pdb")
        with open(outname, 'w') as out:
            out.writelines(enz_lines)
        print(f"✅ enzima_{i+1}.pdb guardada en {carpeta}/")

# ============= MODO AUTOMÁTICO =============
print("\n📦 Modo automático con criterio de colisión basado en log de Packmol...")
print(f"• radio_interno = {radio_interno:.2f} Å, radio_usado = {radio_usado:.2f} Å, radio_exclusion = {radio_exclusion:.2f} Å")
print(f"• umbral_violacion_maxima = {umbral_violacion_maxima:.3f} Å (fallback líneas > {umbral_minimo_lineas})\n")

lineas_por_enzima = contar_lineas_atomicas(enzyme_pdb)
n = 1
exitoso = False
mejor_pdb = None
mejor_n = 0

while True:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_pdb = f"capside_{n}enzimas_{timestamp}.pdb"
    log_file = f"log_packmol_{n}enzimas_{timestamp}.txt"
    input_file = "packmol_tmp.inp"

    generar_input_packmol(output_pdb, n, input_file)
    print(f"🔄 Intentando con {n} enzima(s)...")
    exito_packmol = correr_packmol(input_file, output_pdb, log_file)

    if not exito_packmol:
        print("⛔ Packmol no generó un PDB válido o retornó error. Deteniendo.")
        break

    # Intentar criterio principal: leer violación máxima del log
    violacion = leer_violacion_maxima(log_file)
    if violacion is not None:
        print(f"   ↪ Maximum distance violation reportado por Packmol: {violacion:.4f} Å")
        if violacion > umbral_violacion_maxima:
            print(f"⚠️  Violación {violacion:.4f} Å > {umbral_violacion_maxima:.3f} Å → consideramos colisión. Deteniendo.")
            break
        else:
            print("   ✅ Violación dentro del umbral. Aceptado.")
            mejor_pdb = output_pdb
            mejor_n = n
            exitoso = True
            n += 1
            continue

    # Fallback si el log no trae la métrica
    total_lines = contar_lineas_atomicas(output_pdb)
    print(f"   ↪ Log sin 'Maximum distance violation'. Fallback: líneas ATOM/HETATM = {total_lines}")
    if total_lines < umbral_minimo_lineas:
        print("⚠️  Archivo parece incompleto o con solapamientos (por conteo de líneas). Deteniendo.")
        break

    mejor_pdb = output_pdb
    mejor_n = n
    exitoso = True
    n += 1

if exitoso:
    print(f"\n✅ Máximo empaquetamiento exitoso: {mejor_n} enzima(s).")
    print(f"📁 Archivo generado: {mejor_pdb}")
    extraer_enzimas_individuales(mejor_pdb, mejor_n, lineas_por_enzima)
else:
    print("\n❌ No se logró empaquetar ninguna enzima dentro del umbral de colisión.")
