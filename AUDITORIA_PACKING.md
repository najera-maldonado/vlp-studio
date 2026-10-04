# Auditoría científica independiente — motor de PACKING (`nanocapsule-mvp`)

> **Encargo:** auditoría desde cero del motor de la puerta 2 «Dentro» (radio interno con
> PyMOL + empaquetamiento con PACKMOL + validación estadística por réplicas), con el nivel
> de exigencia de un pilar único: una auditoría paralela concluyó que el motor de dinámica
> molecular no es confiable, así que el packing es hoy el soporte del envío a JOSS.
>
> **Cumplimiento de la regla anti-sesgo:** este informe se redactó **antes** de abrir
> `REVISION_MOTORES_hallazgos_sellados.md` y `AUDITORIA_MD.md`. El cross-check con esos
> documentos está al final (§7), después del juicio propio y del plan.
>
> **Entorno:** no hay PACKMOL ni PyMOL en esta máquina. Cada hallazgo lleva etiqueta
> **[estático]** (deducible del código y de los artefactos commiteados) o
> **[requiere correr]** (necesita los motores reales). Un tercer caso, **[verificado con
> doble]**, marca lo que sí ejecuté sustituyendo PACKMOL por un doble de prueba que emite
> las cadenas de texto reales de PACKMOL: el motor Python corrió de verdad, el que no corrió
> es PACKMOL.
>
> **No se modificó código.** `git status` queda limpio.
>
> Fecha: 2026-10-04 · Auditor: instancia independiente · Rama: `claude/audit-packing-engine-wwph45`

---

## 1. Veredicto

**El motor de packing no está en condiciones de sostener una afirmación científica hoy, y
el problema no es de precisión sino de validez: el criterio que decide cuántas enzimas
caben no mide el empaquetamiento.**

Tres hechos encadenados, los tres verificados:

1. El criterio primario de aceptación busca en el log de PACKMOL una frase
   (`Maximum distance violation:`) **que PACKMOL no escribe nunca**. Lo comprobé contra los
   dos logs reales de PACKMOL que hay commiteados en el repo (versiones 20.14.3 y 21.0.1):
   cero coincidencias.
2. Al no encontrarla, el código cae a un criterio de reserva: «el PDB de salida tiene
   ≥ 10 000 líneas ATOM/HETATM». **Las cápsides de la biblioteca tienen entre 168 480 y
   216 780 átomos**, así que la cápside sola satisface el umbral. El criterio no puede
   observar las enzimas.
3. Con esos dos, lo único que separa «cabe» de «no cabe» es el código de salida del proceso.
   Si PACKMOL devuelve 0 al terminar sin empaquetado perfecto, la capacidad reportada es el
   techo del bucle de búsqueda (`while n <= 100`), es decir **una constante del código**.

Lo demostré ejecutando el motor real contra un PACKMOL de prueba que reproduce el peor caso
honesto: termina con `ENDED WITHOUT PERFECT PACKING`, reporta una violación de 7,43 Å y
**coloca cero enzimas**. El motor informó:

| Magnitud reportada | Valor |
|---|---|
| Capacidad máxima | 100 enzimas |
| Media | 100 |
| Desviación estándar | 0,00 |
| Réplicas exitosas | 2 / 2 |
| Átomos de enzima en `best_packing.pdb` | 0 |

La desviación estándar de cero es lo más peligroso del cuadro: un criterio que acepta todo
hace que todas las réplicas devuelvan el mismo número y **fabrica la apariencia de
convergencia perfecta**.

Sobre las otras tres preguntas del encargo:

- **El signo del margen ±1 Å (CIENCIA-1) tiene respuesta, y es «restar»** — con una
  justificación cuantitativa que doy en P-08 y que no está escrita en `ESTADO.md`. Pero es
  una decisión de segundo orden: el radio interno está fijado por **300 átomos de 216 780**
  (0,14 %), la punta de una cadena lateral de arginina, y la incertidumbre real del concepto
  «radio interno» es de 7 a 13 Å, no de 1 Å (P-09).
- **La validación estadística por réplicas no es reproducible**: la ruta de producción nunca
  pasa semilla, usa el generador global de Python sin sembrar, y las dos claves del YAML que
  existen para esto (`engines.packmol.seed_base`, `use_random_seeds`) no las lee nadie. Dos
  invocaciones idénticas dieron semillas distintas (P-05). Esto contradice directamente
  `PENDIENTES.md` §15, que describe el packing como «geométrico y determinista (semilla
  fija, golden test)».
- **`tests/test_golden_science.py` no prueba el motor de packing.** Prueba
  `substrate_section`, que pertenece a la puerta 1 (poro) — su propio docstring lo dice. La
  cobertura del packing es cero: ni el radio, ni la generación del input, ni el criterio de
  aceptación, ni la estadística, ni las semillas. Y sobre la magnitud que sí congela, congela
  el lado equivocado: mide semiejes de **centros atómicos**, sin radios de van der Waals,
  con un error de factor ×1,8 a ×2,2 (G-03).

**Qué sí está bien** y no debe tocarse en la reparación: la arquitectura en capas
(`app.py` → `services/` → `core/`) es correcta y hace el motor auditable; el centrado de
cápside y enzima en el origen antes de llamar a PACKMOL es correcto y necesario; el input de
PACKMOL que se genera es sintácticamente válido y equivalente al del pipeline original de la
tesis; la paralelización por réplicas con `ProcessPoolExecutor` es sólida; la restricción
`inside sphere` está bien elegida para el problema y restringe todos los átomos, lo cual
verifiqué en el único output real que hay (§2.3). El trabajo de reparación es sobre el
criterio y la estadística, no sobre el diseño.

---

## 1b. Índice de hallazgos

| ID | Severidad | Etiqueta | Hallazgo | § |
|---|---|---|---|---|
| **P-01** | **BLOQUEANTE** | estático | La regex del criterio de aceptación busca una frase que PACKMOL no escribe nunca | §4 |
| **P-02** | **BLOQUEANTE** | verificado con doble | El criterio de reserva (≥10 000 líneas) lo satisface la cápside sola | §4 |
| **P-03** | **BLOQUEANTE** cond. | requiere correr | Solo queda el código de salida; si es 0, la capacidad es el techo del bucle | §4 |
| P-04 | ALTA | verificado con doble | `n_packed` no se mide: es el N que se pidió | §4 |
| P-05 | ALTA | verificado con doble | Sin semilla en producción; `seed_base` y `use_random_seeds` son claves muertas | §4 |
| P-06 | ALTA | estático | `best` es un máximo sobre réplicas publicado como medida | §4 |
| P-07 | MEDIA-ALTA | verificado con doble | El criterio roto produce σ = 0,00 y aparenta convergencia | §4 |
| P-08 | ALTA | estático | **CIENCIA-1: el veredicto es «restar»**, con holgura mínima de 0,5 Å vs 2,5 Å | §3 |
| P-09 | ALTA | estático | El radio interno lo fija el 0,14 % de los átomos (una Arg); incertidumbre 7–13 Å | §3 |
| P-10 | MEDIA | estático | El pseudoátomo expansivo es decorativo; el cálculo es `ceil(min\|r\| − 0,5)` | §3 |
| P-11 | ALTA | estático | El valor de reserva de 90 Å es silencioso; P22 devolverá un valor falso | §3 |
| P-12 | MEDIA | estático | `collision_margin` hardcodeado, divergente de la config | §4 |
| P-13 | MEDIA | requiere correr | La capacidad es de primer orden una función de `radius 5.0` | §4 |
| P-14 | MEDIA | estático | Cotas geométricas: el 100 reportado está fuera de toda cota física | §4 |
| P-16 | MEDIA | estático | Experimentos sin timestamp: se sobrescriben en silencio | §4 |
| P-17 | MEDIA | estático | El motor muta `Input/`; 3 de 4 enzimas ya fueron sobrescritas, GCase sin respaldo | §4 |
| P-18 | MEDIA | estático | `radio_interno.txt` es global y se etiqueta como BMV | §3 |
| P-19 | MEDIA | estático | Timeout de 90 s hardcodeado: la capacidad depende del hardware | §4 |
| P-20 | BAJA | estático | Ningún umbral coincide entre YAML, código, README y CLAUDE.md | §4 |
| P-21 | BAJA | estático | Decenas de GB de PDB intermedios por experimento, sin limpieza | §4 |
| P-22 | ALTA | estático | El PDB entregado pierde los 180 `TER` y no es consumible por la puerta 4 | §4 |
| **G-01** | ALTA | estático | `test_golden_science.py` **no cubre el motor de packing**: cobertura cero | §5 |
| G-02 | MEDIA | verificado corriendo | Su tolerancia de ±0,2 Å está 100 % sin usar (variación real: 0,000) | §5 |
| G-03 | ALTA | verificado corriendo | Congela semiejes de centros atómicos, sin vdW: error de ×1,8 a ×2,2 | §5 |

