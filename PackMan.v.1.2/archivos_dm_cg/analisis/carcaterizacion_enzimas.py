from pymol import cmd
from collections import defaultdict

print("="*80)
print("DIVISIÓN AUTOMÁTICA DE ENZIMAS ENCAPSULADAS")
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

# Recrear dentro_radio exactamente como la tienes
from pymol import stored
stored.xyz = [0.0, 0.0, 0.0]
cmd.iterate_state(1, "sistema", "stored.xyz[0] += x; stored.xyz[1] += y; stored.xyz[2] += z")
n_atoms = cmd.count_atoms("sistema")
center = [coord / n_atoms for coord in stored.xyz]

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

cmd.pseudoatom("centro", pos=center, vdw=radio_interno)
cmd.select("dentro_radio", f"sistema and not resn WT4 and (sistema within {radio_interno} of centro)")

print(f"Átomos en dentro_radio: {cmd.count_atoms('dentro_radio')}")

# Extraer todos los residuos
stored.residuos_raw = []
cmd.iterate("dentro_radio", "stored.residuos_raw.append(int(resi))")
residuos_raw = stored.residuos_raw
residuos_unicos = sorted(list(set(residuos_raw)))

total_residuos = len(residuos_unicos)
print(f"Total residuos: {total_residuos}")
print(f"Rango: {residuos_unicos[0]} - {residuos_unicos[-1]}")

# PREGUNTAR AL USUARIO CUÁNTOS RESIDUOS TIENE CADA ENZIMA
print(f"\n🤔 ¿Cuántos residuos tiene cada enzima individual?")
print(f"   (Ejemplo: 497 residuos por enzima para glucocerebrosidasa)")

while True:
    try:
        residuos_por_enzima = int(input("Residuos por enzima: "))
        if 50 <= residuos_por_enzima <= 2000:
            break
        else:
            print("❌ Por favor ingresa un número entre 50 y 2000 residuos")
    except ValueError:
        print("❌ Por favor ingresa un número válido")

# Calcular cuántas enzimas tenemos automáticamente
n_enzimas = total_residuos // residuos_por_enzima
residuos_sobrantes = total_residuos % residuos_por_enzima

print(f"\n📊 Con {residuos_por_enzima} residuos por enzima:")
print(f"   • {n_enzimas} enzimas completas detectadas")
print(f"   • {residuos_sobrantes} residuos sobrantes")

if residuos_sobrantes > 0:
    print(f"   ⚠️ Los {residuos_sobrantes} residuos sobrantes serán ignorados")

# Dividir residuos en grupos de tamaño fijo
grupos_residuos = []
for i in range(n_enzimas):
    start_idx = i * residuos_por_enzima
    end_idx = start_idx + residuos_por_enzima
    grupo = residuos_unicos[start_idx:end_idx]
    grupos_residuos.append(grupo)
    print(f"Enzima {i+1}: {len(grupo)} residuos ({min(grupo)}-{max(grupo)})")

# Crear selecciones PyMOL
print(f"\n" + "="*60)
print(f"CREANDO SELECCIONES DE LAS {n_enzimas} ENZIMAS ({residuos_por_enzima} RESIDUOS C/U)")
print("="*60)

def crear_seleccion_optimizada(lista_residuos):
    """Crear selección PyMOL optimizada para residuos no consecutivos"""
    if not lista_residuos:
        return ""

    residuos_sorted = sorted(lista_residuos)

    # Para listas largas con muchos gaps, usar selección directa
    if len(residuos_sorted) > 200:
        # Agrupar en chunks de 100 para evitar límites de PyMOL
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

# Arrays de colores y nombres con reserva para hasta 100 enzimas
colores_base = ['marine', 'forest', 'orange', 'red', 'yellow', 'purple', 'cyan', 'magenta', 'brown', 'pink',
                'gray', 'lime', 'violet', 'salmon', 'chocolate', 'gold', 'silver', 'navy', 'olive', 'teal']

# Generar más colores si se necesitan
while len(colores_base) < n_enzimas:
    # Añadir variaciones de los colores base
    base_idx = len(colores_base) % 20
    colores_base.append(f"color{len(colores_base)}")

colores = colores_base[:n_enzimas]

# Nombres automáticos
nombres = [f"E{i+1}" for i in range(n_enzimas)]
enzimas_datos = {}

