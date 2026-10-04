# Auditoría: conversión a grano grueso y motor `sustratinaitor`

> **Encargo.** Determinar si la conversión a coarse-grained (CG) de `sustratinaitor`
> sufre los dos defectos que una auditoría previa atribuyó a la ruta de `PackMan`
> (PDB de entrada sin hidrógenos; pérdida de los registros `TER`). Si está bien hecha,
> extraer su receta y explicar cómo portarla. Auditar además el resto del motor:
> construcción del sustrato, empaquetado alrededor de la cápside y la coherencia de
> resolución registrada como decisión abierta **CIENCIA-2**.
>
> **Método.** Medición directa sobre los PDB del repositorio con Python y NumPy, más
> una reproducción ejecutada de la receta. Todo lo que se afirma aquí sale de un
> comando que se puede volver a correr; ver *Cómo reproducir esta auditoría* al final.

---

## 1. Veredicto en una página

**La conversión de `sustratinaitor` está bien hecha. No sufre ninguno de los dos
defectos.** El fichero `sustratinaitor/1_capside/3J7L_cg.pdb` conserva los 180
registros `TER` y contiene los 3.780 beads que SIRAH deriva de hidrógenos, con
cobertura del 100 % de los residuos que los requieren. Es una conversión limpia,
reproducible paso a paso, y coincide bead a bead con la receta canónica de SIRAH.

**Pero el motor sí hereda el segundo defecto una etapa más tarde.** El fichero que
`gensystem.leap` carga de verdad no es `3J7L_cg.pdb`, sino
`3_empaquetado_packmol/3J7L-GYE.pdb`, y ése tiene **cero** registros `TER`: Packmol
los descarta. La conversión es correcta; el empaquetado la estropea.

**La auditoría previa acertó en el diagnóstico global de `PackMan` y se equivocó en
las dos causas.** Ninguno de los dos defectos que nombró bloquea esa ruta:
`convert_to_cg.sh` pasa por `pdb2pqr`, que añade los hidrógenos y además reconstruye
los `TER` que faltan. Lo que sí bloquea la ruta es otra cosa, verificada
ejecutándola: Packmol escribe seriales de átomo **hexadecimales** a partir del átomo
100.000 y `pdb2pqr` aborta con `ValueError`. La única herramienta de reparación del
repositorio, `fix_pdb_serial.py`, desplaza todas las columnas una posición a partir
de ese mismo átomo, de modo que corrompe el 55 % del fichero.

| Pregunta | Respuesta |
|---|---|
| ¿`sustratinaitor` pierde hidrógenos? | **No.** 3.780 beads derivados de H, 100 % de cobertura |
| ¿`sustratinaitor` pierde los `TER`? | **No en la conversión** (180/180). **Sí en el empaquetado** (0/180) |
| ¿Es portable su receta a `PackMan`? | **Sí**, y es la receta que `PackMan` ya intenta seguir |
| ¿Está resuelto CIENCIA-2? | **No.** El sistema es incoherente y, además, no integrable |

---

## 2. Qué se midió y sobre qué

| Fichero | Partículas | `TER` | Papel |
|---|---:|---:|---|
| `PackMan.../empaquetador/capside.pdb` | 216.780 | 180 | cápside all-atom de partida |
| `PackMan.../empaquetador/enzima.pdb` | 3.973 | 1 | enzima all-atom de partida |
| `PackMan.../capside_1enzimas_2026…pdb` | 220.753 | **0** | salida de Packmol, entrada de `convert_to_cg.sh` |
| `sustratinaitor/1_capside/3J7L_cg.pdb` | 131.820 | **180** | cápside ya convertida a CG |
| `sustratinaitor/2_ligando_GYE/GYE.pdb` | 144 | 1 | ligando all-atom (89 hidrógenos) |
| `sustratinaitor/2_ligando_GYE/GYE_cg_manual.pdb` | 17 | 1 | ligando CG manual, **no usado** |
| `sustratinaitor/3_…/3J7L-GYE.pdb` | 160.620 | **0** | salida de Packmol, entrada de `gensystem.leap` |

La cápside 3J7L son 180 subunidades en dos conformaciones: 60 copias de 689 beads
(149 residuos) y 120 copias de 754 beads (164 residuos). Suman exactamente los 131.820
beads y los 28.620 residuos observados.

---

## 3. Defecto 1 — hidrógenos: `sustratinaitor` está limpio