---

## 2. Evidencia de ejecución existente en el repo

Antes de auditar el código conviene fijar qué resultados reales existen, porque acota lo que
el proyecto puede afirmar.

### 2.1 Hay exactamente una corrida real de PACKMOL de cápside + enzima

`PackMan.v.1.2/archivos_dm_cg/empaquetador/log_packmol_1enzimas_20260324_212620.txt`,
del 2026-03-24, PACKMOL 20.14.3, con **n = 1 enzima**. Y su log dice:

```
  Initial approximation is a solution. Nothing to do.
```

PACKMOL no optimizó nada: la primera posición aleatoria ya cumplía las restricciones. No es
un empaquetamiento, es una colocación.

Los PDB de entrada de esa corrida son **bit a bit los mismos** que los del Studio
(`md5sum` coincide): `capside.pdb` = `Input/Capsides/BMV_IJS9/capside.pdb`,
`enzima.pdb` = `Input/Enzimas/GCase_1OGS/enzima.pdb`, y
`capside_recentrada.pdb` / `enzima_recentrada.pdb` = los `*_centered.pdb` del Studio. Es la
misma ciencia, confirmado.

**No existe en el repo ninguna evidencia de una corrida multi-réplica, ni de N > 1, ni de la
«condición de 6 enzimas» que `PENDIENTES.md` fija como objetivo.** El `README.md` de la raíz
describe la puerta 2 como «✅ real (empaquetamiento multi-réplica)». Esa afirmación no tiene
respaldo commiteado. **[estático]**

### 2.2 El único resultado real no está limitado por el empaquetamiento

Medí la geometría del PDB de salida de esa corrida (220 753 líneas atómicas = 216 780 de
cápside + 3 973 de enzima, consistente):

| Magnitud | Valor |
|---|---|
| Centroide de la enzima | 47,0 Å del centro |
| Átomo de enzima más alejado del centro | 74,37 Å (esfera pedida: 88 Å) |
| Distancia mínima enzima–cápside | 22,0 Å |
| Holgura radial a la pared interna | 15,1 Å |

Con una sola copia y 22 Å de separación, la corrida no ejerce ninguna de las restricciones
estéricas que el motor pretende evaluar. **[estático]**

### 2.3 Confirmación útil: `inside sphere` restringe todos los átomos

El dato anterior sirve de verificación independiente de la semántica de la restricción: el
centroide está a 47,0 Å y el radio circunscrito de GCase es 42,8 Å (47,0 + 42,8 = 89,8 > 88),
pero el átomo más alejado del centro está a 74,37 Å ≤ 88. Es decir, PACKMOL colocó la
molécula de modo que **todos** sus átomos caen dentro de la esfera, no solo su centro. La
restricción está bien entendida en el código. **[estático]**

---

## 3. Radio interno de la cápside (PyMOL) — CIENCIA-1

`src/core/capsid.py:53-168`.

### P-08 — El signo del margen: veredicto «restar», con justificación cuantitativa · ALTA · [estático]

El bucle (`capsid.py:125-137`) recorre `r = 5, 6, … 199` y se detiene en el primer `r` tal que
algún átomo de la cápside esté `within r + 0.5` del pseudoátomo del origen. Como
`within` en PyMOL mide **centro a centro** (ver P-10), eso equivale exactamente a

```
r_c = ceil(r_min − 0.5)        donde r_min = min |x_átomo − centroide|
```

con una rejilla de 1 Å. De ahí, `r_c ∈ [r_min − 0.5, r_min + 0.5)`.

El radio que llega a PACKMOL no es `R_int` sino `R_s = R_int − 2` (el `collision_margin`
hardcodeado, P-12). Sustituyendo:

| Variante | Radio de la esfera de packing | Holgura garantizada frente a `r_min` |
|---|---|---|
| Código actual (`+1`) | `R_s = r_c − 1 ∈ [r_min − 1,5 , r_min − 0,5)` | **tan poco como 0,5 Å** |
| Docstring y CLAUDE.md (`−1`) | `R_s = r_c − 3 ∈ [r_min − 3,5 , r_min − 2,5)` | **≥ 2,5 Å** |

Una holgura de 0,5 Å entre el límite donde se permite colocar un centro atómico de la enzima
y el centro del átomo más interno de la cápside está por debajo de cualquier radio de van der
Waals (C ≈ 1,7 Å; N ≈ 1,55 Å): la esfera, por sí sola, **autoriza un solapamiento duro**. Con
`−1` la holgura mínima (2,5 Å) sigue siendo inferior al contacto vdW (≈ 3,2–3,6 Å) pero ya es
del orden correcto.

Para BMV concretamente: `r_min` = 89,47 Å, `r_c` = 89, y `R_s` vale 88 Å con `+1` frente a
86 Å con `−1`; el volumen disponible cambia un 7 %.

**Veredicto: restar, como dice el docstring.** Es la intención documentada, es la única de
las dos que no autoriza un solapamiento en el peor caso de la rejilla, y coincide con la
recomendación que ya figura en `ESTADO.md`. Lo que falta en `ESTADO.md` es que la decisión es
defendible por una razón concreta y no por prudencia genérica, y que **no es ahí donde está
el problema** — ver P-09.

Nota: lo que de verdad impide los choques con la pared hoy no es la esfera, es la restricción
de distancia propia de PACKMOL (`tolerance` / `radius`, P-13). Conviene decirlo explícitamente
en el código y en el paper, porque cambia qué parámetro hay que justificar.

### P-09 — El «radio interno» lo define una sola cadena lateral · ALTA · [estático]

Calculé la distribución radial de los átomos de cada cápside respecto a su centroide. Para
BMV_IJS9 (216 780 átomos):

| Percentil del radio atómico | Valor |
|---|---|
| mínimo (0,0005 %) | 89,47 Å |
| 0,1 % | 90,8 Å |
| 1 % | 96,6 Å |
| 5 % | 102,1 Å |

Dentro de 2 Å del mínimo hay **300 átomos de 216 780 (0,14 %)**, y el átomo más interno es
el nitrógeno NH1 del guanidinio de Arg26 de la cadena C, repetido por la simetría icosaédrica.
Es decir: el «radio interno» de la cápside está fijado por la punta de una cadena lateral
flexible de arginina, no por la pared proteica. La pared, en términos de densidad, empieza
unos 7 Å más afuera.

Las cuatro cápsides muestran el mismo patrón:

