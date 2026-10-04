# Auditoría científica independiente — motor de poro (Poromania v1.2.0)

**Encargo:** `REVISION_MOTORES.md`. Auditoría desde cero del motor de poro, con foco
acotado en las **dos implementaciones** del mismo análisis (`Poromania.v.1.2.` y
`nanocapsule-mvp/src/services/pore.py`), el **uso de HOLE2** (eje, centro, semilla,
validación de canal), la **mutagénesis** y el **docking con idock**.

**Fecha:** 2026-10-04 · **Auditor:** pasada independiente · **Código:** no modificado.

**Entorno:** HOLE, PyMOL, Vina, idock y obabel **no están instalados** en esta máquina.
Toda conclusión se etiqueta **[ESTÁTICO]** (demostrada sobre el código y los artefactos
commiteados, sin ejecutar motores) o **[REQUIERE CORRER]** (hipótesis que necesita los
binarios). Lo que sí pude ejecutar: Python con numpy, `awk`/`mawk`, y aritmética
geométrica sobre los PDB y las salidas de HOLE commiteadas. El informe sella el orden
pedido: formé criterio propio antes de leer la lista sellada, y el cross-check va al final
(§10).

---

## 1. Veredicto

El motor de poro **no es reproducible hoy**, y la causa no es principalmente la
duplicación de implementaciones. Es más grave y más simple: **el único resultado de poro
que existe en el repositorio está mal atribuido en tres niveles a la vez.**

1. El «mutante» que lo produjo **no está mutado**: `mutants/mut_129HIS_132GLY/receptor.pdb`
   es **byte-idéntico** a `mutants/WT.pdb`. El perfil de 1.92 Å es del tipo salvaje.
2. La estructura de partida **no es la que dicen los scripts commiteados**: es
   `modelos/BMV/poro5fold.pdb` centrado, no `poronatural.pdb`. Con los inputs del repo el
   artefacto **no se puede regenerar**.
3. La geometría con que se midió **no apunta al poro**: el punto semilla cae a **7.59 Å
   del eje de simetría** de un canal cuyo radio mínimo es 1.92 Å, y el eje va **19.3°
   desviado**. La constricción que HOLE acabó trazando está a **11.76 Å** del eje real.

Sobre la pregunta central: las dos implementaciones **no darían el mismo número sobre la
misma entrada**, y no por ruido numérico, sino porque **definen el canal de forma
distinta**. El Studio recupera el eje de simetría del pentámero con error **0.00°**;
Poromania usa un heurístico que yerra 19.3°. Las dos cifras que la documentación atribuye
al mismo poro 5-fold de BMV —**1.92 Å** (Poromania) y **≈1.68 Å** (Studio)— difieren un
14 % y son, hasta donde alcanza la evidencia estática, la huella de esa divergencia.

El juicio no es simétrico: **la implementación nueva del Studio es científicamente la
correcta** en centro y eje, y es la que debe sobrevivir. Pero tiene dos defectos propios
serios (§6, PORO-07 y PORO-08) que invalidan su cribado sobre la estructura pentamérica y
dejan su eje mal condicionado sobre las triméricas, que son justo las que dan el
«2.47 Å» documentado.

### Severidad por bloque

| Bloque | Severidad | Estado |
|---|---|---|
| Atribución del resultado reportado | **CRÍTICA** | el perfil publicado es del WT, no de un mutante |
| Reproducibilidad del artefacto | **CRÍTICA** | inputs commiteados ≠ inputs usados |
| Geometría del canal (Poromania) | **CRÍTICA** | semilla fuera del canal, eje 19.3° desviado |
| Geometría del canal (Studio) | **ALTA** | exacta en C5, mal condicionada en C3 (6.1°), sin guarda |
| Divergencia entre implementaciones | **ALTA** | parámetros y definiciones distintos |
| Determinismo de HOLE | **ALTA** | Poromania sin `rseed`; Studio con `rseed 1` |
| Validación de canal | **ALTA** | existía y **se borró**; hoy solo en el Studio |
| Mutagénesis | **ALTA** | `resi`+`chain` no identifica residuo en el pentámero |
| Docking | **MEDIA** | idock sin semilla; idock y Vina no comparables |
| Presentación de lo ilustrativo | **MEDIA** | se vació el badge «(ilustrativo)» |

---

## 2. Inventario: cuántas implementaciones hay realmente

El encargo habla de dos. Hay **cuatro** rutas de código que calculan o definen el eje y el
centro del poro, más dos copias del driver de HOLE:

| # | Ruta | Papel | Vivo |
|---|---|---|---|
| 1 | `Poromania.v.1.2./pore_analyzer.py` → genera `1crear_mutantes.pml` | define centro y eje, escribe `pore_center.txt` / `pore_vector.txt` | **sí** |
| 2 | `Poromania.v.1.2./scripts/1run_hole.sh` | consume esos `.txt` y llama a HOLE | **sí** |
| 3 | `Poromania.v.1.2./scripts/1run_hole_old.sh` | barrido de 10 vectores + **validación de canal** | no invocado |
| 4 | `nanocapsule-mvp/src/services/pore.py` (`_pore_axis`, `_hole_on`) | eje por tensor de segundo momento + `rseed` | **sí** |
| — | `Poromania.v.1.2./pore_analyzer_backup.py` | versión previa divergente | no invocado |
| — | `mutants/*/scripts/1run_hole{,_old}.sh` | copia por mutante (`3copiar_scripts.sh`) | **sí**, por copia |

`pore_analyzer.py:444-483` define **`calculate_pentamer_center` dos veces**, de forma
idéntica salvo tildes, y **ninguna de las dos se llama**. El `.pml` generado arrastra esa
duplicación literalmente (`1crear_mutantes.pml:49-88`). Es código muerto que además
documenta una intención —centrar en el eje pentamérico— que el código vivo **no** cumple.

`3copiar_scripts.sh` copia `scripts/*` dentro de cada `mutants/mut_*/scripts/`. Verifiqué
que la copia commiteada es **idéntica** a la base (`diff -r scripts
mutants/mut_129HIS_132GLY/scripts` → sin diferencias). Hoy coinciden; el riesgo es que
corregir el eje en `scripts/` deje N copias viejas corriendo la versión anterior sin que
nada lo señale. **[ESTÁTICO]**

---

## 3. Diferencias línea a línea entre las dos implementaciones

Las dos acaban invocando el mismo binario `hole` con un *input deck* de la misma forma. La
divergencia está en **qué valores** le pasan.

### 3.1 El input deck de HOLE

| Tarjeta | Poromania `scripts/1run_hole.sh:37-47` | Studio `pore.py:128-137` | ¿Divergen? |
|---|---|---|---|
| `coord` | `receptor.pdb` (relativo al dir del mutante) | copia del modelo a `workdir/receptor.pdb` | equivalente |
| `radius` | `scripts/vdwradii.lib` | **el mismo fichero**, copiado de `POROMANIA_DIR/scripts` (`pore.py:123`) | **no** — bien |
| `cpoint` | `pore_center.txt`, 2 decimales | `_pdb_centroid(text)`, 3 decimales | **SÍ, radicalmente** |
| `cvect` | `pore_vector.txt`, 2 decimales | `_pore_axis(text, c)`, 4 decimales | **SÍ, radicalmente** |
| `sphpdb` | `hole/resultados/hole_spheres.pdb` | `hole_spheres.pdb` | equivalente |
| `endrad` | `10.0` | `10.0` | no |
| `sample` | **`0.2`** | **`0.25`** | **sí** |
| `rseed` | **ausente** | **`rseed 1`** | **sí** |
| extra | `gmacro`, `quit` | — | sí (inocuo, §6 PORO-13) |

Que `vdwradii.lib` sea **un solo fichero compartido** es un acierto real de la integración
(`pore.py:123`): los radios de van der Waals no pueden divergir entre motores. Conviene
decirlo porque es la única entrada científica que hoy está garantizada idéntica.

### 3.2 Centro del canal (`cpoint`)

**Poromania** (`pore_analyzer.py:415-442`, replicado en `1crear_mutantes.pml:20-47`):

```
para cada pos en sorted(selected_positions) y cada chain:
    CA de (resi=pos, chain=chain)  ->  temp_coords[0]      # solo el PRIMERO
center_avg = media de esos CA
```

El centro es la **media de los CA de los residuos seleccionados**. En la corrida
commiteada eso son 4 átomos (129-132, cadena A), no el centro del canal.

