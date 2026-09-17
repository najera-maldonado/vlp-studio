#!/usr/bin/env python3
"""
Generador de scripts CPPTRAJ para análisis individual usando caracterización automática
- Usa carcaterizacion_capside.py para definir residuos de cápside
- Usa carcaterizacion_enzimas.py para definir residuos de enzimas
- Genera: Enzimas: SASA, RMSF, RMSD
-         Cápside: RyG (Radio de giro), RMSD
- Estructura: analisis_individual/enzimas/enzima#/{sasa,rmsf,rmsd}
-            analisis_individual/capside/{ryg,rmsd}
"""

import os
import glob
import json
from pymol import cmd
from collections import defaultdict

def caracterizar_capside(archivo_pdb, radio_interno):
    """
    Caracterización automática de cápside usando lógica de carcaterizacion_capside.py
    Retorna lista de residuos de la cápside externa
    """
    from pymol import stored

    # Cargar sistema
    cmd.delete("all")
    cmd.load(archivo_pdb, "sistema")

    # Calcular centro geométrico
    stored.xyz = [0.0, 0.0, 0.0]
    cmd.iterate_state(1, "sistema", "stored.xyz[0] += x; stored.xyz[1] += y; stored.xyz[2] += z")
    n_atoms = cmd.count_atoms("sistema")
    center = [coord / n_atoms for coord in stored.xyz]

    # Crear pseudoátomo del centro
    cmd.pseudoatom("centro", pos=center, vdw=radio_interno)

    # Seleccionar SOLAMENTE la cápside (fuera del radio especificado)
    cmd.select("capside_solo", f"sistema and not resn WT4 and not (sistema within {radio_interno} of centro)")

    # Extraer residuos de la cápside
    stored.residuos_capside = []
    cmd.iterate("capside_solo", "stored.residuos_capside.append(int(resi))")
    residuos_capside = sorted(list(set(stored.residuos_capside)))

    return residuos_capside

def caracterizar_enzimas(archivo_pdb, radio_interno, residuos_por_enzima):
    """
    Caracterización automática de enzimas usando lógica de carcaterizacion_enzimas.py
    Retorna lista de grupos de residuos para cada enzima
    """
    from pymol import stored

    # Cargar sistema
    cmd.delete("all")
    cmd.load(archivo_pdb, "sistema")

    # Calcular centro geométrico
    stored.xyz = [0.0, 0.0, 0.0]
    cmd.iterate_state(1, "sistema", "stored.xyz[0] += x; stored.xyz[1] += y; stored.xyz[2] += z")
    n_atoms = cmd.count_atoms("sistema")
    center = [coord / n_atoms for coord in stored.xyz]

    # Crear pseudoátomo del centro
    cmd.pseudoatom("centro", pos=center, vdw=radio_interno)

    # Seleccionar enzimas dentro del radio
    cmd.select("dentro_radio", f"sistema and not resn WT4 and (sistema within {radio_interno} of centro)")

    # Extraer residuos de enzimas
    stored.residuos_raw = []
    cmd.iterate("dentro_radio", "stored.residuos_raw.append(int(resi))")
    residuos_enzimas = sorted(list(set(stored.residuos_raw)))

    # Calcular número de enzimas
    total_residuos = len(residuos_enzimas)
    n_enzimas = total_residuos // residuos_por_enzima

    # Dividir residuos en grupos de tamaño fijo
    grupos_enzimas = []
    for i in range(n_enzimas):
        start_idx = i * residuos_por_enzima
        end_idx = start_idx + residuos_por_enzima
        grupo = residuos_enzimas[start_idx:end_idx]
        grupos_enzimas.append(grupo)

    return grupos_enzimas, n_enzimas

print("="*80)
print("GENERADOR DE ANÁLISIS INDIVIDUAL CON CARACTERIZACIÓN AUTOMÁTICA")
print("="*80)

# DETECCIÓN AUTOMÁTICA DE ARCHIVOS
print("\n🔍 DETECTANDO ARCHIVOS...")

# Detectar directorio 1_* automáticamente
import re
current_path = os.getcwd()
# Buscar patrón 1_* en la ruta actual
match = re.search(r'/1_\d+/', current_path)
if match:
    # Extraer el directorio 1_N
    one_n_dir = match.group(0).strip('/')
    print(f"📁 Directorio detectado: {one_n_dir}")
    # Desde analisis/ necesitamos ir a 1_N/
    base_dir = "../"  # Ir al directorio 1_N
else:
    print("⚠️ No se pudo detectar directorio 1_*, usando directorio padre")
    base_dir = "../"