| Cápside | r_min | 1 % | 5 % |
|---|---|---|---|
| BMV_IJS9 | 89,47 | 96,6 | 102,1 |
| CCMV_1CWP | 92,79 | 97,9 | 102,8 |
| MS2_2MS2 | 103,63 | 107,3 | 110,9 |
| QB_1QBE | 105,94 | 111,5 | 115,8 |

**Consecuencia para el encargo:** discutir el signo de ±1 Å mientras la definición del radio
tiene una incertidumbre conceptual de 7 a 13 Å es optimizar dentro del ruido. La reparación
real es definir el radio interno con un criterio explícito, reportado y defendible —un
percentil de la distribución radial, o una superficie accesible a una sonda del tamaño del
cargo— **y usar radios de van der Waals**, que hoy no entran en el cálculo en ningún punto.

### P-10 — El pseudoátomo expansivo es decorativo · MEDIA · [estático]

`cmd.pseudoatom("centro", pos=[0,0,0], vdw=1.0)`, luego en cada iteración
`cmd.alter("centro", f"vdw={r}")`, `cmd.rebuild()`, `cmd.set("sphere_scale", ...)`,
`cmd.show("spheres", ...)`, `cmd.color("red", ...)`.

Nada de eso afecta al resultado: `within X of sel` en PyMOL es distancia entre centros
atómicos y no consulta el radio de van der Waals (el operador que sí lo haría es `gap`). El
`vdw=r` y el `sphere_scale` son estado de representación. Igualmente, `byres` expande la
selección a residuos completos, pero como solo se compara `count_atoms > 0`, no cambia el
valor.

Por tanto todo el bloque equivale a `ceil(min|r| − 0.5)`. Lo reproduje numéricamente sin
PyMOL para las cuatro cápsides; para BMV da `r_c` = 89, y `89 + 1 = 90`, exactamente el
contenido del `radio_interno.txt` commiteado en el pipeline original. La emulación es
consistente con el artefacto real (con la salvedad de P-11: 90 es también el valor de reserva).

Dos consecuencias: (a) PyMOL es una dependencia pesada —y la razón por la que este cálculo no
está en CI— para un `min` sobre coordenadas que numpy hace en tres líneas; (b) la rejilla de
1 Å introduce un error del mismo orden que el margen que CIENCIA-1 discute.

La confirmación definitiva de la semántica de `within` **[requiere correr]** PyMOL, pero el
sentido está respaldado por el artefacto commiteado.

### P-11 — El valor de reserva de 90 Å es silencioso e indistinguible · ALTA · [estático]

Tres caminos distintos devuelven 90,0 Å sin que el llamante pueda distinguirlos de un cálculo
real:

1. PyMOL no está instalado (`capsid.py:72-77`).
2. El bucle termina sin colisión porque `range(5, 200)` se agota, es decir `r_min > 199,5 Å`
   (`capsid.py:139-142`).
3. Cualquier excepción dentro del bloque (`capsid.py:163-168`), incluido un PDB corrupto.

El endpoint `/api/capsid/radius` devuelve en los tres casos
`{"internal_radius": 90.0, "message": "Radio interno calculado: 90.0 Å"}`.

El caso 2 no es hipotético: el `.gitignore` declara la cápside **P22 (5UU5)** como estructura
real del proyecto (se excluye por el límite de 100 MB de GitHub y se redescarga con
`scripts/fetch_data.sh`). P22 es un orden de magnitud más grande que BMV; su radio interno
supera holgadamente los 200 Å, de modo que el bucle no encontrará colisión y el motor
devolverá 90 Å **para una cápside cuya cavidad es varias veces mayor**, en silencio.

Y hay una coincidencia desafortunada que arruina la trazabilidad de todo lo anterior: para
BMV el valor correcto (89 + 1 = 90,0) **es exactamente igual** al valor de reserva. Ningún
resultado commiteado permite saber si se calculó o si se tomó por defecto. `ESTADO.md` lo
admite de pasada («el radio casi siempre es el fallback 90 Å»), lo cual significa que
CIENCIA-1 nunca ha sido observable en ningún número publicado del proyecto.

### P-18 — `radio_interno.txt` es global y se atribuye a BMV por el nombre · MEDIA · [estático]

`capsid.py:153` escribe `radio_interno.txt` con **ruta relativa al directorio de trabajo**.
`services/library.py:63` lo lee de `paths.PROJECT_ROOT / "radio_interno.txt"` y lo asigna así:

```python
"radius": cached_radius if name.startswith("BMV") else None,
```

Calcular el radio de CCMV, MS2 o QB desde la raíz del proyecto sobrescribe ese archivo, y la
Biblioteca mostrará ese valor **etiquetado como BMV**. Es un error de etiquetado científico en
la interfaz, no solo de cacheo, y la coincidencia de P-11 lo hace difícil de notar.

---

## 4. PACKMOL: restricciones, criterio de convergencia y capacidad máxima

`src/packing/parallel_packer.py`, `src/core/experiment_runner.py`.

El input que genera el motor (capturado ejecutándolo, réplica 1, n = 1):

```
tolerance 2.0
output .../packed_1_attempt0.pdb
seed 812005
filetype pdb

structure .../capside.pdb
  number 1
  fixed 0. 0. 0. 0. 0. 0.
end structure

structure .../enzima.pdb
  number 1
  inside sphere 0. 0. 0. 88.0
  radius 5.0
end structure
```

Sintácticamente correcto y equivalente al del pipeline original de la tesis. El problema está
en cómo se interpreta lo que PACKMOL devuelve.

### P-01 — El criterio primario de aceptación no puede dispararse nunca · BLOQUEANTE · [estático]

`parallel_packer.py:34-36` y `:191-193`:

```python
re.compile(r"Maximum\s+distance\s+violation:\s*([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)")
```

PACKMOL no escribe esa frase. Las cadenas que sí escribe, extraídas de los dos logs reales
commiteados en el repo:

```
  Maximum violation of target distance:     3.970194
  Maximum violation of the constraints: .12571E-01
  Maximum violation of the restraints:    7.7660690978852759E-003
  Max. constraint violation:    0.0000000000000000
```

El orden de las palabras es «violation of target distance», no «distance violation». Ejecuté
la regex del motor contra ambos logs (`log_packmol_1enzimas_*.txt`, PACKMOL 20.14.3, y
`sustratinaitor/3_empaquetado_packmol/packmol_run.log`, PACKMOL 21.0.1): **ninguna
coincidencia en ninguno de los dos**. El fallo viene heredado del script original
(`2Empaquetador_Maximo.py:87`), con la misma regex, así que afecta por igual a los resultados
de la tesis producidos con ese pipeline.

Por tanto `max_violation_threshold` —el parámetro que el YAML, el README y CLAUDE.md
presentan como el criterio de calidad del empaquetamiento— **no tiene ningún efecto**.

### P-02 — El criterio de reserva es ciego a las enzimas · BLOQUEANTE · [verificado con doble]

Al no haber violación, `parallel_packer.py:300-310` cae al conteo de líneas:

```python
total_lines = count_atomic_lines(output_pdb)
if total_lines >= min_lines_threshold:   # 10 000
```

Las cápsides de la biblioteca tienen 168 480 (QB), 173 700 (MS2), 214 440 (CCMV) y 216 780
(BMV) átomos. **El umbral se satisface con la cápside sola**, es decir con cero enzimas
colocadas. El criterio no mide nada del empaquetamiento; mide que el archivo exista.