**Studio** (`common.py:41-56` vía `pore.py:126`): `_pdb_centroid` = media de **todos** los
átomos del PDB. Para un oligómero Cn el centroide **está sobre el eje de simetría**.

Medido sobre el mismo fichero (`mutants/mut_129HIS_132GLY/receptor.pdb`):

| | `cpoint` | Distancia al eje 5-fold real |
|---|---|---|
| Poromania | `9.18 -3.88 2.22` | **7.59 Å** |
| Studio | `0.00 0.00 -0.00` | **0.000 Å** |

Los dos centros están a **10.21 Å** uno del otro. El radio mínimo del canal es 1.92 Å:
la semilla de Poromania está a casi **4 radios** del eje, es decir **dentro de la pared
proteica**, no en la luz del canal. **[ESTÁTICO]**

### 3.3 Eje del canal (`cvect`)

**Poromania** (`pore_analyzer.py:485-497`): `vector = center_avg − first_residue_coord`,
normalizado. Es la **cuerda** del CA del primer residuo al centroide del grupito de
residuos. En la corrida commiteada su longitud antes de normalizar es **4.40 Å**: una base
cortísima, de modo que un desplazamiento pequeño de cualquiera de los dos extremos gira el
eje mucho. No tiene relación con la simetría de la cápside.

**Studio** (`pore.py:70-94`): diagonaliza `aᵀa` con `a = coords − centro` y toma el
eigenvector del **valor propio distinto**, no el de mayor varianza. El docstring lo llama
«tensor de inercia»; es el **tensor de segundo momento** (`Σ r⊗r`). Los eigenvectores
coinciden, pero el **orden de los valores propios está invertido** respecto a la inercia.
El código no depende del orden absoluto —elige por cercanía del par degenerado— así que
**el razonamiento es correcto aunque el nombre en el docstring no lo sea.**

#### Verificación independiente del eje verdadero

Para no arbitrar entre las dos definiciones con una tercera opinión, derivé el eje de la
**propia simetría de la estructura**, sin usar ninguno de los dos algoritmos: centroides
de las 5 subunidades de la cadena A (segmentos `A_6`…`A_10`), normal al plano de mejor
ajuste, y comprobación de que una rotación de 72° mapea los centroides entre sí.

```
valores singulares de los 5 centroides: [40.13  40.13  0.00]   -> coplanares
rotación de 72° : desviación máxima 0.000 Å                     -> simetría C5 EXACTA
eje 5-fold (verdad independiente) = [ 0.276  -0.851   0.447 ]
```

Contra esa verdad:

| | Eje | Error angular |
|---|---|---|
| **Studio** `_pore_axis` | `[ 0.276 -0.851  0.447]` | **0.00°** |
| **Poromania** `pore_vector.txt` | `[-0.397  0.629 -0.668]` | **19.29°** |

El Studio **recupera el eje exacto**. Poromania yerra 19.3°. **[ESTÁTICO]**

### 3.4 Lectura del perfil y del punto de constricción

Aquí, contra lo que esperaba, las dos **coinciden**, y conviene decirlo:

- `2out_tsv.py:15-25` y `_parse_hole_profile` (`pore.py:97-113`) aplican el mismo filtro
  (`radio > 0.5`) sobre `parts[0]`/`parts[1]`. Verifiqué que sobre
  `hole_out.txt` ambos ingieren **exactamente un bloque contiguo** (líneas 1992-2338,
  la tabla `cenxyz.cvec / radius / cen_line_D / sum{s/area}`), 347 filas, y devuelven
  **el mismo mínimo: 1.915 Å en z = −15.382**, que es el que HOLE imprime como
  `Minimum radius found: 1.915 angstroms`. El parseo no está roto. **[ESTÁTICO]**
- Punto de constricción desde `hole_spheres.pdb`: el Studio usa **columnas fijas**
  (`pore.py:195-202`, `line[60:66]`) y `5docking.sh:45` usa **división por campos** de awk.
  Ejecuté los dos sobre el fichero commiteado y dan **el mismo resultado**:
  `r = 1.920` en `(15.033, −12.215, 2.264)`.

El awk de `5docking.sh` **funciona por suerte, no por diseño**: 93 de las 268 líneas
`ATOM` del fichero tienen 10 campos en vez de 11 (el `resSeq` negativo pega
`S` con `-888` → `S-888`), lo que desplaza las columnas. En esas líneas `$10` cae sobre el
segundo `0.00`, falla el test `r>0` y se descartan. Si HOLE escribiera ahí un valor no
nulo, el awk tomaría coordenadas y radio de columnas equivocadas. **[ESTÁTICO]**

Nota sobre ese punto: está a **11.76 Å del eje 5-fold real**. No es la constricción del
poro de simetría; es el cuello del túnel lateral que HOLE encontró al salir de una semilla
mal puesta.

### 3.5 Diferencias de contrato de salida

| | Poromania | Studio |
|---|---|---|
| Origen de Z | `cenxyz.cvec` crudo | **re-centrado**: `positions = z − z(mínimo)` (`pore.py:149`) |
| Validación de canal | ninguna (§6 PORO-04) | `len(rs) < 30` → `RuntimeError` (`pore.py:144-145`) |
| Mínimo | `df["Radio"].min()` global (`3analizar_hole.py:31`) | `min(rs)` sobre la misma lista filtrada |
| Artefactos | TSV + PNG + PDF por mutante | dict JSON a la API |

El re-centrado del Studio es una **mejora de presentación** (el cero queda en la
constricción) pero significa que **los ejes X de las dos salidas no son comparables**: un
perfil de Poromania y uno del Studio superpuestos están desplazados entre sí. Si alguna
figura mezcla ambos, el desplazamiento es invisible. **[ESTÁTICO]**

---

## 4. ¿Cuál generó los resultados reportados en la documentación?

### La cadena de procedencia, reconstruida

`nanocapsule-mvp/PLAN_POROMANIA.md:40-42` lo dice sin ambigüedad:

> **1 perfil calculado**: `mutants/mut_129HIS_132GLY/.../hole_profile.tsv` (347 puntos,
> Z ∈ [-21.6, 13.0], **radio mín 1.92 Å** en Z≈-15.4). De aquí salió el "1.9 Å" de la
> maqueta.

Confirmado punto por punto sobre el fichero: 347 filas, Z ∈ [−21.582, 13.018], mínimo
1.915 Å en Z = −15.382. **Ese número lo generó Poromania**, con la geometría de §3.2-3.3.
Es el **único** resultado de poro real que existe en el repositorio.

Y ese 1.9 Å viaja al Studio como constante ilustrativa. En `pore.py:32`:

```python
_AXIS_MIN = {"3-fold": 1.9, "5-fold": 3.2, "2-fold": 2.6}
```

Aquí hay **dos errores de atribución encadenados**:

- El 1.92 Å se midió sobre una estructura **pentamérica** (`poro5fold.pdb`, §4.2) y quedó
  almacenado como el mínimo del eje **3-fold**.
- El valor del eje 5-fold (`3.2`) **contradice la medición real** del propio Studio.
  `SESION_STUDIO.md:39` reporta «3-fold ≈2.47 Å, 5-fold ≈1.68 Å». La tabla ilustrativa dice
  que el 5-fold es **más ancho** que el 3-fold (3.2 vs 1.9); la medición dice que es
  **más estrecho** (1.68 vs 2.47). **El orden está invertido.** **[ESTÁTICO]**

Las cifras del Studio (`2.47` y `1.68`) solo existen en prosa; no hay en el repositorio
ningún `Output/hole_runs/` ni artefacto que las respalde. **[REQUIERE CORRER]** para
verificarlas.

### 4.1 El «mutante» reportado no está mutado — CRÍTICO

```
$ cmp mutants/WT.pdb mutants/mut_129HIS_132GLY/receptor.pdb
BYTE-IDENTICAL
$ md5sum mutants/WT.pdb mutants/mut_129HIS_132GLY/receptor.pdb
d56a4e539c65c964ffe6fe7cd70a57d3  mutants/WT.pdb
d56a4e539c65c964ffe6fe7cd70a57d3  mutants/mut_129HIS_132GLY/receptor.pdb
```

Idénticos: 5738 líneas, 0 diferencias, desviación máxima de coordenadas 0.0 Å. Y las
identidades de residuo lo confirman en las cinco copias:

```
CA en resi 129 -> {(A,A_6,SER), (A,A_7,SER), (A,A_8,SER), (A,A_9,SER), (A,A_10,SER)}
CA en resi 132 -> {(A,A_6,VAL), (A,A_7,VAL), (A,A_8,VAL), (A,A_9,VAL), (A,A_10,VAL)}
```

La posición 129 sigue siendo **SER** y la 132 sigue siendo **VAL**, en las cinco
subunidades. El wizard de mutagénesis de PyMOL **no cambió nada**, pero el pipeline
siguió adelante sin notarlo: creó el directorio con el nombre del mutante, escribió
`pore_center.txt`, corrió HOLE y produjo el perfil.

**Consecuencia:** el perfil de 1.92 Å es el del **tipo salvaje**, archivado y citado como
el de un doble mutante 129HIS/132GLY. Cualquier conclusión del tipo «esta mutación abre o
cierra el poro» apoyada en ese fichero no tiene base. **[ESTÁTICO]**

Por qué falló, con alta probabilidad: ver §8 (`resi`+`chain` es ambiguo en esta
estructura). Confirmar el mecanismo exacto **[REQUIERE CORRER]** PyMOL.

### 4.2 El artefacto no es reproducible desde los inputs commiteados — CRÍTICO

`1crear_mutantes.pml:5` carga `poronatural.pdb`. Pero:

| Fichero | Átomos | Cadenas | Centroide |
|---|---|---|---|
| `poronatural.pdb` (raíz, lo que el script carga) | 3574 | A, B, C | (98.94, −30.08, 45.91) |
| `mutants/WT.pdb` (lo que el script dice haber guardado) | **5735** | **A, B** | **(0, 0, 0)** |
| `modelos/BMV/poro5fold.pdb` | **5735** | **A, B** | (240.47, 107.63, 260.62) |

Y la identificación es exacta:

```
WT centrado  vs  poro5fold centrado :  max|diferencia| = 0.0 Å
mismo orden de átomos, mismos nombres, mismos resi/chain : True
```

`mutants/WT.pdb` **es** `modelos/BMV/poro5fold.pdb` trasladado a su centroide — la huella
de `center_structures.py`, que centra `poronatural.pdb` **in situ**. La reconstrucción
coherente: alguien copió `poro5fold.pdb` sobre `poronatural.pdb`, lo centró y corrió el
pipeline; después el `poronatural.pdb` de la raíz fue sobrescrito por el de CCMV
(`md5sum` lo confirma: raíz y `modelos/CCMV/poronatural.pdb` son **el mismo fichero**,
`450dfd38…`).

Corolario: `chains = ['A', 'B']` en `1crear_mutantes.pml:14` solo tiene sentido para
`poro5fold`; el `poronatural.pdb` commiteado tiene cadenas A, B y **C**. El script
commiteado es internamente incoherente con su propio input commiteado.

**Si alguien ejecuta hoy el pipeline tal como está en el repositorio, procesa una
estructura distinta (trímero de CCMV en vez de pentámero de BMV) y no puede obtener el
1.92 Å.** **[ESTÁTICO]**

Una nota de limpieza relacionada: `modelos/CCMV/3-folia.pdb` y
`modelos/CCMV/poronatural.pdb` también son el mismo fichero (`450dfd38…`), y
`hole_structures()` (`pore.py:60-67`) solo expone `modelos/*/poro*.pdb`, de modo que
`3-folia.pdb` y `capside.pdb` no son alcanzables desde el Studio.

### 4.3 La geometría con que se midió no apunta al poro — CRÍTICO

Resumen de §3.2-3.3 contra la verdad independiente, todo sobre el mismo fichero:

```
eje 5-fold real                              [ 0.276  -0.851   0.447 ]   (C5 exacta, 0.000 Å)
cvect de Poromania                           19.29° desviado
cpoint de Poromania                          7.59 Å fuera del eje
radio mínimo del canal                       1.92 Å
constricción que HOLE acabó trazando         11.76 Å fuera del eje
```

HOLE hace una búsqueda Monte Carlo del punto de máximo radio desde `cpoint`, en el plano
perpendicular a `cvect`, y avanza. Con la semilla **dentro de la pared**, el primer punto
que encuentra ya está fuera del canal de simetría: el propio `hole_out.txt` lo dice en su
primer bloque —`highest radius point found: at point 12.937 −4.313 −0.431`, `closest atom
surface 2.054 NZ LYS A 130`—, y de ahí sale derivando. El perfil resultante es real como
cálculo y **no es el poro 5-fold**.

**La divergencia entre las dos implementaciones no es un empate entre dos criterios
defendibles. Una de las dos está midiendo el canal que dice medir y la otra no.**

---

## 5. ¿Darían el mismo número sobre la misma entrada?

**No.** Cinco causas independientes, en orden de magnitud del efecto:

1. **`cpoint` distinto** — 10.21 Å de separación; una semilla en la luz del canal, la otra
   en la pared. Es la causa dominante. **[ESTÁTICO]**
2. **`cvect` distinto** — 19.29° de ángulo. Sobre un canal de ~35 Å de largo, eso son
   ~11 Å de desvío lateral acumulado, contra un radio de ~2 Å. **[ESTÁTICO]**
3. **`sample` distinto** — 0.2 vs 0.25 Å. Rejillas distintas ⇒ el mínimo cae en planos
   distintos. Efecto de segundo orden pero **no nulo**: desplaza el mínimo reportado en
   una fracción del paso. **[ESTÁTICO]**
4. **`rseed`** — Poromania no lo fija (§6 PORO-05): HOLE elige semilla por reloj. Dos
   corridas de Poromania sobre la *misma* entrada no tienen por qué coincidir entre sí.
   **[ESTÁTICO]** que el deck no lo fija; cuantificar la dispersión **[REQUIERE CORRER]**.
5. **Filtro `radio > 0.5`** — compartido, pero sesga ambas igual y hacia arriba (§6
   PORO-10).

**Evidencia empírica disponible:** para la misma estructura (BMV `poro5fold`) la
documentación del proyecto reporta **1.92 Å** por la vía Poromania (verificado en el
artefacto) y **≈1.68 Å** por la vía Studio (`SESION_STUDIO.md:39`, sin artefacto). Son
**0.24 Å / 14 %** de diferencia. Que ese delta se deba exactamente a estas cinco causas
**[REQUIERE CORRER]**; que las dos implementaciones no puedan coincidir por construcción
es **[ESTÁTICO]**.

Y la pregunta importante detrás: **ninguno de los dos números está validado**. El 1.92 Å
mide un canal equivocado (§4.3). El 1.68 Å usa la geometría correcta pero no tiene
artefacto que lo respalde, y para los modelos triméricos el eje del Studio está mal
condicionado (§6 PORO-07).

---

## 6. Hallazgos

### PORO-01 · CRÍTICO · [ESTÁTICO] · El mutante publicado es el tipo salvaje

`mutants/mut_129HIS_132GLY/receptor.pdb` ≡ `mutants/WT.pdb` (byte-idéntico, md5
`d56a4e53…`). Posición 129 = SER y 132 = VAL en las 5 subunidades. El perfil de 1.92 Å
—único resultado real del repositorio y origen del «1.9 Å» de la maqueta— es del WT.
Ver §4.1.

### PORO-02 · CRÍTICO · [ESTÁTICO] · El resultado no se regenera desde los inputs del repo

`1crear_mutantes.pml:5` carga `poronatural.pdb` (3574 át., cadenas A/B/C, CCMV) pero el
artefacto salió de `modelos/BMV/poro5fold.pdb` centrado (5735 át., cadenas A/B);
verificado con `max|diff| = 0.0 Å`. Además `chains = ['A','B']` (línea 14) es incoherente
con el input commiteado. Ver §4.2.

### PORO-03 · CRÍTICO · [ESTÁTICO] · Semilla fuera del canal y eje desviado (Poromania)

`cpoint` a 7.59 Å del eje de simetría de un canal de 1.92 Å de radio; `cvect` 19.29°
desviado; constricción trazada a 11.76 Å del eje. `pore_analyzer.py:415-442` (centro) y
`:485-497` (eje). Ver §3.2-3.3 y §4.3.

**Agravante de diseño:** el eje se construye sobre una base de **4.40 Å** (distancia del
primer CA al centroide del grupo). Cuanto más apretada la selección de residuos, más
inestable el eje. El heurístico es **menos fiable cuanto mejor** se elijan los residuos
del poro, que es exactamente al revés de lo que debería.