El mapa oficial `sirah_prot.map` deriva cuatro beads de un hidrógeno y no de un
átomo pesado. Sin hidrógenos explícitos en la entrada, esos beads sencillamente no
se generan.

| Residuo CG | Bead | Se deriva de | Presentes en `3J7L_cg.pdb` |
|---|---|---|---:|
| `sC` (CYS) | `BPG` | `HG` / `HSG` / `HG1` | 180 / 180 |
| `sS` (SER) | `BPG` | `HG` / `HG1` | 1.980 / 1.980 |
| `sT` (THR) | `BPG` | `HG1` / `1HG` | 1.260 / 1.260 |
| `sW` (TRP) | `BPE` | `HE1` | 360 / 360 |

Cobertura del 100 % en los cuatro casos. Además, el conteo de beads por residuo
coincide con el mapa oficial **en los veinte tipos de residuo presentes**, sin un
solo bead de más ni de menos.

La geometría lo confirma de forma independiente: cada bead polar queda a la
distancia de un enlace O–H o N–H de su pareja, que es la firma de un hidrógeno
colocado por `pdb2pqr` y no de un artefacto.

| Par | n | mediana |
|---|---:|---:|
| `sS` `BPG`–`BOG` | 1.980 | 0,999 Å |
| `sT` `BPG`–`BOG` | 1.260 | 1,006 Å |
| `sC` `BPG`–`BSG` | 180 | 1,005 Å |
| `sW` `BPE`–`BNE` | 360 | 1,000 Å |

El contraste está ejecutado, no razonado. Sobre un extracto de 20 subunidades del
repositorio:

| Ruta | beads | `TER` | `BPG` | `BPE` |
|---|---:|---:|---:|---:|
| `pdb2pqr` → `cgconv.pl` | 13.780 | 20 | 380 | 40 |
| `cgconv.pl` directo, sin protonar | 13.360 | 0 | 0 | 0 |

La diferencia de 420 beads es exactamente la suma de los `BPG` y `BPE` perdidos.
Saltarse la protonación cuesta el 3,1 % de los beads del sistema, y son precisamente
los que llevan la química polar de las serinas, treoninas, cisteínas y triptófanos.

---

## 4. Defecto 2 — registros `TER`: limpio en la conversión, perdido en el empaquetado

### Por qué importa

No es una cuestión de estilo de fichero. La librería del propio campo de fuerza lo
hace crítico: en `amino.lib`, cada residuo declara
`!entry.sA.unit.residueconnect` con los valores `1 3`, es decir, **cabeza = `GN`**
(átomo 1) y **cola = `GO`** (átomo 3). tLeaP enlaza la cola de un residuo con la
cabeza del siguiente salvo que un `TER` los separe. No usa la distancia para
decidirlo.

Hay una segunda consecuencia, menos visible. `leaprc.sirah` incluye un
`addPdbResMap` que convierte el primer residuo de cada cadena en su variante
N-terminal (`nX`) y el último en la C-terminal (`cX`). Sin `TER`, sólo el primer y
el último residuo de todo el ensamblaje reciben tipo terminal: los otros 179 pares
quedan como residuos internos. Las variantes terminales difieren en ±1 e respecto a
la interna (verificado en `sA`, `sK` y `sE`), así que **358 posiciones quedarían con
la carga equivocada en 1 e**. La carga neta total se conserva porque los +1 y los −1
se cancelan, lo que hace que el error no salte a la vista en el `charge protein` del
script.

### Qué muestran los ficheros

`3J7L_cg.pdb` está bien: 180 `TER`, 180 segmentos, y las fronteras están
geométricamente lejísimos de un enlace.

| `3J7L_cg.pdb` | n | mín | mediana | máx |
|---|---:|---:|---:|---:|
| `GO(i)`–`GN(i+1)` dentro de subunidad | 28.440 | 2,21 Å | 2,24 Å | 2,27 Å |
| `GO(i)`–`GN(i+1)` cruzando `TER` | 179 | 27,61 Å | 76,87 Å | 216,71 Å |
| `GC(i)`–`GC(i+1)` dentro de subunidad | 28.440 | 2,79 Å | 3,79 Å | 3,87 Å |

Cero huecos internos por encima de 5 Å: las 180 cadenas están completas y continuas.
Cero fronteras por debajo de 5 Å: ninguna pareja de subunidades podría confundirse
con un enlace.

El problema aparece después. Los dos ficheros que salen de Packmol pierden **todos**
los `TER`, y en ambos las fronteras que quedarían encadenadas están entre 26 y 217 Å:

| Fichero de salida de Packmol | `TER` | fronteras | distancia del enlace que tLeaP inferiría |
|---|---:|---:|---|
| `capside_1enzimas_2026….pdb` (PackMan) | 0 | 180 | 26,49 – 215,85 Å (mediana 77,52) |
| `3J7L-GYE.pdb` (sustratinaitor) | 0 | 179 | 27,61 – 216,71 Å (mediana 76,87) |

Como referencia, el enlace peptídico real en esos mismos ficheros mide 1,33 Å
(all-atom) y 2,24 Å (CG). Los enlaces espurios serían entre 20 y 160 veces más
largos que su distancia de equilibrio.

**Conclusión matizada.** La conversión de `sustratinaitor` no tiene este defecto; el
motor sí, porque el `TER` se pierde en la etapa 3 y `gensystem.leap` carga el
fichero ya sin ellos.

---

## 5. Divergencia con la auditoría previa sobre `PackMan`

La auditoría previa concluyó que la ruta de `PackMan` produce topología inválida por
los dos defectos de arriba. **El veredicto es correcto; las dos causas, no.** Lo
comprobé ejecutando la ruta.

### 5.1 El hidrógeno no se pierde: `pdb2pqr` lo pone

`convert_to_cg.sh` no llama a `cgconv.pl` sobre el PDB. Hace primero
`pdb2pqr --ff=AMBER`, que es exactamente el paso que la propia documentación de
SIRAH prescribe (sus tutoriales 5 y 7 parten de `.pqr`). Medido sobre dos
subunidades del repositorio: 2.266 átomos pesados entran, 4.590 átomos salen, de
los cuales 2.324 son hidrógenos. Los beads `BPG` y `BPE` aparecen.

Que `capside.pdb` tenga 0 hidrógenos es cierto y es irrelevante: es la entrada de
`pdb2pqr`, no la de `cgconv.pl`.

### 5.2 El `TER` tampoco se pierde: `pdb2pqr` lo reconstruye

`pdb2pqr` 3.7 detecta las roturas de cadena por geometría y numeración, y reemite
los `TER` aunque la entrada no traiga ninguno. Lo verifiqué en tres variantes
crecientes de dificultad, terminando en un extracto del fichero empaquetado real:

| Entrada | `TER` de entrada | `TER` de salida |
|---|---:|---:|
| 2 subunidades, cadenas `A` y `B`, con `TER` | 2 | 2 |
| 2 subunidades, cadenas `A` y `B`, sin `TER` | 0 | 2 |
| 2 subunidades, **ambas cadena `A`**, sin `TER` | 0 | 2 |
| **20 subunidades del fichero empaquetado real** | 0 | **20** |

En el tercer caso, que reproduce la condición más adversa del fichero real (60
subunidades comparten el mismo `chainID` y repiten la numeración de residuo; hay 477
claves `(cadena, nº residuo)` con multiplicidad hasta 61), `pdb2pqr` colocó el `TER`
en la frontera correcta y produjo una salida idéntica a la del caso con `TER`.

### 5.3 Lo que sí rompe la ruta de `PackMan`

**Bloqueo A — seriales hexadecimales.** El campo de serial del PDB tiene cinco
columnas y se agota en 99.999. Packmol desborda escribiendo hexadecimal:

```
ATOM  186A0  CG  PRO B 163     -61.326-115.412  38.694
```

`capside_1enzimas_2026….pdb` tiene 103.454 seriales no decimales de 220.753, el
primero en el átomo 100.000. `pdb2pqr` los parsea con `int()` y aborta:

```
File ".../pdb2pqr/pdb.py", line 654, in __init__
    self.serial = int(line[6:11].strip())
ValueError: invalid literal for int() with base 10: '349F5'
```

Por eso el extracto de 20 subunidades pasa (sus seriales van por debajo de 99.999) y
el fichero completo no. `convert_to_cg.sh` no puede haberse ejecutado nunca sobre su
propia entrada. `cgconv.pl` es inmune, porque su expresión regular se salta las 12
primeras columnas: el que muere es `pdb2pqr`.

**Bloqueo B — la reparación existente está rota.** `PackMan/fix_pdb_serial.py` se
escribió justo para esto; su docstring dice *"serial numbers that are in
hexadecimal"*. Pero renumera con `f"{atom_serial:5d}"`, que a partir de 100.000
produce seis caracteres y desplaza **todas** las columnas una posición a la derecha:

```
  99999 'ATOM  99999  CB  PRO B 163     -62.741-115.631  39.082'
 100000 'ATOM  100000  CG  PRO B 163     -61.326-115.412  38.694'
```

Las coordenadas pasan de las columnas 31-38 a las 32-39. Como `pdb2pqr` y
`cgconv.pl` parsean por columna fija, el 55 % del fichero sale corrupto. Y, en todo
caso, **ningún script de `PackMan` lo invoca**: no aparece en `convert_to_cg.sh`, ni
en `run_maestro.sh`, ni en `setup_1_1o.sh`.

`3J7L-GYE.pdb` arrastra el mismo desbordamiento (51.951 seriales hexadecimales).
Ahí importa menos porque tLeaP ignora el serial en `loadpdb`, pero rompe a cualquier
otro analizador, el visor del Studio incluido.

---

## 6. La receta de `sustratinaitor`, reconstruida y verificada

El repositorio no guarda el script que generó `3J7L_cg.pdb`. La reconstruí a partir
de las huellas del fichero y después la ejecuté para confirmarla.

**Las huellas.** Los beads `GN`, `GC`, `GO` y `BSG` copian las coordenadas de los
átomos `N`, `CA`, `O` y `SG` de `capside.pdb` con desviación máxima de 0,0000 Å:
misma estructura de partida, sin minimizar. El `chainID` sale **en blanco** aunque
`capside.pdb` traiga `A`/`B`/`C`, que es lo que hace `pdb2pqr` cuando no se le pide
conservarlo. Los `TER` sobreviven porque `cgconv.pl` los propaga explícitamente
(línea 227: `if ( $_ =~ /^(TER|END)/ ) { ... print $OUTPUT "$1\n" }`). Treinta
residuos de 28.620 se desvían por encima de 0,01 Å, con un máximo de 2,32 Å: cadenas
laterales que `pdb2pqr` reconstruyó por faltarle átomos a la estructura experimental.

**La receta.**

1. Partir de la cápside all-atom **sola**, con sus 180 `TER` intactos
   (`capside.pdb`). No del fichero ya empaquetado.
2. Protonar y normalizar a nomenclatura AMBER:
   `pdb2pqr --ff=AMBER capside.pdb capside.pqr`.
   Añade los hidrógenos polares, reconstruye los átomos pesados que falten, descarta
   el `chainID` y reemite los `TER`.
3. Mapear a grano grueso:
   `cgconv.pl -i capside.pqr -o 3J7L_cg.pdb`.
   Propaga los `TER` y numera los beads reiniciando en 0 al pasar de 99.999, sin
   hexadecimal.
4. **Sólo entonces** empaquetar, con la cápside ya en CG como estructura fija.

**La verificación.** Ejecuté los pasos 2 y 3 sobre 20 subunidades extraídas del
fichero empaquetado real:

- 689 beads en la subunidad 1, los mismos que la referencia;
- secuencia de nombres de bead **idéntica**;
- `resname` + `chainID` + `resSeq` **idénticos**;
- la diferencia de coordenadas es una traslación rígida de (−207,9, −207,9, −207,9) Å
  —el recentrado— con un RMSD residual de 0,125 Å, atribuible a la colocación de
  hidrógenos y a las cadenas laterales reconstruidas.

La receta es la canónica de SIRAH. `PackMan` ya la tiene escrita en
`convert_to_cg.sh`; lo que cambia es **cuándo** se aplica y **qué** hay que arreglar
para que corra.

---

## 7. Cómo portarla a `PackMan`

El cambio de fondo es invertir el orden: **convertir primero, empaquetar después.**
Eso resuelve los dos defectos de una vez y, de paso, esquiva los dos bloqueos, porque
la cápside sola tiene 131.820 beads y nunca desborda el campo de serial.

### 7.1 Orden nuevo

| Hoy | Propuesto |
|---|---|
| 1. Packmol: cápside + enzimas → PDB de 220.753 átomos | 1. `pdb2pqr` + `cgconv.pl` sobre `capside.pdb` → cápside CG |
| 2. `pdb2pqr` (aborta con los seriales hex) | 2. `pdb2pqr` + `cgconv.pl` sobre `enzima.pdb` → enzima CG |
| 3. `cgconv.pl` | 3. Packmol con las dos ya en CG |
| 4. tLeaP | 4. Restaurar los `TER` |
| | 5. tLeaP |