Ejecuté el motor real (`ParallelPacker.run_parallel_replicas`) sustituyendo PACKMOL por un
doble que reproduce el peor caso honesto: emite las cadenas reales de PACKMOL, informa
`ENDED WITHOUT PERFECT PACKING` con una violación de 7,43 Å, escribe el `<output>_FORCED` y
deja en `<output>` un PDB que contiene **solo la cápside**. Resultado del motor:
`success=True`, `best=100`, `mean=100`, `stdev=0.00`, `2/2` réplicas exitosas, y
`summary/best_packing.pdb` con exactamente las líneas de la cápside y ningún átomo de enzima.

Que PACKMOL deje un archivo de salida aunque el empaquetado no sea perfecto no es una
suposición: los logs reales lo muestran escribiendo el punto actual durante la optimización
(`Current point written to file:`, `Current structure written to file:`).

### P-03 — Lo único que queda en pie es el código de salida · BLOQUEANTE condicional · [requiere correr]

Tras P-01 y P-02, la única discriminación real es `result.returncode == 0`
(`parallel_packer.py:287`). Hay dos escenarios y la validez de todo el número de capacidad
depende de cuál sea el verdadero:

| Código de salida de PACKMOL sin empaquetado perfecto | Comportamiento del motor (medido con el doble) |
|---|---|
| 0 | Acepta todo. `best` = **100**, el techo de `while n <= 100`. La capacidad es una constante del código. |
| ≠ 0 (p. ej. 173) | La regla de 3 fallos consecutivos detiene la búsqueda. `best` = último n aceptado (4 en mi prueba con fallo a partir de n = 5). |

**Esta es la primera medición que hay que hacer con PACKMOL real, y es de media hora:**
correr un caso deliberadamente imposible (p. ej. 200 copias de GCase en una esfera de 88 Å) y
leer `echo $?`. No pude resolverlo aquí de forma estática: el código fuente de PACKMOL no es
accesible desde este entorno (las URLs de `raw.githubusercontent.com` devuelven 404 para las
rutas probadas y `m3g.github.io`, donde vive la guía de usuario, está bloqueado por el proxy
de red de la sesión).

Importa además que, incluso en el escenario favorable, el motor acepta el archivo que PACKMOL
dejó escrito, que durante los bucles es el «punto actual» y no necesariamente la solución
final; y que no comprueba la existencia de `<output>_FORCED`, que es la señal explícita de
PACKMOL de que el empaquetado no convergió.

### P-04 — `n_packed` no se mide, se asume · ALTA · [verificado con doble]

En ningún punto se cuenta cuántas copias de la enzima hay en el PDB aceptado. `n_packed` es
el `n` que se le pidió a PACKMOL. Bastaría comparar las líneas atómicas del output contra
`n_átomos_cápside + n × n_átomos_enzima` —el script original de la tesis ya calculaba
`lineas_por_enzima` para separar las copias, así que el dato está a mano— para que P-02 fuera
inofensivo. No se hace.

### P-05 — La ruta de producción no es reproducible · ALTA · [verificado con doble]

`experiment_runner.py:160-170` llama a `run_parallel_replicas` **sin pasar `seed_base`**. El
parámetro vale `None` por defecto, y entonces `parallel_packer.py:118` hace
`random.randint(1, 1000000)` sobre el generador global de Python, que nunca se siembra.

Dos invocaciones idénticas del motor dieron semillas distintas:

```
run D1: seeds = [775857, 905539]
run D2: seeds = [847944, 856059]
```

Pasando `seed_base=1234567` explícitamente sí se obtiene `[1234568, 1234569]`, determinista.
La capacidad existe; nadie la usa.

En honor a la precisión: la semilla de cada réplica **sí se registra** en
`replica_N/metadata.json` (`parallel_packer.py:357`), y las de los reintentos son derivables
(`seed + intento × 1000`), así que una corrida pasada se puede replicar *a posteriori* si se
conservan esos archivos. Lo que no se puede es declarar la semilla de antemano, reproducir
desde la configuración, ni —por P-16— confiar en que los `metadata.json` de un experimento no
hayan sido sobrescritos por el siguiente.

Y las dos claves del YAML que están ahí precisamente para esto:

```yaml
engines:
  packmol:
    seed_base: 1234567
    use_random_seeds: false
```

**no las lee ningún módulo** (verificado con `grep` sobre todo `src/`). Son claves muertas que
documentan un comportamiento que no existe. Lo mismo ocurre con `engines.packmol.timeout`
(P-19).

Esto desmonta la premisa que `PENDIENTES.md` §15-16 y `BITACORA.md` §24-25 usan para declarar
el packing «terreno firme»: «el packing es geométrico y determinista (semilla fija, golden
test) → más confiable que la MD». Ninguna de las dos mitades se sostiene: no hay semilla fija
en la ruta de producción y el golden test no cubre el packing (G-01).

### P-13 — La capacidad es, de primer orden, una función de `radius 5.0` · MEDIA · [requiere correr]

En PACKMOL, el `radius` de un bloque `structure` fija el radio **por átomo** de esa estructura,
y la distancia mínima exigida entre dos átomos es la suma de sus radios (el `tolerance` define
el radio por defecto, `tolerance/2`). Bajo esa lectura, el input del motor exige:

- entre átomos de dos copias de la enzima: **≥ 10 Å** (5,0 + 5,0);
- entre un átomo de la enzima y uno de la cápside: **≥ 6 Å** (5,0 + 1,0).

Un contacto de van der Waals real entre átomos pesados es ≈ 3,2–3,6 Å. Exigir 10 Å de
separación entre cualquier par de átomos de dos proteínas globulares es un criterio estérico
muy conservador: equivale a inflar cada enzima con una coraza de 5 Å. La capacidad reportada
es entonces, en primer orden, **una función de este parámetro elegido a mano**, no una medida
de cuántas enzimas caben.

El propio `README.txt` del pipeline original lo dice sin rodeos: «`radius` […] controla la
separación entre copias de la enzima; bajarlo aumenta N pero arriesga solapamientos poco
realistas». Es decir, el número titular es una perilla. (De paso: ese README afirma que el
default de `radius` en PACKMOL es 5 Å; el default es `tolerance/2` = 1,0 Å. El 5,0 es una
elección del proyecto, no un default heredado, y como tal hay que justificarla.)

Marco esto como **[requiere correr]** porque no pude confirmar la semántica exacta de suma de
radios desde este entorno (guía de usuario de PACKMOL inaccesible, ver P-03). Bajo cualquiera
de las lecturas posibles la conclusión práctica no cambia: hace falta un barrido de
sensibilidad `N_max(radius)` antes de publicar un número.

### P-14 — Cotas geométricas para contrastar cualquier número futuro · MEDIA · [estático]

Para que la reparación tenga con qué comparar, calculé las cotas que acotan el resultado
esperable. Con `inside sphere 88` (BMV, variante actual) y el radio circunscrito de cada
enzima medido sobre el PDB real:

| Enzima | R circunscrito | Centros admisibles | Cota conservadora (empaque aleatorio denso de esferas circunscritas, φ = 0,64) |
|---|---|---|---|
| EGFP (4EUL) | 29,7 Å | r ≤ 58,3 Å | ≈ 17 copias |
| GCase (1OGS) | 42,8 Å | r ≤ 45,2 Å | ≈ 5,6 copias |
| Luciferasa (1LCI) | 46,5 Å | r ≤ 41,5 Å | ≈ 4,3 copias |
| Fosfatasa alcalina (1ED8) | 51,5 Å | r ≤ 36,5 Å | ≈ 3,2 copias |

La cota de esferas circunscritas es pesimista (las proteínas no son esferas y se entrelazan);
una cota optimista por volumen, usando el volumen de exclusión real de GCase
(44 056 Å³, del propio `vdw_volumes_results.txt`) dilatado por los 5 Å de `radius`, da del
orden de 20 copias. El valor verdadero de GCase en BMV debería caer entre ~6 y ~20.