for i, (grupo_residuos, color, nombre) in enumerate(zip(grupos_residuos, colores, nombres), 1):
    if not grupo_residuos:
        continue

    seleccion_name = f"enzima_{i}"

    # Crear selección PyMOL
    try:
        seleccion_str = crear_seleccion_optimizada(grupo_residuos)
        cmd.select(seleccion_name, seleccion_str)
        cmd.color(color, seleccion_name)

        n_atomos = cmd.count_atoms(seleccion_name)

        # Verificar que la selección funcionó
        if n_atomos == 0:
            print(f"⚠️ Enzima {i}: Selección vacía, intentando método alternativo...")
            # Método alternativo: selección por lista individual
            seleccion_individual = "resi " + "+".join(map(str, grupo_residuos[:50]))  # Primeros 50
            cmd.select(seleccion_name, seleccion_individual)
            n_atomos = cmd.count_atoms(seleccion_name)

    except Exception as e:
        print(f"❌ Error creando selección para enzima {i}: {e}")
        continue

    # Extraer secuencia
    stored.residuos_seq = []
    cmd.iterate(seleccion_name, "stored.residuos_seq.append((int(resi), resn))")
    residuos_seq = stored.residuos_seq

    if residuos_seq:
        residuos_dict = {resi: resn for resi, resn in residuos_seq}
        residuos_ordenados = sorted(residuos_dict.keys())
        secuencia = [residuos_dict[resi] for resi in residuos_ordenados]

        # Composición
        composicion = defaultdict(int)
        for resn in secuencia:
            composicion[resn] += 1

        # Calcular centro de masa aproximado
        stored.coords_muestra = []
        cmd.iterate_state(1, f"{seleccion_name} and name CA",
                         "stored.coords_muestra.append((x, y, z))")
        coords_muestra = stored.coords_muestra

        if coords_muestra:
            import numpy as np
            centro_masa = np.array(coords_muestra).mean(axis=0)
            distancia_centro = np.linalg.norm(centro_masa - np.array(center))
        else:
            centro_masa = [0, 0, 0]
            distancia_centro = 0

        enzimas_datos[i] = {
            'seleccion': seleccion_name,
            'residuos': grupo_residuos,
            'n_residuos': len(grupo_residuos),
            'n_atomos': n_atomos,
            'secuencia': secuencia,
            'composicion': dict(composicion),
            'centro_masa': centro_masa,
            'distancia_centro': distancia_centro,
            'color': color,
            'nombre': nombre
        }

        # Crear pseudoátomo para centro
        if len(coords_muestra) > 0:
            com_name = f"centro_enzima_{i}"
            cmd.pseudoatom(com_name, pos=centro_masa.tolist(), vdw=4.0)
            cmd.show("spheres", com_name)
            cmd.color(color, com_name)
            cmd.label(com_name, f'"E{i}\\n{len(grupo_residuos)}"')

        print(f"✅ Enzima {i} ({nombre}):")
        print(f"   Residuos: {len(grupo_residuos)}")
        print(f"   Átomos: {n_atomos}")
        print(f"   Rango: {min(grupo_residuos)}-{max(grupo_residuos)}")
        print(f"   Distancia centro: {distancia_centro:.2f}Å")
        print(f"   Primeros 10: {' '.join(secuencia[:10])}")
        print(f"   Selección: {seleccion_name}")

        # Verificar si la enzima está completa (comparar átomos esperados)
        atomos_esperados = len(grupo_residuos) * 4.8  # ~4.8 átomos por residuo en SIRAH
        if n_atomos < atomos_esperados * 0.5:
            print(f"   ⚠️ POSIBLEMENTE INCOMPLETA (esperados: ~{atomos_esperados:.0f})")
        else:
            print(f"   ✅ COMPLETA")

# Verificar identidad
print(f"\n" + "="*60)
print("VERIFICACIÓN DE IDENTIDAD")
print("="*60)

if len(enzimas_datos) >= 2:
    print("RESUMEN:")
    for i in sorted(enzimas_datos.keys()):
        data = enzimas_datos[i]
        print(f"  Enzima {i}: {data['n_residuos']} residuos, {data['n_atomos']} átomos")

    # Comparar secuencias
    if len(enzimas_datos) >= 2:
        print(f"\nSIMILARIDAD DE SECUENCIAS:")
        ids = sorted(enzimas_datos.keys())
        for i in range(len(ids)):
            for j in range(i+1, len(ids)):
                id1, id2 = ids[i], ids[j]
                seq1 = enzimas_datos[id1]['secuencia']
                seq2 = enzimas_datos[id2]['secuencia']

                min_len = min(len(seq1), len(seq2))
                if min_len > 10:  # Solo comparar si hay suficientes residuos
                    diferencias = sum(1 for a, b in zip(seq1[:min_len], seq2[:min_len]) if a != b)
                    similaridad = (1 - diferencias/min_len) * 100
                    print(f"  Enzima {id1} vs {id2}: {diferencias}/{min_len} diferencias, {similaridad:.1f}% similar")

# Configurar visualización
cmd.hide("everything")
cmd.show("cartoon", "sistema")
cmd.color("gray80", "sistema")
cmd.set("cartoon_transparency", 0.8, "sistema")

for data in enzimas_datos.values():
    cmd.set("cartoon_transparency", 0.0, data['seleccion'])

cmd.hide("everything", "resn WT4")
cmd.show("mesh", "centro")
cmd.color("red", "centro")
cmd.set("transparency", 0.8, "centro")
cmd.center("dentro_radio")

print(f"\n✅ DIVISIÓN POR TERCIOS COMPLETADA")
print(f"📊 Enzimas creadas: {len(enzimas_datos)}")
selecciones = [data['seleccion'] for data in enzimas_datos.values()]
print(f"🎯 Selecciones: {', '.join(selecciones)}")

# Verificar cuáles están completas
enzimas_completas = [i for i, data in enzimas_datos.items()
                    if data['n_atomos'] > data['n_residuos'] * 2]  # Al menos 2 átomos por residuo

if len(enzimas_completas) == n_enzimas:
    print(f"🎉 LAS {n_enzimas} ENZIMAS ESTÁN COMPLETAS DENTRO DEL RADIO")
else:
    print(f"⚠️ Solo {len(enzimas_completas)} de {n_enzimas} enzimas están completas: {enzimas_completas}")

print("="*80)