Ventajas concretas: cada `pdb2pqr` corre sobre un fichero pequeño y con `TER`
propios; el radio interno y la tolerancia de Packmol se miden entre objetos de la
misma resolución; y el resultado final tiene 134.232 beads en vez de 220.753 átomos
—la enzima convertida por esta misma receta da 2.412 beads, comprobado—, con lo que
el desbordamiento de serial sólo afecta al tramo final.

### 7.2 El paso que falta en los dos motores: restaurar los `TER`

Packmol no escribe `TER` entre moléculas y no tiene opción para hacerlo. Hoy
`sustratinaitor` no lo compensa y `PackMan` lo compensa por accidente, apoyándose en
que `pdb2pqr` corre después. Con el orden invertido ya no hay `pdb2pqr` después, así
que **hace falta un paso explícito**. La señal está en el fichero: la numeración de
residuo reinicia en cada subunidad, y detectarlo basta (180/180 fronteras localizadas
correctamente en las pruebas de este informe). Un postproceso que recorra el PDB e
inserte un `TER` donde el número de residuo no avanza, y que además renumere los
seriales con desbordamiento controlado en vez de hexadecimal, cubre lo que falta.

Ése es también el arreglo correcto para `fix_pdb_serial.py`: sustituir
`f"{atom_serial:5d}"` por un contador que vuelva a 0 al pasar de 99.999, tal como ya
hace `cgconv.pl`, y preservar los `TER` en lugar de limitarse a no borrarlos.

### 7.3 Si se prefiere no invertir el orden

Mantener `empaquetar → convertir` es viable, porque `pdb2pqr` repara hidrógenos y
`TER` por sí solo. Sólo hay que desbloquearlo: arreglar `fix_pdb_serial.py` y
llamarlo desde `convert_to_cg.sh` antes de `pdb2pqr`. Es menos trabajo, pero deja la
tolerancia de Packmol midiéndose entre átomos all-atom, que es lo que luego hay que
traducir a una distancia CG, y obliga a `pdb2pqr` a tragarse 220.753 átomos con
claves de residuo repetidas 61 veces. Recomiendo invertir el orden.

---

## 8. Auditoría del resto del motor `sustratinaitor`

### 8.1 Etapa 2 — construcción del sustrato (`2_ligando_GYE/`)

La parametrización química all-atom es correcta y ortodoxa: `antechamber` con GAFF2
y cargas AM1-BCC vía `sqm`, `GYE.mol2` + `GYE.frcmod`, cargados en tLeaP con
`leaprc.gaff2` y guardados como `GYE.off`/`GYE.pdb`. No tengo reparos ahí.

**El mapeo CG manual de 17 beads, en cambio, no es utilizable.** No es sólo que no
se haya usado: es que no podría usarse tal como está.

| Problema | Evidencia |
|---|---|
| Nombres de bead repetidos dentro del residuo | `GC` ×2 y `GO` ×2. tLeaP identifica átomos por nombre dentro del residuo |
| Colisión con la nomenclatura de SIRAH | `GC` y `GO` son los beads de esqueleto proteico (`CA` y `O`) en `sirah_prot.map` |
| Campo `resSeq` inválido | columnas 23-26 contienen `'A  1'`: la letra de cadena se escribió en el campo del número de residuo |
| Campo `element` inválido | `X` |
| Geometría incompatible con enlaces | 6 de 16 pares consecutivos superan 5 Å; el par `BCT`–`BF1` mide **39,33 Å** |
| Etiquetado invertido respecto a la geometría | el `README` sitúa `BF1` en la región C1-C4, que se une a la amida, pero `d(BCE,BF1) = 24,71 Å` frente a `d(BCE,BF6) = 2,61 Å` |
| No existe topología CG | no hay `.lib`, `.frcmod` ni `.mol2` para los 17 beads: sólo coordenadas |

El `BCT`–`BF1` de 39,33 Å no es un error de mapeo sino un malentendido sobre qué es
el fichero: las dos colas están extendidas en direcciones opuestas y los beads se
listaron en orden de fichero, no en orden de conectividad. Pero mientras no haya una
topología que declare los enlaces, ese orden es la única conectividad que un
programa puede inferir.

**Consecuencia práctica:** la opción "todo CG" de CIENCIA-2 no es un cambio de
cableado. Requiere construir el ligando CG de nuevo, con nombres de bead que no
colisionen, un PDB bien formado y una parametrización CG real. El fichero actual
sirve como boceto de la partición en 17 grupos, nada más.

### 8.2 Etapa 3 — empaquetado alrededor de la cápside (`3_empaquetado_packmol/`)