Dos lecturas: la «condición de 6 enzimas» que `PENDIENTES.md` fija como objetivo es
geométricamente razonable para GCase; y el **100 que el motor reporta hoy está fuera de
cualquier cota física**, lo que confirma por una vía independiente que es un artefacto del
techo del bucle.

### P-06 — «best» es un estadístico de valor extremo publicado como si fuera una medida · ALTA · [estático]

`_consolidate_results` (`parallel_packer.py:370-449`) reporta `best = max(n_packed_list)`
junto a `mean`, `median` y `stdev`, y `app.py:307` lo expone como `best_result`, que el
frontend muestra como el número titular (`packing.js:65`: «Packing real OK: N enzimas»).

El máximo sobre réplicas crece monotónicamente en esperanza con el número de réplicas. Como
`n_replicas` es un control de la interfaz (`packing.js:58`), **el número titular depende de
cuántas réplicas pidió el usuario** y no es comparable entre corridas. No hay intervalo de
confianza, ni test de convergencia (¿se estabiliza `best` al aumentar las réplicas?), ni
declaración del `n_replicas` junto al valor.

Para una publicación hay que elegir una cantidad y definirla: o la mediana con su IQR sobre un
`n_replicas` fijo y declarado, o el máximo etiquetado como tal con su `n_replicas`. Hoy se
publican las dos cosas mezcladas.

### P-07 — El criterio roto fabrica precisión aparente · MEDIA-ALTA · [verificado con doble]

Consecuencia conjunta de P-02 y P-06 que merece nombre propio porque es el modo de fallo más
engañoso: cuando el criterio acepta todo, todas las réplicas devuelven el techo, la desviación
estándar sale 0,00 y la interfaz muestra «σ = 0,00» con «7/7 réplicas». Un lector —un revisor
de JOSS, un comité de tesis— lee eso como un método que converge perfectamente. Es lo
contrario: es la firma de que el criterio no discrimina.

Además, `stdev` vale 0 también cuando hay una sola réplica exitosa
(`parallel_packer.py:417`), y se reporta como un 0 real.

### P-12 — `collision_margin` hardcodeado, divergente de la config · MEDIA · [estático]

`parallel_packer.py:268`:

```python
collision_margin = 2.0  # margen por defecto como en original
packing_radius = internal_radius - collision_margin
```

ignora `packing.collision_margin` del YAML. Mientras tanto
`Capsid.get_geometric_properties()` (`capsid.py:238-240`) **sí** calcula un `packing_radius`
leyendo la config — pero ese método no participa en la ruta de packing: es código muerto con
una semántica divergente. Dos definiciones del mismo parámetro científico en el mismo
repositorio, una viva y hardcodeada, otra muerta y configurable.

### P-19 — Timeout hardcodeado que convierte la capacidad en una medida del hardware · MEDIA · [estático]

`parallel_packer.py:283`: `timeout=90`, ignorando `engines.packmol.timeout: 300`. Con 216 780
átomos fijos y N creciente, PACKMOL se vuelve más lento cuanto más difícil es el caso, así que
un timeout corto se traduce en «no cabe» justo donde la medición importa. El resultado
dependería de la máquina.

Además `except (subprocess.TimeoutExpired, Exception)` (`:312`) es equivalente a
`except Exception` y silencia cualquier fallo como «este N no cabe»; y los descriptores que se
pasan al subproceso (`stdin=open(input_file)`, `stdout=open(log_file, "w")`, `:280-281`) no se
cierran, lo que con cientos de invocaciones por réplica puede agotar los descriptores del
proceso.

### P-16 — Provenance: los experimentos se sobrescriben en silencio · MEDIA · [estático]

`ExperimentManager.setup_experiment` (`experiment_manager.py:69`) usa
`Output/<cápside>/<enzima>` **sin timestamp**: repetir un experimento sobrescribe el anterior,
incluido `summary/statistics.json` y `best_packing.pdb`. CLAUDE.md promete
`Output/Experiments/[timestamp]/replica_[N]/`, que es lo correcto y no es lo que hace el
código.

También: `self.n_replicas = 7` está hardcodeado (`:47`) mientras el YAML dice 10, así que se
crean 7 carpetas y el packer crea el resto o deja huérfanas las sobrantes; y
`consolidate_results` / `save_replica_result` son código muerto (el packer hace su propia
consolidación), con una lógica de selección de la mejor réplica distinta de la que sí corre.

### P-17 — El motor muta su propia biblioteca de entrada · MEDIA · [estático]

`Capsid.center_structure` y `Cargo.center_structure` escriben `<stem>_centered.pdb` **junto al
archivo de entrada**, es decir dentro de `Input/`, que está versionado. Correr un experimento
ensucia el repositorio.

Peor: el estado actual de `Input/Enzimas/` muestra que esto ya ocurrió de forma desigual. Medí
los centroides:

| Enzima | centroide de `enzima.pdb` | ¿hay `.pdb.original`? |
|---|---|---|
| Alkaline_Phosphatase_1ED8 | (0, 0, 0) | sí |
| EGFP_4EUL | (0, 0, 0) | sí |
| Luciferasa_1LCI | (0, 0, 0) | sí |
| **GCase_1OGS** | **(210,2, 192,4, 206,3)** | **no** |

Tres de las cuatro entradas canónicas fueron sobrescritas por un paso de centrado, con copia
de respaldo; la cuarta —precisamente la enzima terapéutica del caso de uso— no lo fue y no
tiene respaldo. La biblioteca de entrada es un estado parcialmente derivado, no un conjunto de
datos primario, y nada en el repo lo documenta.

### P-21 — Volumen de salida sin control · BAJA · [estático]

Cada réplica escribe `packed_{n}_attempt{a}.pdb` para cada N probado, y cada uno incluye la
cápside completa (~18 MB para BMV). Con el techo de 100, dos intentos y 10 réplicas, el orden
de magnitud por experimento es de decenas de GB. No hay limpieza, y `io.cleanup_temp: true`
del YAML tampoco se lee.

### P-22 — El PDB que entrega el motor no es consumible aguas abajo · ALTA · [estático]

El entregable de la puerta 2 es la entrada de la puerta 4. Medí qué le pasa a la segmentación
en cadenas de la cápside a lo largo del pipeline, sobre los archivos reales commiteados:

| Archivo | Registros `TER` | Átomos |
|---|---|---|
| `capside.pdb` (entrada, del PDB) | **180** | 216 780 |
| `capside_recentrada.pdb` (tras el centrado con PyMOL) | **3** | 216 780 |
| `capside_1enzimas_*.pdb` (salida de PACKMOL) | **0** | 220 753 |

Las 180 subunidades de la cápside entran separadas por `TER` y salen fundidas. La primera
pérdida (180 → 3) **la causa el propio motor de packing** en su paso de centrado
(`Capsid.center_structure` → `cmd.save`), antes de que PACKMOL intervenga; la segunda (3 → 0)
la causa PACKMOL. Sin `TER`, cualquier consumidor que construya topología —tLeaP en la puerta
4— encadena residuos consecutivos a través de los límites de subunidad y crea enlaces
covalentes espurios entre proteínas distintas.

Dos problemas más del mismo entregable:

- **Los números de serie pasan a hexadecimal.** PACKMOL agota el campo de 5 caracteres en
  99 999 y continúa `186A0`, `186A1`… (`0x186A0` = 100 000). Con cápsides de 170 000 a 217 000
  átomos, **más de la mitad de cada archivo de salida lleva seriales no estándar**. El propio
  Studio sobrevive porque parsea por columnas fijas (verifiqué: `_count_atoms_chains` cuenta
  los 220 753 átomos correctamente), pero cualquier herramienta que lea el serial como entero
  falla.
