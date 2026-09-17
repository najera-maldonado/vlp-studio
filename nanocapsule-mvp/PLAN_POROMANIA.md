# PLAN · Conectar Poromania (HOLE real) y sustratinaitor a Pac-Pore

Diseño de integración. **No implementado aún** — decidido "solo diseño" el 2026-07-23.
Objetivo: que la vista **Pac-Pore** del studio use perfiles de poro **reales** de
`Poromania.v.1.2.` en vez de la curva ilustrativa.

Carpetas hermanas (junto a `nanocapsule-mvp/`):
`Escritorio/Pac-Zyme/uno solo/Poromania.v.1.2.` y `.../sustratinaitor`.

---

## 1 · Qué son (estructura real)

### Poromania.v.1.2. — pipeline HOLE2 + mutagénesis + docking
Etapas:
1. **Descubrimiento del poro** (`pore_analyzer.py`, `visualize_pore.py`): carga
   `poronatural.pdb`, calcula centro geométrico del poro, detecta residuos que lo
   revisten en las 3 cadenas (A/B/C).
2. **Mutagénesis** (`1crear_mutantes.pml`): genera `mutants/mut_*/receptor.pdb`
   aplicando la mutación a las 3 cadenas simultáneamente.
3. **Análisis HOLE** (`4generarhole.sh` → `scripts/1run_hole.sh` →
   `2out_tsv.py` → `3analizar_hole.py`): corre HOLE2 y produce por estructura
   `hole/resultados/hole_profile.tsv`, `hole_out.txt`, `perfil_*.png/pdf`.
4. **Docking** (`smiles_docking_pipeline.py`, `generate_ligand_from_smiles.py`):
   SMILES → PDBQT → vina/idock → afinidad por mutante (aún sin calcular).

### Modelo de datos (lo que importa para integrar)
- Estructuras de entrada: `modelos/BMV/{poronatural,poro3fold,poro5fold,capside}.pdb`,
  `modelos/CCMV/{poronatural,3-folia}.pdb`.
- Por mutante `mutants/mut_<ID>/`:
  - `receptor.pdb` — estructura mutada.
  - `pore_center.txt` — 3 floats (centro del poro, ya centrado). Ej: `9.18 -3.88 2.22`.
  - `pore_vector.txt` — 3 floats (eje del canal). Ej: `-0.40 0.63 -0.67`.
  - `selected_positions.txt` — residuos mutados. Ej: `129,130,131,132`.
  - `hole/resultados/hole_profile.tsv` — **`Z \t Radio`** (cabecera incluida).
- **Formato clave:** el TSV `Z / Radio` es EXACTAMENTE lo que consume la vista
  Pac-Pore (`positions` / `radius`). No hay que transformar nada.

### Estado real hoy
- **1 perfil calculado**: `mutants/mut_129HIS_132GLY/.../hole_profile.tsv`
  (347 puntos, Z ∈ [-21.6, 13.0], **radio mín 1.92 Å** en Z≈-15.4). De aquí salió
  el "1.9 Å" de la maqueta.
- **Sin docking** calculado todavía.
- **Herramientas instaladas**: `hole` (~/bin/hole/hole), `pymol`, `vina`,
  `idock`, `obabel` → se pueden generar perfiles nuevos.

### sustratinaitor — sustrato GYE + MD (rama aparte)
Construye la glucosilceramida (GYE, **714 Da**) en coarse-grained (SIRAH) y
empaqueta 200 copias alrededor de la cápside 3J7L (`3J7L_cg.pdb`, 131.820 beads)
con Packmol, para solvatar/ionizar y correr MD-CG. Relevante para la puerta
**Análisis MD** y para datos reales del sustrato, no para el perfil del poro.

---

## 2 · Cómo implementarlo

### Fase 1 — leer perfiles ya calculados (rápido, real, sin riesgo)
1. **`src/core/paths.py`**: añadir
   `POROMANIA_DIR = PROJECT_ROOT.parent / "Poromania.v.1.2."` (configurable por env).
2. **Backend** (nuevo `pore_service.py` o en `packing_service.py`):
   - `pore_structures()` → escanea `POROMANIA_DIR` y devuelve la lista de
     estructuras con perfil disponible:
     `[{id, tipo:'nativo'|'mutante', mutaciones, has_profile, min_radius}]`.
     (busca `mutants/*/hole/resultados/hole_profile.tsv` y perfiles nativos si los hay).
   - `pore_profile_real(structure_id)` → lee ese TSV y devuelve el MISMO formato que
     hoy usa `pore_profile()`: `{positions, radius, pore_min, min_index,
     mutaciones, source:'HOLE real'}`. Marca zonas `<2 Å`.
3. **`/api/pore/profile`**: preferir el TSV real; la gaussiana queda solo como
   *fallback* etiquetado "ilustrativo" cuando no exista perfil.
   Añadir `/api/pore/structures` para poblar el selector.
4. **`studio.html` (vista Pac-Pore)**:
   - Selector "estructura/mutante analizado" (desde `/api/pore/structures`).
   - Dibujar la curva real; añadir las marcas de constricción `<2 Å` (como
     `3analizar_hole.py`).
   - Badge `(ilustrativo)` → **`HOLE real`** cuando la fuente es un TSV.
   - Mantener el veredicto pasa/no-pasa vs radio del sustrato (ya existe).

### Fase 2 — generar bajo demanda (pesado, opcional, herramientas ya están)
5. Botón "Generar HOLE" que corre el pipeline (`pymol -cq` + `hole`) sobre una
   estructura nativa (`modelos/BMV/poro3fold.pdb`, `poro5fold.pdb`) o un mutante.
   Asíncrono (cola/proceso en background); al terminar aparece su `hole_profile.tsv`
   y se puede leer con la Fase 1. Reusar los scripts de Poromania, no reescribir HOLE.

### Sustratos reales
Los radios/pesos del sustrato salen de `Poromania/ligand_info.txt`
(glucosilceramida 714 Da) y del diseño; sustituir los valores ilustrativos de
`_SUBSTRATES` por los reales cuando se confirmen los radios de sección.

---

## 3 · Riesgos / decisiones abiertas
- **Acoplamiento entre carpetas**: el studio (nanocapsule-mvp) leería de una carpeta
  hermana. Mejor por ruta configurable (env var) que hardcodeada.
- **Centro/eje del poro**: cada estructura tiene su `pore_center`/`pore_vector`; si se
  quisiera superponer la esfera/eje en el visor 3D, usar esos ficheros.
- **Alcance del selector**: hoy solo hay 1 perfil real; la Fase 1 ya es útil pero la
  vista se llena de verdad tras generar más (Fase 2).