**Lo que está bien.** La mecánica es correcta y, cosa poco común, reproducible.
Packmol convergió de verdad: `Success`, función objetivo final 19,86, violación
máxima de distancia 0,000, 133 s. La cápside entra como estructura `fixed` centrada
en el origen, que es la forma correcta de que el ligando quede acotado por la pared
real y no por una esfera aproximada. No hay un solo átomo de GYE por debajo de la
tolerancia de 2,0 Å respecto a la cápside. Y aunque `packmol_input.inp` no fija
semilla, Packmol usa su valor por defecto 1234567, registrado en el log, de modo que
la corrida es repetible.

Nota menor de procedencia: hay dos logs, `packmol.log` (85 líneas, truncado a mitad
de la optimización, con la función objetivo aún en 1.455) y `packmol_run.log` (408
líneas, completo). Conviene borrar el truncado para que nadie lo lea como el
resultado.

**Lo que no está bien: la caja elige mal el espacio.** `EXPLICACION.md` describe la
caja como ajustada al volumen de la cápside. Lo está a lo largo de los ejes —holgura
de 10,5 a 11,2 Å sobre una semiextensión de 139,6/136,0/141,5 Å—, pero una caja no es
una esfera: sus esquinas llegan a 259,5 Å del centro, muy por fuera de la cápside, de
radio externo 142,6 Å.

| Región | Volumen |
|---|---:|
| Caja de Packmol | 26.902 nm³ |
| Esfera de radio externo de la cápside | 12.142 nm³ |
| Lumen (radio interno 89,5 Å) | 3.000 nm³ |

El espacio libre que Packmol encuentra son, por tanto, las esquinas (≈14.760 nm³)
más el lumen (≈3.000 nm³). El reparto resultante de las 200 moléculas:

| Ubicación del centro de masa | Moléculas |
|---|---:|
| Lumen (r < 89,5 Å) | **40** |
| Cáscara (89,5 ≤ r ≤ 142,6 Å) | 36 |
| Exterior (r > 142,6 Å) | 124 |

Dieciocho moléculas quedan **íntegramente** dentro del lumen.

Esto merece una decisión, no un arreglo automático. La puerta 1 del embudo pregunta
si el sustrato **entra por el poro**. Colocar de antemano el 20 % del sustrato dentro
de la cápside responde esa pregunta por decreto. Si el objetivo es medir permeación,
el empaquetado debería restringirse al exterior —`outside sphere 0. 0. 0. 143`
combinado con la caja— y dejar el lumen vacío. Si el objetivo era otro (saturar el
sistema, o estudiar la salida del producto), conviene decirlo en el `README`, porque
hoy el texto no lo menciona y el reparto observado no es el que la descripción
sugiere.

### 8.3 Etapa 4 — ensamblaje y simulación (`4_ensamblaje_y_simulacion/`)

No se ha ejecutado, y tal como está no podría ejecutarse. Tres cosas concretas:

1. **Los nombres no cuadran.** `gensystem.leap` escribe
   `3J7L-GYE_cg.prmtop` y `3J7L-GYE_cg.ncrst`. `run_MD.sh` declara
   `prmtop=3J7L-GYE_cg-WAT.prmtop` y `name=3J7L-GYE_cg-WAT`, es decir, busca
   `3J7L-GYE_cg-WAT.prmtop` y `3J7L-GYE_cg-WAT.ncrst`, que nadie genera. Lo único
   que sí se llama `-WAT` es el PDB de `savepdb`. El primer `pmemd.cuda` fallaría.
2. **Faltan los cuatro `.in`.** `run_MD.sh` invoca `em1_WT4.in`, `em2_WT4.in`,
   `eq1_WT4.in` y `eq2_WT4.in`; la carpeta sólo contiene `gensystem.leap` y
   `run_MD.sh`. Existen en `PackMan/archivos_dm_cg/`, sin que nada documente que hay
   que copiarlos.
3. **El comentario no describe al código.** Dice *"Add solvent, counterions and 0.15M
   NaCl"*, pero `addIonsRand protein NaW 0` sólo neutraliza: no añade sal de fondo.
   El mismo desajuste está en `PackMan/archivos_dm_cg/gensystem.leap`. O se añade la
   sal o se corrige el comentario; mezclar ambas cosas en un método publicado es
   peor que cualquiera de las dos.

Detalle menor: `gensystem.leap` de `sustratinaitor` omite el
`set default PBradii mbondi3` que sí tiene el de `PackMan`. Irrelevante en solvente
explícito, relevante si luego se quiere MM-PBSA.