- **Las copias de la enzima no son separables por cadena.** En la salida real todos los átomos
  de la enzima llevan cadena `A`, la misma que una cadena de la cápside. El script original
  resolvía esto con aritmética de líneas (`extraer_enzimas_individuales`), que asume que la
  cápside va primero y que todas las copias tienen exactamente el mismo número de líneas. El
  Studio no hace ni eso. Nótese la inversión: la **vista previa ilustrativa** sí asigna un ID
  de cadena distinto a cada copia (`services/packing.py:123-130`), mientras el resultado real
  no — el camino ilustrativo produce un archivo más usable que el científico.

Este hallazgo coincide con el de la auditoría paralela de MD, a la que llegué por separado
(§7).

### P-20 — Umbrales contradictorios entre código y documentación · BAJA · [estático]

| Parámetro | YAML | Default del código | README | CLAUDE.md | Efectivo |
|---|---|---|---|---|---|
| `max_violation_threshold` | 0,10 | 0,05 | 0,05 | 0,10 | ninguno (P-01) |
| `exclusion_radius` | 5,0 | 10,0 | 10 Å | 5,0 Å y 10 Å | **5,0** |
| `collision_margin` | 2,0 | 2,0 hardcoded | — | — | 2,0 (P-12) |
| `n_replicas` | 10 | 7 / 10 | 7 | 7-10 | según llamada |

Son irrelevantes mientras P-01 siga en pie, pero son exactamente los números que un revisor
de JOSS leerá para entender el método, y hoy no hay dos fuentes que coincidan.

---

## 5. ¿`tests/test_golden_science.py` comprueba lo que importa?

**No, en dos sentidos distintos.**

### G-01 — No cubre el motor de packing en absoluto · ALTA · [estático]

El archivo prueba `substrate_section`, que vive en `src/services/pore.py` y pertenece a la
**puerta 1 (poro)**. Su propio docstring lo declara: «el radio de sección mínima de un
sustrato […] la ciencia de la puerta 1 ("¿cabe por el poro?")».

Cobertura real del motor de packing, archivo por archivo:

| Componente | Tests |
|---|---|
| `capsid.py` · radio interno | ninguno |
| `parallel_packer.py` · generación del input | ninguno |
| `parallel_packer.py` · criterio de aceptación | ninguno |
| `parallel_packer.py` · consolidación estadística | ninguno |
| `experiment_runner.py` · orquestación, semillas | ninguno |
| `experiment_manager.py` | ninguno |

`tests/test_smoke.py` lo dice explícitamente: «NO ejercen los motores lentos (HOLE, PyMOL,
Vina, Packmol)». El único test que roza el Studio 3D (`test_preview_enzymes_returns_pdb`)
ejercita la **colocación aleatoria de preview**, que no usa PACKMOL ni el radio calculado.

Esto explica por qué P-01 y P-02 —dos defectos que invalidan el resultado y que un solo test
con un doble de PACKMOL habría cazado— sobrevivieron a toda la fase de cimientos, a un
refactor del monolito y a la puesta en CI. Corrí la suite completa: **22 tests, todos verdes,
1,49 s**, con el motor de packing en el estado que describe §1.

### G-02 — Como test de la puerta 1 funciona, pero su oráculo es holgado · MEDIA · [verificado corriendo]

Lo ejecuté con RDKit 2026.03.6 frente a los valores de referencia tomados con 2025.9.1:

| SMILES | Golden | Medido | Δ | Margen sin usar de la tolerancia ±0,2 |
|---|---|---|---|---|
| CCO (etanol) | 1,02 | 1,02 | 0,000 | 0,200 |
| OCC1OC(O)C(O)C(O)C1O (glucosa) | 1,95 | 1,95 | 0,000 | 0,200 |
| CC(=O)Oc1ccccc1C(=O)O (aspirina) | 1,15 | 1,15 | 0,000 | 0,200 |

La variación real entre dos versiones mayores de RDKit es **0,000**, así que la tolerancia de
±0,2 Å está íntegramente sin usar y equivale a ±20 % del valor más pequeño congelado: un
cambio sistemático del 19 % en el etanol pasaría el test. A su favor: sí cazaría un cambio de
semieje mínimo a mediano (Δ = 0,25 / 0,34 / 1,72). El test `test_substrate_section_deterministic`
es legítimo (verifiqué que `substrate_section` no cachea, así que recalcula de verdad).

### G-03 — La magnitud congelada no es la magnitud física · ALTA · [verificado corriendo]

`substrate_section` (`pore.py:601-612`) toma los semiejes de los **centros atómicos** tras una
PCA y devuelve el menor. No usa radios de van der Waals. La sección por la que una molécula
realmente pasa por un poro es esa envolvente **más** el radio de los átomos del borde. Lo
calculé:

| Molécula | Semiejes de centros | Golden | Semiejes con vdW | Sección física | Factor |
|---|---|---|---|---|---|
| Glucosa | [1,95 · 2,29 · 2,98] | 1,95 | [3,49 · 3,80 · 4,74] | 3,49 Å | ×1,8 |
| Etanol | [1,02 · 1,27 · 1,56] | 1,02 | [2,22 · 2,59 · 3,01] | 2,22 Å | ×2,2 |

La evidencia de que esto importa está **en el mismo módulo**: la tabla `_SUBSTRATES`
(`pore.py:22-27`) lleva radios de sección de literatura de 3,5 a 5,1 Å —glucosilceramida 4,4 Å—
mientras el cálculo propio da 1,95 Å para la glucosa. Son dos escalas distintas, y la puerta 1
compara el radio del poro contra una u otra según el camino.

Es decir: el golden test protege con dos decimales de precisión una cantidad que está
subestimada por un factor cercano a dos. Es un buen test de regresión de software sobre una
definición científica equivocada, y hoy es la única pieza del proyecto que se presenta como
«regresión científica».

(G-03 es un hallazgo de la puerta 1, fuera del encargo estricto. Lo incluyo porque el golden
test es parte del encargo y porque el argumento «packing es terreno firme porque tiene golden
test» se apoya en él.)

---

## 6. Plan de reparación priorizado y estimado

Estimaciones en días-persona de trabajo efectivo, para quien ya conoce el código. «Cómputo»
señala tiempo de máquina adicional. El orden es el de dependencia: Fase 0 desbloquea todo lo
demás.

### Fase 0 — Recuperar un número que signifique algo · ~4 días + 0,5 días de cómputo

Sin esto, cualquier cifra de capacidad que el proyecto publique es indefendible, y es la única
fase que bloquea el envío a JOSS.

| # | Acción | Cierra | Esfuerzo |
|---|---|---|---|
| **R-1** | Medir el comportamiento real de PACKMOL: código de salida al terminar con `ENDED WITHOUT PERFECT PACKING`, cadenas exactas del bloque final, y si deja `<output>` además de `<output>_FORCED`. Un caso imposible (200 × GCase en esfera de 88 Å) y `echo $?`. Registrar la versión de PACKMOL. | P-03, P-13 | **0,5 d** |
| **R-2** | Reescribir el criterio de aceptación: parsear `Maximum violation of target distance` del bloque final, detectar `ENDED WITHOUT PERFECT PACKING` y la presencia de `<output>_FORCED` como rechazo explícito, y **retirar el fallback por conteo de líneas**. | P-01, P-02 | **1 d** |
| **R-3** | Verificar `n_packed` contando copias: `(líneas_output − líneas_cápside) / líneas_enzima`, y rechazar si no es el N pedido. El dato ya se calculaba en el script original. | P-04 | **0,5 d** |
| **R-4** | Semilla determinista de punta a punta: `experiment_runner` pasa `engines.packmol.seed_base`, se honra `use_random_seeds`, y la semilla de cada réplica va al `summary/report.txt` además del `metadata.json`. | P-05 | **0,5 d** |
| **R-5** | **La red que no existe:** tests del motor de packing con un doble de PACKMOL que emita las cadenas reales. Casos mínimos: acepta con violación baja; rechaza con violación alta; rechaza un output sin enzimas; rechaza `ENDED WITHOUT PERFECT PACKING`; el `.inp` generado se congela carácter a carácter; la búsqueda incremental se detiene donde debe; con `seed_base` fijo las semillas son reproducibles. Corre en CI sin PACKMOL. | G-01 | **1,5 d** |