### PORO-04 · ALTA · [ESTÁTICO] · Se eliminó la validación de canal que existía

`1run_hole_old.sh:118-151` **validaba el resultado**: extraía el punto más estrecho,
calculaba su distancia al `pore_center` y avisaba explícitamente

```
❌ HOLE2 se desvió del poro seleccionado (distancia: ${DISTANCE}Å > 5Å)
💡 Sugerencia: Verifique los residuos seleccionados o el vector del canal
```

El `1run_hole.sh` **vigente** (líneas 49-66) solo comprueba `normal completion`. Esa
validación es precisamente la que habría detenido PORO-03: la distancia real entre la
constricción y el `pore_center` es **10.18 Å**, el doble del umbral de 5 Å que el script
viejo imponía.

Esto corrige una lectura cómoda: `1run_hole_old.sh` **no es simplemente código muerto**.
Es la versión que tenía la red de seguridad, y la «nueva» la perdió. Borrarlo sin portar
su validación consolidaría la regresión.

Hoy la única validación viva es la del Studio: `pore.py:144-145`, `len(rs) < 30 →
RuntimeError("HOLE no trazó un canal válido")`. Es un acierto, pero detecta canal
*degenerado*, no canal *equivocado*: un canal de 347 puntos a 11.76 Å del eje pasa el
test sin problema.

### PORO-05 · ALTA · [ESTÁTICO] · Poromania no fija `rseed`

El deck de `1run_hole.sh:37-47` no incluye `rseed`. El `hole_out.txt` commiteado lo
documenta:

```
Seed for random number generator:  0 (0 means value set by program)
Seed integer used by ran # generator on this run   2093611
```

Con 1000 pasos de Monte Carlo por plano, la corrida **no es reproducible**. El Studio sí
fija `rseed 1` (`pore.py:136`) — acierto. Medir la dispersión real entre corridas
**[REQUIERE CORRER]**; que el deck no la acote es **[ESTÁTICO]**.

### PORO-06 · ALTA · [ESTÁTICO] · Dos implementaciones divergentes del mismo cálculo

Tabla completa en §3.1. Divergen en `cpoint`, `cvect`, `sample`, `rseed`, origen del eje Z
y validación. `ESTADO.md:61-63` ya reconoce el problema («la misma ciencia existe en dos
sitios que pueden divergir»); esta auditoría lo **cuantifica**: 10.21 Å de centro, 19.29°
de eje, 0.24 Å de resultado documentado.

### PORO-07 · ALTA · [ESTÁTICO] · El eje del Studio no está condicionado para los trímeros

`_pore_axis` elige entre el eigenvector mayor y el menor según **qué par de valores
propios está más cerca**, pero **no comprueba que ese par sea realmente degenerado**.
Medido sobre los cuatro modelos que `hole_structures()` ofrece:

| Modelo | Separación relativa del par | Error del eje vs eje por centroides | Simetría real |
|---|---|---|---|
| `BMV/poro5fold` | **4.5 × 10⁻⁷** | **0.00°** | C5 exacta (0.000 Å) |
| `BMV/poro3fold` | **2.1 × 10⁻¹** | **6.14°** | C3 aproximada (2.01 Å) |
| `BMV/poronatural` | 2.1 × 10⁻¹ | 6.14° | C3 aproximada (2.01 Å) |
| `CCMV/poronatural` | 2.2 × 10⁻¹ | 6.01° | C3 aproximada (2.03 Å) |

Para el pentámero la degeneración es exacta y el método es impecable. Para los **tres
modelos triméricos** los dos valores propios del «plano» difieren un **21 %**: no hay
degeneración, la premisa del docstring (`pore.py:72-77`) no se cumple y la elección entre
prolato y oblato es efectivamente arbitraria. La causa raíz es que los trímeros **no son
C3**: las cadenas tienen distinto número de átomos (1133 / 1240 / 1240 en BMV;
1122 / 1226 / 1226 en CCMV) y una rotación de 120° deja 2.0 Å de desviación.

Un error de 6° sobre un canal de ~30 Å son ~3 Å de desvío lateral, comparable al propio
radio del canal (~2.5 Å). **El «3-fold ≈2.47 Å» que la documentación trata como valor de
referencia reproducible descansa sobre un eje con esa incertidumbre.** **[REQUIERE CORRER]**
para medir cuánto mueve el radio mínimo; la mala condición del heurístico es **[ESTÁTICO]**.

Nota justa: el signo del eigenvector es arbitrario, pero HOLE traza el canal en ambos
sentidos desde `cpoint`, así que el signo **no** es un problema.

### PORO-08 · ALTA · [ESTÁTICO] · El cribado del Studio falla sobre la estructura pentamérica

`_pore_residues` (`pore.py:206-225`) exige que un residuo aparezca en **todas las
cadenas**: `len(v["chains"]) >= len(chains)`, con `chains` de `_chain_ids` (`:179-186`).
En `poro5fold.pdb` las 5 subunidades están **todas etiquetadas cadena A** (distinguidas
solo por `segi`: `A_6`…`A_10`) más una cadena B de 60 átomos. Simulé la función:

| Modelo | Cadenas detectadas | resi totales | «comunes» | Top-3 (distancia al punto sonda) |
|---|---|---|---|---|
| `BMV/poro5fold` | A, B | 148 | **1** | TYR188 a **11.5 Å** |
| `BMV/poro3fold` | A, B, C | 164 | 149 | GLY147 (5.0 Å), THR145 (6.6 Å), GLU84 (6.9 Å) |
| `CCMV/poronatural` | A, B, C | 164 | 149 | GLN149 (6.7 Å), THR146 (7.2 Å), GLU148 (7.8 Å) |

**Precisión sobre el método:** en producción esta función recibe la constricción real de
HOLE (`pore.py:329`), que aquí no puedo calcular. Usé como punto sonda el **centroide** de
cada estructura, que para los modelos bien condicionados está sobre el eje y por tanto
dentro del canal. Las distancias de la última columna son por tanto **indicativas**, no las
que saldrían en producción. **Lo que no depende del punto sonda es la cuenta de residuos
«comunes»** —que solo depende de las etiquetas de cadena— y es ahí donde está el hallazgo.

Sobre el pentámero, el único residuo que pasa el filtro es el que casualmente existe en A
**y** en B. Encadenando (`pore.py:336-345`): `pos` tiene un solo elemento, las ramas
`len(pos) >= 2` y `>= 3` no se activan, y la librería queda en **un único mutante**
construido sobre el único residuo que sobrevive a un filtro que, en esta estructura, no
tiene nada que ver con revestir el poro. El cribado «automático» del Studio sobre
`poro5fold` no criba el poro. Para los trímeros, en cambio, el filtro hace lo que promete:
149 posiciones candidatas sobre 164.

Sobre los trímeros la función sí hace lo que promete. El fallo es específico de la
convención de etiquetado del pentámero. **[ESTÁTICO]**

Riesgo adicional: `_generate_mutants` (`:228-247`) itera `for ch in chains`, incluida la
cadena B de 60 átomos, y emite `w.do_select('/tag//B/188/')` para posiciones que allí
pueden no existir. **[REQUIERE CORRER]** para ver si PyMOL falla o lo ignora.

### PORO-09 · MEDIA · [ESTÁTICO] · `resi` + `chain` no identifica un residuo en el pentámero

Raíz común de PORO-01 y PORO-08. En `poro5fold.pdb` los números de residuo **se repiten**
en las 5 subunidades de la cadena A; lo único que las separa es `segi`. **Ninguna de las
dos implementaciones lee `segi`.** Consecuencias concretas:

- `pore_analyzer.py:426-428`: `cmd.iterate_state(1, "name CA and resi 129 and chain A", …)`
  devuelve **5 coordenadas** y el código toma `stored.temp_coords[0]`, **descartando
  silenciosamente 4 de 5**. Verifiqué que `center_avg` reproducido con esa regla da
  exactamente `9.18 −3.88 2.22` = el `pore_center.txt` commiteado. Es decir: el centro
  publicado es el centroide de 4 CA de **una sola subunidad arbitraria** (la primera en
  orden de fichero), no del poro.
- `1crear_mutantes.pml:126`: `w.do_select('/tag//A/129/')` sobre una selección que
  encierra 5 residuos. Candidato principal a explicar PORO-01.
- `_pore_residues` fusiona las 5 copias bajo un solo número de residuo (PORO-08).