pdb_patterns = ["*_cg-WAT.pdb", "*-WAT.pdb", "capside*.pdb", "*.pdb"]
archivo_pdb = None
for pattern in pdb_patterns:
    archivos = glob.glob(os.path.join(base_dir, pattern))
    if archivos:
        archivos_wat = [f for f in archivos if "WAT" in f or "wat" in f]
        archivo_pdb = os.path.basename(archivos_wat[0]) if archivos_wat else os.path.basename(archivos[0])
        break

# Buscar archivo topology
topo_patterns = ["*.prmtop", "*.top"]
archivo_topo = None
for pattern in topo_patterns:
    archivos = glob.glob(os.path.join(base_dir, pattern))
    if archivos:
        archivo_topo = os.path.basename(archivos[0])
        break

# Buscar archivos de trayectoria
traj_patterns = ["*prod*.nc", "*.nc"]
archivos_traj = []
for pattern in traj_patterns:
    archivos = glob.glob(os.path.join(base_dir, pattern))
    archivos_traj.extend([os.path.basename(f) for f in archivos if "prod" in f.lower()])

if not archivos_traj:
    archivos_nc = glob.glob(os.path.join(base_dir, "*.nc"))
    archivos_traj = [os.path.basename(f) for f in archivos_nc]

print(f"📂 PDB: {archivo_pdb}")
print(f"📂 Topología: {archivo_topo}")
print(f"📂 Trayectorias: {archivos_traj}")

if not all([archivo_pdb, archivo_topo, archivos_traj]):
    print("❌ No se encontraron todos los archivos necesarios")
    exit(1)

# PARÁMETROS DEL USUARIO
print(f"\n🤔 ¿Radio de separación interno (Å)?")
while True:
    try:
        radio_interno = float(input("Radio interno (Å): "))
        if 10.0 <= radio_interno <= 500.0:
            break
        else:
            print("❌ Radio entre 10 y 500 Å")
    except ValueError:
        print("❌ Número válido")

print(f"\n🤔 ¿Cuántos residuos tiene cada enzima individual?")
while True:
    try:
        residuos_por_enzima = int(input("Residuos por enzima: "))
        if 50 <= residuos_por_enzima <= 2000:
            break
        else:
            print("❌ Número entre 50 y 2000 residuos")
    except ValueError:
        print("❌ Número válido")

# CARACTERIZACIÓN AUTOMÁTICA USANDO LOS SCRIPTS ESPECIALIZADOS
print(f"\n🧬 CARACTERIZANDO COMPONENTES AUTOMÁTICAMENTE...")

archivo_pdb_completo = os.path.join(base_dir, archivo_pdb)

# Caracterizar cápside
print(f"🔵 Caracterizando cápside externa...")
residuos_capside = caracterizar_capside(archivo_pdb_completo, radio_interno)
print(f"✅ Cápside: {len(residuos_capside)} residuos")

# Caracterizar enzimas
print(f"🧬 Caracterizando enzimas internas...")
grupos_enzimas, n_enzimas = caracterizar_enzimas(archivo_pdb_completo, radio_interno, residuos_por_enzima)
print(f"✅ Enzimas: {n_enzimas} enzimas detectadas")

# Resumen de caracterización
total_residuos_enzimas = sum(len(grupo) for grupo in grupos_enzimas)
for i, grupo in enumerate(grupos_enzimas, 1):
    print(f"   Enzima {i}: {len(grupo)} residuos ({min(grupo)}-{max(grupo)})")

