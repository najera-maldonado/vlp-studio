> **Nota de la fusión (2026-10-05):** este informe nació en la rama
> `claude/audit-packing-engine-vdvq69` con el nombre `AUDITORIA_PACKING.md`, el mismo que
> la auditoría paralela de `claude/audit-packing-engine-wwph45`. Al fusionar ambas en `main`
> se conservaron las dos: la de wwph45 (que ejecutó el motor con un doble de PACKMOL) quedó
> como `AUDITORIA_PACKING.md` ("PK-A" en `HALLAZGOS_VERIFICADOS.md`) y esta como
> `AUDITORIA_PACKING_B.md` ("PK-B"). Las contradicciones entre ambas están resueltas en
> `HOJA_DE_RUTA.md` §2 (C5, C6). No se cambió nada más del contenido.

# Auditoría científica independiente — motor de packing (Studio, `nanocapsule-mvp`)

> Encargo: `REVISION_MOTORES.md`. Auditoría **desde cero**, con juicio formado **antes** de
> leer `REVISION_MOTORES_hallazgos_sellados.md` y `AUDITORIA_MD.md` (el cross-check está
> al final, §9). Fecha: 2026-10-04. Rama: `claude/audit-packing-engine-vdvq69`.
>
> **Límite del entorno:** no hay PACKMOL, PyMOL, RDKit ni pytest en este contenedor. Todo
> lo que sigue es inspección estática **más** los chequeos que sí se pudieron ejecutar aquí
> con Python puro (réplica NumPy del algoritmo de radio sobre los PDB commiteados, regex
> del packer contra logs reales de PACKMOL, `_consolidate_results` con datos sintéticos) y
> lectura del código fuente de PACKMOL (repositorio `m3g/packmol`, rama master). Cada
> hallazgo lleva etiqueta: `[ESTÁTICO]` = concluible leyendo archivos; `[REQUIERE CORRER]`
> = necesita PACKMOL/PyMOL instalados.
>
> Contexto crítico recibido: la auditoría paralela del motor de MD (PackMan) concluyó que
> **no es confiable**. El packing es, por tanto, el único pilar que sostiene el envío a
> JOSS, y se audita con esa exigencia.

---

## 0. Veredicto en una página

**El packing es más sólido que la MD, pero NO es hoy el "pilar firme, determinista y con
golden test" que describe `BITACORA.md:24-25`.** Esa frase contiene tres afirmaciones y
dos son falsas:

| Afirmación | Realidad | Evidencia |
|---|---|---|
| "geométrico" | Cierto: el modelo es puramente estérico (cápside rígida fija + N enzimas rígidas, sin H, dentro de una esfera). | `parallel_packer.py:259-274` |
| "determinista" | **Falso.** Las semillas de PACKMOL son `random.randint` en cada corrida; la configuración que promete semilla fija (`seed_base: 1234567`, `use_random_seeds: false`) **no se lee en ningún sitio**. | `parallel_packer.py:115-118`, `experiment_runner.py:160-170`, `config/default.yaml:35-40` |
| "con golden test" | **Falso.** `tests/test_golden_science.py` congela el radio de sección de sustratos por SMILES (puerta del poro). **No existe ni un solo test del motor de packing**: ni del `.inp` que se genera, ni del parseo del log, ni del radio, ni de la consolidación. | `test_golden_science.py:1-27`, `test_smoke.py:1-7,128-136` |

Los cinco hallazgos que importan, en orden de gravedad:

1. **[CRÍTICO] El criterio de convergencia documentado no existe en la práctica.** El regex
   que busca `Maximum distance violation:` nunca casa con la salida real de PACKMOL (que
   escribe `Maximum violation of target distance:`). Verificado aquí contra dos logs reales
   de PACKMOL 20.14.3 commiteados en el repo: devuelve `None` en ambos. Como consecuencia,
   **toda** corrida cae al "fallback" de contar líneas `ATOM/HETATM ≥ 10000`, que la cápside
   sola (168 480 – 216 780 átomos) satisface siempre. El umbral `max_violation_threshold`
   (0.10 Å) es decorativo. El único criterio real es: *PACKMOL devolvió exit 0 y el fichero
   de salida existe*. Si la versión de PACKMOL instalada devuelve exit 0 cuando **no**
   converge (las versiones anteriores a la introducción de `exit_codes.f90` lo hacen), una
   estructura **con solapamientos** sería aceptada como "cabe", porque PACKMOL escribe puntos
   intermedios al fichero de salida regular durante la optimización ("Current solution
   written to file"). → §3.2.
2. **[CRÍTICO] Modo degradado silencioso que empaqueta fuera de la cápside.** Si el módulo
   Python `pymol` no importa en el proceso de Flask (y `ESTADO.md:109-110` dice que "el radio
   casi siempre es el fallback 90 Å", lo que indica que ese es el caso habitual), el runner
   usa radio 90 Å para **cualquier** cápside **y** la cápside **sin centrar**. PACKMOL, con
   `fixed 0 0 0 0 0 0` y **sin** la palabra clave `center`, deja las coordenadas tal cual
   (confirmado en `cenmass.f90`: `fixed` pone `domass=.false.`). Para BMV, cuyo `capside.pdb`
   está centrado en (207.9, 207.9, 207.9), las enzimas se empaquetan en una esfera vacía a
   360 Å de la cápside: cero colisiones, "capacidad" artificial. Para QB (centroide en
   x = 73.9) la esfera queda descentrada 74 Å. → §2.3.
3. **[ALTO] La "capacidad máxima" depende del hardware.** `timeout=90` s está hardcodeado
   (la config dice 300 y no se lee), un timeout cuenta como "no cabe", y 7 procesos PACKMOL
   compiten por CPU. El número reportado es "lo que PACKMOL resolvió en 90 s en esta
   máquina", no una propiedad de la cápside. La causa de cada fallo no se registra. → §3.3.
4. **[ALTO] La perilla dominante de la capacidad es `radius 5.0` y está mal entendida.** En
   PACKMOL el `radius` de una estructura es el radio **por átomo**, y la distancia mínima
   entre dos átomos es la **suma de sus radios** (`fparc.f90`: `tol=(radius(i)+radius(j))**2`).
   Con `radius 5.0` y cápside al valor por defecto (tolerance/2 = 1.0): **10 Å** entre átomos
   de enzimas distintas y **6 Å** enzima-cápside. El README dice 10 Å, la config 5 Å, el
   packer por defecto 10 Å. No hay análisis de sensibilidad y el valor no tiene justificación
   física escrita. → §3.1.
5. **[MEDIO] CIENCIA-1 (±1 Å) tiene respuesta geométrica, no de preferencia.** El bucle
   entero de PyMOL devuelve `r_first` con `d_min − 0.5 < r_first ≤ d_min + 0.5`, donde
   `d_min` es la distancia del centroide al **centro** del átomo más cercano. Sumar 1 Å
   (código) reporta como "radio interno" un valor que **sobrestima** la cavidad física en
   ≈ 2–3 Å (habría que restar el radio de vdW del átomo, ≈ 1.7 Å, no sumar). Restar 1 Å
   (docstring) da ≈ `d_min − 1 ± 0.5`, es decir, aproximadamente el radio físico. **El código
   implementa lo contrario de lo que dice** y de lo que dicen `README.md:131,255` y
   `CLAUDE.md:99`. Impacto en capacidad: pequeño (volumen ×0.93 para BMV) porque PACKMOL
   además choca contra la cápside real; impacto en lo que se *reporta* como radio: directo.
   → §2.2.

Lo que SÍ está bien (verificado): la cápside entra a PACKMOL como estructura **fija** con
sus 216 780 átomos reales, de modo que cuando el centrado funciona la pared que acota a las
enzimas es la real, no la esfera; la esfera `inside sphere` se aplica a centros atómicos
(`comprest.f90`) y es la que impide colocar enzimas fuera; el centrado (cuando PyMOL está)
usa el mismo centroide para radio y para `capside_centered.pdb`, así que ambas cosas son
coherentes; la réplica NumPy del algoritmo de radio reproduce **exactamente** los 90 Å de
`PackMan.v.1.2/archivos_dm_cg/empaquetador/radio_interno.txt` para BMV; y las semillas
usadas sí quedan en `metadata.json` de cada réplica (reproducibilidad *a posteriori*).

---

## 1. Alcance, método e inventario

### 1.1 Qué se auditó

| Pieza | Archivo | Papel |
|---|---|---|
| Radio interno | `nanocapsule-mvp/src/core/capsid.py` | Pseudoátomo expansivo en PyMOL; recentrado; `radio_interno.txt` |
| Centrado | `capsid.py:170-219`, `src/core/cargo.py:59-115` | PyMOL, media de coordenadas |
| Orquestación | `src/core/experiment_runner.py` | Radio → centrado → parámetros → réplicas |
| Motor | `src/packing/parallel_packer.py` | Genera `.inp`, corre PACKMOL, búsqueda incremental, consolida |
| Carpetas/metadata | `src/core/experiment_manager.py` | 7 réplicas hardcodeadas |
| Config | `nanocapsule-mvp/config/default.yaml` | Parámetros (varios ignorados) |
| Fachada | `src/services/packing.py`, `src/web/app.py:252-320` | Endpoints `/api/capsid/radius`, `/api/experiment/run` |
| Biblioteca | `src/services/library.py:61-85` | Muestra el radio cacheado |
| Tests | `tests/test_smoke.py`, `tests/test_golden_science.py`, `.github/workflows/ci.yml` | Red de seguridad |
| Origen | `PackMan.v.1.2/archivos_dm_cg/empaquetador/1calcula_radio_interno.py`, `2Empaquetador_Maximo.py` | Scripts de la tesis de los que se migró |

### 1.2 Inventario geométrico de los inputs commiteados (medido aquí, Python puro)

| Estructura | Átomos | H | HETATM | Centroide | d_min al centroide (átomo) | r_max |
|---|---|---|---|---|---|---|
| BMV_IJS9 `capside.pdb` | 216 780 | 0 | 0 | **(207.90, 207.90, 207.90)** | 89.47 Å (NH1 ARG C26) | 143.58 Å |
| CCMV_1CWP | 214 440 | 0 | 0 | (0, 0, 0) | 92.79 Å (CG2 VAL C27) | 146.47 Å |
| MS2_2MS2 | 173 700 | 0 | 0 | (0, 0, 0) | 103.63 Å (NH2 ARG C49) | 144.15 Å |
| QB_1QBE | 168 480 | 0 | 0 | **(73.89, 0, 0)** | 105.94 Å (O ARG B57) | 147.23 Å |
| GCase_1OGS `enzima.pdb` | 3 973 | 0 | 0 (glicanos retirados) | (210.2, 192.4, 206.3) | — | 42.79 Å |
| EGFP_4EUL | 1 948 | 0 | 22 | (0, 0, 0) | — | 29.69 Å |
| Luciferasa_1LCI | 3 967 | 0 | 0 | (0, 0, 0) | — | 46.54 Å |
| Alk. Phosphatase_1ED8 | 6 620 | 0 | 0 | (0, 0, 0) | — | 51.54 Å |

Observaciones: dos de las cuatro cápsides de la biblioteca **no están centradas** (relevante
para el hallazgo 2); ninguna estructura tiene hidrógenos (relevante para interpretar
`tolerance 2.0`); en BMV y CCMV el átomo que define la esfera inscrita es un residuo del
brazo N-terminal (ARG 26 / VAL 27 de la cadena C), una región flexible y parcialmente
desordenada en los cristales: la "esfera interna" la fija el residuo más móvil de la cápside.

---

## 2. Radio interno de la cápside (PyMOL)

### 2.1 Qué hace realmente el algoritmo `[ESTÁTICO]`

`capsid.py:125-137`: para `r = 5…199`, selecciona `byres (capa within r+0.5 of centro)` y
se detiene en el primer `r` con átomos. Luego `capsid.py:146` suma 1.0.

- `within` en PyMOL mide distancia **entre centros atómicos**; el `vdw` que se le asigna al
  pseudoátomo en `capsid.py:111-113,126-127` y el `cmd.rebuild()` son **cosméticos**: no
  afectan a la selección. El algoritmo es, exactamente, `r_first = min{ r ∈ ℤ : d_min ≤ r + 0.5 }`.
- Por tanto `r_first ∈ (d_min − 0.5, d_min + 0.5]` y lo que se reporta es `r_first + 1 ∈ (d_min + 0.5, d_min + 1.5]`.
- `byres` expande a residuos completos; no cambia el criterio de parada (solo cuenta > 0).
- Coste: ~200 selecciones sobre 2·10⁵ átomos. Innecesario: `d_min` se calcula exacto con
  NumPy en milisegundos y sin PyMOL (ver §7, test propuesto T1).

**Réplica ejecutada aquí** (NumPy sobre los PDB commiteados, misma regla `d_min ≤ r+0.5`):

| Cápside | d_min | r_first | Código (+1) → radio reportado | Esfera PACKMOL (−2) | Docstring (−1) → esfera | Físico ≈ d_min − 1.7 |
|---|---|---|---|---|---|---|
| BMV | 89.47 | 89 | **90** | 88 | 88 → 86 | 87.8 |
| CCMV | 92.79 | 93 | 94 | 92 | 92 → 90 | 91.1 |
| MS2 | 103.63 | 104 | 105 | 103 | 103 → 101 | 101.9 |
| QB | 105.94 | 106 | 107 | 105 | 105 → 103 | 104.2 |

El valor 90 para BMV coincide con `PackMan.v.1.2/archivos_dm_cg/empaquetador/radio_interno.txt`
(= `90`) y con `packmol_tmp.inp` (`inside sphere 0.0 0.0 0.0 88`). Es decir, el algoritmo
migrado reproduce el original de la tesis; la réplica NumPy es una **verificación estática
independiente de PyMOL** del resultado histórico. Que el fallback por defecto sea también
90.0 (`default.yaml:7`) hace que para BMV sea **imposible distinguir desde el resultado** si
PyMOL corrió o no: un diseño que oculta el modo degradado.

### 2.2 CIENCIA-1 — el signo del ±1 Å `[ESTÁTICO]`

Hechos:

- Original (`1calcula_radio_interno.py:34-41`): detecta colisión en `r` y da **un paso más**
  (`r+1`), comentario "Expansión 1 Å más allá de la colisión". Intención original: **+1**.
- Migración (`capsid.py:57-59`): el docstring declara como "cambio importante" pasar a
  **−1** ("margen interno de seguridad"), pero `capsid.py:144-147` implementa **+1** con el
  comentario "CORRECCIÓN: … como en original". Desde el commit inicial (`d5035a2`) ya era así:
  **el −1 nunca se implementó**. `README.md:131,255` y `CLAUDE.md:99` documentan el −1.
- `parallel_packer.py:268-269` resta después un `collision_margin = 2.0` **hardcodeado**
  (ignora `packing.collision_margin` de la config, aunque `capsid.py:237-239` sí lo lee en un
  método que nadie usa).

Análisis geométrico (independiente de preferencias):

- La cantidad física "radio de la cavidad" es la distancia del centro a la **superficie** del
  átomo más cercano: `d_min − r_vdW ≈ d_min − 1.7 Å`. Ni +1 ni −1 la calculan; el bucle
  entero añade además ±0.5 Å de cuantización.
- **+1 (código)** reporta `≈ d_min + 1`: sobrestima la cavidad física en ≈ 2.7 Å. Como radio
  "interno" publicable es incorrecto por construcción (cae *dentro* del átomo de la pared).
- **−1 (docstring)** reporta `≈ d_min − 1`: coincide con el radio físico dentro del error de
  cuantización. Es el único de los dos que puede defenderse como "radio interno".
- Para el **empaquetado** el signo importa poco: PACKMOL además impone 6 Å entre átomos de
  enzima y de cápside (§3.1), así que la esfera (88 u 86 Å para BMV) rara vez es la
  restricción activa junto a la pared. El efecto sobre la capacidad es ≤ 7 % en volumen
  (`(86/88)³ = 0.93`) y probablemente menor en número de enzimas.

**Recomendación (para que la decida Lucio, con estos datos):** sustituir el bucle por
`d_min` exacto (NumPy, sin PyMOL) y reportar dos números con nombre distinto: *radio interno
físico* `= d_min − r_vdW` y *radio de la esfera de empaquetado* `= radio físico − margen`.
Eso disuelve CIENCIA-1 (ya no hay un "±1" que elegir) y hace el cálculo testeable en CI. Si
se quiere conservar el método histórico, implementar lo que dice el docstring (−1) y
actualizar el comentario del código, o viceversa; lo inaceptable para JOSS es el estado
actual (código ≠ docstring ≠ README).

### 2.3 Modo degradado sin PyMOL `[ESTÁTICO; efecto REQUIERE CORRER]` — CRÍTICO

Cadena de eventos en `experiment_runner.py:97-117` cuando `from pymol import cmd` falla
(`capsid.py:10-16` pone `PYMOL_AVAILABLE=False`):

1. `calculate_internal_radius()` **no lanza**: devuelve 90.0 (`capsid.py:72-77`) para
   cualquier cápside. Para MS2/QB (radio real ≈ 105–107 Å) eso recorta el volumen de la
   cavidad un **37–40 %** → capacidad sistemáticamente subestimada.
2. `center_structure()` **sí lanza** `RuntimeError` (`capsid.py:184-185`) → lo captura el
   `except` de `experiment_runner.py:114-117`, que imprime y sigue, dejando `capsid_file`
   apuntando al **PDB original sin centrar**.
3. El `.inp` lleva `fixed 0. 0. 0. 0. 0. 0.` **sin `center`** (`parallel_packer.py:260-263`).
   En PACKMOL, `fixed` desactiva el recentrado de esa molécula (`cenmass.f90`: `domass=.false.`;
   solo `center`/`centerofmass` lo reactivan). Nótese que el `.inp` de sustratinaitor
   (`sustratinaitor/3_empaquetado_packmol/packmol_input.inp:8`) **sí** lleva `center`: el
   autor conocía la palabra clave.
4. Resultado para BMV: cápside con centroide en (207.9, 207.9, 207.9), esfera de 88 Å en el
   origen → separación 360 Å > r_max 143.6 Å → **las enzimas se empaquetan en el vacío**,
   nunca chocan con la cápside, y la "capacidad" es la de una esfera libre de 88 Å (la
   búsqueda subiría hasta donde el timeout de 90 s lo permita). Para QB la esfera queda
   desplazada 74 Å: parte dentro, parte atravesando la pared.
5. Nada en el resultado (`statistics.json`, UI) delata el modo degradado: el radio es 90
   igual que el real de BMV, y `success=True`.

Evidencia de que este camino se usa: `ESTADO.md:109-110` ("el radio casi siempre es el
fallback 90 Å"); `/api/health` (`app.py:50-53`) comprueba `shutil.which("pymol")` — el
**binario** — pero el código necesita el **módulo Python** `pymol` en el intérprete de Flask,
que es otra cosa (un venv sin `pymol` da binario ✓ y módulo ✗). El badge "PACKMOL LISTO" de
la UI no cubre PyMOL.

**Cómo confirmarlo (REQUIERE CORRER, en la máquina de Lucio):**
```bash
cd nanocapsule-mvp
# 1) ¿el intérprete que corre Flask importa pymol?
python3 -c "from pymol import cmd; print('pymol OK')"
# 2) ejecutar un experimento BMV+GCase con 1 réplica y medir dónde quedaron las enzimas
python3 - <<'EOF'
import glob, math
f = sorted(glob.glob("Output/BMV_IJS9/GCase_1OGS/replica_1/packed_*_attempt*.pdb"))[-1]
caps, enz = [], []
for l in open(f):
    if l.startswith(("ATOM","HETATM")):
        (caps if len(caps) < 216780 else enz).append((float(l[30:38]), float(l[38:46]), float(l[46:54])))
cc = [sum(c[i] for c in caps)/len(caps) for i in range(3)]
ce = [sum(e[i] for e in enz)/len(enz) for i in range(3)]
print("centroide cápside", cc, "centroide enzimas", ce, "separación", math.dist(cc, ce))
EOF
# Esperado si está bien: separación < ~40 Å. Si PyMOL no importó: ≈ 360 Å.
```

**Corrección mínima (dos líneas, sin tocar ciencia):** añadir `center` bajo `fixed` en el
`.inp` (hace al empaquetado inmune al centrado previo) y convertir la ausencia de PyMOL en
**error**, no en fallback silencioso (o, mejor, eliminar la dependencia: centroide y `d_min`
con NumPy).

### 2.4 Otros hallazgos del radio `[ESTÁTICO]`

- **Atribución falsa en la Biblioteca.** `capsid.py:153-155` escribe `radio_interno.txt` en
  el **CWD** (sin nombre de cápside); `library.py:61-68,84-85` lo lee desde `PROJECT_ROOT` y
  lo muestra **siempre como el radio de BMV**. Calcular el radio de QB desde la UI deja la
  Biblioteca mostrando 107 Å para BMV. Medio.
- **Esfera inscrita vs cavidad real.** La cavidad icosaédrica no es esférica; la esfera
  inscrita la define el átomo más interno (en BMV/CCMV, un brazo N-terminal flexible).
  Como *constraint de permanencia* ("no salgas de la cápside") es una buena elección
  conservadora; como *estimador de volumen disponible* subestima. Documentarlo. Bajo.
- Las excepciones de PyMOL se tragan y devuelven 90 (`capsid.py:163-168`): mismo patrón de
  fallo silencioso que §2.3. Bajo (mismo arreglo).

---

## 3. Constraints de PACKMOL, criterio de convergencia y capacidad máxima

### 3.1 El `.inp` que se genera (`parallel_packer.py:249-274`) `[ESTÁTICO]`

```
tolerance 2.0
output packed_N_attemptA.pdb
seed <aleatoria>
filetype pdb
structure capside_centered.pdb
  number 1
  fixed 0. 0. 0. 0. 0. 0.
end structure
structure enzima_centered.pdb
  number N
  inside sphere 0. 0. 0. <radio−2>
  radius 5.0          # desde config (packer por defecto: 10.0)
end structure
```

Semántica verificada en el código fuente de PACKMOL:

| Elemento | Qué significa de verdad | Fuente |
|---|---|---|
| `tolerance 2.0` | Radio por átomo por defecto = tolerance/2 = 1.0 Å; distancia mínima entre dos átomos = suma de radios. | `fparc.f90`: `tol = (radius(icart)+radius(jcart))**2` |
| `radius 5.0` (enzima) | **Cada átomo** de enzima tiene radio 5 Å. Enzima–enzima: ≥ **10 Å** entre centros atómicos. Enzima–cápside: ≥ **6 Å**. No es "distancia entre enzimas" como dice `default.yaml:12` ni "10 Å entre enzimas" como dice `README.md:65,264`. | `fparc.f90` |
| `inside sphere … R` | Se evalúa sobre **centros** atómicos (sin radio). Todas las posiciones atómicas de cada enzima dentro de R. | `comprest.f90` (tipo 8) |
| `fixed x y z a b c` | Rotación (a,b,c) y traslación (x,y,z) aplicadas a las coordenadas **tal cual**; **no** se centra salvo `center`. | `cenmass.f90`, `app/packmol.f90` |
| `seed` | Entero; por defecto 1234567 en PACKMOL. | `getinp.f90` |
| convergencia interna | `precision 1e-2` por defecto sobre la función objetivo; `maxit 20`, `nloop` por defecto (400 en el log). | `getinp.f90`, log línea 29 |

Juicio científico sobre los constraints:

- `tolerance 2.0` sobre átomos pesados sin H es el valor estándar de PACKMOL para
  all-atom y aquí es irrelevante porque `radius 5.0` lo domina (6 Å y 10 Å efectivos). Esas
  distancias (centro–centro entre átomos pesados) equivalen a huecos de ≈ 2.5 Å y ≈ 6.5 Å
  entre superficies de vdW: **físicamente generosas** (una capa de agua). Defendible como
  "sin contacto directo", pero es una **decisión que fija la capacidad** y no está
  justificada ni documentada en ninguna parte del repo. La capacidad escala con
  `(R_cav / (R_enz + radius))³`: pasar de 5 a 2.5 Å o a 10 Å cambia el número de enzimas
  del orden de ±30 %.
- Inconsistencia de valores: `default.yaml:13` = 5.0; `parallel_packer.py:81` y
  `experiment_runner.py:134` (fallback) = 10.0; `README.md:65,264` = 10 Å. En producción
  gana la config (5.0). Alto riesgo de que lo publicado no describa lo corrido.
- La esfera de radio `radio−2` es **redundante** con la pared real para evitar
  solapamientos (PACKMOL ya choca contra los 216 780 átomos fijos) y sólo es necesaria para
  impedir enzimas **fuera**. Al ser la esfera inscrita, además recorta el volumen cerca de
  los ejes 3 y 5 (donde la pared está más lejos). Es conservador, no un bug; documentarlo.
- Falta `add_amber_ter` y la cadena/numeración de la cápside se pierde: el PDB resultante
  es apto para contar enzimas pero **no para pasarlo a tLeaP** (lo detalla `AUDITORIA_MD.md`,
  MD-03). Si el packing alimenta a PackMan, ese `.inp` debe arreglarse aquí.

### 3.2 Criterio de aceptación de una corrida `[ESTÁTICO + REQUIERE CORRER]` — CRÍTICO

Código: `parallel_packer.py:287-310`.

1. **El regex nunca casa.** `parallel_packer.py:34-36,191-193` busca
   `Maximum\s+distance\s+violation:`. PACKMOL (confirmado en `writesuccess.f90` y en los dos
   logs reales commiteados) escribe `Maximum violation of target distance:` y `Maximum
   violation of the constraints:`. Ejecutado aquí:
   ```
   ParallelPacker()._read_max_violation("PackMan.v.1.2/.../log_packmol_1enzimas_20260324_212620.txt") -> None
   ParallelPacker()._read_max_violation("sustratinaitor/3_empaquetado_packmol/packmol_run.log")      -> None
   ```
   Heredado del original `2Empaquetador_Maximo.py:87` (mismo regex, mismo fallback).
2. **El fallback acepta siempre.** `count_atomic_lines(output) ≥ 10000`
   (`parallel_packer.py:300-310`) lo cumple la cápside sola (≥ 168 480 líneas). El umbral
   `max_violation_threshold` (`default.yaml:20`, `experiment_runner.py:135`) **no
   interviene nunca**. Lo que queda es: `returncode == 0 and output_pdb.exists()`.
3. **¿Es eso suficiente?** Depende de la versión de PACKMOL:
   - Cuando PACKMOL **no converge**, escribe el mejor punto a `<output>_FORCED`
     (`checkpoint.f90`) y, en versiones con `exit_codes.f90`, termina con exit **173**. En
     ese caso la corrida se rechaza correctamente (por el exit code).
   - Pero PACKMOL **también escribe puntos intermedios al fichero de salida regular**
     durante la optimización ("Current solution written to file: …", visto en
     `sustratinaitor/.../packmol_run.log:342,366`). Por tanto `output_pdb.exists()` puede ser
     cierto tras una corrida no convergida. Si la versión instalada (el log de PackMan dice
     **20.14.3, build de Packmol-Memgen/AmberTools**) termina con `stop` (exit 0) al no
     converger, **una estructura con solapamientos pasa como "cabe"**.
   - Un **timeout** (`TimeoutExpired`) sí se rechaza (`parallel_packer.py:312-315`), aunque el
     fichero intermedio quede en disco.
4. **Lo que se documenta no es lo que se hace.** `CLAUDE.md` ("Max distance violation:
   0.10Å"), `default.yaml:18-24`, `2Empaquetador_Maximo.py:34-35`.

**Cómo confirmarlo (REQUIERE CORRER):**
```bash
# Caso imposible: 40 GCase en una esfera de 30 Å, pocas iteraciones para que acabe rápido.
cd nanocapsule-mvp && cat > /tmp/imposible.inp <<'EOF'
tolerance 2.0
filetype pdb
output /tmp/imposible.pdb
seed 1
nloop 5
structure Input/Enzimas/GCase_1OGS/enzima_centered.pdb
  number 40
  inside sphere 0. 0. 0. 30.
  radius 5.0
end structure
EOF
packmol < /tmp/imposible.inp > /tmp/imposible.log; echo "exit=$?"
ls -la /tmp/imposible.pdb /tmp/imposible.pdb_FORCED 2>&1
grep -c "^ATOM" /tmp/imposible.pdb 2>/dev/null
grep -n "violation\|FORCED\|Success\|ENDED" /tmp/imposible.log | tail
# Si exit=0 y /tmp/imposible.pdb existe con >=10000 líneas → el packer lo habría aceptado.
packmol 2>&1 </dev/null | grep -i version
```

**Corrección mínima:** regex `Maximum violation of target distance:\s*([-+\d.eE]+)` tomado
del **último** match (bloque "Success!"), exigir además la cadena `Success!` en el log, y
tratar la ausencia de ambas como **fallo**, nunca como fallback de líneas. Añadir el test T2
(§7) con los logs reales ya commiteados como fixtures.

### 3.3 Búsqueda de la capacidad máxima `[ESTÁTICO]` — ALTO

`parallel_packer.py:322-346`: `n = 1, 2, 3, …`; cada `n` tiene 2 intentos
(`seed`, `seed+1000`), `timeout=90` s por intento; parada tras 3 fallos consecutivos; tope 100.

- **El timeout define la ciencia.** `timeout=90` (`parallel_packer.py:283`) está
  hardcodeado; `engines.packmol.timeout: 300` (`default.yaml:33`) no se lee. Un `n` que
  PACKMOL resolvería en 120 s se declara "NO cabe". Con 216 780 átomos fijos + N×3 973, el
  coste por iteración GENCAN crece con N; el único log real (N=1) tardó 2.1 s porque "Initial
  approximation is a solution"; no hay evidencia de los tiempos a N ≈ 10. Además corren
  `min(cpu, 7)` procesos a la vez (`parallel_packer.py:31`): la capacidad medida con 10
  réplicas en un portátil de 4 núcleos será **menor** que con 1 réplica en una workstation,
  por pura contención. Esto es incompatible con reportar "capacidad de la cápside".
- **No se registra por qué falla** un `n`: timeout, exit≠0, `_FORCED`, excepción, todo acaba
  en el mismo `False` (`parallel_packer.py:312-320`). Sin eso no se puede distinguir "no
  cabe" de "no le dio tiempo".
- El criterio "3 fallos consecutivos" es una heurística razonable para un máximo
  estocástico, pero con 2 intentos por `n` la probabilidad de parar antes del verdadero
  máximo es alta cuando el problema se vuelve duro (justo cerca de la capacidad). Aumentar
  intentos cerca del fallo (p. ej. 2 → 6 cuando `n ≥ best_n`) es barato.
- Orden de magnitud (sanidad, calculado aquí): esfera de 88 Å = 2.86·10⁶ Å³; GCase
  `V_vdW` = 44 056 Å³ (`vdw_volumes_results.txt`), `Rg` 22.6 Å → esfera equivalente 29.2 Å.
  Cotas: 65 (volumen vdW, irreal), 27 (esferas equivalentes al 100 %), 17 (con +5 Å de
  `radius`), **≈ 11** (empaquetado aleatorio, φ ≈ 0.64). El "14" que menciona el comentario
  de `parallel_packer.py:328` es plausible con `radius` entre 2.5 y 5 Å. Útil como control:
  un resultado ≫ 20 para GCase en BMV delataría el modo degradado de §2.3.

### 3.4 Parámetros de config que el código ignora `[ESTÁTICO]`

| Clave en `default.yaml` | Línea | ¿Se lee? | Valor real usado |
|---|---|---|---|
| `packing.collision_margin` | 10 | No (solo `capsid.get_geometric_properties`, sin llamadas) | 2.0 hardcodeado `parallel_packer.py:268` |
| `packing.max_violation_threshold` | 20 | Se lee, pero el regex nunca casa | inoperante |
| `packing.min_lines_threshold` | 24 | Sí | 10000 (siempre satisfecho) |
| `engines.packmol.timeout` | 33 | No | 90 s `parallel_packer.py:283` |
| `engines.packmol.seed_base` | 37 | No | `random.randint` `parallel_packer.py:118` |
| `engines.packmol.use_random_seeds` | 40 | No | siempre aleatorio |
| `experiments.n_replicas` | 96 | Sí (10) | pero `ExperimentManager.n_replicas = 7` `experiment_manager.py:47` → `experiment_metadata.json` dice 7 mientras corren 10 |

---

## 4. Validación estadística por réplicas

### 4.1 Qué se calcula `[ESTÁTICO]`

`parallel_packer.py:409-421` (y duplicado en `experiment_manager.py:181-190`, código que no
se ejecuta en el flujo actual): sobre `n_packed` de las réplicas con `success`, `best`,
`worst`, `mean`, `median`, `stdev` (muestral). La UI (`packing.js:76-100`) muestra las
cuatro barras y el "best" como resultado. Comprobado aquí con 10 valores sintéticos
`[9,10,10,11,9,10,12,10,9,10]` → `best 12, mean 10, stdev 0.94`: la aritmética es correcta.

### 4.2 Qué significan y qué no `[ESTÁTICO]`

- Cada réplica es una **búsqueda estocástica de un máximo**; su `n_packed` es una **cota
  inferior** de la capacidad real bajo este modelo. El estimador correcto de la capacidad es
  `best` (máximo sobre réplicas), y crece con el número de réplicas hasta saturar. `mean` y
  `stdev` describen la **variabilidad del buscador** (semilla + timeouts + contención de
  CPU), **no** una incertidumbre física de la cápside ni de la enzima. Presentarlos como
  "estadística del empaquetamiento" (UI, `report.txt`) invita a leerlos como lo segundo.
- **Criterio de suficiencia** ausente: con 10 réplicas, si `best` lo alcanza una sola, la
  búsqueda no ha saturado y 10 es poco; si lo alcanzan ≥ 5, probablemente sí. Ese número
  (`fracción de réplicas que alcanzan best`) es el que soporta o no la conclusión, y no se
  reporta. Recomendación: reportarlo y añadir réplicas hasta que `best` se repita ≥ k veces.
- **El número de réplicas es inconsistente**: 7 en `experiment_manager.py:47`, `README.md:40,96,258`
  y `CLAUDE.md`; 10 en `default.yaml:96`, `experiment_runner.py:47` y la UI. Las carpetas
  `replica_1..7` las crea el manager y `replica_8..10` el packer.
- **No hay réplicas de nada más**: ni del radio (determinista, bien), ni de la sensibilidad a
  `radius`/`tolerance`/timeout. Para una afirmación publicable ("caben N enzimas") hace falta
  al menos la curva `best(radius)` para 2–3 valores y `best(timeout)` para demostrar que el
  timeout no es la restricción activa.
- `stdev` con `n=1` se fuerza a 0 (`parallel_packer.py:417`): correcto evitar el error, pero
  debería reportarse como "no definida".
- Condición aguas abajo: `BITACORA.md:17-18` y `PENDIENTES.md:18` hablan de "réplicas →
  condición de 6 enzimas → all-atom". Si ese 6 sale de este motor, hereda todo lo anterior
  (modo degradado, timeout, `radius`), y hoy **no hay ningún resultado commiteado** que lo
  respalde: `nanocapsule-mvp/.gitignore` excluye `Output*/` y `radio_interno*.txt`, y
  `git log --all` no contiene ningún `statistics.json` ni `report.txt`. Única evidencia de
  ejecución real: el log de 1 enzima en PackMan.

### 4.3 ¿Cuántas réplicas, qué dispersión? `[REQUIERE CORRER]`

No se puede decir desde el repo: no hay ninguna corrida registrada. Protocolo mínimo para
responderlo (también sirve como test de integración lento, fuera de CI):

```bash
cd nanocapsule-mvp && python3 - <<'EOF'
# Mismo caso, 3 configuraciones; semillas FIJAS (hay que pasar seed_base; hoy la UI no puede).
from src.packing.parallel_packer import ParallelPacker
import json
p = ParallelPacker(max_workers=1)          # 1 worker: sin contención, tiempos comparables
for label, kw in {"base": {}, "radius2.5": {"exclusion_radius": 2.5}, "radius10": {"exclusion_radius": 10.0}}.items():
    r = p.run_parallel_replicas("Input/Capsides/BMV_IJS9/capside_centered.pdb",
                                "Input/Enzimas/GCase_1OGS/enzima_centered.pdb",
                                n_replicas=10, internal_radius=90.0, seed_base=1234567,
                                output_dir=f"Output/audit_{label}", **kw)
    vals = sorted(x["n_packed"] for x in r["all_results"])
    print(label, "best", r["best"], "mean %.2f sd %.2f" % (r["mean"], r["stdev"]),
          "frac_best %.1f" % (vals.count(r["best"]) / len(vals)), vals)
EOF
# Luego repetir "base" con seed_base=1234567 → debe dar la MISMA lista (reproducibilidad),
# y con timeout 300 s (editar parallel_packer.py:283) → si best sube, el timeout era la restricción.
grep -l "FORCED\|Maximum number of GENCAN" Output/audit_base/replica_*/packmol_log_*.txt | wc -l   # no convergidas
```

---

## 5. Reproducibilidad real

| Pregunta | Respuesta | Evidencia | Etiqueta |
|---|---|---|---|
| ¿Semillas fijas? | **No.** `seed_base=None` por defecto y el runner no lo pasa → `random.randint(1, 10⁶)`. La config que promete semilla fija no se lee. | `parallel_packer.py:83,115-118`; `experiment_runner.py:160-170`; `default.yaml:35-40` | ESTÁTICO |
| ¿Se registra la semilla usada? | Sí, en `replica_i/metadata.json` (`seed`), y el `.inp` lleva `seed`. Reproducible *a posteriori* si alguien reinyecta `seed_base` a mano (no hay CLI ni endpoint para ello). | `parallel_packer.py:253-257,353-366` | ESTÁTICO |
| ¿PACKMOL es determinista con semilla fija? | Sí (mono-hilo, PRNG propio), **siempre que no intervenga el timeout**: el mismo input puede converger en una máquina y agotar 90 s en otra. | `parallel_packer.py:283` | REQUIERE CORRER |
| ¿El radio es reproducible? | Sí, determinista; reproducido aquí con NumPy para las 4 cápsides. Pero el fichero `radio_interno.txt` se escribe en el CWD y se gitignora. | §2.1; `.gitignore` | ESTÁTICO |
| ¿Los inputs commiteados reproducen lo reportado? | No hay nada reportado que reproducir: cero outputs del Studio en el repo. El único resultado real (PackMan, 1 enzima, seed 1234567 por defecto de PACKMOL) sí es reproducible y coincide con el radio recalculado aquí. | §4.2 | ESTÁTICO |
| ¿La versión de PACKMOL queda registrada? | No. Ni versión ni exit code ni tiempo de ejecución en `metadata.json`. El log sí tiene la versión, pero el log no se conserva como artefacto del experimento. | `parallel_packer.py:353-362` | ESTÁTICO |
| ¿CI valida algo del packing? | **No.** `ci.yml` corre `pytest -q` = humo + golden del poro. | `.github/workflows/ci.yml:45-47` | ESTÁTICO |

### 5.1 `tests/test_golden_science.py` — ¿comprueba lo que importa? `[ESTÁTICO]`

- Comprueba `substrate_section(smiles)` (RDKit + PCA) para 3 SMILES con tolerancia 0.2 Å
  y determinismo. Eso es la **puerta del poro**, no el packing. El docstring
  (`test_golden_science.py:1-9`) lo dice honestamente; lo que miente es `BITACORA.md:24`
  ("packing … con golden test").
- **Cobertura del motor de packing en la suite: cero.** `test_smoke.py:128-136` ejercita
  `/api/preview/enzymes`, que es colocación **aleatoria sin PACKMOL** (`services/packing.py:45-73`).
  Ninguno de estos fallos lo cazaría un test actual: el regex muerto, el `fixed` sin
  `center`, el fallback sin centrar, el timeout hardcodeado, el 7 vs 10, la atribución de
  radio a BMV.
- Para JOSS el riesgo es doble: el revisor verá "golden test" en la bitácora y una suite
  verde, y nada de eso toca el único motor que se afirma firme.

---

## 6. Tabla consolidada de hallazgos

Severidad: CRÍTICO = invalida o puede invalidar el número reportado · ALTO = el número
depende de algo ajeno a la ciencia o lo documentado no es lo corrido · MEDIO = error de
reporte/interpretación · BAJO = deuda. Comando: ver la sección referida.

| ID | Sev. | Hallazgo | Evidencia (archivo:línea) | Etiqueta | Confirmar con |
|---|---|---|---|---|---|
| PK-01 | **CRÍTICO** | Regex de violación nunca casa con PACKMOL → umbral 0.10 Å inoperante; el fallback de ≥10000 líneas acepta siempre; posible aceptación de estructuras no convergidas (fichero intermedio + exit 0) según versión | `parallel_packer.py:34-36,191-193,287-310`; logs reales `PackMan…/log_packmol_1enzimas_20260324_212620.txt:127-128`, `sustratinaitor/…/packmol_run.log:342,366,387`; origen `2Empaquetador_Maximo.py:87` | ESTÁTICO (mecanismo) · REQUIERE CORRER (exit code de 20.14.3) | §3.2 |
| PK-02 | **CRÍTICO** | Sin módulo `pymol`: radio 90 para todo **y** cápside sin centrar + `fixed` sin `center` → enzimas fuera de la cápside (BMV) o esfera descentrada 74 Å (QB); fallo silencioso | `experiment_runner.py:97-117`; `capsid.py:72-77,184-185`; `parallel_packer.py:260-263`; `Input/Capsides/BMV_IJS9/capside.pdb` centroide (207.9,207.9,207.9); PACKMOL `cenmass.f90`; `ESTADO.md:109-110` | ESTÁTICO (mecanismo) · REQUIERE CORRER (si ocurre en la máquina de Lucio) | §2.3 |
| PK-03 | **ALTO** | Semillas aleatorias; `seed_base`/`use_random_seeds` de la config ignorados; sin forma de reinyectar la semilla desde UI/CLI | `parallel_packer.py:83,115-118`; `experiment_runner.py:160-170`; `default.yaml:35-40` | ESTÁTICO | `grep -rn seed_base src/` → solo en el packer |
| PK-04 | **ALTO** | `timeout=90` hardcodeado (config 300 ignorada); timeout = "no cabe"; 7 procesos en paralelo → capacidad dependiente de hardware/carga; causa del fallo no registrada | `parallel_packer.py:31,283,312-320`; `default.yaml:33` | ESTÁTICO · REQUIERE CORRER (medir `best(timeout)`) | §4.3 |
| PK-05 | **ALTO** | `radius 5.0` = radio **por átomo**; 10 Å enzima–enzima y 6 Å enzima–cápside; valor sin justificación; README (10), config (5), packer (10) discrepan; sin sensibilidad | `parallel_packer.py:81,273`; `default.yaml:12-13`; `README.md:65,264`; `experiment_runner.py:134`; PACKMOL `fparc.f90` | ESTÁTICO · REQUIERE CORRER (curva `best(radius)`) | §3.1, §4.3 |
| PK-06 | **MEDIO** | CIENCIA-1: código +1 (reproduce original), docstring/README/CLAUDE −1; +1 sobrestima el radio físico ≈ 2.7 Å; el bucle entero añade ±0.5 Å; `collision_margin` hardcodeado | `capsid.py:57-59,144-147`; `1calcula_radio_interno.py:34-41`; `README.md:131,255`; `CLAUDE.md:99`; `parallel_packer.py:268-269` | ESTÁTICO (reproducido con NumPy) | §2.2; test T1 |
| PK-07 | **MEDIO** | Fallback 90 Å para MS2/QB (reales 105–107) recorta 37–40 % del volumen; indistinguible del valor real de BMV | `default.yaml:7`; `capsid.py:74,141,166`; tabla §2.1 | ESTÁTICO | §2.1 |
| PK-08 | **MEDIO** | `best` presentado junto a `mean/stdev` como si fueran estadística física; falta "fracción de réplicas que alcanzan best"; 7 vs 10 réplicas; `experiment_metadata.json` dice 7 | `parallel_packer.py:409-421`; `experiment_manager.py:47,72-74,86`; `default.yaml:96`; `packing.js:76-100` | ESTÁTICO | §4 |
| PK-09 | **MEDIO** | Cero tests del packing; "golden test" de la bitácora es del poro; CI no cubre el motor | `test_golden_science.py:1-27`; `test_smoke.py:1-7,128-136`; `ci.yml:45-47`; `BITACORA.md:24` | ESTÁTICO | §5.1, §7 |
| PK-10 | **MEDIO** | `radio_interno.txt` sin nombre de cápside, en CWD, mostrado siempre como BMV en la Biblioteca | `capsid.py:153-155`; `library.py:61-68,84-85` | ESTÁTICO | calcular radio de QB en la UI y mirar Biblioteca |
| PK-11 | **BAJO** | PDB resultante sin `TER`/cadenas útiles (sin `add_amber_ter`) → no apto para tLeaP sin pasos extra | `parallel_packer.py:249-274`; cf. `AUDITORIA_MD.md` MD-03 | ESTÁTICO | `grep -c '^TER' summary/best_packing.pdb` |
| PK-12 | **BAJO** | Esfera inscrita definida por un brazo N-terminal flexible; subestima la cavidad real cerca de los ejes 3/5; no documentado | tabla §1.2 (ARG C26 / VAL C27) | ESTÁTICO | — |
| PK-13 | **BAJO** | Excepciones tragadas con fallback a 90 (`capsid.py:163-168`); handles de fichero sin cerrar (`parallel_packer.py:278-285`); metadata sin versión/exit code/tiempo | `capsid.py:163-168`; `parallel_packer.py:278-285,353-362` | ESTÁTICO | — |
| PK-14 | **BAJO** | `/api/health` reporta `pymol` por `which` (binario) cuando el código requiere el módulo Python → el badge no detecta PK-02 | `app.py:50-53`; `capsid.py:10-16` | ESTÁTICO | `python3 -c "from pymol import cmd"` en el intérprete de Flask |

---

## 7. Tests que faltan y que **sí pueden correr en CI** (sin PACKMOL ni PyMOL)

Propuestos, no implementados (la decisión de tocar código es de Lucio):

- **T1 — Radio sin PyMOL (golden real del packing).** Calcular `d_min` y `r_first` con
  NumPy sobre `Input/Capsides/*/capside.pdb` y fijar: BMV 89.47 → 90 (+1) / 88 (−1); CCMV
  92.79; MS2 103.63; QB 105.94 (tolerancia 0.01 Å). Caza regresiones del centrado y de
  la regla de ±1, y documenta la decisión CIENCIA-1 en un número.
- **T2 — Parseo del log con fixtures reales.** Copiar a `tests/fixtures/` los dos logs
  commiteados (PackMan 1 enzima, sustratinaitor) y exigir que `_read_max_violation` devuelva
  `0.0` y `0.0`, no `None`. Hoy ese test **falla** (PK-01); es el test más valioso del
  motor.
- **T3 — Generación del `.inp`.** Llamar a la escritura del input con un `subprocess`
  parcheado (`monkeypatch`) y comprobar: `center` bajo `fixed`, `inside sphere 0 0 0 <R−margen>`
  con el margen de config, `radius` de config, `seed` = `seed_base + i`, `add_amber_ter`.
- **T4 — Semillas y config.** Con `use_random_seeds: false` las semillas de 10 réplicas deben
  ser `seed_base+1 … +10` y las de dos corridas idénticas, iguales.
- **T5 — Consolidación.** `_consolidate_results` con listas sintéticas (incl. réplicas
  fallidas y n=1): `best`, `frac_best`, `stdev` indefinida para n=1, `n_replicas_total`.
- **T6 — Modo degradado explícito.** Con `PYMOL_AVAILABLE=False`, `run_maximum_packing`
  debe **lanzar** (o marcar `degraded=True` en el resultado), nunca devolver `success=True`.
- **T7 (lento, fuera de CI, marcado `@pytest.mark.engine`).** El protocolo de §4.3 con
  `max_workers=1`, `seed_base` fijo, dos corridas → listas idénticas; y comprobar que el
  centroide de las enzimas de `best_packing.pdb` está a < 40 Å del de la cápside.

---

## 8. Qué pedirle a Lucio para cerrar lo que aquí no se pudo

1. Salida de `packmol` (versión) y `echo $?` tras el caso imposible de §3.2 en **su**
   máquina.
2. `python3 -c "from pymol import cmd"` con el intérprete que arranca Flask (§2.3).
3. Cualquier `statistics.json` / `report.txt` / `metadata.json` de experimentos ya corridos
   (están gitignorados): con ellos se puede decir cuántas réplicas alcanzaron `best`, qué
   semillas se usaron y si hubo timeouts (buscando logs truncados sin "Success!").
4. De dónde sale la "condición de 6 enzimas": si es de este motor, con qué `radius`,
   timeout y radio.

---

## 9. Cross-check con las revisiones previas (leídas DESPUÉS de formar el juicio)

### 9.1 Contra `REVISION_MOTORES_hallazgos_sellados.md` (sección "Packing (Studio)")

| Sospecha sellada | Mi juicio |
|---|---|
| Código +1 vs docstring −1 (CIENCIA-1); reporte +1 vs uso −1 | **Coincide**, y añado la resolución geométrica (§2.2): el +1 sobrestima el radio físico, el −1 lo aproxima; la decisión limpia es calcular `d_min − r_vdW` y eliminar el bucle. |
| "Positivo: PACKMOL incluye la cápside como estructura fija → las enzimas quedan acotadas por la pared real aunque la esfera sea aproximada" | **Parcialmente en desacuerdo.** Es cierto **solo si la cápside llega centrada**. `fixed` sin `center` no recentra, y el runner usa el PDB original sin centrar cuando PyMOL falla (PK-02). El "de-riesgo" se convierte en el fallo más grave del motor justo en el modo que `ESTADO.md` describe como habitual. |
| "Réplicas con semillas aleatorias = metodología correcta" | **En desacuerdo en lo que importa.** Semillas aleatorias son aceptables para muestrear, pero (a) la configuración promete semillas fijas y se ignora, (b) no hay manera de reinyectarlas, (c) el timeout hace que ni con semilla fija el resultado sea reproducible entre máquinas (PK-03, PK-04). |
| `exclusion_radius=5.0` es la perilla principal; documentarla | **Coincide y lo preciso**: es radio por átomo, suma de radios → 10 Å / 6 Å efectivos; README/config/packer discrepan (PK-05). |
| Calificación global "sospechas (menores)" | **En desacuerdo.** La pasada sellada no detectó PK-01 (regex muerto → criterio de convergencia inexistente), PK-02 (empaquetado fuera de la cápside), PK-04 (timeout define la capacidad), PK-09 (cero tests) ni PK-10. El packing tiene dos hallazgos críticos, no "menores". |

### 9.2 Contra `AUDITORIA_MD.md` (rama `claude/audit-packman-dynamics-engine-52svym`, commit `d0793e5`)

- Coincidimos en que el **único paso con evidencia de ejecución** en todo el proyecto es el
  empaquetado de 1 enzima en PackMan (log real, 0 violaciones), y en que ese caso es
  determinista porque **no escribe `seed`** y PACKMOL usa 1234567 por defecto. Matizo: eso
  vale para `2Empaquetador_Maximo.py`, **no** para el Studio, que sí escribe una semilla
  aleatoria en cada `.inp`.
- Su medida del radio interno de la cápside de PackMan (89.5 Å) coincide con mi `d_min` de
  BMV (89.47 Å): misma estructura, mismo resultado, dos métodos independientes.
- Su MD-03 (PDB empaquetado sin `TER` → tLeaP encadena todo) aplica también al PDB que
  produce el Studio (PK-11): si el packing debe alimentar la MD, el `.inp` necesita
  `add_amber_ter` y conservar identificadores de cadena.
- Su MD-17 (+1 Å en `1calcula_radio_interno.py`) es el origen de PK-06; aquí se resuelve
  geométricamente.
- Ninguna de las dos revisiones previas examinó el criterio de aceptación de PACKMOL
  (PK-01) ni el modo degradado (PK-02); son hallazgos nuevos de esta pasada.

### 9.3 Qué cambia para JOSS

El envío puede sostenerse en el packing **solo después** de: arreglar PK-01 y PK-02 (dos
cambios pequeños y verificables: regex + `Success!`, `center` + error explícito sin PyMOL),
leer la config que ya existe (PK-03, PK-04, PK-05: semilla, timeout, margen), reportar la
fracción de réplicas que alcanzan `best`, y añadir T1–T5 a CI para que la palabra "golden
test" sea cierta para este motor. Nada de ello reescribe ciencia; todo ello es hacer que el
código haga lo que la documentación ya afirma.