---

## 9. CIENCIA-2 — coherencia de resolución

### 9.1 El estado actual, con números

La sospecha registrada en `ESTADO.md` §4b se confirma, y es más grave de lo que el
texto sugiere.

| Componente | Resolución | Partículas |
|---|---|---:|
| Cápside 3J7L | CG SIRAH | 131.820 beads |
| Ligando GYE × 200 | **all-atom** GAFF2/AM1-BCC | 28.800 átomos, de ellos **17.800 hidrógenos** |
| Agua (`solvateOct … WT4BOX`) | CG SIRAH (WT4) | pendiente |
| Contraiones (`addIonsRand NaW`) | CG SIRAH | pendiente |

El 17,9 % de las partículas del soluto son all-atom, y el 61,8 % de cada molécula de
ligando son hidrógenos explícitos. El mapeo CG de 17 beads existe pero Packmol
empaquetó el de 144 átomos.

### 9.2 El argumento que cierra la decisión: el paso de integración

La discusión en `ESTADO.md` plantea CIENCIA-2 como un dilema abierto entre "todo CG"
y "todo all-atom". Hay un hecho que lo cierra antes de llegar al dilema: **el sistema
actual no es integrable con el protocolo que el propio repositorio define.**

Los ficheros `eq1_WT4.in` y `eq2_WT4.in` que `run_MD.sh` invoca especifican

```
nstlim = 500, dt = 0.020,
ntc = 1, ntf = 1,
cut = 12.0, nrespa = 1,
```

Es decir, **20 fs de paso y `ntc=1`/`ntf=1`, sin ninguna restricción**. Correcto para
SIRAH, donde el grado de libertad más rápido es un bead pesado. Pero un enlace C–H
vibra con un período cercano a 10 fs. Integrar 17.800 hidrógenos explícitos, sin
restringir, con un paso del doble de su período no es inexacto: es inestable desde
los primeros pasos. Ni siquiera activar SHAKE lo salvaría, porque SHAKE sobre
hidrógenos permite 2–4 fs, no 20.

El híbrido tampoco se ampara en el soporte multiescala de SIRAH. El campo de fuerza
lo ofrece, pero para interfaces concretas y parametrizadas —agua WT4/TIP3P vía
`wt4tip3p.off`, ADN híbrido vía `hyb_dna.frcmod`, con las correcciones de
`LJoff.frcmod`—, no como licencia para sumergir un soluto GAFF2 arbitrario en un
baño CG. No hay parámetros cruzados GAFF2↔SIRAH para este ligando.

### 9.3 Recomendación

**Ir a todo CG**, y tratar la construcción del ligando CG como trabajo pendiente
real, no como un cambio de ruta de fichero:

1. Rehacer el mapeo CG de GYE arreglando lo de §8.1: nombres de bead únicos y sin
   colisión con los de proteína, PDB bien formado, orden de ficha coherente con la
   conectividad química.
2. Generar su topología CG (`.lib`/`.off` con enlaces y cargas, `.frcmod` con los
   parámetros que falten). Es el paso que hoy no existe en absoluto.
3. Validar el ligando solo —en una caja de WT4, con el mismo protocolo— antes de
   meterlo junto a la cápside.
4. Reempaquetar con el GYE CG y decidir a la vez la cuestión de §8.2: si el sustrato
   va sólo fuera o también dentro.

La alternativa "todo all-atom" es inviable, y conviene dejarlo dicho con el número
delante: la cápside sola son 216.780 átomos antes de solvatar, y con agua explícita
el sistema se va a varios millones, muy por encima de lo que justifica una puerta de
cribado.

Mientras tanto, propongo cambiar el estado de CIENCIA-2 de *"aplazado hasta correr
esa MD"* a **decidido: todo CG, con el ligando CG por construir**. El aplazamiento se
justificaba en que la MD arbitraría; el paso de integración ya arbitró.

---

## 10. Hallazgos por severidad