### PORO-10 · MEDIA · [ESTÁTICO] · El filtro `radio > 0.5` sesga el mínimo hacia arriba

`2out_tsv.py:22` y `pore.py:111` descartan todo punto con radio ≤ 0.5 Å. El filtro es
**funcionalmente necesario** tal como está escrito el parseo —es lo que excluye el
preámbulo de texto de HOLE, porque ambos parsers intentan `float()` sobre cualquier línea—
pero tiene un coste científico directo: **un poro ocluido se reporta más ancho de lo que
es**, o desaparece. Si una mutación cierra el canal a 0.3 Å, esos puntos se borran y el
«mínimo» pasa a ser el primer punto superviviente (> 0.5 Å).

Esto es justo lo contrario de lo que el cribado necesita: el pipeline busca mutantes que
**abran** el poro comparando contra mutantes que lo **cierran**, y el cierre es
precisamente el régimen que el filtro no puede representar. En `hole_spheres.pdb`, **93 de
268** registros tienen radio ≤ 0.5 Å.

El mismo defecto afecta a `_constriction_point` (`pore.py:201`, `r > 0.5`), que es lo que
**centra la caja de docking**: en un mutante ocluido la caja se centraría en otro sitio.

### PORO-11 · MEDIA · [ESTÁTICO] · El mínimo se toma global, sin validar que sea el canal

`3analizar_hole.py:31-32` toma `df["Radio"].min()` sobre todo el perfil. Sin la validación
de PORO-04, nada garantiza que ese mínimo pertenezca al canal pretendido. En la corrida
commiteada el mínimo está a 10.18 Å del centro declarado. El Studio hace lo mismo
(`pore.py:146`) pero al menos su `cpoint` está sobre el eje.

El umbral de «zona estrecha» también está descoordinado dentro del propio script: la
métrica usa `< 2.0 Å` (línea 33) mientras el gráfico dibuja la línea de referencia y las
cruces en `1.4 Å` (líneas 49-54). Dos umbrales sin justificación declarada en la misma
figura.

### PORO-12 · BAJA · [ESTÁTICO] · La extracción del radio mínimo en shell devuelve vacío

`1run_hole.sh:55`:

```bash
MIN_RAD=$(grep -i "minimum radius" "$RAWOUT" | head -1 | awk '{print $NF}' | sed 's/angstroms\.//')
```

La línea de HOLE es ` Minimum radius found:      1.915 angstroms.`, de modo que `$NF` es
`angstroms.` y el `sed` lo borra **entero**. Ejecutado sobre el fichero commiteado:

```
MIN_RAD extraido = []     ->  el echo del radio NUNCA se imprime
```

El radio correcto sería `$(NF-1)`. Es cosmético (el número real está en el TSV), pero el
pipeline **nunca** mostró el radio que decía mostrar.

### PORO-13 · BAJA · [ESTÁTICO] · Tarjetas rechazadas por HOLE sin que nada lo detecte

El deck de Poromania termina en `gmacro` y `quit`, y HOLE responde:

```
***Unrecognized line read: gmacro
***Unrecognized line read: quit
```

Inocuo (HOLE calcula `Gmacro` de todos modos), pero revela que **nadie revisó la salida**:
el script no busca `Unrecognized` y habría ignorado igual una tarjeta científica mal
escrita, p. ej. un `rseed` mal tecleado.

### PORO-14 · MEDIA · [ESTÁTICO] · Docking: idock sin semilla y no comparable con Vina

**Poromania** (`5docking.sh:56-72`) escribe `idock.conf` con `receptor`, `input_folder`,
`output_folder`, centro, tamaño, `threads` y `max_conformations = 500`, y **no fija
semilla**: el docking no es reproducible. Además `max_conformations` acota el número de
poses de salida, **no** el esfuerzo de búsqueda, así que no hay ningún parámetro que
controle la exhaustividad.

`threads = $(nproc)` hace que el resultado dependa del **número de núcleos de la máquina**.
Para un docking estocástico sin semilla, eso convierte el hardware en una variable
científica no registrada.

**Studio** (`pore.py:439-479`) usa **Vina** con `--exhaustiveness 8` y `--seed 1`:
reproducible. Pero **idock y Vina son funciones de scoring distintas**: las afinidades de
los dos caminos **no son comparables entre sí**, y la documentación no distingue cuál
produjo qué. `ESTADO.md:19` y `SESION_STUDIO.md:50-53` presentan el docking como una sola
capacidad «real de punta a punta».

Tamaño de caja, también divergente: Poromania `L = 2·(r_min + 6)` con piso de 24 Å
(`5docking.sh:46-47`); Studio `size = max(24, round(2·(pore_min + 6)))` (`pore.py:538`).
Coinciden en la fórmula pero el Studio **redondea a entero**. Para `r_min = 1.92` ambos
caen en el piso de 24 Å; divergen solo por encima de 6 Å de radio.

Sobre la correlación radio–afinidad (`dock_correlate`, `pore.py:493-560`): `_pearson`
devuelve `None` con menos de 3 puntos y se calcula sobre **WT + hasta 4 mutantes**, es
decir **n ≤ 5**. `SESION_STUDIO.md:53` reporta «abrir el poro debilita la unión (r≈0.9)».
Un Pearson de 0.9 con n=5 tiene p ≈ 0.04 y un intervalo de confianza que llega a rozar el
cero: **no sostiene una afirmación mecanística**. Y si el cribado corrió sobre
`poro5fold`, los «mutantes» del eje X son los de PORO-08. **[ESTÁTICO]** el tamaño de
muestra; **[REQUIERE CORRER]** reproducir el 0.9.

Lo que sí está corregido: `found_any` en `5docking.sh:123` se pone a 1 dentro del bucle
(VLP-02). Verificado — ese bug ya no está.

### PORO-15 · MEDIA · [ESTÁTICO] · Valores ilustrativos presentados contra radios reales

`pore.py:22-32` declara en comentario que `_SUBSTRATES` y `_AXIS_MIN` son **ilustrativos**
(«Valores de literatura del diseño — ILUSTRATIVOS hasta portar el cálculo real»), y
`pore_profile` (`:615-649`) devuelve una **gaussiana sintética** con `illustrative: True`.

