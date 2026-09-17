from pathlib import Path

# 📁 Carpeta de resultados completa
resultados_dir = Path("hole/resultados")
resultados_dir.mkdir(parents=True, exist_ok=True)

# 📄 Rutas internas
infile_path = resultados_dir / "hole_out.txt"
outfile_path = resultados_dir / "hole_profile.tsv"

# ✍️ Escritura del TSV si el archivo original existe
if infile_path.exists():
    with open(infile_path) as infile, open(outfile_path, "w") as outfile:
        outfile.write("Z\tRadio\n")  # Cabecera TSV
        for line in infile:
            if line.strip().startswith("#") or "RADIUS" in line or line.strip() == "":
                continue
            partes = line.strip().split()
            try:
                z = float(partes[0])
                radio = float(partes[1])
                if radio > 0.5:
                    outfile.write(f"{z:.3f}\t{radio:.3f}\n")
            except Exception:
                continue
else:
    print(f"❌ No se encontró el archivo de entrada: {infile_path}")