| # | Severidad | Motor | Hallazgo | Dónde |
|---|---|---|---|---|
| 1 | **Alta** | ambos | Packmol descarta los 180 `TER`; sin ellos tLeaP enlazaría subunidades separadas 26–217 Å y 358 residuos quedarían con tipo y carga de terminal equivocados | `3J7L-GYE.pdb`, `capside_1enzimas_….pdb` |
| 2 | **Alta** | sustratinaitor | Resolución mixta no integrable: 17.800 hidrógenos explícitos con `dt=0.020` y `ntc=1` (CIENCIA-2) | `packmol_input.inp`, `eq*_WT4.in` |
| 3 | **Alta** | PackMan | `pdb2pqr` aborta con los seriales hexadecimales que Packmol escribe tras el átomo 99.999; la ruta no puede haber corrido nunca completa | `convert_to_cg.sh` |
| 4 | **Alta** | PackMan | `fix_pdb_serial.py` desplaza todas las columnas una posición a partir del átomo 100.000, y ningún script lo llama | `fix_pdb_serial.py:36` |
| 5 | **Media** | sustratinaitor | El mapeo CG de GYE es inutilizable: nombres duplicados, colisión con beads de proteína, `resSeq` inválido, sin topología | `GYE_cg_manual.pdb` |
| 6 | **Media** | sustratinaitor | 40 de 200 moléculas de sustrato quedan en el lumen, lo que prejuzga la pregunta de la puerta 1 | `packmol_input.inp` |
| 7 | **Media** | sustratinaitor | La etapa 4 no puede correr: `run_MD.sh` busca un `prmtop` que `gensystem.leap` no produce, y faltan los cuatro `.in` | `4_ensamblaje_y_simulacion/` |
| 8 | Baja | ambos | El comentario promete 0,15 M NaCl; `addIonsRand … 0` sólo neutraliza | `gensystem.leap` |
| 9 | Baja | sustratinaitor | No hay script que documente cómo se generó `3J7L_cg.pdb`; la receta estaba sólo en el fichero | `1_capside/` |
| 10 | Baja | sustratinaitor | `packmol.log` está truncado a mitad de optimización y convive con el log completo | `3_empaquetado_packmol/` |

### Orden de trabajo sugerido

Los hallazgos 1, 3 y 4 son mecánicos y se arreglan juntos con un único postproceso de
PDB: insertar `TER` donde reinicia la numeración de residuo y renumerar seriales con
desbordamiento controlado. Eso desbloquea los dos motores. El 7 y el 8 son de
minutos. El 2, el 5 y el 6 son ciencia y piden decisión del autor: son los que de
verdad separan "el pipeline corre" de "el resultado significa algo".

---

## 11. Qué no pude verificar

Con honestidad sobre los límites de esta pasada:

- **No ejecuté tLeaP ni AMBER.** No están instalados en este entorno. La predicción
  de que tLeaP encadenaría las subunidades se apoya en `residueconnect = 1 3` de
  `amino.lib`, en el `addPdbResMap` de `leaprc.sirah` y en la geometría medida, no en
  un `prmtop` generado. Es la comprobación que cerraría el hallazgo 1 del todo, y es
  barata para quien tenga AmberTools: cargar `3J7L-GYE.pdb` y contar moléculas en el
  `prmtop`.
- **No corrí `pdb2pqr` sobre el fichero completo de 220.753 átomos.** Aborta antes,
  por el hallazgo 3. La verificación a escala de 20 subunidades es representativa del
  formato, pero no descarta que a 180 subunidades aparezcan problemas de memoria o de
  heurística de cadena.
- **`pdb2pqr` 3.7.1** es el que instalé aquí. No sé con qué versión se generó
  `3J7L_cg.pdb`; el RMSD residual de 0,125 Å en la reproducción es compatible con una
  diferencia de versión en la colocación de hidrógenos.
- **No hay trayectorias ni outputs de MD en el repositorio**, así que nada de esto
  dice cómo se comportó una simulación: dice si el sistema de partida es válido.

---

## 12. Cómo reproducir esta auditoría

Dos scripts, añadidos en `herramientas/auditoria_cg/`:

```bash
# Mediciones sobre los PDB del repositorio (sólo necesita numpy; scipy es opcional)
python3 herramientas/auditoria_cg/auditar_cg.py

# Reproducción ejecutada de la receta de conversión (necesita perl y pdb2pqr)
pip install pdb2pqr
herramientas/auditoria_cg/reproducir_receta.sh
```

El primero imprime todos los conteos, distancias y repartos citados en este informe.
El segundo reconstruye la cápside CG a partir del all-atom y la compara bead a bead
contra `3J7L_cg.pdb`, mostrando en la misma tabla lo que se pierde al saltarse la
protonación.

---

*Auditoría realizada el 2026-10-04 sobre el árbol de trabajo en la rama*
*`claude/audit-sirah-coarse-grain-conversion-e9h0rt`. Cada afirmación cuantitativa*
*procede de uno de los dos scripts de arriba.*
