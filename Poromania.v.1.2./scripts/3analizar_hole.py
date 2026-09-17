#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# ➤ Nombre del mutante desde el nombre de carpeta actual
mut_name = Path.cwd().name

# ➤ Directorio donde están los resultados HOLE
resultados_dir = Path("hole/resultados")
resultados_dir.mkdir(parents=True, exist_ok=True)

# ➤ Leer el TSV generado por HOLE
tsv_path = resultados_dir / "hole_profile.tsv"
if not tsv_path.exists():
    print(f"❌ Archivo TSV no encontrado: {tsv_path}")
    exit(1)

df = pd.read_csv(tsv_path, sep=r"\s+")
df["CanalCoord"] = pd.to_numeric(df["Z"], errors="coerce")
df["Radio"] = pd.to_numeric(df["Radio"], errors="coerce")
df = df.dropna()

# ➤ Check if data is empty
if df.empty:
    print(f"❌ No se encontraron datos válidos del poro en {mut_name}")
    print("   HOLE2 no pudo identificar un canal válido en esta estructura.")
    exit(1)

# ➤ Cálculos básicos
min_radio = df["Radio"].min()
coord_min = df.loc[df["Radio"].idxmin(), "CanalCoord"]
estrechos = df[df["Radio"] < 2.0]
tiene_cuello_estrecho = not estrechos.empty
if tiene_cuello_estrecho:
    inicio = estrechos["CanalCoord"].min()
    fin = estrechos["CanalCoord"].max()
    anchura = fin - inicio
else:
    inicio = fin = anchura = None

# ➤ Gráfico mejorado
fig, ax = plt.subplots(figsize=(24, 12), dpi=300)

# Línea del perfil
ax.plot(df["CanalCoord"], df["Radio"], color="black", linewidth=1.2, label="Radio del canal")

# Línea horizontal del umbral
ax.axhline(1.4, color="red", linestyle="--", linewidth=0.6, label="Umbral 1.4 Å")

# Cruces naranjas donde radio < 1.4 Å
ax.scatter(df["CanalCoord"][df["Radio"] < 1.4],
           df["Radio"][df["Radio"] < 1.4],
           color="orange", marker="x", s=20, zorder=5, label="Radio < 1.4 Å")

# Punto verde en el mínimo
ax.plot(coord_min, min_radio, marker="o", markersize=8, color="green", label=f"Mínimo: {min_radio:.2f} Å")

# ➤ Detalles estéticos
ax.set_title(f"Perfil del poro {mut_name}", fontsize=14, weight='bold')
ax.set_xlabel("Coordenada a lo largo del canal (Å)", fontsize=12, weight='bold')
ax.set_ylabel("Radio del canal (Å)", fontsize=12, weight='bold')
ax.grid(True, linestyle=":", linewidth=0.5)
ax.legend(loc="best", fontsize=9)

# ➤ Layout limpio
fig.tight_layout()

# ➤ Guardar archivos
fig.savefig(resultados_dir / f"perfil_{mut_name}.png", dpi=300)
fig.savefig(resultados_dir / f"perfil_{mut_name}.pdf", dpi=300)

# ➤ Salida por consola
print(f"📏 Mínimo radio: {min_radio:.2f} Å en coord: {coord_min:.2f}")
if tiene_cuello_estrecho:
    print(f"🔻 Zona estrecha (<2 Å): de {inicio:.2f} a {fin:.2f} (anchura: {anchura:.2f} Å)")
else:
    print("✅ No hay zona <2 Å continua en este perfil.")