residuos_sobrantes = (total_residuos_enzimas // residuos_por_enzima) * residuos_por_enzima
if residuos_sobrantes != total_residuos_enzimas:
    print(f"   ⚠️ {total_residuos_enzimas - residuos_sobrantes} residuos sobrantes ignorados")

def crear_rango_residuos(lista_residuos):
    """Crear máscara de residuos para CPPTRAJ"""
    if not lista_residuos:
        return ""

    residuos_sorted = sorted(lista_residuos)
    rangos = []
    inicio = residuos_sorted[0]
    anterior = residuos_sorted[0]

    for resi in residuos_sorted[1:]:
        if resi != anterior + 1:
            if inicio == anterior:
                rangos.append(str(inicio))
            else:
                rangos.append(f"{inicio}-{anterior}")
            inicio = resi
        anterior = resi

    if inicio == anterior:
        rangos.append(str(inicio))
    else:
        rangos.append(f"{inicio}-{anterior}")

    return ",".join(rangos)

# CREAR ESTRUCTURA DE DIRECTORIOS
print(f"\n📁 CREANDO ESTRUCTURA DE DIRECTORIOS...")

base_dir = "analisis_individual"
os.makedirs(base_dir, exist_ok=True)

# Directorio para enzimas
enzimas_dir = os.path.join(base_dir, "enzimas")
os.makedirs(enzimas_dir, exist_ok=True)

for i in range(1, n_enzimas + 1):
    enzima_dir = os.path.join(enzimas_dir, f"enzima{i}")
    os.makedirs(enzima_dir, exist_ok=True)
    os.makedirs(os.path.join(enzima_dir, "rmsf"), exist_ok=True)
    os.makedirs(os.path.join(enzima_dir, "sasa"), exist_ok=True)
    os.makedirs(os.path.join(enzima_dir, "rmsd"), exist_ok=True)

# Directorio para cápside
capside_dir = os.path.join(base_dir, "capside")
os.makedirs(capside_dir, exist_ok=True)
os.makedirs(os.path.join(capside_dir, "ryg"), exist_ok=True)
os.makedirs(os.path.join(capside_dir, "rmsd"), exist_ok=True)

print(f"✅ Estructura creada en: {base_dir}/")

# GENERAR SCRIPTS CPPTRAJ INDIVIDUALES
print(f"\n📝 GENERANDO SCRIPTS CPPTRAJ...")

# Configuración común
archivos_traj_unicos = list(set(archivos_traj))
traj_str = " ".join([f"../../../../../{f}" for f in archivos_traj_unicos])

# Scripts para enzimas
for i, grupo_residuos in enumerate(grupos_enzimas, 1):
    if not grupo_residuos:
        continue

    rango_residuos = crear_rango_residuos(grupo_residuos)
    enzima_dir = os.path.join(enzimas_dir, f"enzima{i}")

    # SCRIPT RMSF
    rmsf_script = f"""# RMSF para enzima {i}
# Residuos: {min(grupo_residuos)}-{max(grupo_residuos)}

parm ../../../../../{archivo_topo}
trajin {traj_str}

# RMSF backbone (GN,GO,GC para SIRAH)
atomicfluct :{rango_residuos}&@GN,GO,GC out enzima{i}_rmsf_backbone.dat byres

# RMSF all-atom
atomicfluct :{rango_residuos} out enzima{i}_rmsf_all.dat byres

run
"""

    with open(os.path.join(enzima_dir, "rmsf", "rmsf.cpptraj"), "w") as f:
        f.write(rmsf_script)

    # SCRIPT SASA
    sasa_script = f"""# SASA para enzima {i}
# Residuos: {min(grupo_residuos)}-{max(grupo_residuos)}

parm ../../../../../{archivo_topo}
trajin {traj_str}

# Superficie accesible al solvente
surf :{rango_residuos} out enzima{i}_sasa.dat

run
"""

    with open(os.path.join(enzima_dir, "sasa", "sasa.cpptraj"), "w") as f:
        f.write(sasa_script)

    # SCRIPT RMSD
    rmsd_script = f"""# RMSD para enzima {i}
# Residuos: {min(grupo_residuos)}-{max(grupo_residuos)}

parm ../../../../../{archivo_topo}
trajin {traj_str}

# RMSD backbone
rms first :{rango_residuos}&@GN,GO,GC mass out enzima{i}_rmsd_backbone.dat

# RMSD all-atom
rms first :{rango_residuos} mass out enzima{i}_rmsd_all.dat

run
"""

    with open(os.path.join(enzima_dir, "rmsd", "rmsd.cpptraj"), "w") as f:
        f.write(rmsd_script)

    print(f"✅ Scripts para enzima {i} creados")

# Scripts para cápside
if residuos_capside:
    rango_capside = crear_rango_residuos(residuos_capside)

    # SCRIPT RyG (Radio de giro)
    ryg_script = f"""# Radio de giro para cápside
# Residuos: {min(residuos_capside)}-{max(residuos_capside)}

parm ../../../../{archivo_topo}
trajin {" ".join([f"../../../../{f}" for f in archivos_traj_unicos])}

# Radio de giro
radgyr :{rango_capside} out capside_ryg.dat mass

run
"""

    with open(os.path.join(capside_dir, "ryg", "ryg.cpptraj"), "w") as f:
        f.write(ryg_script)

    # SCRIPT RMSD
    rmsd_script = f"""# RMSD para cápside
# Residuos: {min(residuos_capside)}-{max(residuos_capside)}

parm ../../../../{archivo_topo}
trajin {" ".join([f"../../../../{f}" for f in archivos_traj_unicos])}

# RMSD backbone
rms first :{rango_capside}&@GN,GO,GC mass out capside_rmsd_backbone.dat

# RMSD all-atom
rms first :{rango_capside} mass out capside_rmsd_all.dat

run
"""

    with open(os.path.join(capside_dir, "rmsd", "rmsd.cpptraj"), "w") as f:
        f.write(rmsd_script)

    print(f"✅ Scripts para cápside creados")

# CREAR SCRIPT EJECUTOR PRINCIPAL
print(f"\n🚀 CREANDO SCRIPT EJECUTOR...")

ejecutor_script = f"""#!/bin/bash
# Ejecutor de análisis individual
# Estructura: analisis_individual/enzimas/enzima#/{{rmsf,sasa,rmsd}}
#            analisis_individual/capside/{{ryg,rmsd}}

echo "================================================================================"
echo "EJECUTANDO ANÁLISIS INDIVIDUAL"
echo "================================================================================"

cd {base_dir}

# Análisis de enzimas
"""

for i in range(1, n_enzimas + 1):
    ejecutor_script += f"""
echo "🧬 Analizando enzima {i}..."
cd enzimas/enzima{i}

echo "  📊 RMSF..."
cd rmsf && cpptraj -i rmsf.cpptraj && cd ..

echo "  🔍 SASA..."
cd sasa && cpptraj -i sasa.cpptraj && cd ..

echo "  📈 RMSD..."
cd rmsd && cpptraj -i rmsd.cpptraj && cd ..

cd ../..
"""

ejecutor_script += f"""
# Análisis de cápside
echo "🏗️ Analizando cápside..."
cd capside

echo "  ⚪ Radio de giro..."
cd ryg && cpptraj -i ryg.cpptraj && cd ..

echo "  📈 RMSD..."
cd rmsd && cpptraj -i rmsd.cpptraj && cd ..

cd ..

echo "✅ Análisis completado"
echo "📁 Resultados organizados en:"
echo "   - enzimas/enzima#/rmsf/enzima#_rmsf_*.dat"
echo "   - enzimas/enzima#/sasa/enzima#_sasa.dat"
echo "   - enzimas/enzima#/rmsd/enzima#_rmsd_*.dat"
echo "   - capside/ryg/capside_ryg.dat"
echo "   - capside/rmsd/capside_rmsd_*.dat"
"""

with open(f"ejecutar_analisis_individual.sh", "w") as f:
    f.write(ejecutor_script)

os.chmod("ejecutar_analisis_individual.sh", 0o755)

# Guardar información del sistema con caracterización automática
info_sistema = {
    "metodo": "caracterizacion_automatica",
    "n_enzimas": n_enzimas,
    "radio_interno": radio_interno,
    "residuos_por_enzima": residuos_por_enzima,
    "archivo_pdb": archivo_pdb,
    "archivo_topo": archivo_topo,
    "archivos_traj": archivos_traj,
    "residuos_capside": residuos_capside,
    "grupos_enzimas": grupos_enzimas,
    "caracterizacion": {
        "capside_residuos_totales": len(residuos_capside),
        "enzimas_residuos_totales": sum(len(grupo) for grupo in grupos_enzimas),
        "rango_capside": (min(residuos_capside), max(residuos_capside)) if residuos_capside else (0, 0),
        "rangos_enzimas": [(min(grupo), max(grupo)) for grupo in grupos_enzimas if grupo]
    }
}

with open(f"{base_dir}/sistema_info.json", "w") as f:
    json.dump(info_sistema, f, indent=2)

print(f"\n" + "="*80)
print("✅ GENERACIÓN COMPLETADA CON CARACTERIZACIÓN AUTOMÁTICA")
print("="*80)

print(f"\n🧬 CARACTERIZACIÓN UTILIZADA:")
print(f"   • Método: Automático usando scripts especializados")
print(f"   • Radio interno: {radio_interno} Å")
print(f"   • Residuos por enzima: {residuos_por_enzima}")

print(f"\n📊 COMPONENTES CARACTERIZADOS:")
print(f"   • {n_enzimas} enzimas: SASA, RMSF, RMSD")
print(f"   • 1 cápside: RyG, RMSD")
print(f"   • Total scripts: {n_enzimas * 3 + 2}")

print(f"\n🔍 DETALLES DE CARACTERIZACIÓN:")
print(f"   • Cápside: {len(residuos_capside)} residuos ({min(residuos_capside)}-{max(residuos_capside)})")
for i, grupo in enumerate(grupos_enzimas, 1):
    if grupo:
        print(f"   • Enzima {i}: {len(grupo)} residuos ({min(grupo)}-{max(grupo)})")

print(f"\n📁 ESTRUCTURA CREADA:")
print(f"   analisis_individual/")
print(f"   ├── enzimas/")
for i in range(1, n_enzimas + 1):
    print(f"   │   ├── enzima{i}/")
    print(f"   │   │   ├── rmsf/rmsf.cpptraj")
    print(f"   │   │   ├── sasa/sasa.cpptraj")
    print(f"   │   │   └── rmsd/rmsd.cpptraj")
print(f"   └── capside/")
print(f"       ├── ryg/ryg.cpptraj")
print(f"       └── rmsd/rmsd.cpptraj")

print(f"\n🚀 PARA EJECUTAR:")
print(f"   bash ejecutar_analisis_individual.sh")

print(f"\n📋 INFORMACIÓN GUARDADA EN:")
print(f"   analisis_individual/sistema_info.json")

print("="*80)