Un doble de PACKMOL utilizable como punto de partida quedó en el scratchpad de esta sesión;
conviene reescribirlo como fixture del repo a partir de los logs reales commiteados, que son
la mejor especificación disponible.

### Fase 1 — Hacer defendible el radio interno · ~4 días

| # | Acción | Cierra | Esfuerzo |
|---|---|---|---|
| **R-6** | **Decidir CIENCIA-1 por escrito: restar.** Justificación en P-08 (con `+1` la holgura mínima garantizada es 0,5 Å, por debajo de cualquier radio de vdW; con `−1` es 2,5 Å). Alinear código, docstring y CLAUDE.md, y documentar que el radio efectivo es `R_int − collision_margin`. | CIENCIA-1 | **0,5 d** |
| **R-7** | Eliminar los valores de reserva silenciosos: si el radio no se puede calcular, error explícito, nunca 90,0 Å. Quitar el techo de 200 Å (o derivarlo del tamaño de la estructura) para que P22 no devuelva un valor falso. Distinguir en la respuesta de la API `calculado` de `por defecto`. | P-11 | **0,5 d** |
| **R-8** | Redefinir el radio interno con un criterio explícito y reportado, **con radios de van der Waals**: percentil de la distribución radial o superficie accesible a una sonda del tamaño del cargo, sin rejilla de 1 Å. Reportar en el output tanto el criterio como el valor. Decidir si PyMOL sigue aportando algo (el cálculo actual es un `min` sobre coordenadas) — si no, quitarlo de la ruta y **ganar la posibilidad de testear el radio en CI**. | P-09, P-10 | **2 d** |
| **R-9** | Cachear el radio **por cápside** (dentro de `Input/Capsides/<nombre>/` o un JSON indexado), no en un archivo global atribuido a BMV por prefijo de nombre. | P-18 | **0,5 d** |
| **R-10** | Un solo sitio de lectura de parámetros: `collision_margin`, `timeout`, `exclusion_radius`. Sincronizar YAML / README / CLAUDE.md y borrar las claves muertas o implementarlas. | P-12, P-19, P-20 | **0,5 d** |

### Fase 2 — Estadística publicable y entregable usable · ~5,5 días + cómputo

| # | Acción | Cierra | Esfuerzo |
|---|---|---|---|
| **R-11** | Definir la cantidad reportada. Propuesta: `N_max` por réplica como variable aleatoria; titular = **mediana con IQR** sobre un `n_replicas` fijo y declarado; el máximo se muestra etiquetado como «máximo observado en N réplicas». Añadir la curva de convergencia `best` frente a `n_replicas`, que es lo que demuestra que las réplicas bastan. | P-06, P-07 | **1,5 d** |
| **R-12** | Barrido de sensibilidad `N_max(radius)` y `N_max(tolerance)` — p. ej. `radius` ∈ {2, 3, 4, 5} Å — y publicarlo. Es la diferencia entre «caben 6» y «caben 6 bajo este criterio estérico, y así cambia si lo relajas». | P-13, P-14 | **1 d + cómputo** |
| **R-13** | Provenance: directorio de experimento con timestamp y sin sobrescribir; guardar en el `summary` la config efectiva, la versión de PACKMOL, las semillas y los hashes de los PDB de entrada. Dejar de escribir en `Input/`: los centrados van a `Output/` o a un cache. Restaurar o documentar el estado derivado de `Input/Enzimas/` (y respaldar GCase, que no tiene `.original`). Limpiar los `packed_*.pdb` intermedios. | P-16, P-17, P-21 | **1,5 d** |
| **R-14** | Contrastar el resultado contra las cotas geométricas de P-14 como test de cordura permanente: un `N_max` fuera del rango de la cota es un fallo, no un resultado. | P-14 | **0,5 d** |
| **R-15** | **Arreglar el entregable:** preservar los `TER` de las 180 subunidades a través del centrado (guardar con PyMOL conservando la segmentación, o centrar con una transformación de coordenadas que no reescriba el archivo) y reinsertarlos tras PACKMOL; asignar un ID de cadena o un número de residuo distinto a cada copia de la enzima; y normalizar los seriales hexadecimales. Añadir al test de R-5 la comprobación de que la salida tiene 180 + N bloques separables. Sin esto la puerta 2 no puede alimentar a la puerta 4. | P-22 | **1,5 d** |

### Fase 3 — Validación externa y golden test que importe · ~2,25 días + investigación

| # | Acción | Cierra | Esfuerzo |
|---|---|---|---|
| **R-16** | Corregir `substrate_section` para incluir radios de vdW, re-medir los valores golden y unificar la escala con `_SUBSTRATES`. Mientras no se decida, documentar en el test que el valor es un semieje de centros y **no** una sección física. | G-03 | **1 d** |
| **R-17** | Ajustar la tolerancia del golden a la variación real medida (0,000 entre dos versiones mayores de RDKit): ±0,05 Å absoluto, o relativa al valor. | G-02 | **0,25 d** |
| **R-18** | Validación externa: comparar la capacidad calculada contra la carga enzimática medida experimentalmente en VLP publicadas (ya está en `PENDIENTES.md` línea 71). Es lo que convierte el número en ciencia y no en geometría. | — | **1–2 semanas de investigación dirigida** |

### Resumen

| Fase | Esfuerzo | Bloquea |
|---|---|---|
| 0 — criterio y red de tests | ~4 d + 0,5 d cómputo | **el envío a JOSS y cualquier cifra publicable** |
| 1 — radio interno | ~4 d | CIENCIA-1 y la cápside P22 |
| 2 — estadística, provenance y entregable | ~5,5 d + cómputo | el método de la tesis y la puerta 4 |
| 3 — golden y validación externa | ~2,25 d + investigación | la comparabilidad con la literatura |

**Total Fases 0-2: unas 14 días-persona**, sin contar cómputo ni R-18.

### Nota sobre el envío a JOSS

JOSS revisa software, no resultados científicos, así que la Fase 0 no es formalmente un
requisito de aceptación. Pero el `README.md` de la raíz afirma hoy «empaquetamiento
multi-réplica» como función real y verificada de la puerta 2, y esa afirmación es la que un
revisor comprobará. Con el criterio actual, un revisor que corra el motor con PACKMOL
instalado obtendrá 100 enzimas y una desviación estándar de 0,00, o bien un número que no
podrá reproducir porque no hay semilla. **R-1 a R-5 son el mínimo antes de enviar**, y son
cuatro días. La alternativa honesta, si hay prisa, es reetiquetar la puerta 2 en el README y
en `ESTADO.md` como «motor listo, criterio de capacidad en revisión» —igual que ya se hizo con
la MD— y enviar describiendo solo lo que está verificado.

Conviene además corregir en `PENDIENTES.md` §15-16 y `BITACORA.md` §24-25 la frase que sostiene
que el packing es terreno firme «por ser determinista y tener golden test»: tras esta auditoría
ninguna de las dos premisas se sostiene, y es la frase sobre la que se apoyó la decisión
estratégica de seguir adelante con JOSS mientras se audita la MD.