El problema es la presentación. El commit `40f4b03` («quitar el badge '(ilustrativo)' del
título del perfil de poro») vació el badge en `studio.html` y en `pac-pore.js:71`, de modo
que el panel **«Perfil del poro · HOLE»** ya no marca que la curva mostrada por defecto es
sintética. La línea de estado sí lo sigue diciendo («Perfil ilustrativo — usa "Correr
HOLE" para datos reales», `pac-pore.js:76`), así que la información no desapareció del
todo, pero el rótulo que la llevaba junto al título sí.

Y el veredicto PASA/OCLUIDO (`pac-pore.js:238`) compara `d.pore_min` —que puede venir de
la gaussiana— contra un radio de sustrato **ilustrativo** (`_SUBSTRATES`), salvo que el
usuario introduzca un SMILES. Dos valores no medidos produciendo un dictamen binario con
aspecto de resultado.

Ya señalado en §4: `_AXIS_MIN` además **invierte el orden** 3-fold/5-fold respecto a la
medición real del propio motor.

### PORO-16 · BAJA · [ESTÁTICO] · Errores silenciados en las rutas del Studio

- `screen_mutants` (`pore.py:371-372`) y `dock_correlate` (`:550-551`): `except Exception:
  continue`. Un fallo de HOLE, de obabel o de Vina **desaparece de la tabla sin dejar
  rastro**, y el usuario ve un cribado «completo» con menos filas.
- `_generate_mutants` (`:247`): `subprocess.run(["pymol", …])` sin `check=True` y sin mirar
  `returncode`, `stdout` ni `stderr`. Si PyMOL falla, el único síntoma es que el PDB no
  existe y `screen_mutants` hace `continue` (`:357`). **Esta es exactamente la forma de
  fallo de PORO-01**: la mutagénesis no se aplica y el pipeline continúa.
- `evaluate_mutant` (`:302-307`) calcula `delta` contra un `hole_out.txt` **cacheado** en
  `Output/hole_runs/`, que pudo generarse con otra versión del código o otros parámetros.
  Si no existe, `delta` es `None` silenciosamente. Sin sello de procedencia no hay forma de
  saber si el delta compara peras con peras.

### PORO-17 · BAJA · [ESTÁTICO] · Duplicación y código muerto

- `calculate_pentamer_center` definida **dos veces** y nunca llamada
  (`pore_analyzer.py:444-483`, propagado a `1crear_mutantes.pml:49-88`).
- `pore_analyzer_backup.py` (482 líneas, versión divergente: usa posiciones comunes en vez
  de selección manual, y su `generate_pymol_script` **no escribe** `pore_center.txt` ni
  `pore_vector.txt`). No se invoca, pero es una tercera definición del flujo.
- `test_fixed.pml`, `test_new_coords.pml`: prototipos sin referencias.
- El motor de HOLE se copia por mutante (`3copiar_scripts.sh`); hoy idéntico al base,
  mañana no necesariamente.
- `ligand.pdbqt` y `glucosilceramida.pdbqt` son el **mismo fichero** (md5 `d5f9c3d0…`).
- `CLAUDE.md` de Poromania documenta `cpoint (219.21, 171.38, 312.96)` como parámetro fijo
  «optimizado»; el valor real del artefacto commiteado es `9.18 −3.88 2.22`. También cita
  `automated_test.py` y `clickaqui.sh`, que **no existen** en el repositorio.

### PORO-18 · informativo · [ESTÁTICO] · La cuantización a 2 decimales es inocua

`pore_center.txt` y `pore_vector.txt` se escriben con `%.2f`
(`1crear_mutantes.pml:146,151`), frente a `%.3f`/`%.4f` del Studio. Medí el efecto: el
`cvect` commiteado tiene norma **1.0029** (no unitario) y está a **0.11°** del valor sin
cuantizar; el `cpoint` pierde ≤ 0.005 Å por eje. **Despreciable** frente a los 19.29° y
7.59 Å de PORO-03. Lo registro para que no se confunda con una causa.

---

## 7. Lo que está bien

No todo divergente es un defecto, y conviene fijar lo que no hay que tocar:

- **`_pore_axis` del Studio es el método correcto** y sobre el pentámero es exacto
  (0.00°). La idea —eigenvector del valor propio **no** degenerado, no el de mayor
  varianza— es la adecuada para simetría Cn, y el comentario de `pore.py:75-77` explica
  bien por qué el eje de máxima varianza cae en el plano. Le falta la guarda de
  degeneración (PORO-07), no el razonamiento.
- **`rseed 1`** en el Studio (`pore.py:136`).
- **Validación de canal degenerado** (`pore.py:144-145`, `len(rs) < 30`).
- **`vdwradii.lib` compartido** (`pore.py:123`): los radios de van der Waals no divergen.
- **Los dos parsers de perfil coinciden** y extraen correctamente el mínimo que HOLE
  imprime (verificado: 1.915 Å en z = −15.382, bloque de líneas 1992-2338).
- **Los dos extractores de constricción coinciden** sobre el fichero commiteado
  (`r = 1.920` en `15.033 −12.215 2.264`), aunque el de Poromania sea frágil.
- **`substrate_section`** (`pore.py:571-612`) es la pieza más sólida del módulo: ETKDGv3
  con `randomSeed = 42`, fallback con semilla fija, PCA por SVD y menor semieje. Tiene
  **test golden con tolerancia** (`tests/test_golden_science.py`) y un test explícito de
  determinismo. Es el patrón que el resto del motor debería imitar.
- **VLP-02 está realmente corregido**: `found_any = 1` dentro del bucle
  (`5docking.sh:123`).
- **El `.pdb` de esferas se sirve al visor 3D por B-factor** (`pac-pore.js:27`), que es la
  forma honesta de mostrar el canal: se ve *dónde* está, no solo su número.

---

## 8. Mutagénesis — análisis específico

**Flujo:** `pore_analyzer.py` (interactivo) → genera `1crear_mutantes.pml` → PyMOL aplica
el wizard de mutagénesis a todas las cadenas → guarda `mutants/mut_*/receptor.pdb` +
`pore_center.txt` + `pore_vector.txt` + `selected_positions.txt`.

**Lo que funciona por diseño:** mutar la posición equivalente en **todas** las cadenas
(`1crear_mutantes.pml:117-129`) es la decisión correcta para un poro simétrico; romper la
simetría cambiaría el canal por una razón distinta de la que se quiere estudiar. Y recalcular
el centro **después** de mutar (`:133-137`) es acertado: la mutación mueve los CA.

**Lo que está roto:**

1. **La mutación no se aplicó** (PORO-01): el producto es el WT.
2. **`resi` + `chain` no identifica un residuo** (PORO-09): `w.do_select('/tag//A/129/')`
   abarca 5 residuos en `poro5fold`. Causa raíz más probable de (1). **[REQUIERE CORRER]**
   para confirmar el comportamiento exacto del wizard.
3. **No hay verificación posterior.** Nada comprueba que el residuo mutado tenga la
   identidad pedida. Un `assert` de tres líneas sobre el PDB de salida habría detenido
   PORO-01 en el acto. El Studio tiene el mismo hueco (`pore.py:228-247`).
4. **La semilla de aleatoriedad protege lo que no importa.** `random.seed(42)`
   (`pore_analyzer.py:354`) hace reproducible la *elección* de mutaciones, pero no se
   registra qué posiciones estaban disponibles cuando se eligieron —y eso depende del radio
   de sonda que el usuario teclee interactivamente—. La semilla da una falsa sensación de
   reproducibilidad sobre un flujo cuyo input real **no se registra en ninguna parte**.
5. **`DEL` (deleción) está en la lista de aminoácidos** (`pore_analyzer.py:288-289`) y se
   implementa con `cmd.remove` (`:514-516`). Borrar un residuo de una cadena deja una
   **ruptura de backbone** sin cerrar ni minimizar: la estructura resultante no es
   físicamente válida para medir un canal. El Studio no ofrece `DEL` (`_AA3`,
   `pore.py:250-271`) — acierto suyo.
6. **Ni un `cmd.sort`/minimización tras `cmd.rebuild()`.** El wizard de PyMOL coloca el
   rotámero más probable sin relajar el entorno. Para una cadena lateral grande (TRP) en un
   canal estrecho, el radio medido depende del rotámero elegido. Es una decisión
   defendible —y rápida— pero debe **declararse**: el «TRP cierra el poro −1.97 Å» de
   `SESION_STUDIO.md:48` es un efecto de rotámero no relajado, no una predicción de
   estructura. **[REQUIERE CORRER]** para cuantificar la sensibilidad al rotámero.

**El flujo es interactivo y eso es, en sí, el problema de reproducibilidad de fondo.**
`pore_analyzer.py:598-672` pide por `input()` el radio de sonda, las posiciones y las
mutaciones. El `.pml` generado es el único registro de lo decidido, y no guarda el radio
de sonda usado. No hay forma de reconstruir por qué se eligieron 129-132.

---

## 9. Uso de HOLE2 — resumen del bloque pedido

| Aspecto | Poromania | Studio | Veredicto |
|---|---|---|---|
| **Centro del canal** | media de CA de residuos seleccionados, de **una** subunidad; 7.59 Å fuera del eje | centroide de todos los átomos; **0.000 Å**, sobre el eje | Studio correcto |
| **Eje del canal** | cuerda primer-CA → centroide, base 4.40 Å; **19.29°** de error | eigenvector del valor propio no degenerado; **0.00°** en C5, **6.14°** en C3 | Studio correcto, con reserva en C3 |
| **Semilla** | ninguna (HOLE usó 2093611 por reloj) | `rseed 1` | Studio correcto |
| **Validación de canal** | ninguna (existía en `1run_hole_old.sh` y **se borró**) | `len(rs) < 30`; no detecta canal *equivocado* | ambas insuficientes |
| **Muestreo** | `sample 0.2` | `sample 0.25` | divergente, sin justificar |
| **Radios vdW** | `scripts/vdwradii.lib` | el mismo fichero | consistente |
| **`endrad`** | 10.0 | 10.0 | consistente |

Sobre `endrad 10.0`: significa que HOLE considera «fin del canal» un radio de 10 Å. En el
perfil commiteado el radio **arranca ya en 9.88 Å** y termina en 10.00 Å, es decir el
canal útil está acotado por ese umbral en ambos extremos. Para un poro de cápside de
~2 Å de constricción, 10 Å es generoso y hace que el perfil incluya la boca y parte del
exterior. Es defendible, pero **el valor no está justificado en ningún sitio** y es el que
fija la longitud del perfil que se grafica. **[ESTÁTICO]**

Sobre `sample`: ni 0.2 ni 0.25 Å están justificados. Como el mínimo se toma punto a punto
sobre esa rejilla, el paso **acota la precisión del número reportado**. Declarar el paso
junto al radio («1.92 ± paso/2») sería más honesto que tres decimales.

---

## 10. Cross-check contra la pasada previa sellada

Leí `REVISION_MOTORES_hallazgos_sellados.md` **después** de cerrar §1-§9, como pide el
briefing. Comparación punto por punto de la sección Poromania:

| Sospecha previa | Mi resultado |
|---|---|
| «`1run_hole.sh` no tiene `rseed`» | **Confirmado** y ampliado: el `hole_out.txt` commiteado documenta la semilla por reloj (2093611). PORO-05. |
| «el eje = centroide − primer residuo; ¿cae fuera del canal?» | **Confirmado y cuantificado.** No es solo que *pueda* caer fuera: **cae**. 19.29° de error de eje, 7.59 Å de centro fuera del eje, constricción a 11.76 Å. La sospecha era correcta y **subestimaba** el problema. PORO-03. |
| «`3analizar_hole.py` toma el mínimo global sin validar canal degenerado» | **Confirmado**, con un matiz importante: el problema no es solo el canal *degenerado* sino el canal *equivocado*, y el filtro `radio > 0.5` añade un sesgo que la sospecha no menciona. PORO-10, PORO-11. |
| «`calculate_pentamer_center` definida dos veces y no se usa» | **Confirmado** (`pore_analyzer.py:444-483`). PORO-17. |
| «`5docking.sh`: `found_any` ya parece arreglado» | **Confirmado**: línea 123, correcto. |
| «el Studio es una versión más nueva; compara ambas y verifica cuál generó los resultados» | **Hecho** (§3, §4). Respuesta: los generó **Poromania**, con la geometría equivocada, sobre una estructura **no mutada** que además **no es** la que los scripts commiteados cargan. |

### Dónde mi juicio difiere de la pasada previa

1. **Lo más grave no estaba en la lista.** Ninguna sospecha previa menciona que
   `mut_129HIS_132GLY/receptor.pdb` sea **byte-idéntico al WT** (PORO-01) ni que el
   artefacto **no se regenere** desde los inputs commiteados (PORO-02). Son los dos
   hallazgos críticos de esta auditoría y ambos se ven con un `cmp` y un conteo de átomos.
   La lista previa auditó *scripts*; el fallo estaba en los *artefactos*.

2. **`1run_hole_old.sh` no es «código muerto».** La pasada previa lo agrupa con los
   fósiles a limpiar (vía `ESTADO.md:86-87`). Es la versión que **tenía la validación de
   canal** —la única que habría detectado PORO-03— y la vigente la perdió. Clasificarlo
   como basura a borrar consolidaría una regresión. PORO-04.

3. **El Studio no es simplemente «la versión más nueva».** La pasada previa lo trata como
   contexto. Mi evidencia dice que es **científicamente la correcta** en centro y eje
   (0.00° contra 19.29°) y que debe ser la única que sobreviva. El juicio no es simétrico
   entre las dos implementaciones.

4. **El Studio tiene dos defectos propios graves que la lista previa no recoge**, por
   haberlo tratado solo como contexto: su heurístico de eje está **mal condicionado para
   los tres modelos triméricos** (PORO-07, 6.14° de error, degeneración de 21 %) —justo
   los que dan el «2.47 Å» de referencia— y su cribado automático **falla sobre el
   pentámero** (PORO-08, 1 residuo a 11.5 Å de la constricción). Promover el Studio sin
   arreglar estos dos no resuelve el problema.

5. **La cadena de procedencia del «1.9 Å» tiene un error extra.** El número se midió sobre
   una estructura **pentamérica** y quedó guardado en `_AXIS_MIN` como mínimo del eje
   **3-fold**, con el orden 3-fold/5-fold **invertido** respecto a la medición real del
   propio Studio. §4.

6. **Una sospecha previa queda matizada a la baja, en justicia.** El awk de
   `5docking.sh:45` es frágil (93 de 268 líneas rompen el troceado por campos) pero sobre
   el fichero commiteado **da el mismo resultado** que el parseo por columnas fijas del
   Studio. No es hoy una fuente de divergencia numérica. PORO-14.

En lo que ambas pasadas coinciden, coincidimos por evidencia independiente, no por
lectura. En lo que difieren, mi evidencia está en los comandos citados y es verificable
sin instalar nada.

---

## 11. Plan de reparación

Orden por dependencia, no por severidad: **R1 y R2 son prerrequisitos de todo lo demás**,
porque sin ellos no se sabe qué se está arreglando.

### Fase 0 — Congelar lo que no se puede defender (antes de tocar código)

| # | Acción | Cierra | Esfuerzo |
|---|---|---|---|
| **R1** | **Retirar de circulación el 1.92 Å y todo lo derivado.** Marcar `mutants/mut_129HIS_132GLY/` como **no válido** con un `INVALIDO.md` en la carpeta que explique PORO-01/02/03. No borrarlo: es la evidencia. Corregir `PLAN_POROMANIA.md:40-42`, `ESTADO.md:19,57`, `SESION_STUDIO.md:36-53` y `BITACORA.md:77` para que ninguna diga «real de punta a punta» mientras no haya un perfil validado. | PORO-01, PORO-02 | horas |
| **R2** | **Un sello de procedencia por corrida**, junto a cada salida: ruta y **md5 del PDB de entrada**, `cpoint`, `cvect`, `sample`, `rseed`, versión de HOLE, commit del código, fecha. Sin esto cualquier reparación es infalsificable. Ya está priorizado como acción 2 en `INVESTIGACION_REPRODUCIBILIDAD_2026-09-17.md:140-141`. | PORO-02, PORO-16 | 1 día |

### Fase 1 — Una sola definición del canal

| # | Acción | Cierra | Esfuerzo |
|---|---|---|---|
| **R3** | **Declarar `pore.py` la única implementación** del eje y el centro. `1run_hole.sh` pasa a leer `pore_center.txt`/`pore_vector.txt` **generados por `pore.py`**, no por `pore_analyzer.py`. Retirar `calculate_pore_vector` y `calculate_pore_center_for_structure` del generador del `.pml`. Una sola fuente, un solo sitio donde corregir. | PORO-03, PORO-06 | 2-3 días |
| **R4** | **Guarda de degeneración en `_pore_axis`.** Si `min(\|w1−w0\|, \|w2−w1\|) / max(w)` supera un umbral (el pentámero da 4.5e-07, los trímeros 2.1e-01: un umbral de 1e-3 los separa con holgura), **no adivinar**: devolver error y exigir el eje explícito. Para los trímeros, el eje por **centroides de subunidad** —el que usé como verdad independiente en §3.3— es más robusto porque no depende de la composición atómica de cada cadena. Corregir también «tensor de inercia» → «tensor de segundo momento» en el docstring. | PORO-07 | 1-2 días |
| **R5** | **Identificar residuos por `segi`, no por `chain`.** Leer la columna 73-76 del PDB en `_chain_ids`/`_pore_residues` (`pore.py:179-225`) y usar la **subunidad** como unidad de simetría. Esto arregla el cribado del pentámero y la selección de CA. Mientras no esté, **documentar que `poro5fold` no es apto para el cribado automático**. | PORO-08, PORO-09 | 2-3 días |
| **R6** | **Restaurar la validación de canal** que `1run_hole_old.sh:118-151` tenía, en `_hole_on`: distancia entre la constricción y el eje declarado. Con el eje correcto el umbral puede ser estricto (~2-3 Å, del orden del radio). Que **falle**, no que avise: un canal a 11.76 Å del eje debe ser un error, no una nota en un log. Mantener además el `len(rs) < 30`. **Antes de borrar `1run_hole_old.sh`, portar esta lógica.** | PORO-04, PORO-11 | 1-2 días |
| **R7** | **Separar el parseo del filtro científico.** Delimitar la tabla de HOLE por su cabecera (`cenxyz.cvec`) en vez de por `try: float()` sobre todas las líneas; entonces el `radio > 0.5` deja de ser necesario para parsear y puede **eliminarse**, de modo que un poro ocluido se reporte como ocluido. Aplicar lo mismo a `_constriction_point`. Detectar `***Unrecognized line read` y fallar. | PORO-10, PORO-13 | 1-2 días |

### Fase 2 — Que la mutagénesis haga lo que dice

| # | Acción | Cierra | Esfuerzo |
|---|---|---|---|
| **R8** | **Verificar toda mutación tras aplicarla.** Releer el PDB de salida y comprobar que la posición tiene la identidad pedida **en todas las subunidades**; si no, fallar con el detalle. Tres líneas que habrían evitado PORO-01 entero. Aplicar en `_generate_mutants` (`pore.py:228-247`) y en el `.pml`. | PORO-01, PORO-09 | 1 día |
| **R9** | **`check=True` y propagación de errores.** Quitar los `except Exception: continue` de `screen_mutants` (`:371`) y `dock_correlate` (`:550`): registrar el fallo y **mostrarlo en la tabla** como fila fallida. Inspeccionar el `returncode` de PyMOL. Un cribado con huecos silenciosos es peor que uno que falla. | PORO-16 | 1 día |
| **R10** | **Declarar o eliminar `DEL`.** Si se mantiene (`pore_analyzer.py:288`), cerrar y minimizar el backbone tras `cmd.remove`; si no, retirarlo de la lista. Documentar también que el wizard **no relaja el entorno**, y que por tanto un Δradio por mutación es un efecto de rotámero. | PORO-09 (5,6) | 1 día |

### Fase 3 — Docking honesto

| # | Acción | Cierra | Esfuerzo |
|---|---|---|---|
| **R11** | **Elegir un motor de docking, uno solo.** Si es Vina, retirar `5docking.sh` del camino vivo; si es idock, fijar su semilla y portar el flujo del Studio. Mientras coexistan, **no mezclar afinidades en una misma figura**: scoring distinto, números incomparables. Fijar `threads` a un valor constante para que el hardware no sea una variable. | PORO-14 | 2-3 días |
| **R12** | **Retirar la correlación radio–afinidad hasta tener n suficiente**, o publicarla con su n y su intervalo de confianza. Con n ≤ 5, `r ≈ 0.9` no sostiene «abrir el poro debilita la unión». Reemplazar el `_pearson` opaco por un retorno `{r, n, p}`. | PORO-14 | 1 día |

### Fase 4 — Que no vuelva a pasar

| # | Acción | Cierra | Esfuerzo |
|---|---|---|---|
| **R13** | **Golden file para un perfil de poro**, con `numpy.allclose` y tolerancia declarada, sobre la estructura **mejor condicionada** —`BMV/poro5fold`, cuya simetría C5 es exacta y cuyo eje se recupera con 0.00°—, **no** sobre un trímero. Replicar el patrón de `tests/test_golden_science.py`, que ya es correcto. Añadir asserts de sanidad: radio > 0, ≥ 30 puntos, constricción dentro del umbral del eje. Es la acción 4 de `INVESTIGACION_REPRODUCIBILIDAD_2026-09-17.md:144`. | PORO-05, PORO-06 | 2 días |
| **R14** | **Test de simetría como guardia de entrada.** Antes de correr HOLE, comprobar que la estructura tiene la simetría que se le atribuye (rotación de 360/n grados sobre el eje candidato, desviación máxima de centroides de subunidad). Los trímeros dan 2.0 Å: eso debe aparecer en el informe de la corrida, no descubrirse en una auditoría. | PORO-07 | 1 día |
| **R15** | **Restaurar la divulgación de lo ilustrativo.** Reponer el badge que `40f4b03` vació, o —mejor— **no mostrar la gaussiana por defecto**: panel vacío con «Corre HOLE para ver el perfil». Y no emitir veredicto PASA/OCLUIDO cuando **ambos** lados de la comparación son ilustrativos. Sustituir `_AXIS_MIN` por los valores medidos, con el orden 3-fold/5-fold corregido, o eliminarlo. | PORO-15 | 1 día |
| **R16** | **Limpieza, al final y con cuidado.** Retirar `pore_analyzer_backup.py`, `test_*.pml`, la `calculate_pentamer_center` duplicada, el `glucosilceramida.pdbqt` redundante y las copias por mutante de `scripts/`. **`1run_hole_old.sh` solo después de R6.** Corregir `CLAUDE.md` de Poromania (el `cpoint` «fijo» que documenta no corresponde a ninguna corrida real; cita ficheros inexistentes). Es VLP-05, con la advertencia de §10 punto 2. | PORO-17 | 1-2 días |
| **R17** | **Arreglar la extracción del radio en shell** (`1run_hole.sh:55`): `$(NF-1)` en vez de `$NF`. Trivial, pero hoy el pipeline nunca imprime el radio que dice imprimir. | PORO-12 | minutos |

### Lo que hace falta y no está en el repositorio

Para cerrar lo etiquetado **[REQUIERE CORRER]** se necesita, y conviene pedírselo a Lucio:

- **Un entorno con HOLE, PyMOL, Vina e idock** instalados y con versión registrada. El
  `hole_out.txt` commiteado declara `HOLE release 2.2.005 (07 August 2016)`: ese es el
  único número de versión de motor que existe hoy en el repositorio.
- **Dispersión real de HOLE sin `rseed`**: N corridas sobre la misma entrada → cuánto se
  mueve el radio mínimo. Decide si PORO-05 es un detalle o un problema de primer orden.
- **El radio de sonda y las posiciones** usados en la sesión interactiva que produjo
  `1crear_mutantes.pml` (hoy irrecuperables: el flujo no los registra).
- **Confirmación de qué estructura se quería analizar**: ¿el poro 3-fold o el 5-fold de
  BMV? La carpeta dice una cosa, los scripts otra, y `_AXIS_MIN` una tercera.
- **Si existen `Output/hole_runs/` o `Output/cribado/`** en la workstation: son los
  artefactos que respaldarían el 2.47 Å y el 1.68 Å. Hoy no hay ninguno en el repositorio.
- **Si el 1.92 Å llegó a la tesis o a alguna figura publicada.** De ser así, R1 deja de
  ser una tarea de documentación y pasa a ser una corrección que hay que emitir.

---

## Apéndice · Cómo reproducir las comprobaciones de esta auditoría

Todo lo siguiente corre **sin HOLE, PyMOL, Vina ni idock**. Solo Python con numpy.

```bash
cd Poromania.v.1.2.

# PORO-01 — el mutante es el WT
cmp mutants/WT.pdb mutants/mut_129HIS_132GLY/receptor.pdb && echo "BYTE-IDENTICAL"
md5sum mutants/WT.pdb mutants/mut_129HIS_132GLY/receptor.pdb

# PORO-02 — el input commiteado no es el que se usó
python3 -c "
import numpy as np
f=lambda p: np.array([[float(l[30:38]),float(l[38:46]),float(l[46:54])]
    for l in open(p,errors='ignore') if l.startswith(('ATOM','HETATM'))])
a,b=f('mutants/WT.pdb'),f('modelos/BMV/poro5fold.pdb')
print('WT vs poro5fold centrados, max|diff| =', abs((a-a.mean(0))-(b-b.mean(0))).max())
print('atomos poronatural.pdb (raiz) =', len(f('poronatural.pdb')))"

# PORO-03 / PORO-07 — eje verdadero por simetria vs los dos heuristicos
#   (script completo en el cuerpo del informe, §3.3 y §6 PORO-07)

# PORO-12 — la extraccion del radio devuelve vacio
R=mutants/mut_129HIS_132GLY/hole/resultados/hole_out.txt
echo "[$(grep -i 'minimum radius' $R | head -1 | awk '{print $NF}' | sed 's/angstroms\.//')]"

# PORO-05 / PORO-13 — semilla por reloj y tarjetas rechazadas
grep -n -E "Seed|Unrecognized|Minimum radius" $R

# PORO-14 — los dos extractores de constriccion coinciden
awk '($1=="ATOM"||$1=="HETATM"){r=$10+0; if(r>0 && (min==""||r<min)){min=r;x=$7;y=$8;z=$9}}
     END{printf "%.3f %.3f %.3f  r=%.3f\n",x,y,z,min}' \
    mutants/mut_129HIS_132GLY/hole/resultados/hole_spheres.pdb
```

---

*Fin de la auditoría. Las conclusiones **[ESTÁTICO]** se sostienen sobre los comandos
citados y son verificables sin instalar ningún motor. Las **[REQUIERE CORRER]** quedan
explícitamente abiertas: ninguna conclusión crítica de §1 depende de ellas.*
