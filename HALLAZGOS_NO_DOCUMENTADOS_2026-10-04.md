# Hallazgos NO documentados — revisión completa del proyecto (2026-10-04)

> **Qué es esto.** Una pasada por **todo** el repositorio buscando errores que **no**
> estuvieran ya anotados en `ESTADO.md §4`, `PENDIENTES.md` ni
> `REVISION_MOTORES_hallazgos_sellados.md`. Los problemas ya conocidos (bug de
> `found_any`, resolución mixta de `sustratinaitor`, `heat*.in` all-atom, Docker sin
> motores, docs fósiles, código muerto de Poromania, CIENCIA-1/2/3…) **no se repiten aquí**.
>
> **Método.** Lectura del código + verificación ejecutada donde era posible: `bash -n`,
> `py_compile`, `node --check`, `ruff`, `pytest`, cliente de prueba de Flask, parsers
> reproducidos contra los datos reales del repo, y recálculos independientes con NumPy.
> Cada hallazgo dice **cómo se comprobó**. Las sospechas que **no** se sostuvieron están
> listadas al final: también es información.
>
> **Esto no modifica ningún motor.** Es un informe; las correcciones se deciden aparte.

---

## Resumen: los siete que importan

| # | Qué pasa | Dónde | Efecto |
|---|----------|-------|--------|
| 1 | El mutante de Poromania **es el WT** (byte a byte) | `1crear_mutantes.pml` | Todos los resultados de `mutants/mut_129HIS_132GLY/` describen el WT |
| 2 | El sistema de `sustratinaitor` tiene **199 de 200 sustratos fuera de la cápside** | `packmol_input.inp` | El sistema listo para MD no es "sustrato alrededor", es sustrato *en otro sitio* |
| 3 | El centro/eje del poro se calcula sobre **una** subunidad del pentámero | `pore_analyzer.py:428` | HOLE arranca 7.6 Å descentrado |
| 4 | El preview del Studio genera **PDB corrupto** con ≥23 enzimas | `services/packing.py:138` | Coordenadas corridas una columna; la cápside se pierde |
| 5 | El packing **no es reproducible** (semilla aleatoria) | `parallel_packer.py:118` | Contradice `PENDIENTES.md:15` ("semilla fija") |
| 6 | Si falla el centrado, las enzimas se empaquetan **en el vacío** | `experiment_runner.py:114` | BMV: esfera de empaque a 221 Å del átomo más cercano |
| 7 | El análisis de MD mide **164 residuos** en vez de la cápside de 28 620 | `generar_analisis_individual.py:43` | `capside_rmsd/ryg` no miden la cápside; las enzimas no se analizan |

**Patrón que se repite en los cuatro motores:** una restricción geométrica se especifica
**respecto al origen** mientras la estructura vive **a 360 Å del origen** (los ficheros de
cápside traen centroide (207.9, 207.9, 207.9)). Pasa en el packing del Studio (§2.4) y en
`sustratinaitor` (§7.1). Y el segundo patrón: **el motor externo declara éxito** porque
cumplió exactamente la restricción que se le pidió, así que nada avisa.

---

# 1 · Poromania — mutagénesis

## 1.1 · ALTA — el "mutante" versionado es idéntico al WT

```
$ md5sum mutants/WT.pdb mutants/mut_129HIS_132GLY/receptor.pdb
d56a4e539c65c964ffe6fe7cd70a57d3  mutants/WT.pdb
d56a4e539c65c964ffe6fe7cd70a57d3  mutants/mut_129HIS_132GLY/receptor.pdb
```

Los residuos siguen siendo los silvestres en las cinco subunidades:

```
resi 129 resn SER  (debería ser HIS)   × segi A_6 A_7 A_8 A_9 A_10
resi 132 resn VAL  (debería ser GLY)   × segi A_6 A_7 A_8 A_9 A_10
```

Todo lo que cuelga de ese directorio —el perfil de HOLE, el mínimo de 1.915 Å, el mapa
APBS, el PDF y el PNG del perfil— **describe el WT con etiqueta de mutante**.

Dos defectos concretos en `1crear_mutantes.pml:122-129`:

- Falta `cmd.refresh_wizard()` entre `cmd.wizard('mutagenesis')` y `w.set_mode(aa)`. Sin
  ese paso el wizard no inicializa el modo y `w.apply()` es un no-op **silencioso**.
- `w.do_select(f"/{tag}//{chain}/{pos}/")` deja vacío el hueco de `segi`. Esta estructura
  es un pentámero cuyas 5 copias **comparten `chain A`** y solo se distinguen por `segi`
  (`A_6`…`A_10`), así que el selector resuelve a **5 residuos a la vez** y el wizard
  espera uno.

Agravante independiente de PyMOL: **nada verifica que la mutación se aplicó**. No se
compara `resn` después de `apply()`, ni se comprueba que el `receptor.pdb` difiera del WT.

## 1.2 · ALTA — el centro del poro es el de una sola subunidad

`pore_analyzer.py:428` y `1crear_mutantes.pml:33` hacen
`coord = stored.temp_coords[0]  # Primer (y único) resultado`. El comentario es falso: la
selección devuelve **5 átomos** (uno por subunidad) y el código se queda con el primero.
Recalculado con NumPy sobre `WT.pdb`:

| Magnitud | Valor |
|---|---|
| `pore_center.txt` versionado | (9.18, −3.88, 2.22) |
| Centroide de **solo** la subunidad A_10 | (8.80, −3.90, 1.86) — a **0.52 Å** |
| Centroide de los 25 CA de las 5 subunidades | (1.82, −5.60, 2.94) — a **7.59 Å** |
| Centroide de **todas** las CA (centro de simetría real) | (0.20, −0.61, 0.32) |

El punto de arranque de HOLE está anclado a una subunidad, no al eje C5. Es un defecto
**distinto** del heurístico ya anotado en el archivo sellado: aquí la simetría se rompe
antes de aplicar cualquier heurístico.

## 1.3 · ALTA — `2out_tsv.py:22` descarta las constricciones sin avisar

`if radio > 0.5:` borra del perfil todo punto con radio ≤ 0.5 Å. Un poro **ocluido** —
justo lo que el motor existe para detectar— pierde su zona de interés, y
`3analizar_hole.py` reporta como mínimo el primer punto superviviente: **un poro cerrado
se informa como abierto**. Además `ax.plot` une los puntos consecutivos, así que el hueco
se dibuja como una recta continua. En el dataset actual sobreviven 347/347 puntos, así que
el bug está **latente pero determinista**.

## 1.4 · ALTA — `foto_poro.pml:33-39` tiene la cámara cableada a otra máquina

`set_view` fija el origen de cámara en (220.41, 169.12, 316.35) con `clip slab, 80`,
mientras la molécula está centrada en el origen (`.pqr`: min −55/−34/−63, max 52/49/40).
Distancia centro→cámara: **421 Å**. Con un slab de 80 Å los `cmd.png()` salen vacíos.
Evidencia consistente: `cargas_apbs/` no tiene directorio `snap/`. La misma matriz está
duplicada en `2cargarsuperficies.sh:82-88`.

## 1.5 · ALTA — `1crear_mutantes.pml:14` no cubre todas las cadenas del input versionado

