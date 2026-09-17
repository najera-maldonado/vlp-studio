from pymol import cmd

# Cargar cápside
cmd.load("capside.pdb", "capside")
cmd.center("capside")
cmd.orient("capside")

# Calcular centro geométrico
stored = {'xyz': [0.0, 0.0, 0.0]}
cmd.iterate_state(1, "capside", "stored['xyz'][0] += x; stored['xyz'][1] += y; stored['xyz'][2] += z")
n_atoms = cmd.count_atoms("capside")
center = [coord / n_atoms for coord in stored['xyz']]

# Crear pseudoátomo
cmd.pseudoatom("centro", pos=center, vdw=1.0)
cmd.show("spheres", "centro")
cmd.set("sphere_scale", 1.0, "centro")
cmd.color("red", "centro")

# Crear selección de cápside sin el centro
cmd.select("capa", "capside and not centro")

# Buscar colisión
print("\n=== Buscando colisión con pseudoátomo ===")
colision_detectada = False

for r in range(5, 200):  # puedes ajustar el máximo
    cmd.alter("centro", f"vdw={r}")
    cmd.rebuild()
    cmd.select("cercano", f"byres (capa within {r + 0.5} of centro)")
    colisiones = cmd.count_atoms("cercano")
    print(f"Radio {r} Å → {colisiones} átomos en colisión")
    
    if colisiones > 0 and not colision_detectada:
        print(f"\n⚠️ Primera colisión detectada a {r} Å")
        radio_colision = r
        colision_detectada = True
    elif colision_detectada:
        radio_colision = r
        print(f"\n✅ Expansión 1 Å más allá de la colisión: {r} Å")
        break

# Guardar en archivo
with open("radio_interno.txt", "w") as f:
    f.write(f"{radio_colision}\n")
