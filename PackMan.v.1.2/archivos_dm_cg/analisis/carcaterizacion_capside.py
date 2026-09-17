from pymol import cmd
import numpy as np

print("="*80)
print("ANÁLISIS AUTOMÁTICO DE LA CÁPSIDE")
print("="*80)

# Cargar sistema - DETECCIÓN AUTOMÁTICA DE ARCHIVO
cmd.delete("all")

import os
import glob

# Buscar archivo PDB apropiado en directorio actual y padre
pdb_patterns = [
    "*_cg-WAT.pdb",      # Patrón principal: capside-X_cg-WAT.pdb
    "*-WAT.pdb",         # Alternativo: capside-X-WAT.pdb
    "capside*.pdb",      # Cualquier archivo que empiece con capside
    "*.pdb",             # Último recurso: cualquier PDB
    "../*_cg-WAT.pdb",   # Buscar en directorio padre
    "../*-WAT.pdb",      # Buscar en directorio padre
    "../capside*.pdb",   # Buscar en directorio padre
    "../*.pdb"           # Último recurso en directorio padre
]

archivo_sistema = None
for pattern in pdb_patterns:
    archivos = glob.glob(pattern)
    if archivos:
        # Preferir archivos con WAT (sistema solvatado)
        archivos_wat = [f for f in archivos if "WAT" in f or "wat" in f]
        if archivos_wat:
            archivo_sistema = archivos_wat[0]
        else:
            archivo_sistema = archivos[0]
        break

if archivo_sistema:
    print(f"📂 Archivo detectado: {archivo_sistema}")
    cmd.load(archivo_sistema, "sistema")
else:
    print("❌ No se encontró archivo PDB apropiado")
    print("   Archivos disponibles:", [f for f in os.listdir(".") if f.endswith(".pdb")])
    exit(1)

# Centro geométrico (igual que el radio interno)
from pymol import stored
stored.xyz = [0.0, 0.0, 0.0]
cmd.iterate_state(1, "sistema", "stored.xyz[0] += x; stored.xyz[1] += y; stored.xyz[2] += z")
n_atoms = cmd.count_atoms("sistema")
center = [coord / n_atoms for coord in stored.xyz]

print(f"Centro del sistema: ({center[0]:.2f}, {center[1]:.2f}, {center[2]:.2f})")

# PREGUNTAR AL USUARIO EL RADIO DE LA ESFERA INTERNA
print(f"\n🤔 ¿Cuál es el radio de la esfera interna (en Å)?")
print(f"   (Radio que separa enzimas internas de la cápside externa)")
print(f"   Ejemplo: 89 para sistemas típicos")

while True:
    try:
        radio_interno = float(input("Radio interno (Å): "))
        if 10.0 <= radio_interno <= 500.0:
            break
        else:
            print("❌ Por favor ingresa un radio entre 10 y 500 Å")
    except ValueError:
        print("❌ Por favor ingresa un número válido")

print(f"\n📏 Usando radio interno de {radio_interno} Å para separar componentes")

# Crear pseudoátomo del centro con el radio especificado
cmd.pseudoatom("centro", pos=center, vdw=radio_interno)

# Seleccionar SOLAMENTE la cápside (fuera del radio especificado)
# Excluir completamente las enzimas internas
cmd.select("capside_solo", f"sistema and not resn WT4 and not (sistema within {radio_interno} of centro)")
atomos_capside = cmd.count_atoms("capside_solo")

print(f"✅ CÁPSIDE SELECCIONADA (fuera del radio {radio_interno}Å): {atomos_capside} átomos")
print(f"🚫 Enzimas internas EXCLUIDAS completamente del análisis")

