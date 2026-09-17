# SESIÓN · Studio PAC-ZYME — registro y cambios

Registro de la sesión **2026-07-23 → 2026-07-24**. Complementa `LO_APRENDIDO.md`
(la visión) con el estado real del código. Arranque:

```bash
cd nanocapsule-mvp && FLASK_DEBUG=0 python3 src/web/app.py   # http://localhost:5000/
```

El studio (`src/web/templates/studio.html`) es una SPA con pestañas servida por
Flask. Motores reales en carpetas hermanas: `../Poromania.v.1.2.` (HOLE/docking),
`../sustratinaitor` (sustrato+MD), `../PackMan.v.1.2` (MD SIRAH).

---

## 1 · Las 5 pestañas

### BIBLIOTECA (`/api/library/detail`) — datos reales
Tablas de cáscaras (T-number por nº de cadenas, PDB, átomos, cadenas, radio) y
cargos (PDB, uso, enfermedad, átomos, Rg y V excl de `vdw_volumes_results.txt`).
Clic en fila → fija estructura y salta al Studio.

### STUDIO 3D — visor NGL + empaquetado
- Preview de enzimas **dentro** de la cápside (colocación aleatoria en el radio).
- **Sustrato alrededor** (`/api/preview/substrate`): N copias del sustrato en una
  caja alrededor de la cápside (cavidad+exterior). El sustrato es **elegible por
  SMILES** (RDKit genera la 3D real; presets glucosilceramida/glucosa/aspirina).
  Nº de sustratos elegible (slider 1-300).
- Esfera de radio interno como **malla** (cilindros); crece animada al calcular radio.
- **Preparador DM**: checkbox que dibuja la **box de simulación** (cubo de alambre)
  + botón que genera `packmol_input.inp` + `gensystem.leap` reales
  (`/api/md/box`, `/api/md/prepare`).
- Cápside coloreada por cadena; enzimas/sustratos por `modelindex`; fondo blanco.

### PAC-PORE — REAL de punta a punta (motor: Poromania)
- **Perfil HOLE real** (`/api/pore/run_hole`): corre el binario `hole` sobre los
  modelos de Poromania (`modelos/*/poro*.pdb`) con el **eje de simetría exacto**
  (eigenvector del valor propio distinto del tensor de inercia) + `rseed`.
  Poros nativos 3-fold ≈2.47 Å, 5-fold ≈1.68 Å, reproducibles (~300 pts).
- **Sustrato por SMILES** (`/api/pore/section`): radio de sección mínima real
  (RDKit PCA) → pasa/no-pasa real vs el poro.
- **Canal 3D** (`/api/pore/channels`, `/api/pore/channel`): carga el
  `hole_spheres.pdb` real en un visor NGL, coloreado por radio (B-factor).
- **Cribado de mutantes**:
  - *Auto* (`/api/pore/screen`): identifica residuos del poro en la constricción,
    genera librería GLY/ALA con PyMOL, corre HOLE en cada uno, tabla rankeada.
  - *Manual* (`/api/pore/mutant`): escribes `pos:AA` (p.ej. `84:TRP,145:ASP`) y
    evalúa ese mutante. TRP cierra el poro (−1.97 Å), GLY lo abre (+0.82).
- **Docking + correlación** (`/api/pore/dock`): prepara receptor (obabel `-xr` +
  gasteiger) y ligando (SMILES), dockea con **vina** en caja centrada en la
  constricción (WT + mutantes), scatter radio-de-poro vs afinidad + Pearson.
  Insight: abrir el poro **debilita** la unión (r≈0.9).

### DE-INMUNIZACIÓN (`/api/deimmuno/data`) — ilustrativo
Scatter ΔMHC vs ΔΔG con la diana, ancla R312Q·Bing 2024. Pendiente NetMHCIIpan/FEP.

### ANÁLISIS MD (`/api/md/examples`) — ilustrativo, anclado a PackMan
Reproductor que dibuja RMSD/RMSF/SASA frame a frame + subir `.dat` de 2 columnas.
5 ejemplos (producción sana, la explosión, RMSF, SASA). Listo para conectar a PackMan.

---

## 2 · Archivos tocados

- `src/services/packing_service.py` — TODO el backend nuevo (ver funciones abajo).
- `src/web/app.py` — rutas nuevas (`/api/library/detail`, `/api/pore/*`,
  `/api/deimmuno/data`, `/api/md/*`, `/api/preview/substrate`).
- `src/web/templates/studio.html` — las 5 vistas, pestañas, toda la lógica JS.
- `src/core/paths.py` — `POROMANIA_DIR` (carpeta hermana).

**Funciones de servicio nuevas:** `library_detail`, `pore_config`, `pore_profile`,
`substrate_section`, `pore_channels`, `pore_channel_content`, `hole_structures`,
`_pore_axis`, `_hole_on`, `run_hole`, `screen_mutants`, `evaluate_mutant`,
`dock_correlate`, `deimmuno_data`, `md_examples`, `md_box`, `md_prepare`,
`preview_substrate`.

**Salidas generadas:** `Output/hole_runs/` (perfiles+canales HOLE),
`Output/cribado/` (mutantes+canales), `Output/docking/` (pdbqt+poses).

---

## 3 · Aprendido (no obvio)

- **PDB de preview:** cápside = modelo 0; cada enzima/sustrato = MODEL 1..N →
  NGL `/0` vs `not /0`, color por `modelindex`. La cápside NO está en el origen
  (hay que recentrar enzimas/sustratos a su centroide).
- **NGL:** esferas son *impostors* → `wireframe` no aplica; para malla real,
  geometría de cilindros. `radiusType:'bfactor'` + `colorScheme:'bfactor'` pinta
  el canal HOLE por radio.
- **HOLE:** eje del poro = eigenvector del valor propio DISTINTO del tensor de
  inercia (simetría Cn), NO el de mayor varianza (cae en el plano → canal
  degenerado). Es **no-determinista sin `rseed`**. Canal válido ⇒ ≥30 puntos.
- **PyMOL mutagénesis:** sintaxis `/obj//chain/resi/` + `cmd.set_wizard()` tras
  cada `apply()`. Todos los mutantes en UNA llamada `pymol -cq`.
- **Docking (vina 1.1.2):** receptor DEBE ser rígido (`obabel -xr`) o falla con
  "Unknown or inappropriate tag". Ligando desde SMILES con `obabel --gen3d`.
- **Servidor:** `FLASK_DEBUG=0` no autorecarga → reiniciar tras cambios en `.py`;
  plantilla `.html` en vivo. `pkill -f "app.py"` se auto-mata; usar `pgrep` sobre
  `src/web/app.py`.
- Herramientas instaladas: `hole` (~/bin/hole), `pymol`, `vina`, `idock`, `obabel`,
  RDKit 2025.09.1, numpy.
- La maqueta PAC-ZYME es ilustrativa (lo dice su pie); usar siempre datos calculados.

---

## 4 · Pendientes

- [ ] Puertas **De-inmunización** y **Análisis MD**: siguen ilustrativas
  (requieren NetMHCIIpan/FEP y correr la MD de PackMan). Análisis MD ya acepta
  `.dat` reales subidos.
- [ ] **Radio interno** solo cacheado para BMV en la Biblioteca; faltan las otras 4.
- [ ] Portada **EMBUDO** (overview de las 4 puertas) — no construida.
- [ ] Refinamiento fino: eje del poro residuo-a-residuo de Poromania (más exacto
  que el de simetría Cn, aunque este ya es correcto).
- [ ] Sin git (la carpeta no es repo) ni arranque durable; sin tests de los
  endpoints nuevos.