---

## 7. Cross-check con las revisiones previas

Esta sección se escribió después de todo lo anterior. Hasta este punto no se había abierto
ninguna revisión previa.

### 7.1 Frente a `REVISION_MOTORES_hallazgos_sellados.md`

La pasada previa dedica al packing tres puntos y los titula explícitamente **«sospechas
(menores)»**. **La discrepancia principal es de severidad, y es grande:** lo que esa pasada
clasifica como menor incluye, bajo mi evidencia, tres defectos bloqueantes (P-01, P-02, P-03)
que hacen que la capacidad reportada no sea una medición. Ninguno de los tres aparece en el
documento sellado.

**Dónde coincidimos, y donde su observación es buena:**

- **Código ≠ docstring en el margen ±1 Å.** Coincidencia plena; es CIENCIA-1 y ya estaba en
  `ESTADO.md`. Lo que añado es el veredicto con su razón cuantitativa (P-08): `+1` deja una
  holgura mínima garantizada de 0,5 Å, por debajo de cualquier radio de van der Waals.
- **«El radio *reportado* es `+1` mientras el radio *efectivo* es `−1`».** Observación afilada
  y correcta, y llegamos a lo mismo por caminos distintos: mi tabla de P-08 da
  `R_s = r_c − 1` para la variante actual, exactamente su «radio efectivo −1». Es una
  divergencia reporte-uso real: `radio_interno.txt` y la Biblioteca muestran 90 Å, PACKMOL
  recibe 88 Å, y nada en la interfaz lo dice.
- **«`exclusion_radius = 5.0` es la perilla principal de capacidad — documéntala/valídala».**
  Coincidencia, y es el único punto donde la pasada previa apunta al corazón del problema
  científico. Lo cuantifico en P-13 y P-14 y lo convierto en una acción concreta (R-12, el
  barrido de sensibilidad).

**Dónde contradigo un punto marcado como positivo.** El documento sellado anota, como factor
que *de-riesga*:

> «PACKMOL incluye la cápside como estructura **fija** […] → las enzimas quedan acotadas por
> la pared real aunque la esfera sea aproximada. Réplicas con semillas aleatorias =
> metodología correcta.»

La primera mitad es cierta y además importante: es la razón por la que el error de la esfera
no produce solapamientos groseros, y mi P-08 llega a la misma conclusión por otra vía. Pero
está sobrevalorada: la cota la impone la restricción de distancia de PACKMOL, que bajo la
lectura de suma de radios exige 6 Å entre enzima y cápside y bajo la de `tolerance` exige 2 Å
—es decir, **puede autorizar contactos por debajo del contacto de van der Waals** (≈ 3,4 Å),
y en cualquier caso es un parámetro elegido a mano, no la pared física. «Acotadas por la pared
real» es verdad como protección contra el absurdo, no como garantía estérica.

La segunda mitad la contradigo de frente. «Réplicas con semillas aleatorias = metodología
correcta» es cierto como diseño de muestreo y falso como implementación: la ruta de producción
no pasa semilla maestra, usa el RNG global sin sembrar, y las dos claves del YAML que existen
para esto están muertas (P-05). Más grave, el documento no observa que el estadístico titular
es un **máximo sobre réplicas** (P-06), que crece con el número de réplicas y que la interfaz
deja elegir — así que no hay una «metodología de réplicas», hay réplicas sin una cantidad
definida que estimar.

**Lo que la pasada previa no vio** (P-01, P-02, P-03, P-04, P-06, P-07, P-09, P-10, P-11,
P-16, P-17, P-18, P-19, P-21, P-22, G-01, G-03): en particular, que el criterio de aceptación
no se dispara nunca, que el de reserva es ciego, que el golden test no cubre este motor, y que
el radio interno lo define el 0,14 % de los átomos.

**La lección metodológica es la que el propio briefing anticipaba.** El documento sellado
declara que todo se derivó «SOLO leyendo el código». Leyendo el código, el regex de P-01
parece correcto: busca una frase plausible sobre violación de distancia. Lo que lo delata es
contrastarlo con los **logs reales que están commiteados en este mismo repositorio**, y lo que
mide el daño es ejecutar el motor con un doble de PACKMOL. `REVISION_MOTORES.md` lo pedía
textualmente: «no te quedes leyendo scripts […] el comportamiento real vale más que la
inspección». Esa diferencia de método es la que explica casi toda la divergencia de severidad.

**Consecuencia estratégica.** Si los hallazgos sellados se hubieran tomado como norma, la
conclusión operativa sobre el packing habría sido «reconciliar un docstring y documentar una
perilla» — que es, en esencia, el estado en el que `PENDIENTES.md` y `BITACORA.md` declararon
el packing «terreno firme» y lo eligieron como base del envío a JOSS mientras se audita la MD.
Esa elección hay que revisarla a la luz de la Fase 0.

### 7.2 Frente a `AUDITORIA_MD.md` (auditoría paralela de dinámica molecular)

Ese documento no está en `main`; vive en la rama `claude/audit-packman-dynamics-engine-52svym`.
Lo consulté solo después de cerrar mi juicio. Es coherente con el contexto del encargo:
concluye que los `.in` commiteados son stubs (≈ 240 ps frente a 1,03 µs de la referencia
SIRAH), que el protocolo mezcla resoluciones y que la topología que construye la ruta
automatizada es inválida. No contradice nada de lo mío y no cambia ninguna de mis
conclusiones.

Dos puntos de contacto que sí importan para el packing:

- **Convergencia independiente sobre los `TER`.** Esa auditoría detecta que el PDB empaquetado
  no tiene ningún registro `TER` y que eso haría que tLeaP enlace covalentemente las 180
  subunidades. Lo verifiqué por mi cuenta sobre los archivos reales y lo confirmo (P-22),
  añadiendo la atribución: **la primera pérdida, de 180 a 3, la causa el paso de centrado del
  propio motor de packing**, no PACKMOL. Es decir, es un defecto de mi motor, no heredado, y
  lo incorporo a mi plan como R-15.
- **Coincidimos en que el empaquetado es el único paso con evidencia de ejecución** de toda la
  cadena cápside-enzima. Esa coincidencia refuerza mi §2: esa evidencia consiste en una sola
  corrida, con n = 1, cuyo log dice `Initial approximation is a solution. Nothing to do.`
  Que el packing sea el eslabón con más evidencia que la MD no lo convierte en un eslabón
  validado.

### 7.3 Aviso: existe otra auditoría de packing en paralelo

La rama `claude/audit-packing-engine-vdvq69` contiene un archivo **con este mismo nombre**,
`AUDITORIA_PACKING.md`, de otra pasada independiente sobre este mismo motor.
**Deliberadamente no lo he leído**, para no contaminar el juicio que se pedía desde cero: es
exactamente el tipo de documento contra el que protege la regla anti-sesgo.

Dos implicaciones prácticas para Lucio:

1. **Colisión de nombres.** Las dos ramas aportan un `AUDITORIA_PACKING.md` distinto en la
   raíz. Fusionar ambas producirá un conflicto; conviene decidir antes si se renombran (por
   ejemplo con el sufijo de la rama) o si se consolidan en un solo documento.
2. **Dos juicios independientes sobre el mismo motor son más valiosos que uno.** La
   comparación vale la pena, y en particular vale la pena comprobar si la otra pasada detectó
   P-01 y P-02. Puedo hacer ese contraste en una sesión aparte, con el orden correcto: mi
   informe ya está cerrado y fechado, así que leerlo ahora no afecta a lo que aquí se
   concluye.