# Verificar que tenemos la cápside
if atomos_capside > 0:
    # Extraer residuos de la cápside (solo la esfera externa)
    stored.residuos_capside = []
    cmd.iterate("capside_solo", "stored.residuos_capside.append(int(resi))")
    residuos_capside = stored.residuos_capside

    residuos_unicos = sorted(list(set(residuos_capside)))

    print(f"\n🔵 Cápside identificada (SOLO ESFERA EXTERNA):")
    print(f"  Residuos únicos: {len(residuos_unicos)}")
    print(f"  Rango: {min(residuos_unicos)} - {max(residuos_unicos)}")
    print(f"  ✅ Enzimas completamente excluidas del análisis")

    # MANEJAR LA CÁPSIDE COMO UNA SOLA UNIDAD EXTERNA
    print(f"\n📦 Analizando ÚNICAMENTE la cápside externa (esfera hacia afuera)")

    # Solo un grupo con todos los residuos de la cápside
    grupos_capside = [residuos_unicos]
    print(f"Cápside completa: {len(residuos_unicos)} residuos")

    def crear_seleccion_residuos(lista_residuos):
        """Crear selección PyMOL desde lista de residuos"""
        if not lista_residuos:
            return ""

        residuos_sorted = sorted(lista_residuos)

        # Para listas muy largas, usar método optimizado
        if len(residuos_sorted) > 200:
            chunks = []
            for i in range(0, len(residuos_sorted), 100):
                chunk = residuos_sorted[i:i+100]
                chunks.append("+".join(map(str, chunk)))
            return "resi " + "+".join(chunks)

        # Para listas más pequeñas, usar rangos
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

        return "resi " + "+".join(rangos)

    # Crear selección de la cápside completa
    print(f"\n" + "="*60)
    print("CREANDO SELECCIÓN DE CÁPSIDE COMPLETA")
    print("="*60)

    capside_data = {}
    grupo_residuos = grupos_capside[0]  # Solo hay un grupo
    color = 'cyan'
    nombre = 'completa'

    if grupo_residuos:
        seleccion_name = f"capside_{nombre}"

        try:
            # Crear selección
            seleccion_str = crear_seleccion_residuos(grupo_residuos)
            cmd.select(seleccion_name, seleccion_str)
            cmd.color(color, seleccion_name)

            n_atomos = cmd.count_atoms(seleccion_name)

            if n_atomos == 0:
                print(f"⚠️ Cápside {nombre}: Selección vacía")
            else:
                # Calcular centro de masa
                stored.coords_capside = []
                cmd.iterate_state(1, seleccion_name,
                                 "stored.coords_capside.append((x, y, z))")
                coords_capside = stored.coords_capside

                if coords_capside:
                    centro_masa = np.array(coords_capside).mean(axis=0)
                    distancia_centro = np.linalg.norm(centro_masa - np.array(center))
                else:
                    centro_masa = np.array([0, 0, 0])
                    distancia_centro = 0

                # Extraer secuencia de muestra
                stored.residuos_seq = []
                rango_muestra = f"{min(grupo_residuos)}-{min(grupo_residuos)+19}"
                cmd.iterate(f"{seleccion_name} and resi {rango_muestra}",
                           "stored.residuos_seq.append((int(resi), resn))")
                residuos_seq = stored.residuos_seq

                secuencia_muestra = [resn for resi, resn in sorted(residuos_seq)]

                capside_data[nombre] = {
                    'seleccion': seleccion_name,
                    'n_residuos': len(grupo_residuos),
                    'n_atomos': n_atomos,
                    'rango': (min(grupo_residuos), max(grupo_residuos)),
                    'color': color,
                    'centro_masa': centro_masa,
                    'distancia_centro': distancia_centro,
                    'secuencia_muestra': secuencia_muestra
                }

                # Crear pseudoátomo para el centro de masa
                if len(coords_capside) > 0:
                    com_name = f"centro_capside_{nombre}"
                    cmd.pseudoatom(com_name, pos=centro_masa.tolist(), vdw=8.0)
                    cmd.show("spheres", com_name)
                    cmd.color(color, com_name)
                    cmd.label(com_name, f'"Cápside\\n{len(grupo_residuos)}r"')

                print(f"✅ Cápside {nombre} ({color}):")
                print(f"   Residuos: {len(grupo_residuos)}")
                print(f"   Átomos: {n_atomos}")
                print(f"   Rango: {min(grupo_residuos)}-{max(grupo_residuos)}")
                print(f"   Distancia centro: {distancia_centro:.2f}Å")
                print(f"   Primeros 10: {' '.join(secuencia_muestra[:10])}")
                print(f"   Selección: {seleccion_name}")

        except Exception as e:
            print(f"❌ Error creando selección para cápside {nombre}: {e}")

    # La selección ya es la cápside completa
    if capside_data:
        print(f"\n✅ Selección 'capside_completa' creada")

    # Colorear la cápside externa seleccionada
    cmd.color("cyan", "capside_solo")
    print(f"🎨 Cápside coloreada en cian para visualización")

else:
    print(f"❌ No se encontraron átomos de cápside fuera del radio de {radio_interno}Å")
    print("   Intenta con un radio menor para capturar la cápside")

# Crear también la selección de todo el sistema proteico
cmd.select("sistema_proteico", "sistema and not resn WT4")
total_proteico = cmd.count_atoms("sistema_proteico")

print(f"\n" + "="*60)
print("RESUMEN DEL SISTEMA")
print("="*60)

print(f"Total proteico: {total_proteico} átomos")
print(f"🔵 CÁPSIDE EXTERNA (análisis): {atomos_capside} átomos ({atomos_capside/total_proteico*100:.1f}%)")
print(f"🚫 Enzimas internas (excluidas): {total_proteico - atomos_capside} átomos ({(total_proteico - atomos_capside)/total_proteico*100:.1f}%)")

# Configurar visualización
print(f"\n" + "="*60)
print("CONFIGURACIÓN DE VISUALIZACIÓN")
print("="*60)

cmd.hide("everything")
cmd.show("cartoon", "sistema")

# Sistema base muy transparente
cmd.color("gray90", "sistema")
cmd.set("cartoon_transparency", 0.95, "sistema")

# Destacar ÚNICAMENTE la cápside externa
cmd.set("cartoon_transparency", 0.2, "capside_solo")

# Destacar la cápside completa
for data in capside_data.values():
    cmd.set("cartoon_transparency", 0.2, data['seleccion'])

# Mostrar el radio de 89Å
cmd.show("mesh", "centro")
cmd.color("red", "centro")
cmd.set("transparency", 0.8, "centro")

# Ocultar agua
cmd.hide("everything", "resn WT4")
cmd.center("sistema")

# Resumen final
print(f"\n🎉 CÁPSIDE IDENTIFICADA EXITOSAMENTE")

print(f"\n🎯 SELECCIÓN DE CÁPSIDE CREADA:")
print(f"     - capside_solo (ÚNICAMENTE la cápside externa - sin enzimas)")
if capside_data:
    for nombre in sorted(capside_data.keys()):
        data = capside_data[nombre]
        print(f"     - {data['seleccion']} ({data['color']}) - {data['n_residuos']} residuos, {data['n_atomos']} átomos")

print(f"\n📋 USO:")
print(f"   Cápside ÚNICAMENTE: pymol -c carcaterizacion_capside.py")
print(f"   ✅ Enzimas completamente excluidas del análisis")
print(f"   🔵 Solo cápside externa seleccionada")

print("="*80)