`chains = ['A', 'B']`, pero `modelos/BMV/poronatural.pdb` tiene cadenas **A, B y C**, las
tres con los residuos 129-132. Re-ejecutar el script hoy produce un mutante **asimétrico**
sin aviso, contradiciendo `CLAUDE.md` ("mutations simultaneously across all protein
chains (A, B, C)"). Nota adicional: `poronatural.pdb` (3574 átomos, segi D/E/F) y
`mutants/WT.pdb` (5735 átomos, segi A_6…A_10) son estructuras **distintas**: los
artefactos de `mutants/` no provienen del input versionado.

## 1.6 · MEDIA — el radio mínimo nunca se imprime

`scripts/1run_hole.sh:55` toma `awk '{print $NF}'` de ` Minimum radius found:  1.915
angstroms.` → `$NF` es `angstroms.`, el `sed` lo deja **vacío**, y el `if [ -n "$MIN_RAD" ]`
de la línea 56 es código muerto. El valor está en `$(NF-1)`. Ejecutado sobre el fichero
real: `MIN_RAD=[]` → no imprime nada.

## 1.7 · MEDIA — fallbacks numéricos silenciosos en `1run_hole.sh:12-22`

Sin `pore_center.txt` → `CPOINT="0.0 0.0 0.0"`; sin `pore_vector.txt` → `CVECT="0 0 1"`.
Solo se imprime un `⚠️` y **el script continúa**: HOLE corre desde el origen a lo largo de
Z, declara "normal completion", y el TSV, la gráfica y el "📏 Mínimo radio" resultan
indistinguibles de un resultado válido.

## 1.8 · MEDIA — código de salida 0 cuando HOLE falla

Verificado sin HOLE instalado: `1run_hole.sh` imprime "❌ HOLE2 falló" y sale **0** (la
rama de error no hace `exit 1`). `clickautomatico.sh` no tiene `set -e`, así que los pasos
2 y 3 corren sobre la salida vacía. Y `1run_hole.sh:35` hace `rm -f "$RAWOUT" "$SPHERES"`
**antes** de correr HOLE: un fallo destruye el `hole_spheres.pdb` anterior.

## 1.9 · MEDIA — `4generarhole.sh:4` aborta el lote completo

`3analizar_hole.py` hace `exit(1)` legítimamente ante un canal degenerado. Con `set -e`,
ese código mata el script entero: reproducido con dos mutantes, el segundo **nunca se
procesa** y no hay mensaje. Inconsistente con `5docking.sh:124`, que usa `|| true` para lo
mismo.

## 1.10 · MEDIA — `6generador_triptico.sh:20` aborta en el primer mutante incompleto

`find "$mut_dir/hole/resultados" …` sobre un directorio inexistente devuelve ≠0 y
`set -euo pipefail` mata el script. La rama defensiva de las líneas 23-26 ("Se omite") es
**inalcanzable** en ese caso.

## 1.11 · MEDIA — `2cargarsuperficies.sh:59` escribe en `/`

El heredoc `cat > "$outdir/foto_poro.pml"` está **después** del `done`. Sin mutantes (o si
la última iteración hizo `continue`), `outdir` está vacío → `cat > "/foto_poro.pml"`.
Reproducido: `target=[/foto_poro.pml]`. Incluso con mutantes, el `.pml` se escribe solo en
el **último** directorio, no en todos.

## 1.12 · MEDIA — la malla gruesa de APBS es más pequeña que la molécula

`cglen 80 80 80` está cableado, pero la molécula mide 107.5 × 83.4 × 102.6 Å. Del log real
(`cargas_apbs/log_apbs.txt:89-90`): malla x[−41.6, 38.4] vs molécula x[−55.3, 52.2] →
**~13.8 Å de proteína fuera de la malla** en cada extremo de X y ~11.3 Å en Z. APBS no da
error; la condición de frontera `bcfl sdh` y el potencial cerca del borde quedan
inválidos, y el `.dx` se usa tal cual en `ramp_new`.

## 1.13 · MEDIA — dos definiciones de "mejor score" de docking

`poses.txt` se ordena con `sort -n` **sin `-k`**, es decir por número de pose, no por
score. Luego `5docking.sh:100` hace un barrido correcto del mínimo, pero
`smiles_docking_pipeline.py:135-137` lee `f.readline()` y lo rotula "Mejor score".
Reproducido con `1→-7.5, 2→-9.9, 3→-8.1`: el pipeline informa −7.5; el mínimo real es
−9.9. El `except:` desnudo de la línea 140 además traga el error e imprime "✓ Docking
completado".

## 1.14 · MEDIA — campos por espacios sobre un PDB de ancho fijo

`5docking.sh:45,50` usa `awk` con campos separados por espacios, pero en el
`hole_spheres.pdb` real el centinela de HOLE ya aparece pegado: `QSS SPH S-888` → `$5` es
`S-888` y los campos van corridos en **93 de 361 líneas**. Hoy es inocuo por casualidad
(en esas líneas `$10` vale 0.00 y el filtro las descarta), pero con un `resSeq` de 3
dígitos (`S-100`) `$7,$8,$9` serán `(y, z, radio)` → **el centro de la caja de docking
queda corrupto** sin aviso.

## 1.15 · MEDIA — `center_structures.py` invalida los ficheros de eje

Reescribe `receptor.pdb` **in place** restando el centroide, pero no toca
`pore_center.txt` ni `pore_vector.txt`, que quedan en el sistema de coordenadas anterior.
Además el glob es `mutants/mut_*`, así que **`WT.pdb` no se centra**: mutantes y
referencia quedan en marcos distintos y dejan de ser comparables.

## 1.16 · MEDIA — "anchura" y "continua" no describen lo que se calcula

`3analizar_hole.py:36-38` calcula `max − min` de **todos** los puntos < 2 Å del perfil, no
de un tramo contiguo, y lo rotula "anchura"; la línea 78 afirma "No hay zona < 2 Å
**continua**". Con dos constricciones separadas se informaría una zona estrecha de decenas
de Å. En el dataset actual los 12 puntos < 2 Å resultan contiguos, así que el valor
publicado es correcto **por casualidad**.

## 1.17 · MEDIA — el fallback a UFF es inalcanzable

`generate_ligand_from_smiles.py:95-109`: `MMFFOptimizeMolecule` devuelve `-1` sin lanzar
excepción cuando no puede asignar parámetros. El código captura solo excepciones, así que
imprime "⚠️ Optimización MMFF parcial (código: -1)", **nunca entra al bloque UFF**, y
devuelve la geometría sin minimizar. El ligando se usa en docking sin que nadie lo sepa.

## 1.18 · MEDIA — mutantes aleatorios duplicados o idénticos al WT

`pore_analyzer.py:359-371`: `random.sample` + `random.choice` sin control de unicidad. Con
4 posiciones y 1 mutación por mutante hay 84 combinaciones; pedir 20 mutantes da ~90 % de
probabilidad de colisión, y `1crear_mutantes.pml:141` usa `mkdir(exist_ok=True)` → el
segundo **sobreescribe** al primero. Además `random.choice(all_aa)` puede devolver el
aminoácido silvestre (un "mutante" = WT) y `'DEL'` entra en el sorteo, borrando residuos.

## 1.19 · MEDIA — protonación inconsistente entre rutas

`2cargarsuperficies.sh:19` usa `pdb2pqr --with-ph=4.5` para la electrostática;
`5docking.sh:34` usa `obabel -p 7.4` para el receptor de docking; el ligando se protona a
7.4. El mapa de cargas y el sistema de docking describen estados de ionización distintos
de la misma proteína. Nada lo documenta ni lo valida.

## 1.20 · BAJA — varios

- `pore_analyzer.py:132-162`: `resi` es `str` en PyMOL y los `sorted()` son
  lexicográficos → las posiciones se listan como `100, 101, 13, 2, 99`. Igual en
  `1crear_mutantes.pml:111`, que produce tags como `mut_132GLY_9ALA`.
- `3analizar_hole.py:49` usa umbral 1.4 Å en la gráfica y 2.0 Å en la métrica impresa.
- `2out_tsv.py:16`: los dos filtros son no-ops (HOLE no usa `#`, y la cabecera real es
  `cenxyz.cvec radius` en **minúsculas**). El único filtro efectivo es el `except`, que
  traga cualquier línea mal formada sin contarla.
- `1run_hole.sh:45-46`: `gmacro` y `quit` no son tarjetas válidas de HOLE 2.2.005 (el
  output real dice `***Unrecognized line read: gmacro`). Inocuo, pero nadie revisa esos
  avisos.
- `4generarhole.sh:17-18`: el `chmod +x scripts/*.sh` está **dentro** del `if [ -x … ]`,
  o sea después de la prueba que pretendía habilitar.
- `generate_ligand_from_smiles.py:200,215`: con `-o algo.sdf`, `temp_sdf == output_path`
  y el `unlink()` final **borra la salida**.
- `3copiar_scripts.sh`: sin shebang, sin `set -e`, sin comprobar el `cp`.
- `run_pore_analysis.py:18` y `visualize_pore.py:29`: `os.system` ignorando el código de
  retorno → salen 0 aunque PyMOL no esté instalado.

---

# 2 · Studio — empaquetamiento y preview

## 2.1 · ALTA — el preview corrompe el PDB a partir del átomo 100 000

`services/packing.py:138` formatea el serial con `f"{atom_counter:5d}"`. El contador
arranca en 10 000; con GCase (3973 átomos) se pasa de 99 999 en la **copia 23**, y el
campo crece a 6 caracteres **desplazando una columna todo el resto de la línea**. El
deslizador de la interfaz llega a 50 (`studio.html:68`). Verificado:

```
preview(BMV_IJS9, GCase_1OGS, n_enzymes=25)
→ 9 325 líneas atómicas con coordenadas ilegibles por columnas
→ ejemplo: 'ATOM  100000  C   HIS W 328     254.028 174.190 205.408'
→ el ID de cadena de esas líneas pasa a ser ' '
```

Con EGFP (1948 átomos) el umbral cae en la copia 47 — también dentro del rango del
deslizador. El convenio PDB corta el serial en 99 999; hay que reiniciarlo o usar hybrid-36.

## 2.2 · ALTA — el PDB del preview es inválido para cualquier parser estándar

Dos problemas acumulados en `services/packing.py:120` y `:147-148`:

- la cápside se inserta **íntegra**, incluido su propio registro `END`, que queda en medio
  del fichero;
- la rama `elif line.strip(): lines.append(line)` copia **todos** los registros no-ATOM de
  la enzima dentro de cada `MODEL`, así que cada modelo lleva su propio `CRYST1`, `TER` y
  **`END`**.

Verificado con Biopython sobre un preview de 2 enzimas:

| | |
|---|---|
| ATOM/HETATM en el fichero | 224 726 |
| Átomos que ve Biopython | **11 471** |
| Átomos del modelo 0 (la cápside) | **3 613** de ~216 780 |

Es decir: **la cápside se pierde**. En el navegador no se nota porque NGL es tolerante
—que es justo por lo que la verificación visual de VLP-04a lo dio por bueno—, pero el
fichero que se guarda en `Output/Generated_PDBs/` y el que viaja en el ZIP de descarga
están roto para PyMOL, MDAnalysis, Packmol o AMBER.

## 2.3 · ALTA — el packing no es reproducible

`config/default.yaml:37-40` declara `seed_base: 1234567` y `use_random_seeds: false`.
**Nadie lee ninguna de las dos claves** (verificado por grep y por inspección):
`experiment_runner.py:160-170` llama a `run_parallel_replicas()` **sin** `seed_base`, el
parámetro queda en `None` (`parallel_packer.py:83`) y cada réplica usa
`random.randint(1, 1000000)` (línea 118).

Esto contradice de frente a `PENDIENTES.md:15-16`: *"el packing es geométrico y
determinista (semilla fija, golden test) → más confiable que la MD"*. Dos ejecuciones del
mismo experimento no son reproducibles. El preview tampoco lo es (verificado: dos llamadas
idénticas devuelven contenidos distintos, `random` sin semilla en `_random_positions`).

## 2.4 · ALTA — si falla el centrado, las enzimas se empaquetan en el vacío

`parallel_packer.py:262` escribe la cápside como `fixed 0. 0. 0. 0. 0. 0.` **sin** la
palabra clave `center`, así que Packmol la deja en sus coordenadas originales; las enzimas
van a `inside sphere 0. 0. 0. {radio−2}`. Todo depende de que la cápside llegue
pre-centrada, lo que solo ocurre si `center_structure()` tuvo éxito. Pero en
`experiment_runner.py:97-117` el `try` cubre a la vez el radio y el centrado: si PyMOL no
está (o el centrado falla), la excepción se captura, se avisa por `print`, y
**`capsid_file` sigue apuntando al fichero sin centrar**.

Medido sobre los datos del repo:

| Cápside | Centroide → origen | r_ext | Átomo más cercano al origen | ¿Interseca la esfera de 88 Å? |
|---|---|---|---|---|
| **BMV_IJS9** | **360.1 Å** | 143.6 Å | **221.4 Å** | **No** |
| QB_1QBE | 73.9 Å | 147.2 Å | 36.8 Å | Parcialmente (la pared) |

Con BMV, las enzimas se colocan en una esfera **completamente vacía**, a cientos de Å de
la cápside, sin una sola violación estérica. Packmol declara éxito y el Studio informa "N
enzimas empaquetadas". `md.py:159` sí usa `center` + `fixed`: las dos rutas que escriben
Packmol no coinciden.

Nota relacionada: `Input/Capsides/BMV_IJS9/capside.pdb` **no está centrada** (centroide
207.9, 207.9, 207.9) mientras el `capside_centered.pdb` versionado al lado sí lo está, y
el packing parte siempre del primero.

## 2.5 · MEDIA — un experimento totalmente fallido se reporta en verde

`parallel_packer.py:384-390` devuelve `{"success": False, "error": "Ninguna réplica fue
exitosa"}`. `app.py:303-320` responde **200** con `status: "completed"` y **no reenvía
`error`**. `packing.js:61` solo comprueba `!r.ok || d.status === 'error'`, nunca
`d.success`. Resultado: `Packing real OK: 0 enzimas · 0/10 réplicas` en verde, gráficas a
cero y el motivo real perdido.

## 2.6 · MEDIA — el campo "Radio interno (Å)" se ignora en el experimento real

`packing.js:8` envía `radius` en el preview, pero `doRun` (línea 56) no lo manda, y
`run_experiment()` no tiene parámetro de radio: `experiment_runner.py:98-105` siempre
recalcula con PyMOL o cae al default de 90 Å. El usuario pone 120 Å, ve el preview a
120 Å, pulsa "Ejecutar packing real" y el packing corre a otro radio. Preview y
experimento son geométricamente incomparables.

## 2.7 · MEDIA — tres perillas de `config/default.yaml` que el código ignora

| Clave | YAML | Qué gana de verdad |
|---|---|---|
| `engines.packmol.timeout` | 300 s | `parallel_packer.py:283` → `timeout=90` **cableado** |
| `engines.packmol.seed_base` / `use_random_seeds` | 1234567 / false | nadie las lee (ver 2.3) |
| `packing.collision_margin` | 2.0 | `parallel_packer.py:268` lo **re-cablea** a 2.0 |

El timeout importa: BMV tiene 216 780 átomos; Packmol se mata a los 90 s, el `except` lo
cuenta como "no cabe" y tras 3 fallos consecutivos la réplica termina. **Subir el timeout
en el YAML no tiene ningún efecto**, así que la capacidad de empaquetamiento reportada
depende de un reloj de pared cableado.

## 2.8 · MEDIA — cada corrida sobrescribe la anterior

`experiment_manager.py:69`: `experiment_dir = output_base_dir / capsid / enzyme`, **sin
timestamp**. `CLAUDE.md:104` documenta `Output/Experiments/[timestamp]/replica_[N]/`. Hoy,
repetir el mismo par cápside-enzima pisa los `replica_*/`, el `summary/` y el
`statistics.json` del experimento previo. Para un pipeline científico es pérdida de datos
silenciosa.

## 2.9 · MEDIA — `n_replicas` fijo a 7 en el gestor

`experiment_manager.py:47` cablea `self.n_replicas = 7`, ignorando
`experiments.n_replicas: 10` y el parámetro que llega de la API. `setup_experiment` crea 7
directorios mientras `ParallelPacker` crea los N que le pidan; `consolidate_results()`
solo recorre 1..7 y `get_replica_dir(8)` lanza. Está latente porque el flujo vivo usa el
consolidador del packer, no el del gestor. En ese consolidador del gestor hay además un
error de etiquetado: `_generate_report` recorre `all_values` (solo las réplicas exitosas)
con `enumerate(..., 1)`, así que el número de réplica del informe **no** es el real.

## 2.10 · BAJA — los IDs de cadena del preview colapsan

`services/packing.py:130`: `chain_ids[i % len(chain_ids)][0]` trunca a un carácter, así
que la lista de 702 identificadores que se construye justo antes queda inútil: las copias
26 a 51 reciben **todas** la cadena `A`.

---

# 3 · Studio — biblioteca y datos derivados

## 3.1 · ALTA — el radio cacheado se atribuye siempre a BMV

`capsid.py:153` guarda el radio en un fichero **único y global** (`radio_interno.txt`, sin
clave por cápside) y `library.py:85` lo muestra con
`"radius": cached_radius if name.startswith("BMV") else None`. Verificado escribiendo
`131.0` como si lo hubiera generado CCMV:

```
biblioteca: BMV_IJS9  radius= 131.0      ← dato de CCMV etiquetado como BMV
biblioteca: CCMV_1CWP radius= None
```

Calcular el radio de cualquier cápside hace que la interfaz lo muestre en la fila de BMV.
Es un dato científico mal etiquetado en la UI.

## 3.2 · MEDIA — el radio se escribe en una ruta relativa al CWD

`capsid.py:153` usa `output_file = "radio_interno.txt"` (relativo), mientras `library.py:63`
lo lee en `paths.PROJECT_ROOT / "radio_interno.txt"`. Arrancando como documenta
`CLAUDE.md:31` (`cd src/web && python app.py`) el fichero acaba en
`src/web/radio_interno.txt` y la columna "R int (Å)" se queda en "—" para siempre.
Contradice el docstring de `paths.py:1-8` ("elimina las rutas relativas frágiles… sin
importar el directorio de trabajo actual"). Hoy no existe ningún `radio_interno.txt` bajo
`nanocapsule-mvp/`, así que la columna está vacía en la práctica.

## 3.3 · MEDIA — el endpoint de radio presenta el default como medición

Verificado sin PyMOL instalado:

```
POST /api/capsid/radius {"capsid": "CCMV_1CWP"}
→ 200 {"status": "success", "internal_radius": 90.0,
        "message": "Radio interno calculado: 90.0 Å"}
```

`capsid.py:72-77` devuelve el default de 90 Å y el endpoint lo rotula `success` y
"calculado". `/api/health` sí informa `pymol: false`, pero este endpoint no lo consulta.
El usuario no puede distinguir una medición de un valor por defecto, y ese número alimenta
el radio de empaquetamiento.

## 3.4 · MEDIA — la columna "volumen" no es un volumen de van der Waals

`library.py:53` sirve la columna `Volume(Å³)` de
`Input/Enzimas/vdw_volumes_results.txt`. Ese fichero lo escribe
`fast_vdw_volume.py:211`, y lo que guarda es
`vol_avg = (vol_empirical + vol_grid) / 2`, donde `vol_empirical = n_atoms × 11.5 Å³`
(`fast_vdw_volume.py:104`). Es decir: **la mitad del número publicado es una estimación de
sobremesa por conteo de átomos**, bajo una cabecera y un título que dicen "VAN DER WAALS
VOLUMES". Verificado aritméticamente:

| Enzima | n×11.5 | Publicado | Grid implícito | Grid recalculado |
|---|---|---|---|---|
| Alkaline Phosphatase | 76 130 | 73 797 | 71 464 | **71 464** (2.0 Å) |
| EGFP | 22 149 | 20 980 | 19 811 | **19 811** (1.5 Å) |
| GCase | 45 690 | 44 056 | 42 422 | **42 422** (1.8 Å) |
| Luciferasa | 45 620 | 44 418 | 43 216 | — |

La coincidencia exacta entre el grid implícito y mi recálculo independiente confirma la
fórmula. El sesgo es de +3 % a +6 % sobre el valor calculado, sistemáticamente al alza.

## 3.5 · MEDIA — cuatro scripts calculan el mismo volumen con distinta selección de átomos

`fast_vdw_volume.py:26` filtra **solo `ATOM`**, mientras
`calculate_vdw_volume.py:43`, `calculate_vdw_volume_optimized.py:26` y
`calculate_single_enzyme.py:24` incluyen `ATOM` **y** `HETATM`. El fichero que la
biblioteca sirve lo generó el único que descarta `HETATM`, así que para EGFP se excluyen
los 22 átomos del cromóforo (residuo `CRO`, parte covalente de la proteína). Efecto
numérico hoy: Rg 16.98 Å vs 16.89 Å — despreciable. Efecto estructural: la tabla dice
1926 átomos y la biblioteca muestra 1948 para la misma enzima, y cualquier enzima con
metal o cofactor perdería esos átomos en silencio.

## 3.6 · BAJA — "cadenas" y el número T no son lo que parecen

`common.py:37` cuenta **identificadores de cadena distintos** en la columna 22. Las cuatro
cápsides reutilizan solo A/B/C para sus 180 subunidades:

```
BMV_IJS9   216 780 átomos  IDs=3 (A,B,C)  bloques TER=180  segid únicos=180
CCMV_1CWP  214 440 átomos  IDs=3          bloques TER=3    segid únicos=1
MS2_2MS2   173 700 átomos  IDs=3          bloques TER=3    segid únicos=1
QB_1QBE    168 480 átomos  IDs=3          bloques TER=3    segid únicos=1
```

La interfaz informa "3 cadenas" para una cápside de 180 subunidades. Peor:
`library.py:83` deriva el número T de esa cuenta (`_T_NUMBER.get(chains)`), así que
"T=3" sale **por coincidencia** con el número de IDs, no de ningún cálculo
cristalográfico; un fichero con un ID por subunidad mostraría "T=180". Además CCMV, MS2 y
QB no separan sus subunidades con `TER`, lo que explica que un parser estándar colapse la
cápside (ver 2.2).

## 3.7 · BAJA — los radios "ilustrativos" alimentan un veredicto PASA/NO PASA

`pore.py:22-27` marca `_SUBSTRATES` como "ILUSTRATIVOS hasta portar el cálculo real", pero
esos radios entran en `screen_mutants(substrate_radius=…)` y producen la columna `passes`
(`pore.py:367`) y el texto "PASA / NO PASA" de `pac-pore.js:146,245`. El veredicto se
presenta sin ninguna marca de que el umbral es de literatura sin verificar.

---

# 4 · Studio — PAC-PORE

## 4.1 · ALTA — el perfil de poro sintético quedó sin marca de "ilustrativo"

El commit `40f4b03` ("PAC-PORE: quitar el badge '(ilustrativo)' del título del perfil de
poro") vació el badge en `studio.html:183` y puso `$('pore-badge').textContent = ''` en
`pac-pore.js:71`. Pero el endpoint que alimenta ese gráfico, `/api/pore/profile` →
`pore.py:615 pore_profile()`, **sigue devolviendo una gaussiana sintética**: un mínimo
cableado por eje (`_AXIS_MIN = {3-fold: 1.9, 5-fold: 3.2, 2-fold: 2.6}`) más un
desplazamiento derivado del **nombre** de la cápside
(`(sum(ord(c) for c in capsid_name) % 7) * 0.05`), y su propio docstring dice "HOY es
ilustrativo". El payload incluso devuelve `illustrative: True`, y el frontend lo ignora.

Encima, `pac-pore.js:244` escribe con ese número el pie
`Poro nativo mín X Å · sustrato Y Å · PASA/NO PASA`. La ruta de HOLE real sí se etiqueta
(`pac-pore.js:226` pone `(HOLE real · …)`), así que ahora **el gráfico fabricado y el
medido se presentan igual**. Es el único hallazgo introducido por el commit más reciente.

## 4.2 · ALTA — el Studio reimplementó la mutagénesis con el mismo patrón que falló

`pore.py:238-241` genera exactamente la misma secuencia de wizard que produjo un mutante
idéntico al WT en Poromania (§1.1):

```python
cmd.wizard('mutagenesis'); w=cmd.get_wizard()
w.set_mode('GLY'); w.do_select('/m_129G//A/129/'); w.apply(); cmd.set_wizard()
```

Sin `refresh_wizard()` y con el hueco de `segi` vacío. Y tampoco verifica el resultado:
`pore.py:247` **ignora el código de retorno** de PyMOL y la única comprobación es
`if not pdb.exists(): continue` (`pore.py:356`). Un mutante no mutado da `delta = 0.00` y
se ordena junto al WT sin levantar ninguna alarma.

Agravante de alcance: `modelos/BMV/poro5fold.pdb` tiene **2 IDs de cadena (A, B) y 10
segis** (`A_6…A_10`, `B_6…B_10`), así que `_chain_ids` devuelve `['A','B']` y el selector
`/{tag}//A/{pos}/` casa con **5 residuos a la vez** — la misma ambigüedad de Poromania.
No pude ejecutar PyMOL aquí, así que esto queda como **riesgo estructural muy probable,
no como fallo observado**: se cierra en un minuto comparando `resn` antes y después.

## 4.3 · MEDIA — el cribado falla con `TypeError` cuando HOLE no deja esferas

`_constriction_point` devuelve `None` si ningún registro tiene radio > 0.5 (verificado), y
`screen_mutants` lo pasa tal cual a `_pore_residues`. Verificado:

```
screen_mutants con constricción None → TypeError: unsupported operand type(s) for -: 'float' and 'NoneType'
```

El usuario recibe un 500 con un `TypeError` en vez de "HOLE no trazó un canal".

## 4.4 · MEDIA — `pac-pore.js:104` lanza cuando el cribado no devuelve mutantes

`screen_mutants` descarta en silencio los mutantes cuyo HOLE falla
(`pore.py:371-372 except Exception: continue`) y puede devolver `"mutants": []`. Entonces
`const best = d.mutants[0]` es `undefined` y `best.name` lanza: el usuario ve
`Error cribado: TypeError: Cannot read properties of undefined (reading 'name')` en lugar
de "ningún mutante abrió el poro".

## 4.5 · MEDIA — `pac-pore.js:210` es un `catch` vacío

`loadHoleStructures()` se traga cualquier error de `/api/pore/structures`. El
`<select id="holeStructure">` queda vacío y los cuatro botones que dependen de él
(`runHole`, `runScreen`, `runManualMutant`, `runDock`) salen por la puerta de atrás sin
decir nada. Combinado con 4.6: toda la puerta PAC-PORE muere con la consola limpia.

## 4.6 · MEDIA — `paths.py:25` cablea el nombre de carpeta con el punto final

`POROMANIA_DIR = PROJECT_ROOT.parent / "Poromania.v.1.2."`. Hoy resuelve, pero al subir
Poromania a 1.3 — o al renombrar `nanocapsule-mvp/` como planea VLP-05
(`ESTADO.md:178`) — `pore_channels()` y `hole_structures()` devuelven listas **vacías sin
error** (`pore.py:43-44`, `:63-64`) y, por 4.5, sin un solo mensaje.

## 4.7 · Verificado correcto — el eje del poro del Studio

Al contrario que el de Poromania (§1.2), `pore.py:_pore_axis` **sí** resuelve el eje de
simetría. Comparado con un eje calculado de forma independiente (normal del plano que
pasa por los centroides de subunidad):

| Modelo | Subunidades | Desviación |
|---|---|---|
| BMV/poro5fold | 10 | **0.0°** |
| BMV/poro3fold | 3 | 6.1° |
| BMV/poronatural | 3 | 6.1° |
| CCMV/poronatural | 3 | 5.8° |

Para el pentámero la coincidencia es exacta. Las desviaciones de ~6° en los trímeros
pueden venir de mi propia referencia (un plano por 3 puntos es exacto pero su normal solo
aproxima el eje C3 si las subunidades son simétricas), así que **no las cuento como
hallazgo**; vale la pena cerrarlo con una referencia mejor.

---

# 5 · Studio — API, rutas y preparador de DM

## 5.1 · MEDIA — el guardarraíl de `/api/result/pdb` es un `startswith` de cadenas

`app.py:372` valida con `str(target).startswith(str(paths.OUTPUT_DIR.resolve()))`. Un
directorio hermano cuyo nombre empiece por `Output` lo pasa. Verificado:

```
GET /api/result/pdb?path=/…/nanocapsule-mvp/Output_leak/secret.pdb  → 200  'SECRET LEAKED'
GET /api/result/pdb?path=/etc/passwd                                 → 403
```

El docstring promete "valida que la ruta esté dentro de `Output/`". Lo correcto es
`Path.is_relative_to()`.

## 5.2 · MEDIA — `/api/files/cleanup` borra todo con `days_old: 0`

`app.py:482` toma `days_old` del JSON sin validar y lo pasa a `timedelta`. Verificado:

```
POST /api/files/cleanup {"days_old": 0}  → 200 {"removed": 1, …}   (el fichero de prueba desapareció)
```

Un `0` o un negativo borra **todos** los PDB generados, sin confirmación. Por el mismo
camino, `n_enzymes`, `n_replicas`, `n` y `radius` llegan a los servicios sin ninguna
validación de rango.

## 5.3 · MEDIA — el "Preparador DM" acepta un SMILES y lo ignora

`md.py:146-184`: `md_prepare(capsid, n_substrate, smiles)` solo devuelve el SMILES en la
respuesta; el bloque Packmol que genera dice siempre `structure sustrato.pdb` (línea 161),
un fichero que el endpoint nunca produce. `studio-core.js:154` manda `$('smiles').value` y
pinta `# SMILES <...>` en la salida, sugiriendo que el input usa ese sustrato. No lo usa.
El docstring del módulo afirma que genera "inputs Packmol + tLeaP **reales**".

## 5.4 · MEDIA — el preparador de DM emite all-atom para un motor coarse-grained

`md.py:166-177` genera `leaprc.protein.ff19SB` + `leaprc.gaff2` + `leaprc.water.tip3p` y
`solvateOct sys TIP3PBOX 10.0`. El único motor de MD del proyecto (PackMan) usa SIRAH CG:
`archivos_dm_cg/gensystem.leap` hace `source leaprc.sirah`, `set default PBradii mbondi3`
y `solvateOct protein WT4BOX 12 0.7`. Los inputs que el Studio ofrece **no son los del
motor que existe**, y además son irrealizables: 216 780 átomos de cápside solvatados en
TIP3P son decenas de millones de átomos, y un PDB de cápside crudo (sin hidrógenos, con
IDs de cadena repetidos) no pasa por `tleap` con ff19SB.

## 5.5 · BAJA — se dibuja el box de DM de otra cápside

`studio-core.js:120` invalida la caché comparando `mdBoxCapsid === capsid`, pero
`renderPDB` usa `mdBoxData` sin comprobar a qué cápside corresponde. Marcar "Mostrar box"
con BMV (`box_half` 172.3, centro 207.9³) y cambiar a MS2 pinta el box de BMV sobre la
cápside de MS2.

## 5.6 · BAJA — `center_structure` escribe dentro de `Input/`

`capsid.py:190` y `cargo.py:82` guardan `*_centered.pdb` **junto al fichero de entrada**,
es decir dentro de la biblioteca versionada. Cada experimento reescribe datos de entrada
commiteados.

## 5.7 · BAJA — efecto secundario en el import

`common.py:21` instancia `StructureFetcher(str(paths.INPUT_DIR))` a nivel de módulo y
`structure_fetcher.py:34` hace `mkdir(exist_ok=True)` en el constructor: importar
`src.services.packing_service` **crea el directorio `Input/`**. Sin `parents=True`, además
lanzaría si faltara el padre.

---

# 6 · Empaquetado, CI, tests y tablero

## 6.1 · MEDIA — el paquete instalado no es importable

`setup.py:41-42` usa `find_packages(where='src')` + `package_dir={'': 'src'}`. Verificado
instalando en un venv limpio:

```
$ pip install --no-deps nanocapsule-mvp/
$ ls site-packages/   →  core  engines  io  services  web      (no hay 'src' ni 'packing')
$ python -c "import src.core"   → ModuleNotFoundError: No module named 'src'
$ python -c "import packing"    → ModuleNotFoundError: No module named 'packing'
```

Dos causas: **(a)** todo el código importa con prefijo `src.` (`app.py:17-18`,
`common.py:15-17`, `pore.py:16-17`, `conftest.py:5`), que no existe tras la instalación;
**(b)** `src/packing/` es el **único** subpaquete sin `__init__.py`, así que
`find_packages` no lo ve y `parallel_packer` no se distribuye — `experiment_runner.py:12`
lo importa sin guardas. Desde el repo funciona solo porque Python 3 lo resuelve como
namespace package, y `pythonpath = .` de `pytest.ini` lo oculta en los tests.

## 6.2 · MEDIA — el puerto fantasma 5001 del fallback

`config.py:104` devuelve `"web": {"port": 5001}` en la config cableada de respaldo (y sin
clave `debug`). Si `config/default.yaml` no se carga —p.ej. el montaje
`./config:/app/config` de `docker-compose.yml:16` queda vacío— Flask escucha en **5001**
mientras `Dockerfile:53` expone 5000, compose publica `5000:5000` y los **dos**
healthchecks pegan a `localhost:5000`: contenedor permanentemente *unhealthy* e
inalcanzable, con el log imprimiendo `http://localhost:5001/`.

## 6.3 · MEDIA — `ruff` sin pin en un CI que se declara reproducible

`.github/workflows/ci.yml:37` instala `ruff` suelto, y no está en `requirements.lock`,
mientras el comentario de la línea 33 dice "Desde el lock (versiones exactas) → CI
reproducible e idéntico a la imagen". Una release de ruff que active reglas nuevas por
defecto tumba el CI de `main` sin un solo commit al código.

## 6.4 · MEDIA — dos tests verdes que no comprueban nada

`test_smoke.py:69-78` solo exige que la respuesta sea una lista:

```python
def test_pore_channels_shape(client):   assert isinstance(r.get_json()["channels"], list)
def test_pore_structures_shape(client): assert isinstance(r.get_json()["structures"], list)
```

Pero `pore_channels()` y `hole_structures()` devuelven `[]` cuando `POROMANIA_DIR` no
existe. Combinado con 4.6, **el escenario de fallo más probable de PAC-PORE deja los dos
tests en verde con la puerta entera muerta**. Deberían exigir las cuatro claves conocidas.

Lo mismo en el preview: `test_smoke.py:136` es
`assert "MODEL" in body and "END" in body` con `n_enzymes=2`. `"END"` es subcadena de
`"ENDMDL"`, así que la segunda mitad es tautológica, no se compara el número de modelos
con `n_enzymes`, y con 2 enzimas nunca se alcanza el desbordamiento de serial de §2.1.
**Los 22 tests pasan** (verificado) con todos los defectos de §2 presentes.

Rutas sin ninguna cobertura (las ejercí a mano, responden 200): `/api/capsid/radius`,
`/api/preview/substrate`, `/api/experiment/run`, `/api/result/pdb`, `/api/pore/channel`,
`/api/files/*`, `/api/download/*`, `/api/structure/*`, `/api/file/*`.

## 6.5 · MEDIA — el tablero `salud.sh` pinta verde con tests fallando

`salud.sh:36-40`:

```bash
res="$( cd nanocapsule-mvp && python3 -m pytest -q 2>/dev/null | tail -1 )"
case "$res" in *passed*) ok "$res" ;; *) no "…" ;; esac
```

Verificado: `res="1 failed, 21 passed in 1.70s"` entra por la rama `*passed*` → ✓ verde.
Hay que probar `*failed*|*error*` **antes**, o usar el código de salida de pytest (que el
`$( … | tail -1 )` descarta).

## 6.6 · MEDIA — `vlpstudio.kdl` sobrescribe el builtin `test` de bash

`herramientas/vlpstudio.kdl:32` define `test(){ … }` y luego hace
`export -f studio test salud …`. Al exportarse, **cualquier script bash lanzado desde ese
pane** hereda un `test` que siempre devuelve 0. Reproducido:

```
$ bash -c 'test(){ :; }; export -f test; bash -c "if test -f /no/existe; then echo MAL; else echo ok; fi"'
MAL
```

`salud.sh` usa `[` y se salva, pero `scripts/fetch_data.sh:36` usa `if [ -f "$dest" ]` …
y cualquier script de motor que use `test` en vez de `[` se comporta mal en silencio.
Conviene renombrar la función (`pruebas`) y no exportarla.

## 6.7 · MEDIA — una descarga fallida envenena la biblioteca para siempre

`scripts/fetch_data.sh:21-28`: en la rama `wget`, `wget -O "$2"` crea y trunca el destino
**antes** de la petición. Verificado: con un 404, `wget` sale 8 y deja un fichero de
**0 bytes**. Si falla también el fallback de la línea 48, queda un
`Input/Capsides/P22_5UU5/capside.pdb` vacío, y la siguiente ejecución dice "✓ ya existe —
se omite" para siempre. `list_available_capsides()` solo comprueba `.exists()`, así que la
cápside vacía aparece en la biblioteca y en los dos selectores: `_pdb_centroid` devuelve
`[0,0,0]`, `_max_radius` devuelve 0.0, `md_box` devuelve `box_half: 0.0` y
`preview_substrate` devuelve 0 copias — **todo sin un error**. Con `curl` ≥ 8 no ocurre
(verificado), así que el defecto es específico de la rama `wget`.

## 6.8 · MEDIA — `THIRD_PARTY.md` dice que no se redistribuye SIRAH, y sí se redistribuye

`THIRD_PARTY.md` afirma que el código "**NO** los incorpora ni los redistribuye" y lista
**SIRAH** bajo "Motores que NO se distribuyen (los aporta el usuario)". Pero el repositorio
versiona **146 ficheros (3.9 MB)** de la distribución SIRAH 2.3 en
`PackMan.v.1.2/archivos_dm_cg/sirah_x2.3_24-07.amber/`, incluidos sus `tools/` con licencia
GPL (`tools/COPYING` es el texto de la GPLv2) y el toolkit CGCONV. `.gitignore` no lo
menciona.

Matiz importante: `cgconv.pl` es **GPL-2.0-or-later**, que *sí* es compatible con AGPLv3,
así que no veo un conflicto de licencias; el problema es que **la declaración es falsa** y
que los términos de SIRAH ("académica; verificar términos", según la propia tabla) nunca se
verificaron antes de publicarlo. Para JOSS/Zenodo esto es del tipo que bloquea.

## 6.9 · BAJA — metadatos de versión incoherentes

`setup.py:33` declara `version='1.0.0'` mientras `nanocapsule-mvp/VERSION`, `CITATION.cff`
y el release de GitHub dicen **0.1.0**. También `setup.py:48` declara
`python_requires='>=3.7'`, imposible: el lock se generó con 3.12, `pyproject.toml:7` fija
`target-version = "py312"`, el Dockerfile usa `python:3.12-slim` y
`rdkit==2025.9.1` / `flask==3.1.3` no soportan 3.7-3.9. Los `classifiers` se detienen en
3.11.

## 6.10 · BAJA — el job `engines` del CI no verifica `sustratinaitor`

`ci.yml:51-54` afirma verificar "que TODO su Python parsea", pero `sustratinaitor` tiene
**0 ficheros `.py`**: su único ejecutable es `4_ensamblaje_y_simulacion/run_MD.sh`, que
`compileall` no mira y para el que no hay `bash -n`. Para ese motor el job es decorativo.

## 6.11 · BAJA — el pane "Plan" del tablero está roto

`salud.sh:47`: el patrón `^\| \*\*VLP-0` omite **VLP-10 y VLP-11** (ya hechos, nunca se
mostrarán); `VLP-0[0-9]` no casa los sub-tickets `VLP-04a/b/c`, así que el `sed` no
sustituye y el pane **vuelca la fila markdown completa**; con `LC_CTYPE=POSIX` el `(.)` no
casa el `✅` multibyte y **ninguna** fila se transforma; y el
`|| echo "(ESTADO.md no encontrado)"` cuelga del `sed`, no del `grep`, así que es código
muerto.

## 6.12 · BAJA — `vlpstudio.kdl` tiene cableada la ruta de una máquina concreta

`/home/luciernaga/Escritorio/Pac-Zyme/uno solo`, repetida **5 veces** (líneas 15, 32, 43,
49, 54) y versionada. En cualquier otro clon los 4 panes arrancan en `$HOME` y los 6
comandos del pane manual fallan todos. VLP-05 (renombrar `nanocapsule-mvp/`) lo romperá
aún más.

## 6.13 · BAJA — claves muertas en `config/default.yaml`

Verificado por grep que **nadie** lee: `engines.pymol.headless`, `engines.pymol.quiet`,
`io.temp_dir`, `io.cleanup_temp`, `io.output_formats`, `io.default_capsid`,
`io.default_enzyme`, `io.example_capsid`, `io.example_enzyme`, **toda** la sección
`logging` (el código solo usa `print()`), `experiments.output_base_dir`,
`experiments.keep_temp_files`, `experiments.auto_generate_reports`, `web.cors_enabled` y
**toda** la sección `library` (cuyas rutas `"../Input/Capsides"` ya sustituyó `paths.py`).

## 6.14 · BAJA — detalles de frontend

- `library.js:33`: el `catch` solo escribe en `tb-caps`; `tb-enz` se queda en "Cargando…"
  para siempre ante un fallo de `/api/library/detail`.
- `studio.css:26`: la regla cubre `select, input[type=number]`, así que los tres campos de
  texto reales (`#smiles`, `#poreSmiles`, `#manualMut`) caen al ancho por defecto del
  navegador y rompen la retícula.
- `studio.css:49-51`: la clase `.status.load` que usan `studio-core.js:6` y tres sitios de
  `pac-pore.js` **no está definida**; "cargando" es visualmente idéntico a neutro.

---

# 7 · sustratinaitor

## 7.1 · ALTA — el sistema empaquetado tiene 199 de 200 sustratos fuera de la cápside

`3_empaquetado_packmol/packmol_input.inp` pide las 200 copias de GYE
`inside box -150.336 -147.174 -151.982 150.336 147.174 151.982`, una caja centrada en el
**origen**, mientras la cápside CG vive a 360 Å de ahí. Medido sobre el fichero de salida
versionado, `3J7L-GYE.pdb`, tomando como referencia el centroide real de la cápside:

| | |
|---|---|
| Centroide de la cápside CG | (207.9, 207.9, 207.9) — **360.1 Å** del origen |
| Caja envolvente de la cápside | min (68.3, 71.9, 66.4) · max (347.5, 343.9, 349.4) |
| Centroide de las 200 copias de GYE | **(3.0, −0.2, 8.7)** |
| Caja envolvente del GYE | min (−144.9, −147.2, −150.9) · max (150.3, 147.2, 152.0) |

Clasificando las 200 moléculas respecto a la cápside (superficie interna r = 89.5 Å,
externa r = 142.6 Å):

| Ubicación | Moléculas |
|---|---|
| Totalmente en la cavidad | **0** |
| Totalmente fuera de la cápside | **199** |
| Atravesando la pared | 1 |

El input declara la cápside con `center` + `fixed 0. 0. 0. 0. 0. 0.`, que debería
trasladarla al origen; en el fichero de salida **no está trasladada**. Sea por la versión
de Packmol (21.0.1, según el log) o porque el output se generó con otro input, el hecho
empírico es que el sistema versionado tiene la cápside y la nube de sustrato en regiones
disjuntas del espacio.

Y nadie lo detecta: `packmol_run.log:387-390` dice **`Success!`** con
`Maximum violation of target distance: 0.000000`, porque Packmol cumplió exactamente la
restricción que se le pidió. Esto es **anterior** y **adicional** al desajuste de
resolución CG/all-atom ya documentado: incluso resolviendo aquello, la geometría es otra
cosa. Lo correcto es `inside sphere` alrededor del centro real de la cápside, como hace el
empaquetador de PackMan (`2Empaquetador_Manual.py:58`).

## 7.2 · ALTA — los nombres de topología no coinciden entre `tleap` y `run_MD.sh`

```
gensystem.leap:20  saveAmberParmNetcdf protein 3J7L-GYE_cg.prmtop 3J7L-GYE_cg.ncrst
gensystem.leap:21  savepdb              protein 3J7L-GYE_cg-WAT.pdb
run_MD.sh:5        export prmtop=3J7L-GYE_cg-WAT.prmtop
run_MD.sh:6        export name=3J7L-GYE_cg-WAT
```

Solo el PDB lleva el sufijo `-WAT`; tleap nunca escribe `3J7L-GYE_cg-WAT.prmtop`. La
primera llamada de `run_MD.sh:9` muere con "unable to open prmtop" y, al no haber `set -e`
ni comprobación de `$?`, las cuatro etapas siguientes se lanzan igual sobre ficheros
inexistentes y el script **termina con código 0** sin un mensaje propio.

## 7.3 · MEDIA — `4_ensamblaje_y_simulacion/` no contiene nada de lo que sus scripts piden

El directorio solo tiene `run_MD.sh` y `gensystem.leap` (verificado). Faltan: `em1_WT4.in`,
`em2_WT4.in`, `eq1_WT4.in`, `eq2_WT4.in` (los pide `run_MD.sh:9-15`);
`sirah_x2.3_24-07.amber/` (lo pide `gensystem.leap:2-3`); `GYE.mol2` y `GYE.frcmod` (están
en `2_ligando_GYE/`); `3J7L-GYE.pdb` (está en `3_empaquetado_packmol/`). No hay script ni
documento que copie nada allí. `tleap -f gensystem.leap` falla ya en el `addPath`.

## 7.4 · MEDIA — no hay etapa de producción y no se comprueba nada

Las 4 invocaciones de `run_MD.sh` (líneas 9, 11, 13, 15) no verifican `$?`, no hay
`set -e`, y **no se invoca ningún `prod_md_WT4.in`**. Contrasta con el `run_MD.sh` de
PackMan, que sí revisa `$?` tras cada etapa.

---

# 8 · PackMan — parámetros AMBER/SIRAH

> Comparados contra los inputs oficiales que el propio repo trae en
> `archivos_dm_cg/sirah_x2.3_24-07.amber/tutorial/`, usando `tutorial/5` y `tutorial/8`
> (sistemas proteína + WT4, los aplicables). Todo esto es **adicional** al problema ya
> documentado de que los `heat*.in` son all-atom.

## 8.1 · ALTA — falta `&ewald chngmask=0` en 10 de los 13 inputs

`em1_WT4.in:11`, `em2_WT4.in:11`, `heat1..heat6:21`, `density_eq.in:22` y `final_eq.in:20`
terminan **sin** bloque `&ewald`. Todos los inputs SIRAH de referencia lo llevan
(`tutorial/5/em1_WT4.in:15-17`, `tutorial/5/eq1_WT4.in:23-25`, `tutorial/8/em1_WT4.in:15-17`),
y `tutorial/7/heat_Prot-Lip.in:26-29` lo comenta literalmente: `chngmask=0, ! Only
required to avoid SANDER error`.

Con `sander` (que `run_MD.sh:86` ofrece como motor) el cálculo aborta; con `pmemd.cuda` no
aborta pero **regenera** la lista de exclusiones 1-2/1-3/1-4 desde la conectividad SIRAH,
que es justo lo que `chngmask=0` existe para impedir → electrostática incorrecta en la
minimización, todo el calentamiento y las dos equilibraciones NPT. Que `eq1`, `eq2` y
`prod_md` **sí** lo tengan (líneas 21-23) confirma que es un olvido, no una decisión.

## 8.2 · ALTA — `configurar_simulacion.sh:353` restringe todo el sistema

```
restraintmask=':*&!@H=',  ! Todos los átomos pesados
```

En una topología SIRAH **no hay hidrógenos**: las perlas de WT4 se llaman `WN1, WN2, WP1,
WP2` y los iones `NaW/ClW/KW` (verificado en `sirah_x2.3_24-07.amber/solv.lib`). Así que
`!@H=` no excluye nada y la máscara selecciona cápside + enzimas + **todo el solvente y
todos los iones**, con `restraint_wt=2.4`. La referencia restringe solo la proteína:
`tutorial/5/eq1_WT4.in:17-19` → `':1-46'`; `tutorial/8/eq1_WT4.in:19` → `':1-114'`.

Efecto: eq1 (5-10 ns según el propio prompt del script) **congela la caja completa**. El
solvente no puede relajarse ni la densidad converger — lo contrario de lo que el script
anuncia en su línea 96 ("mientras el solvente e iones se adaptan").

## 8.3 · ALTA — el generador no reescribe el calentamiento, que queda fijo a 300 K

`configurar_simulacion.sh` escribe `em1, em2, eq1, eq2, prod_md` (líneas 300, 319, 334,
365, 396) pero **no** `heat1..6`, `density_eq` ni `final_eq`, que `run_MD.sh:128` sí
ejecuta y que tienen `temp0` cableado a 300.0 (`heat6:10`, `density_eq.in:9`,
`final_eq.in:9`). Si el usuario elige 310 K —opción que el script ofrece explícitamente en
su línea 37, "temperatura fisiológica"— la cadena real es 0→300 K, densidad a 300 K,
equilibración final a 300 K, y luego `eq1` **salta a 310 K con `irest=0`**. Discontinuidad
térmica silenciosa.

## 8.4 · MEDIA-ALTA — `eq1` descarta 7 etapas de dinámica previa

`eq1_WT4.in:3` tiene `imin=0, ntx=1, irest=0`, y `run_MD.sh:264-269` le pasa
`-c ${NAME}_density.ncrst`, el resultado de heat1→heat6→density_eq. Con `irest=0` AMBER
**descarta las velocidades**, reinicia el reloj a 0 y regenera velocidades Maxwell desde
`tempi=300.0`: las ~60 ps de rampa térmica y los 50 ps de equilibración de densidad quedan
termodinámicamente anulados. En la referencia esto es correcto porque allí `eq1` **es** la
primera etapa dinámica tras minimizar (`tutorial/5/eq1_WT4.in:3-4`, con `tempi=0.0`); aquí
se insertó una cadena de calentamiento delante sin cambiar `ntx/irest` a 5/1. El resto de
la cadena sí es continua (heat2..heat6, density_eq, final_eq, eq2 y prod usan
`ntx=5, irest=1`).

## 8.5 · MEDIA — las 7 etapas con `ntwx` no reciben `-x`: se pierden las trayectorias

`heat1..6` definen `ntwx=500` y `density_eq.in:10` define `ntwx=1000`, pero ninguna de las
invocaciones de `run_MD.sh` (líneas 177, 189, 201, 213, 225, 237, 250) pasa `-x`. AMBER
escribe entonces al nombre por defecto `mdcrd` y **las 7 etapas se sobrescriben entre sí**:
al final solo queda la de `density_eq`. Las trayectorias de calentamiento —justo donde se
diagnostican las explosiones— se pierden sin aviso.

## 8.6 · MEDIA — `gamma_ln` incoherente dentro del propio protocolo

`heat1..6:15`, `density_eq.in:17` y `final_eq.in:17` usan `gamma_ln=2.0`, mientras
`eq1/eq2/prod_md:10` usan **50.0**, que es el valor de referencia para proteína+WT4
(`tutorial/5/eq1_WT4.in:10`, `tutorial/8/eq1_WT4.in:10`; la serie lipídica usa 5.0, nunca
2.0, que es un valor all-atom). El sistema se calienta y equilibra con un acoplamiento 25×
más débil que el que se usa después, así que el estado al que llega `eq1` no es el del
protocolo. Y `configurar_simulacion.sh:344,375,406` **degrada** los ficheros versionados:
reescribe eq1/eq2/prod con `gamma_ln = 5.0`.

## 8.7 · MEDIA — `temp0 = $TEMP.0` se rompe con una temperatura decimal

`validate_positive` (`configurar_simulacion.sh:14`) acepta `^[0-9]+\.?[0-9]*$`, así que
`310.5` pasa, y la interpolación de las líneas 345, 376 y 407 produce `temp0 = 310.5.0`.
Namelist Fortran inválido → `pmemd`/`sander` aborta al leer `&cntrl` en eq1, eq2 y
producción a la vez.

## 8.8 · MEDIA — `ntpr=ntwx=ntwr=50` frente a 5000 de referencia

`prod_md_WT4.in:6`, `eq1_WT4.in:6` y `eq2_WT4.in:6`. Es **independiente** del `nstlim=500`
ya documentado: al restaurar `nstlim` a longitud de producción (50 000 000 pasos, el valor
de `tutorial/5/md_WT4.in`), `ntwx=50` escribiría **1 000 000 de fotogramas** en vez de
10 000 — decenas de TB para este sistema — y `ntwr=50` forzaría un restart cada 1 ps.

## 8.9 · BAJA — parámetros menores

- `density_eq.in:14-16` y `final_eq.in:14-16`: `barostat=2` (Monte Carlo) con `taup=2.0`;
  `taup` solo aplica al barostato Berendsen (`barostat=1`), queda inerte.
- `gensystem.leap:7`: `set default PBradii mbondi3` es un conjunto de radios GB all-atom;
  ningún input usa `igb` y SIRAH no define radios mbondi3 para sus perlas. Los tutoriales
  no lo ponen. Escribe radios sin sentido en el prmtop.
- `heat1..6`, `density_eq.in`, `final_eq.in`: omiten `ioutfm=1` y `ntxo=2`, presentes en
  todos los inputs de referencia. `run_MD.sh` nombra las salidas `.ncrst`, así que en
  builds donde `ntxo` por defecto es 1 esos ficheros serían restarts ASCII con extensión
  NetCDF.

**Verificado correcto** (no son hallazgos): la rampa térmica es continua y el `tempi` de
cada etapa coincide con el `temp0` de la anterior; los bloques `&wt type='TEMP0'` / `'END'`
están completos en las 6 etapas y no se necesita `DISANG`; todas las combinaciones
`ntb/ntp` son coherentes con el ensamble; `ntr=1` siempre va con `restraint_wt`; `iwrap` y
`nscm` tampoco se fijan en la referencia; y los 13 `.in` que valida `run_MD.sh:128` son
exactamente los que existen y se ejecutan.

---

# 9 · PackMan — empaquetador y orquestación

## 9.1 · ALTA — la regex de violación nunca coincide: el bucle no tiene criterio de parada

`2Empaquetador_Maximo.py:87` busca `"Maximum distance violation:"`. Packmol **no imprime
esa cadena**. Verificado contra los dos logs reales del repo:

```
$ grep -o "Maximum[^:]*:" empaquetador/log_packmol_1enzimas_20260324_212620.txt | sort -u
Maximum internal distance of type            1 :
Maximum number of GENCAN loops for all molecule packing:
Maximum violation of target distance:          ← la real
Maximum violation of the constraints:
Maximum violation of the restraints:
```

Así que `leer_violacion_maxima()` devuelve siempre `None`, el bloque de decisión (líneas
156-167) **nunca se ejecuta** y se cae al fallback de la línea 170: `if total_lines <
10000: break`. Como la cápside sola aporta 216 780 líneas ATOM, la condición nunca se
cumple: el bucle incrementa `n` indefinidamente, relanzando Packmol sobre un PDB de 17 MB
(~133 s por corrida según el log) hasta que Packmol falle solo o se agote el disco. **El
"máximo empaquetamiento" reportado no tiene ninguna relación con colisiones.** El propio
`README.txt` anticipa el síntoma ("El log no muestra 'Maximum distance violation'") sin
darse cuenta de que es el caso siempre.

## 9.2 · ALTA — `2Empaquetador_Manual.py:14` ignora `radio_interno.txt`

`radio_interno = 90` cableado, mientras `2Empaquetador_Maximo.py:19-26` sí lee el fichero y
`README.txt:104` documenta que el modo manual usa "`inside sphere` usando
`radio_interno − 2 Å`". `run_maestro.sh:35` ejecuta `1calcula_radio_interno.py` (que
escribe el fichero) y la línea 38 ejecuta acto seguido el **manual**, que lo descarta. Hoy
es invisible porque el fichero contiene `90`; con otra cápside de radio interno 60 Å
seguiría usando `inside sphere 0 0 0 88` y colocaría enzimas dentro de la pared proteica.

## 9.3 · ALTA — `setup_1_1o.sh` y `setup_universal_md.sh` generan ficheros vacíos y declaran éxito

```
setup_1_1o.sh:31  sed "s/NENZIMAS/$N_ENZIMAS/g" "$SOURCE_DIR/gensystem_template.leap" > "$TARGET_DIR/gensystem.leap"
setup_1_1o.sh:34  sed "s/NENZIMAS/$N_ENZIMAS/g" "$SOURCE_DIR/run_MD_template.sh"     > "$TARGET_DIR/run_MD.sh"
```

**No existe ningún fichero `*template*` en el repositorio** (verificado con `find`: solo
aparecen los directorios `templates/` de Flask). `sed` falla, pero la redirección ya creó
los destinos → `gensystem.leap` y `run_MD.sh` de **0 bytes**; la línea 35 les hace
`chmod +x` y la 37 imprime `✓ Configurado`. En `setup_universal_md.sh` es peor: la
salvaguarda de las líneas 47 y 53 (`grep -q "DIRNAME"`) pasa **precisamente porque el
fichero está vacío**, así que tampoco avisa.

## 9.4 · ALTA — `run_maestro.sh:41` recoge el PDB viejo versionado

```bash
GENERATED_FILE=$(ls capside_${N_ENZIMAS}enzimas_*.pdb | head -1)
```

La línea 28 copia `archivos_dm_cg/*` (incluido `empaquetador/`) al directorio de trabajo, y
`empaquetador/` trae versionado **`capside_1enzimas_20260324_212620.pdb`** (17.8 MB). `ls`
ordena lexicográficamente, así que para `N_ENZIMAS=1` ese nombre de marzo precede a
cualquier timestamp de hoy: **el PDB recién empaquetado se descarta** y se propaga el
precocinado a `cgconv.pl` → tleap → MD. Toda la cadena simula una estructura antigua
mientras los logs dicen que se empaquetó. Mismo efecto en `2Empaquetador_*.py:34-38`: como
`enzima_recentrada.pdb` y `capside_recentrada.pdb` están versionados, el recentrado **se
salta siempre** aunque `capside.pdb`/`enzima.pdb` hayan cambiado. Debería ser `ls -t` y/o
invalidación por mtime.

## 9.5 · ALTA — `run_maestro.sh:74` invoca un script que no existe

`if bash ejecutar_analisis_cpptraj.sh; then` — ese nombre **no aparece en ningún lugar del
repo** (verificado). En `analisis/` solo hay `ejecutar_analisis_individual.sh`,
`ejecutar_todo_paralelo_progreso.sh`, `ejecutar_todos_graficos.sh` y
`copiar_scripts_grafiqueo.sh`. El paso 6 del workflow maestro nunca corre: se imprime
`⚠️ Análisis falló, pero continuando...` y el workflow **termina anunciando éxito**.
Además hace falta `generar_analisis_individual.py` antes (es quien crea los `.cpptraj`), y
`run_maestro.sh` tampoco lo invoca.

## 9.6 · MEDIA — `1calcula_radio_interno.py` reporta un radio 1 Å mayor que el libre

- Líneas 28-29: `cmd.alter("centro", f"vdw={r}")` + `cmd.rebuild()` es **código muerto**;
  la selección de la línea 30 usa `within {r + 0.5} of centro`, una distancia al
  pseudoátomo, no su radio vdW. El bucle solo localiza el átomo más interno.
- Líneas 38-41: tras la primera colisión reasigna `radio_colision = r` (= colisión + 1) y
  rompe. El valor escrito es **1 Å mayor** que el radio de colisión.

Verificado: el átomo más interno de `capside_recentrada.pdb` está a 89.5 Å del centro, y el
bucle produce 90 (el contenido real de `radio_interno.txt`). Los empacadores restan
`margen_colision = 2` → `inside sphere 0 0 0 88`, **1.5 Å por dentro de la superficie
interna y por debajo de la `tolerance 2.0`** declarada en el input de Packmol. El volumen
declarado disponible solapa la zona prohibida, y `2Empaquetador_Maximo.py` empuja N
exactamente contra ese margen negativo.

## 9.7 · MEDIA — `run_maestro.sh:20` produce `N_ENZIMAS="1o"`

El glob de la línea 11 (`[0-9]*_[0-9]*`) casa con `1_1o`, que es un nombre esperado (hay un
`setup_1_1o.sh` dedicado), y `cut -d'_' -f2` devuelve `1o`. Entonces el `int(input(...))`
de `2Empaquetador_Manual.py:20` lanza `ValueError`, `ls capside_1oenzimas_*.pdb` no
encuentra nada, `GENERATED_FILE` queda vacío y `cp "" …` falla. Sin `set -e` (desactivado a
propósito en la línea 6) el bucle sigue hasta el `continue` de la línea 53.

## 9.8 · MEDIA — `cd` sin verificar, con desbalance posible

`run_maestro.sh:31,34,45,52,73,79,90`: ninguno comprueba el resultado. Caso concreto: si
`cd analisis` (línea 73) falla, el `cd ..` de la línea 79 sube de `$DIR` a la raíz y el
`cd ..` de la línea 90 sale **por encima** de `PackMan.v.1.2/`; la siguiente iteración
ejecuta `cp -r archivos_dm_cg/* "$DIR/"` en el directorio padre equivocado.

## 9.9 · MEDIA — `prod-q_gpu.bsub` apunta a un clúster y a ficheros inexistentes

- Línea 6: `source /tmpu/scunam/config/tipo_nodo.sh` — ruta del clúster del autor.
- Línea 12: `-p capside-3_cg-WAT.prmtop -c capside-3_cg-WAT_eq2.ncrst`. La convención que
  produce `setup_universal.sh:15-16` es `capside-<DIR>-cg-WAT.*` (con guion, no `_cg`), y
  ese nombre no casa con el glob `capside-*-cg-WAT.prmtop` de `run_MD.sh:39`.
- Arranca desde `_eq2.ncrst`, **saltándose `final_eq`** (etapa 7 de `run_MD.sh`), así que
  el estado inicial de producción no es el que define el protocolo.
- No tiene `#!/bin/bash`, ni `#BSUB -J`, ni límite de tiempo de pared.

## 9.10 · BAJA — dos más

- `1calcula_radio_interno.py:45`: si en `range(5, 200)` nunca se detecta colisión,
  `radio_colision` queda **sin definir** → `NameError`, no se escribe el fichero, y
  `run_maestro.sh:35` no comprueba nada y continúa.
- `run_MD.sh:134-139`: ante inputs ausentes solo imprime
  `Continuando con available input files...`. Si falta p.ej. `heat3_100to150.in`, `heat4`
  se lanza con `-c ${NAME}_heat3.ncrst`, que no existe; el usuario ve un fallo de AMBER en
  vez del diagnóstico real.

---

# 10 · PackMan — pipeline de análisis

## 10.1 · ALTA — se confunde la numeración PDB con el índice absoluto de residuo de cpptraj

`generar_analisis_individual.py:43-44` recoge `int(resi)` de PyMOL y emite ese conjunto
tal cual como máscara cpptraj (`:{rango_residuos}`, líneas 270, 273, 289, 305, 308, 330,
346, 349). Pero una máscara `:N-M` de cpptraj se refiere al índice **secuencial absoluto**
del residuo en la topología, no al `resSeq` del PDB. Medido sobre los ficheros del repo:

| Fichero | Residuos | `resSeq` distintos | Cadenas |
|---|---|---|---|
| `empaquetador/capside.pdb` | 28 620 | **164** (26-189) | A, B, C (repetidas 60×) |
| `sustratinaitor/1_capside/3J7L_cg.pdb` | 28 620 | **164** (26-189) | ninguna |
| `empaquetador/enzima.pdb` | 497 | 497 (1-497) | A |

Consecuencias concretas:

- `caracterizar_capside` devuelve como máximo 164 números → máscara `:26-189` → cpptraj
  analiza los **primeros 164 residuos de la topología** (≈0.6 % de la cápside, un trozo de
  un solo protómero). `capside_ryg.dat` y `capside_rmsd_*.dat` **no miden la cápside**.
- `caracterizar_enzimas` (líneas 74-88): como todas las copias comparten `resSeq` 1-497,
  el `set()` las colapsa y `n_enzimas = 497 // 497 = 1` **siempre**, con 1 o con 20 enzimas
  empaquetadas. Aplicado a la cápside sola (164 únicos) sale `n_enzimas = 0`: cero scripts
  generados, sin error.
- Y los rangos de la cápside (26-189) están **contenidos** en los de la enzima (1-497), así
  que las máscaras "cápside" y "enzima 1" se solapan y, en el prmtop (donde Packmol pone la
  cápside primero), ambas apuntan a los primeros residuos de la cápside: **la enzima nunca
  se analiza**.

La separación geométrica tiene que traducirse a índices absolutos del prmtop, no a
`set(int(resi))`.

## 10.2 · ALTA — `local` fuera de función: el resumen final reporta 100 % de errores

`ejecutar_todo_paralelo_progreso.sh:265,278` usan `local status=$(cat …)` en el **cuerpo
principal** del script, no dentro de una función. Verificado:

```
$ bash -c 'local x=1'
bash: line 1: local: can only be used in a function
```

Bash imprime el error, `$status` queda vacío, `[ "$status" = "COMPLETADO" ]` es falso y
`((ERRORES++))` se ejecuta para **todos** los trabajos. El resumen reporta
`Exitosos: 0` y la línea 292 nunca sugiere el paso siguiente, aunque todo haya ido bien.

## 10.3 · ALTA — `wait` sobre un PID que no es hijo del subshell

`ejecutar_todo_paralelo_progreso.sh:59`: `cpptraj` se lanza en la línea 38 dentro del
subshell de `ejecutar_con_progreso`, y el `( … ) &` de las líneas 42-69 es un *nieto*, para
el que `$cpptraj_pid` es un hermano:

```
wait: pid 1461 is not a child of this shell
subshell wait rc=127
```

Así que `resultado=127` **siempre** → la línea 66 escribe `ERROR` en el `.status` y `-1` en
el `.progress` en cuanto termina el bucle de monitoreo, incluso cuando cpptraj acabó
perfectamente. El monitor marca ❌ en todos los análisis. Hay que capturar el código de
salida en el mismo shell que creó el proceso.

## 10.4 · MEDIA — la escala temporal de los graficadores está cableada (100× de error)

- `grafiqueo/capside/plot_ryg.py:12`: `time_ns = frames * 1000 / 10000`, y la línea 29
  fija `ax.set_xlim(0, 1000)`.
- `grafiqueo/capside/plot_rmsd.py:18-19`: `time = (frames - 1) * 0.1` ("Assuming 10000
  frames for 1000 ns").
- `grafiqueo/enzimas/plot_sasa.py:40`: `time_ns = frames / len(frames) * 1000`.

Esos 0.1 ns/fotograma corresponden al `ntwx=5000` de la referencia, pero
`prod_md_WT4.in:6` usa `ntwx=50` con `dt=0.020` ps → **0.001 ns/fotograma**, 100× menos.
El eje temporal queda equivocado en dos órdenes de magnitud y, con el `set_xlim(0,1000)` de
`plot_ryg.py`, la curva sale comprimida contra el origen: la figura queda prácticamente
vacía. La normalización de `plot_sasa.py:40` es además adimensionalmente incorrecta: el
último fotograma vale 1000 ns sea la trayectoria de 10 ps o de 1 µs. El tiempo por
fotograma debe derivarse de `dt × ntwx`.

## 10.5 · MEDIA — `zone_colors` definido dentro de una rama condicional

`compara_enzimas_misma_capside.py:190` lo define dentro de `if backbone_data_found:` y las
líneas 230 y 271 lo usan bajo guardas distintas. Si falta `enzimaN_rmsf_backbone.dat` pero
existe `enzimaN_rmsf_all.dat` y se pasaron `--zones`, la línea 230 lanza
`NameError: name 'zone_colors' is not defined`. Y `ejecutar_todos_graficos.sh:213,219`
redirige todo a `/dev/null`, así que el usuario solo ve `❌ Error al generar gráfico` sin
traza.

## 10.6 · BAJA — `tick_labels` requiere matplotlib ≥ 3.9

`compara_enzimas_misma_capside.py:354`: en matplotlib < 3.9 el parámetro se llama `labels`
y esto es un `TypeError` no capturado (está fuera de cualquier `try`). Combinado con la
redirección a `/dev/null` de §10.5, el diagnóstico se pierde.

---

# 11 · PackMan — `fix_pdb_serial.py`

## 11.1 · ALTA — desborda el serial exactamente en el caso para el que se escribió

`fix_pdb_serial.py:36` usa `f"{record_type:6s}{atom_serial:5d} {atom_name:4s}…"` y
`capside.pdb` tiene **216 780** átomos. Verificado ejecutando la f-string sobre una línea
real:

| Serial | Longitud | Columnas 31-38 (x) |
|---|---|---|
| 99 999 | 76 | `' 197.216'` ✓ |
| 100 000 | 77 | `'  197.21'` ✗ |

A partir del átomo 100 000 todo el registro se desplaza una columna: un lector de columnas
fijas (tleap, cpptraj, PyMOL) leería x = 197.21 en vez de 197.216 y la z saldría truncada o
desplazada al campo de ocupancia. Es el mismo defecto que §2.1 del Studio, en otro
fichero. Hay que emitir hybrid-36 o reiniciar el serial.

## 11.2 · MEDIA — el símbolo de elemento acaba en las columnas 73-74, no 77-78

El separador tras el factor B es de 6 espacios; hacen falta 10. Verificado: el elemento
queda en el campo `segID` del formato PDB y las columnas 77-78 quedan vacías. Cualquier
herramienta que lea el elemento del sitio estándar lo ve en blanco y recae en adivinarlo
por el nombre del átomo; las que leen `segID` reciben el símbolo del elemento.

## 11.3 · MEDIA — el script no lo invoca nadie, y el problema que resuelve está vivo

`grep -rn fix_pdb_serial` solo lo encuentra en sí mismo, en `README.md:25` y en
`diagrama_archivos_dm.md:34`. No aparece en `run_maestro.sh`, `convert_to_cg.sh`,
`setup_*.sh` ni en ningún `.py`. Y el problema de seriales sí existe sin resolver:
`1_capside/3J7L_cg.pdb` **reinicia** el serial en 1 en el átomo 100 001, `capside.pdb` lo
**satura en 99999** para sus últimos ~117 000 átomos, y la salida de Packmol
`3J7L-GYE.pdb` emite seriales **hexadecimales** (`186A0`, `186A1` = 100 000, 100 001).
Tres convenciones distintas en el mismo pipeline.

## 11.4 · BAJA — los `CONECT` no se renumeran

El comentario dice "Keep other lines as-is (REMARK, CONECT, etc.)", pero los
`ATOM`/`HETATM` **sí** se renumeran, así que cualquier `CONECT` superviviente apunta a
seriales que ya no existen.

---

# 12 · Sospechas comprobadas que NO se sostienen

Las dejo escritas para que nadie las vuelva a perseguir:

- **Path traversal en `/api/download/single/<filename>`.** Werkzeug lo bloquea; probados
  cinco vectores (`..%2f`, `....//`, doble codificación): 404.
- **`/classic` roto.** Los 8 endpoints que llama `index.html` existen en `app.py`.
- **Desfase JS ↔ backend.** Cruzadas las 20 URLs de `fetch(...)` contra las 32 rutas, y
  los ~60 `$('id')` contra los `id=` de `studio.html`: **sin un solo desfase**, incluidos
  métodos y nombres de campo. Tampoco hay globales duplicados ni `const` redeclarado entre
  los 6 ficheros (38 nombres únicos), y el orden de carga es correcto.
- **Tags de git ausentes.** Existen en el remoto (`studio/v0.1.0`, `poromania/v1.2.0`,
  `packman/v1.2.0`, `sustratinaitor/v1.2.0`… y `v0.1.0`); solo no están en este clon.
- **`requirements.txt` vs `requirements.lock`.** Las 7 dependencias directas coinciden; no
  falta ningún paquete importado por el código.
- **`ruff` y el job `engines` fallando en CI.** Ejecutados: `ruff check` y
  `ruff format --check` pasan limpios; `compileall` sale 0. No hay ningún `|| true` ni
  `continue-on-error` en `ci.yml`.
- **`2out_tsv.py` capturando tablas numéricas ajenas de `hole_out.txt`.** Reproducido el
  parser sobre el fichero real: 347 líneas aceptadas, todas del perfil, que coinciden
  exactamente con las 347 filas del TSV.
- **Sensibilidad del volumen al espaciado de rejilla adaptativo.** Medida: 0.2 % (EGFP),
  0.4 % (GCase), 1.2 % (AlkPhos) entre 1.5 y 2.0 Å. Irrelevante; el problema del volumen
  es la fórmula (§3.4), no la rejilla.
- **El eje de poro del Studio.** Coincide 0.0° con el eje C5 calculado de forma
  independiente (§4.7).
- **`md_prepare` colocando la caja en el sitio equivocado.** El `inside box` está centrado
  en el origen, coherente con `center` + `fixed 0. 0. 0.`. Consistente.
- **`center_structures.py` desbordando el campo de 8 caracteres.** Tras centrar, las
  coordenadas quedan en ±63 Å.
- **`salud.sh:22` fallando por el prefijo `src.`.** Ejecutado: funciona.

En los motores de MD:

- **Rampa de temperatura discontinua en `heat1..6`.** Es continua: el `tempi` de cada etapa
  coincide con el `temp0` de la anterior (0→50→100→150→200→250→300). Los bloques
  `&wt type='TEMP0'` / `'END'` están completos y bien formados en las 6 etapas, y no hace
  falta `DISANG` porque no hay `type='REST'`.
- **Combinaciones `ntb`/`ntp` incoherentes con el ensamble.** Son correctas: NVT en
  em/heat, NPT en density/final/eq/prod. `igb` no aparece en ningún fichero y `ntr=1`
  siempre va acompañado de `restraint_wt`.
- **`iwrap` y `nscm` sin fijar.** Tampoco se fijan en los inputs de referencia: no es una
  desviación.
- **`skinnb=5` ausente.** Aparece en `tutorial/6` y `tutorial/7` (series lipídicas) pero
  **no** en `tutorial/5` ni `tutorial/8`, que son las referencias proteína+WT4 aplicables.
- **`addIonsRand … NaW 0` con el contraión del signo equivocado.** Las cargas netas
  calculadas desde los propios ficheros son: cápside CG 0 (3000 sK+sR frente a 3000
  sD+sE), enzima −1, GYE +0.002 e. `NaW` es el signo correcto en los dos motores.
- **Secuencia de etapas de `run_MD.sh` desalineada con los ficheros.** La lista de
  validación de la línea 128 enumera exactamente los 13 `.in` que se ejecutan, y los 13
  existen.
- **Profundidad de los `../../../../..` en los `.cpptraj` generados.** Correcta: 5 niveles
  para enzimas y 4 para cápside resuelven ambos al directorio del sistema.
- **Tercera columna de `capside_ryg.dat`.** `plot_ryg.py:9` lee `data[:,2]` como "RoG
  Maximum"; `radgyr` de cpptraj genera ese dataset por defecto (solo se suprime con
  `nomax`, que el generador no pasa). Correcto.
- **`center_structures.py` desbordando el campo de 8 caracteres** y **sintaxis**: `bash -n`
  sobre los 20 scripts shell y `py_compile` sobre los 19 Python salen limpios.

Nota de discrepancia: una pasada previa de este mismo trabajo contó 18 sustratos dentro de
la cavidad, 86 fuera y 96 en la pared en §7.1. Mi recuento, tomando como referencia el
centroide **real** de la cápside y no el origen, da **0 / 199 / 1**. Mando mi medición
porque la cápside no está en el origen; es justo el punto del hallazgo.

---

# 13 · Lo que no pude verificar aquí

Para cerrarlo hace falta el entorno con los motores instalados:

- **La mutagénesis del Studio (§4.2).** Sin PyMOL no pude confirmar si reproduce el fallo
  de Poromania. Es la verificación de mayor valor por minuto invertido: cargar un modelo,
  mutar y comparar `resn` antes/después.
- **`applyOpacity()` (`studio-core.js:37-43`).** Si `r.name` de un `RepresentationElement`
  de NGL no devuelve `'surface'`, el deslizador de opacidad no hace nada. El proxy bloqueó
  el CDN, así que no pude leer la versión de NGL. Se cierra en consola con
  `comp.eachRepresentation(r => console.log(r.name, r.repr && r.repr.type))`.
- **`pore_analyzer.py:57`** (`sphere_scale` vs el radio usado en el `within` de la línea
  68): posible desacuerdo entre la esfera dibujada y la usada en la selección.
- **Doble protonación** en `generate_ligand_from_smiles.py:126` (`obabel -p` sobre una
  molécula que ya trae hidrógenos de `Chem.AddHs`).
- **`&cntrl` terminado con `&end` en vez de la barra `/`** (`em1_WT4.in:11`,
  `eq1_WT4.in:19`…, frente a `tutorial/5/em1_WT4.in:13-14`, que pone ambos). Es una
  desviación real del formato de referencia, pero sin `gfortran` aquí no pude comprobar si
  el lector de namelist de AMBER acepta `&end` como terminador. **No lo cuento como bug.**
- **Si la MD de PackMan llegó a correr alguna vez.** No hay en el repo ni trayectorias ni
  `.dat` ni `.out` de ninguna etapa, así que todos los hallazgos de §8-§11 son sobre los
  *scripts commiteados*, no sobre lo que se ejecutó. Para cerrar §8.1 (`chngmask`) y §8.4
  (`irest=0`) hacen falta los `.out` reales, que `REVISION_MOTORES.md` ya pide.

---

# 14 · Si hubiera que arreglar solo tres cosas

Sin entrar en las decisiones científicas (CIENCIA-1/2/3 siguen siendo de Lucio), estas tres
son las de mayor relación entre daño evitado y esfuerzo:

1. **Verificar que las mutaciones se aplican** (§1.1 y §4.2). Comparar `resn` antes y
   después de `w.apply()` y abortar si no cambió. Es una guarda de tres líneas que
   convierte el fallo más grave del repositorio en un error visible, en los dos motores.
2. **Comprobar que la región de empaquetado interseca la estructura** (§2.4 y §7.1). Antes
   de escribir el input de Packmol, verificar que el centro de la esfera o caja cae dentro
   de la cápside. Cubre de golpe el packing del Studio y `sustratinaitor`, y ataca el
   patrón de fondo: restricciones respecto al origen sobre estructuras que no están en el
   origen.
3. **Que los fallos silenciosos dejen de ser silenciosos.** El hilo común de casi todo este
   informe: fallbacks numéricos que se presentan como mediciones (§1.7, §3.3), códigos de
   salida ignorados (§1.8, §4.2, §7.2, §9.3), `except` vacíos (§4.4, §4.5) y motores
   externos que declaran éxito porque cumplieron la restricción equivocada (§2.4, §7.1).
   Mientras eso siga así, cada hallazgo corregido deja sitio al siguiente sin que nadie
   lo note.
