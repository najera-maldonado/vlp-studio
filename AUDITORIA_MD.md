# Auditoría científica independiente — motor PackMan v1.2 (MD coarse-grained SIRAH)

> Encargo: `REVISION_MOTORES.md`. Auditoría **desde cero**, formada **antes** de leer
> `REVISION_MOTORES_hallazgos_sellados.md` (el cross-check está al final, §10).
> Fecha: 2026-10-04. Rama: `claude/audit-packman-dynamics-engine-52svym`.
>
> **Límite del entorno:** no hay AMBER, tLeaP, cpptraj, PyMOL ni GPU. Todo lo que sigue
> es **inspección estática** salvo los chequeos geométricos sobre los PDB, que sí se
> ejecutaron aquí con Python/NumPy (§3.4). Cada hallazgo lleva una etiqueta:
> `[ESTÁTICO]` = concluible leyendo los archivos; `[REQUIERE CORRER]` = necesita AMBER.

---

## 0. Veredicto en una página

1. **Los `.in` commiteados NO son de producción.** Las tres etapas SIRAH reales
   (`eq1`, `eq2`, `prod_md`) tienen `nstlim = 500` → **10 ps cada una**. Los títulos
   prometen 15 ns, 35 ns y "0.01ns (fast test)". El protocolo completo commiteado suma
   **≈ 240 ps**; la referencia SIRAH equivalente suma **1,03 µs**. Nada de lo que se
   describe como "producción" en `texto_tesis_archivos_dm.md` puede salir de estos inputs.
2. **El protocolo mezcla dos resoluciones.** `heat1..6`, `density_eq` y `final_eq` son
   inputs all-atom (`dt = 2 fs`, SHAKE, `cut = 9`, máscara `@CA,C,N,O`, `gamma_ln = 2`)
   aplicados a una topología SIRAH, donde ninguno de esos nombres de átomo existe y los
   parámetros de referencia son `dt = 20 fs`, `cut = 12`, `@GN,GO`, `gamma_ln = 50`.
3. **La ruta automatizada (`run_maestro.sh`) construye una topología inválida** por dos
   defectos independientes, ambos verificables sin correr nada:
   - El PDB que entra a `cgconv.pl` **no tiene hidrógenos** y SIRAH mapea beads de
     SER/THR/CYS/TRP **desde hidrógenos** (`HG`, `HG1`, `HE1`). Faltarían **3 866 beads**
     (3 780 de la cápside + 86 de la enzima) que tLeaP tendría que inventar.
   - El PDB empaquetado **no tiene ningún registro `TER`** (la cápside original tiene 180,
     el re-centrado de PyMOL deja 3, Packmol deja 0). tLeaP encadena residuos consecutivos
     hasta un `TER`: 180 subunidades + 1 enzima quedarían **enlazadas covalentemente** en
     una sola cadena con enlaces espurios de decenas de Å.
4. **Las etapas SIRAH tienen restricciones apagadas** (`ntr = 0` en `eq1` y `eq2`) aunque
   sus títulos digan "proteína completa" / "esqueleto"; la referencia restringe con
   2,4 y 0,24 kcal·mol⁻¹·Å⁻² sobre `@GN,GO`.
5. **Reproducibilidad: no hay nada que reproducir.** `ig = -1` en todos los inputs (igual
   que SIRAH, pero sin registrar la semilla), ningún `mdout`, `prmtop`, `leap.log`,
   trayectoria ni `.dat` commiteado. Las únicas "cifras reportadas" de MD viven como
   **curvas sintéticas** en `nanocapsule-mvp/src/services/md.py` (RMSD 2,8 Å, SASA
   41 893 Å², RMSF r = 0,81/0,12 y una **explosión de `heat1` a 17 666 K**). Esa explosión
   es coherente con los defectos 2 y 3 y es el único rastro de que algo llegó a correr.

**Conclusión:** tratar toda cifra de dinámica como **no verificada**. El motor requiere
reconstruir la preparación del sistema (hidrógenos, `TER`, disulfuros) y reemplazar el
protocolo por el de SIRAH antes de que cualquier corrida tenga sentido.

---

## 1. Qué se auditó y cómo

| Fuente | Uso en esta auditoría |
|---|---|
| `PackMan.v.1.2/archivos_dm_cg/*.in` (13 archivos) | Protocolo MD commiteado |
| `archivos_dm_cg/sirah_x2.3_24-07.amber/tutorial/{5,7,8,2}/*.in` | **Patrón oficial SIRAH** (5 = proteína en WT4; 7 = proteína-lípido con etapa de heat; 8 = glicoproteína; 2 = DNA) |
| `archivos_dm_cg/{run_MD.sh,gensystem.leap,setup_universal.sh,prod-q_gpu.bsub}` | Orquestación y construcción del sistema |
| `PackMan.v.1.2/{run_maestro.sh,convert_to_cg.sh,configurar_simulacion.sh,setup_*.sh,copy_md_files.sh}` | Rutas alternativas de preparación |
| `archivos_dm_cg/empaquetador/*` | Estructuras de entrada y empaquetado (único paso con evidencia de ejecución) |
| `sirah_x2.3_24-07.amber/{leaprc.sirah,*.lib,tools/CGCONV/*}` | Qué exige el force field (nombres de beads, mapeo) |
| `archivos_dm_cg/analisis/*` | Cómo se extraerían las métricas |
| `sustratinaitor/4_ensamblaje_y_simulacion/gensystem.leap`, `sustratinaitor/1_capside/3J7L_cg.pdb` | Comparador interno: misma cápside convertida a CG por el autor en otro motor |
| `nanocapsule-mvp/src/services/md.py`, `ESTADO.md`, `PENDIENTES.md`, `BITACORA.md`, `texto_tesis_archivos_dm.md` | Qué se "reporta" sobre la MD |

Historia git: los 13 `.in`, `run_MD.sh`, `gensystem.leap` y `prod-q_gpu.bsub` entraron en
un único commit (`d5035a2`, 2026-09-17) y no han cambiado desde entonces. No hay historia
previa que permita saber qué versión corrió en el clúster.

---

## 2. Tarea 1 — ¿Inputs de producción o stubs?

### 2.1 Tabla de duración (lo que realmente simula cada archivo)

| Archivo | Título del archivo | `nstlim` | `dt` (ps) | Tiempo real | Referencia SIRAH | Veredicto |
|---|---|---|---|---|---|---|
| `em1_WT4.in:4` | Minimización 1 | maxcyc 5000 / ncyc 2500 | — | — | `tutorial/5/em1_WT4.in:4` maxcyc 5000 / ncyc 100 | ok en ciclos; **sin restricciones** (ref: `ntr=1`, 2,4 sobre `@GN,GO`) |
| `em2_WT4.in:4` | Minimización 2 | 5000 / 2500 | — | — | `tutorial/5/em2_WT4.in:4` | ok |
| `heat1..6_*.in:6` | Gradual heating | 5000 ×6 | 0.002 | 10 ps ×6 = 60 ps | **no existe** etapa así en SIRAH-proteína (`tutorial/5/eq1_WT4.in:11` arranca de `tempi=0` directo a NPT) | all-atom (§3) |
| `density_eq.in:6` | Density equilibration | 25000 | 0.002 | 50 ps | no existe | all-atom |
| `eq1_WT4.in:5` | **"15ns"** equilibración NPT | **500** | 0.020 | **10 ps** | `tutorial/5/eq1_WT4.in:5` 250 000 → 5 ns | **stub** (1 500× más corto que su título) |
| `eq2_WT4.in:5` | **"35ns"** equilibración NPT | **500** | 0.020 | **10 ps** | `tutorial/5/eq2_WT4.in:5` 1 250 000 → 25 ns | **stub** (3 500× más corto) |
| `final_eq.in:6` | Final NPT equilibration | 50000 | 0.002 | 100 ps | no existe | all-atom |
| `prod_md_WT4.in:5` | **"0.01ns producción (fast test)"** | **500** | 0.020 | **10 ps** | `tutorial/5/md_WT4.in:5` 50 000 000 → 1 µs | **stub declarado** |

Total commiteado: **≈ 240 ps**, de los cuales **10 ps** son "producción".
Total referencia SIRAH (em → eq1 → eq2 → md): **≈ 1,03 µs**.

### 2.2 Evidencia adicional

- `prod_md_WT4.in:1` se autodenomina *"fast test"*. `[ESTÁTICO]`
- Frecuencias de escritura `ntpr = ntwx = ntwr = 50` (`eq1_WT4.in:6`, `eq2_WT4.in:6`,
  `prod_md_WT4.in:6`) → 1 frame por ps: configuración de prueba, no de producción
  (referencia: 5000 pasos = 100 ps, `tutorial/5/md_WT4.in:6`). `[ESTÁTICO]`
- `configurar_simulacion.sh:300-420` **sí** genera `em1/em2/eq1/eq2/prod` con duraciones
  reales (5 ns / 25 ns / 100 ns por defecto, `dt = 20 fs`) — pero **no está commiteado el
  resultado de haberlo corrido**: los `.in` del repo no coinciden con su salida (p. ej. la
  salida tiene `ntr=1` en `em1` y `eq1/eq2`; el repo tiene `ntr=0`). `[ESTÁTICO]`
- `prod-q_gpu.bsub:12` lanza `prod_md_WT4.in` en un clúster LSF (`q_gpu_v100`,
  `amber/22_gpu`, rutas `/tmpu/scunam/...`) sobre un sistema llamado `capside-3_cg-WAT`
  que **ningún script commiteado produce** (los scripts generan `capside-<dir>-cg-WAT`),
  partiendo de `_eq2.ncrst` y saltando `final_eq`. Es la única huella de una ruta manual
  distinta a `run_MD.sh`; sus inputs reales no están en el repo. `[ESTÁTICO]`

**Comando para confirmar** (en la workstation/clúster donde corrió):
```bash
grep -H "nstlim\|dt *=" *_prod*.out *_eq1*.out *_eq2*.out | head      # qué nstlim/dt se usó de verdad
grep -H "NSTEP" *_prod*.out | tail -1                                 # cuántos pasos completó
```

---

## 3. Tarea 2 — Parámetros vs. referencia oficial SIRAH

### 3.1 Tabla comparativa

Referencia principal: `tutorial/5/*_WT4.in` (proteína en WT4, el caso análogo). Donde el
tutorial 7 (proteína-lípido, único con etapa `heat`) aporta algo, se indica.

| Parámetro | SIRAH ref. (tutorial/5; 7 entre paréntesis) | `heat1..6` · `density_eq` · `final_eq` | `eq1` · `eq2` · `prod_md` | Salida de `configurar_simulacion.sh` |
|---|---|---|---|---|
| `dt` | **0.020** ps (`5/eq1:5`, `7/heat:10`) | **0.002** (`heat1:7`, `density_eq:7`, `final_eq:7`) ✗ | 0.020 ✓ | 0.020 ✓ |
| `cut` | **12.0** Å (`5/em1:7`, `5/eq1:15`, `7/heat:15`) | **9.0** (`heat1:12`, `density_eq:11`, `final_eq:11`) ✗ | 12.0 ✓ | 12.0 ✓ |
| `ntc`/`ntf` (SHAKE) | **1 / 1** — sin SHAKE (`5/eq1:13`); `leaprc.sirah:10-11` fija elemento `V` precisamente para que no se aplique SHAKE | **2 / 2** (`heat1:8`, `density_eq:8`, `final_eq:8`) ✗ (inocuo pero revela origen all-atom) | 1 / 1 ✓ | 1 / 1 ✓ |
| Termostato | `ntt=3`, **`gamma_ln=50`** (`5/eq1:10`); (`7`: 5.0; `8`: `ntt=11`) | `ntt=3`, **`gamma_ln=2.0`** (`heat1:15`, `density_eq:17`, `final_eq:17`) ✗ | 50 ✓ | **5.0** (`configurar_simulacion.sh:344,375,406`) — válido en tutorial 7, distinto del tutorial 5 |
| Barostato | `ntb=2, ntp=1, pres0=1` Berendsen por defecto (`5/eq1:8`); (`7`: `taup=8`) | `barostat=2` (Monte Carlo), `taup=2` (`density_eq:14-16`, `final_eq:14-16`) — no aparece en ningún `.in` de SIRAH | Berendsen ✓ | Berendsen ✓ |
| `nrespa` | 1 (`5/eq1:15`) | ausente | 1 ✓ | 1 ✓ |
| `&ewald chngmask=0` | presente en **todos** (`5/eq1:23-25`; "only required to avoid SANDER error", `7/heat:28`) | **ausente** en `em1`, `em2`, `heat*`, `density_eq`, `final_eq` → con el motor `sander` que `run_MD.sh:85-87` permite, fallarían | presente ✓ | presente ✓ |
| `skinnb=5` (GPU, sistemas grandes) | `7/heat:27` | ausente | ausente | ausente |
| Restricción minimización | `ntr=1, restraint_wt=2.4, restraintmask='@GN,GO'` (`5/em1:9-11`) | — | **`ntr=0`** (`em1_WT4.in:9`) ✗ | ✓ (`:309-312`) |
| Restricción eq1 | `ntr=1, 2.4`, toda la proteína `':1-46'` (`5/eq1:17-19`) | `heat*`: `ntr=1, 5.0, '@CA,C,N,O'` (`heat1:18-20`) → **máscara vacía en SIRAH** ✗ | **`ntr=0`** (`eq1_WT4.in:17`) ✗ pese al título "proteína completa" | `':*&!@H='` (`:353`) → **restringe también WT4 e iones** (ningún bead SIRAH empieza por H) ✗ |
| Restricción eq2 | `ntr=1, 0.24, '@GN,GO'` (`5/eq2:17-19`) | `density_eq`: `2.0, '@CA,C,N,O'` (`:19-21`) máscara vacía ✗ | **`ntr=0`** (`eq2_WT4.in:17`) ✗ pese al título "esqueleto" | ✓ (`:382-384`) |
| Arranque térmico | `eq1`: `ntx=1, irest=0, tempi=0.0` → 0 K a 300 K dentro de la NPT con Langevin (`5/eq1:3,11`). Sin rampa explícita para proteínas | rampa 0→300 K en 6×10 ps con `nmropt=1` (`heat1:17,22-23`), NVT (`ntb=1`) | `eq1`: `ntx=1, irest=0, tempi=300` → **descarta velocidades** del `density_eq` y las reasigna a 300 K (`eq1_WT4.in:3,11`) | `eq1`: `tempi=0.0` (`:345`) → tras cualquier calentamiento previo **vuelve a 0 K** |
| Temperatura | 300 K (`5`), 310 K (`7`), 298 K (`2`, `8`) | 300 K ✓ | 300 K ✓ | configurable ✓ |
| `ig` | -1 (`5/eq1:10`) | -1 | -1 | -1 |
| Salida | `ntpr=ntwx=ntwr=5000` (100 ps) `ioutfm=1, ntxo=2` | `ntwx=500` (1 ps), sin `ioutfm`/`ntxo` (trayectoria ASCII) | `=50` (1 ps) | configurable (5000 por defecto) ✓ |

### 3.2 Divergencias (todas `[ESTÁTICO]`, todas confirmables con `diff`)

1. **Dos protocolos superpuestos.** `run_MD.sh:128` ejecuta 13 etapas: 2 minimizaciones →
   6 heats → density → eq1 → eq2 → final_eq → prod. SIRAH-proteína son 5. Las 8 etapas
   extra son all-atom (`dt=2 fs`, `cut=9`, SHAKE, `@CA,C,N,O`, `gamma_ln=2`). Los propios
   `CHANGELOG.md:11-12` y `ESTADO.md:73,116-119` (CIENCIA-3) ya lo reconocen; esta
   auditoría lo confirma independientemente y añade que **el script orquestador las sigue
   ejecutando** aunque se regenere con `configurar_simulacion.sh`, que **no** las toca ni
   las borra (solo escribe `em1/em2/eq1/eq2/prod`, `:300-420`).
2. **Máscaras de restricción que no seleccionan nada.** En la topología SIRAH los beads de
   esqueleto se llaman `GN`, `GC`, `GO` (`leaprc.sirah:21-23`; `tutorial/5/em1:11`).
   `'@CA,C,N,O'` (`heat1_0to50.in:20`, `density_eq.in:21`) selecciona 0 átomos. Resultado
   `[REQUIERE CORRER]`: pmemd o aborta o imprime `matches 0 atoms` y corre sin restricción;
   en ningún caso restringe el esqueleto como pretende el comentario.
3. **Las etapas SIRAH están sin restricciones** (`eq1_WT4.in:17`, `eq2_WT4.in:17`
   `ntr=0`). El protocolo oficial restringe toda la proteína (2,4) y luego el esqueleto
   (0,24) durante 30 ns para que el solvente CG se acomode; aquí la cápside de 28 620
   residuos queda libre desde el paso 1 de las etapas CG.
4. **Orden incoherente de temperaturas.** Tras 6 heats + density a 300 K, `eq1` reasigna
   velocidades (`ntx=1, irest=0`), tirando el estado térmico. Con los inputs del
   configurador el efecto es peor: `tempi=0.0` → el sistema vuelve a 0 K.
5. **Cutoff 9 Å en etapas CG.** SIRAH exige 12 Å; WT4 tiene beads grandes y el PME con
   `cut=9` sobre beads SIRAH cambia las interacciones de corto alcance.
6. **Fricción Langevin 2 ps⁻¹** en etapas CG (ref. 50 para proteínas en WT4). Con `dt=2 fs`
   es irrelevante, pero muestra que esos inputs no fueron pensados para SIRAH.
7. **Barostato Monte Carlo** (`barostat=2`) no aparece en ningún `.in` oficial SIRAH; no es
   necesariamente incorrecto pero no está validado por el force field.
8. **Sin `&ewald chngmask=0`** en 11 de 13 archivos: con `sander` (motor que el script
   admite) fallan; con `pmemd.cuda` no importa.
9. **Trayectorias ASCII** en heats/density/final (`ioutfm` ausente) → para 400 k partículas
   y `ntwx=500` serían decenas de GB; coherente con "nunca se corrieron completos".

---

## 4. Tarea 3 — Consistencia del setup del sistema

### 4.1 Lo que hay en el repo (medido aquí con Python, `[ESTÁTICO]`)

| Componente | Medición | Fuente |
|---|---|---|
| Cápside | 216 780 átomos pesados, **0 hidrógenos**, 28 620 residuos, **180 subunidades** = 60 × (A 41–189, B 26–189, C 26–189) con **IDs de cadena y numeración repetidos** 60 veces; radio interno 89,5 Å, externo 143,6 Å (Ø ≈ 287 Å). CCMV-like T=3; primer átomo idéntico al de `sustratinaitor/1_capside/3J7L_cg.pdb` (`197.216 198.950 314.271`) | `empaquetador/capside.pdb`, `capside_recentrada.pdb` |
| Enzima | 3 973 átomos pesados, 0 hidrógenos, 497 residuos (GCasa, 1 cadena, `CRYST1` de cristal), **88 átomos con altloc**, 7 Cys, Rmax 42,8 Å | `empaquetador/enzima.pdb` |
| Empaquetado | 1 enzima, COM a 47 Å del centro, distancia mínima enzima-cápside 23 Å, 0 violaciones Packmol ("Initial approximation is a solution") | `capside_1enzimas_20260324_212620.pdb`, `log_packmol_*.txt` |
| Registros `TER` | `capside.pdb`: **180** · `capside_recentrada.pdb`: **3** · PDB empaquetado: **0** · `sustratinaitor/1_capside/3J7L_cg.pdb` (comparador correcto): **180** | medido con `grep -c '^TER'` |
| Carga neta estimada | cápside K+R−D−E = **0** (1980+1020−1080−1920); enzima **−4**; His neutras (SIRAH mapea `HIS`→`sHe`, `sirah_prot.map:143`); termini ±1 por cadena se cancelan → sistema ≈ −4 | conteo de CA por `resname` |
| Residuos cuyo bead SIRAH se mapea desde un hidrógeno | cápside: SER 1980, THR 1260, CYS 180, TRP 360 = **3 780**; enzima: 36+31+7+12 = **86** | `sirah_prot.map:87,238,248,261` |

### 4.2 Hallazgos de setup

**S-1 — Sin hidrógenos en la ruta automatizada → 3 866 beads ausentes.** `[ESTÁTICO]`
`run_maestro.sh:58-63` dice explícitamente *"salta pdb2pqr"* y pasa el PDB empaquetado
(sin H) a `cgconv.pl`. SIRAH mapea `BPG` de SER/THR/CYS y `BPE` de TRP **desde `HG`,
`HG1`, `HE1`** (`tools/CGCONV/maps/sirah_prot.map:87,238,248,261`) y su ayuda advierte:
*"the user is warned to use protonated input structures"* (`cgconv.pl:358-359`). Esos beads
no estarían en el PDB CG; tLeaP los añadiría con geometría de plantilla, generando
clashes y fuerzas enormes en el primer paso. **Comparador:** el CG de la misma cápside en
`sustratinaitor/1_capside/3J7L_cg.pdb` **sí** tiene 3 420 beads `BPG` (= 1 980 + 1 260 + 180),
es decir, el autor sí sabe generar el CG correcto por otra ruta (con hidrógenos).
`convert_to_cg.sh:27` (pdb2pqr → cgconv) sería la ruta correcta, pero `run_maestro.sh`
no la usa.
*Confirmar:* `perl cgconv.pl -i capside_1enzimas_*.pdb -o test-cg.pdb && grep -c " BPG " test-cg.pdb`
(esperado correcto: 3 494 = SER 2 016 + THR 1 291 + CYS 187; esperado con el PDB actual: 0)
y en `leap.log` buscar `Added missing heavy atom`.

**S-2 — Sin `TER` → topología encadenada.** `[ESTÁTICO]` (el efecto en tLeaP `[REQUIERE CORRER]`)
La función `recentrar()` (`2Empaquetador_Manual.py:23-31`, `2Empaquetador_Maximo.py:38-46`)
re-guarda con PyMOL, que colapsa 180 `TER` en 3 (uno por letra de cadena). Packmol, sin
`add_amber_ter`, escribe **0** `TER` (`packmol_tmp.inp` no lo incluye). `cgconv.pl:227-236`
solo propaga `TER` si lo encuentra. tLeaP corta cadenas únicamente en `TER` (ignora el
chain ID): 180 subunidades + 1 enzima quedarían unidas en una sola cadena con ~180 enlaces
peptídicos espurios de 50–250 Å, y solo 2 residuos terminales (`nX`/`cX`,
`leaprc.sirah` `addPdbResMap`) en vez de 362. Esto por sí solo explica una explosión en
`heat1`. *Confirmar:* `grep -c '^TER' capside-*-cg.pdb` (esperado ≥ 181) y, tras tLeaP,
`cpptraj -p X.prmtop <<< "parminfo"` → número de moléculas de soluto (esperado 181, no 1).
Corrección estándar: `pdb4amber` o `add_amber_ter` en Packmol antes de cgconv.

**S-3 — Disulfuros de la enzima no modelados.** `[ESTÁTICO]`
GCasa tiene 7 Cys y puentes disulfuro; `enzima.pdb` no trae `SSBOND` (0 registros) y
`gensystem.leap` no tiene ningún `bond`. SIRAH exige renombrar `CYS→CYX` antes de cgconv
(mapea a `sX`, `sirah_prot.map:98-104`) y añadir `bond` en LEaP. Las 7 Cys quedarían como
`sC` libres. *Confirmar:* distancias SG–SG < 2,3 Å en `enzima.pdb`.

**S-4 — IDs de cadena y numeración repetidos 60 veces.** `[REQUIERE CORRER]`
Irrelevante para tLeaP si hay `TER`, pero **rompe la ruta `convert_to_cg.sh`**:
`pdb2pqr --ff=AMBER` indexa residuos por (cadena, número) y recibe 60 residuos "A 41".
Resultado probable: error o fusión de residuos. También hace frágil el análisis
(`generar_analisis_individual.py:164` pide "residuos por enzima" y parte bloques por
número de residuo). *Confirmar:* correr `pdb2pqr --ff=AMBER capside_1enzimas_*.pdb t.pqr`
y comparar número de residuos de salida con 29 117.

**S-5 — Caja e iones distintos de la referencia y del motor hermano.** `[ESTÁTICO]`
`gensystem.leap:17` `solvateOct protein WT4BOX 12 0.7`; `sustratinaitor/.../gensystem.leap:16`
usa **20** (valor del tutorial SIRAH). Con `cut=12` y 12 Å de colchón, la distancia mínima
soluto–imagen es ~24 Å: funciona, pero es la mitad de lo que usa el autor en el otro motor
para la misma cápside. `gensystem.leap:15` promete "counterions and 0.15M NaCl" y
`gensystem.leap:18` solo ejecuta `addIonsRand protein NaW 0` (≈ 4 Na⁺ para neutralizar
−4; **ni ClW ni sal**). El tutorial SIRAH añade NaW y ClW explícitos. `[REQUIERE CORRER]`
para la carga exacta: `charge protein` en `leap.log`.

**S-6 — Resolución mezclada en el proyecto.** `[ESTÁTICO]`
El Studio (`nanocapsule-mvp/src/services/md.py:166-176`) genera inputs **all-atom**
(`ff19SB`, `gaff2`, `TIP3P`, `solvateOct ... TIP3PBOX 10`) para la misma cápside; PackMan
es CG SIRAH; sustratinaitor es CG + ligando all-atom (CIENCIA-2). Tres resoluciones para
el mismo sistema, sin un documento que fije cuál es la del resultado reportado.

**S-7 — Altlocs.** `[ESTÁTICO]` cgconv se queda con la posición `A` (`cgconv.pl:245,359-360`),
así que los 88 átomos alternos de la enzima no duplican beads. **OK**, pero `pdb2pqr` en
la otra ruta debe recibir `--keep-chain`/limpieza previa; no se hace.

**S-8 — Lo que está bien del setup.**
- `leaprc.sirah` cargado vía `addPath` + `source` como en el tutorial. ✓
- Closeness 0,7 en `solvateOct` = tutorial. ✓
- `saveAmberParmNetcdf` produce el `.ncrst` que `run_MD.sh:105` espera. ✓
- Radio interno 90 Å (`radio_interno.txt`) coincide con el medido aquí (89,5 Å). ✓
  (Aunque `2Empaquetador_Manual.py:14` lo tiene **hardcodeado** a 90 e ignora el archivo;
  `run_maestro.sh:38` usa justamente el Manual.)
- Packmol determinista (semilla por defecto 1234567 en el log), 0 violaciones, enzima a
  23 Å de la cápside. ✓
- Las máscaras del análisis (`@GN,GO,GC`) sí son CG-aware. ✓

---

## 5. Tarea 4 — Reproducibilidad

| Pregunta | Respuesta | Evidencia |
|---|---|---|
| ¿Semillas fijas? | **No.** `ig=-1` en los 11 `.in` dinámicos. Igual que SIRAH, pero sin ningún `mdout` commiteado no hay forma de recuperar la semilla usada. | `heat1_0to50.in:16`, `eq1_WT4.in:10`, `prod_md_WT4.in:10` … |
| ¿Semilla de empaquetado? | Sí (Packmol 1234567 por defecto; log lo registra). Determinista. | `log_packmol_1enzimas_20260324_212620.txt:18` |
| ¿Qué código generó qué? | Indeterminable: `.in` sin historia (`d5035a2`), `prod-q_gpu.bsub` apunta a un sistema `capside-3_cg-WAT` que ningún script genera, `copy_md_files.sh:4` habla de "archivos del 26 de agosto". | §2.2 |
| ¿Hay outputs? | **Ninguno**: ni `prmtop`, `leap.log`, `mdout`, `.nc`, `.dat`. `.gitignore` no los excluye explícitamente; simplemente nunca se añadieron. | `.gitignore` |
| ¿Qué se "reporta"? | `ESTADO.md:49,59` y `PENDIENTES.md:59`: "MD NUNCA corrida", pestaña MD "ilustrativa". **Pero** `nanocapsule-mvp/src/services/md.py:65-122` ancla curvas sintéticas a cifras concretas ("RMSD final 2.8 Å", "SASA ~41.893 Å²", "RMSF r=0.81" / "r=0.12 el bug de hoy", **"heat1 → 17.666 K · el fallo real"**, `source: packmanreplicas1/1_2`). `texto_tesis_archivos_dm.md:27` habla de un directorio `ReplicaExtra` que no existe. | `md.py:31,69,84-87` |
| ¿Los inputs commiteados reproducen eso? | **No.** 10 ps de producción no pueden dar un RMSD "que converge a 2,8 Å" (≥ decenas de ns). La explosión de `heat1` sí es reproducible en el sentido opuesto: con S-1/S-2 y las máscaras vacías es el resultado esperable. | §2, §3, §4 |
| ¿Nombres estables entre etapas? | `run_MD.sh` escribe `${NAME}_prod.nc`; el `.bsub` escribe `_prod_md.nc`; el análisis busca `*prod*.nc` (`generar_analisis_individual.py:131`) → ambos encajan. Pero `run_maestro.sh:75` llama a `ejecutar_analisis_cpptraj.sh`, **que no existe** (existe `ejecutar_analisis_individual.sh`, que además exige correr antes un generador interactivo). | listado de `analisis/` |

---

## 6. Hallazgos numerados (severidad → evidencia → cómo confirmar)

Escala: **CRÍTICO** (invalida cualquier corrida) · **ALTO** (resultado físicamente
incorrecto o no comparable) · **MEDIO** (desvía del protocolo validado) · **BAJO**
(higiene, fragilidad) · **INFO**.

| # | Sev. | Hallazgo | Evidencia (archivo:línea) | Confirmar con | Tipo |
|---|---|---|---|---|---|
| MD-01 | **CRÍTICO** | `eq1`, `eq2`, `prod` son stubs de 10 ps (títulos: 15 ns, 35 ns, "fast test") | `eq1_WT4.in:1,5` · `eq2_WT4.in:1,5` · `prod_md_WT4.in:1,5` vs `tutorial/5/{eq1,eq2,md}_WT4.in:5` | `grep -H nstlim archivos_dm_cg/*.in` | ESTÁTICO |
| MD-02 | **CRÍTICO** | Ruta `run_maestro.sh` alimenta cgconv sin hidrógenos → 3 866 beads `BPG/BPE` ausentes | `run_maestro.sh:58-63` · `sirah_prot.map:87,238,248,261` · `cgconv.pl:358-359` · 0 átomos H en `capside_1enzimas_*.pdb` | `cgconv.pl -i capside_1enzimas_*.pdb -o t.pdb; grep -c ' BPG ' t.pdb` (esperado 3 494 si estuviera bien) | ESTÁTICO |
| MD-03 | **CRÍTICO** | PDB empaquetado sin `TER` → tLeaP encadena 181 moléculas en una | `capside_recentrada.pdb` (3 TER), `capside_1enzimas_*.pdb` (0 TER) vs `capside.pdb` (180) · `cgconv.pl:227-236` · `2Empaquetador_Manual.py:23-31` | `grep -c '^TER'` en cada PDB; tras tLeaP `cpptraj -p X.prmtop` + `parminfo` (moléculas de soluto: esperado 181) | ESTÁTICO (efecto: REQUIERE CORRER) |
| MD-04 | **ALTO** | 8 de 13 etapas son all-atom sobre topología CG (`dt=2 fs`, `cut=9`, SHAKE, `gamma_ln=2`, `@CA,C,N,O`) | `heat1_0to50.in:7,8,12,15,20` · `density_eq.in:7,8,11,17,21` · `final_eq.in:7,8,11,17` vs `tutorial/5/eq1_WT4.in:5,10,13,15` | `diff heat1_0to50.in sirah_x2.3_24-07.amber/tutorial/7/heat_Prot-Lip.in` | ESTÁTICO |
| MD-05 | **ALTO** | Máscaras `@CA,C,N,O` seleccionan 0 beads SIRAH; `ntr=1` sin efecto o abortando | `heat1..6:20`, `density_eq.in:21` · nombres de beads en `leaprc.sirah:21-23` y `amino.lib` | en `mdout`: `grep -i "matches" *_heat1.out` (verá `matches 0 atoms`) | ESTÁTICO / efecto REQUIERE CORRER |
| MD-06 | **ALTO** | Etapas SIRAH sin restricciones (`ntr=0`) contra protocolo 2,4 → 0,24 kcal·mol⁻¹·Å⁻² sobre `@GN,GO` | `em1_WT4.in:9` · `eq1_WT4.in:17` · `eq2_WT4.in:17` vs `tutorial/5/em1:9-11`, `eq1:17-19`, `eq2:17-19` | `grep -H "ntr" archivos_dm_cg/*.in` | ESTÁTICO |
| MD-07 | **ALTO** | Disulfuros de GCasa no modelados (sin `CYX`, sin `bond`) | `gensystem.leap` (sin `bond`) · `enzima.pdb` (0 `SSBOND`, 7 Cys) · `sirah_prot.map:98-104` | distancias SG–SG en `enzima.pdb`; `grep -c sX capside-*-cg.pdb` (esperado > 0) | ESTÁTICO |
| MD-08 | **ALTO** | Sin outputs ni semilla registrada: nada de lo "reportado" es reproducible; las cifras del Studio son sintéticas | `md.py:20-62,65-122` · `ESTADO.md:49,59` · `ig=-1` en todos los `.in` | pedir a Lucio `mdout`/`leap.log`/`.nc` de `packmanreplicas1/1_2` | ESTÁTICO |
| MD-09 | **MEDIO** | `configurar_simulacion.sh` genera `eq1` con `restraintmask=':*&!@H='` → restringe **todo** el sistema (WT4 e iones incluidos) | `configurar_simulacion.sh:353` · ningún bead SIRAH empieza por H (`amino.lib`, `solv.lib`, `ions.lib`) | tras correr, `grep matches *_eq1.out` (esperado ≈ nº total de partículas) | ESTÁTICO |
| MD-10 | **MEDIO** | `configurar_simulacion.sh` no elimina ni regenera `heat*/density_eq/final_eq`; `run_MD.sh` las sigue ejecutando; su `eq1` tiene `tempi=0.0` → re-enfría tras calentar | `configurar_simulacion.sh:300-420` (solo 5 archivos) · `run_MD.sh:128,174-258` · `:345` | `bash configurar_simulacion.sh; ls archivos_dm_cg/*.in` | ESTÁTICO |
| MD-11 | **MEDIO** | `eq1` descarta velocidades (`ntx=1, irest=0`) tras 110 ps de calentamiento+densidad | `eq1_WT4.in:3` · `run_MD.sh:269` | `grep -A2 "ntx" *_eq1.out` | ESTÁTICO |
| MD-12 | **MEDIO** | Caja 12 Å vs 20 Å (tutorial SIRAH y `sustratinaitor`); solo NaW, sin ClW ni 0,15 M pese al comentario | `gensystem.leap:15-18` vs `sustratinaitor/4_ensamblaje_y_simulacion/gensystem.leap:16-17` | `leap.log`: `charge protein`, número de `NaW`/`ClW` añadidos | ESTÁTICO / carga REQUIERE CORRER |
| MD-13 | **MEDIO** | `pdb2pqr` (ruta `convert_to_cg.sh`) recibe 60 copias de "cadena A, residuo 41…" | `convert_to_cg.sh:27` · estructura de `capside_1enzimas_*.pdb` (§4.1) | `pdb2pqr --ff=AMBER capside_1enzimas_*.pdb t.pqr` y contar residuos | REQUIERE CORRER |
| MD-14 | **MEDIO** | Barostato MC y `cut=9` en etapas CG no validados por SIRAH; sin `chngmask=0` en 11/13 `.in` (falla con `sander`); sin `skinnb=5` para GPU en sistema de ~400 k partículas | `density_eq.in:11,14` · `final_eq.in:11,14` · `tutorial/7/heat_Prot-Lip.in:27-28` | correr `pmemd.cuda` 100 pasos y leer errores de `skinnb` | ESTÁTICO / REQUIERE CORRER |
| MD-15 | **MEDIO** | Análisis RMSF sin alineamiento previo (`atomicfluct` sin `rms` antes) → RMSF contaminado por traslación/rotación global; coincide con el "RMSF sin ajuste r=0.12 · el bug de hoy" del Studio. `surf` (LCPO) no tiene parámetros para beads SIRAH | `generar_analisis_individual.py:266-275,285-291` · `md.py:102-110` | `cpptraj` con y sin `rms first` antes de `atomicfluct`; revisar warnings de `surf` | ESTÁTICO / REQUIERE CORRER |
| MD-16 | **BAJO** | `run_maestro.sh` llama a `analisis/ejecutar_analisis_cpptraj.sh` (no existe); `setup_1_1o.sh:31-34` y `setup_universal_md.sh:41-44` usan `gensystem_template.leap` y `run_MD_template.sh` (no existen); `N_ENZIMAS` de `1_1o` sería `1o` | `run_maestro.sh:75` · listado de `archivos_dm_cg/` | `ls archivos_dm_cg/*template*` | ESTÁTICO |
| MD-17 | **BAJO** | `2Empaquetador_Manual.py` ignora `radio_interno.txt` (hardcode 90); `1calcula_radio_interno.py` suma +1 Å al radio de colisión (CIENCIA-1) | `2Empaquetador_Manual.py:14` · `1calcula_radio_interno.py:38-41` | — | ESTÁTICO |
| MD-18 | **BAJO** | `prod-q_gpu.bsub` documenta una ruta manual en clúster con nombres de sistema no generados por ningún script, saltando `final_eq` | `prod-q_gpu.bsub:12` | pedir el directorio del clúster | ESTÁTICO |
| MD-19 | **INFO** | Versión SIRAH: carpeta `x2.3_24-07`, `leaprc` "2.3 [Nov 2023]", `0README` "March 2025". Registrar cuál se usó | `leaprc.sirah:7` · `0README:3` | — | ESTÁTICO |
| MD-20 | **INFO** | Trayectorias ASCII (`ioutfm` ausente) en heats/density/final; `ntwx=500` → decenas de GB | `heat1_0to50.in:11` | — | ESTÁTICO |

---

## 7. Lo que está bien (para no tirar lo que funciona)

- El empaquetado es determinista, está documentado y tiene log de ejecución real
  (`log_packmol_1enzimas_20260324_212620.txt`): 0 violaciones, enzima a 23 Å de la pared.
- `eq1/eq2/prod_md` **sí** tienen la física SIRAH correcta en todo salvo duración y
  restricciones (`dt=20 fs`, `cut=12`, `ntc=ntf=1`, `gamma_ln=50`, `chngmask=0`, NPT).
- `configurar_simulacion.sh` genera `em1/em2/eq2/prod` prácticamente idénticos al tutorial
  (restricciones `@GN,GO` 2,4/0,24, duraciones reales). Solo falla la máscara de `eq1`
  (MD-09) y `gamma_ln=5` vs 50.
- `gensystem.leap` carga SIRAH correctamente, usa closeness 0,7 y `saveAmberParmNetcdf`
  coherente con `run_MD.sh`.
- El análisis usa máscaras CG (`@GN,GO,GC`) y busca `*prod*.nc`, compatible con ambos
  nombres de salida.
- El autor **ya produjo un CG correcto de esta cápside** (`sustratinaitor/1_capside/3J7L_cg.pdb`:
  180 `TER`, 3 420 `BPG`), lo que demuestra que la ruta con hidrógenos funciona.

---

## 8. Qué correr para cerrar cada hallazgo (orden recomendado)

Todo esto exige AmberTools (tleap, cpptraj), pdb2pqr y, para el paso 5, pmemd.cuda. Sin
GPU, los pasos 1–4 bastan para confirmar MD-02, MD-03, MD-05, MD-07, MD-12 y MD-13.

```bash
cd PackMan.v.1.2/archivos_dm_cg/empaquetador

# 1) MD-03: TER por etapa
grep -c '^TER' capside.pdb capside_recentrada.pdb capside_1enzimas_20260324_212620.pdb

# 2) MD-02: beads que cgconv puede/no puede generar sin H
perl ../sirah_x2.3_24-07.amber/tools/CGCONV/cgconv.pl -i capside_1enzimas_20260324_212620.pdb -o sinH-cg.pdb
grep -c ' BPG ' sinH-cg.pdb        # esperado 0 (defecto). Correcto: 3494
pdb4amber -i capside_1enzimas_20260324_212620.pdb -o conTER.pdb --add-missing-atoms   # añade TER por distancia
pdb2pqr --ff=AMBER --keep-chain conTER.pdb conH.pqr                                     # MD-13: ¿sobrevive la numeración repetida?
perl ../sirah_x2.3_24-07.amber/tools/CGCONV/cgconv.pl -i conH.pqr -o conH-cg.pdb
grep -c ' BPG ' conH-cg.pdb; grep -c '^TER' conH-cg.pdb                                 # esperado 3494 y >=181

# 3) MD-03/MD-07/MD-12: topología
cd .. && sed "s/AUTO_DETECT_CAPSID/empaquetador\/conH-cg.pdb/; s/AUTO_DETECT_OUTPUT/test/" gensystem.leap > t.leap
tleap -f t.leap | tee tleap.out
grep -i "charge\|Added missing\|Warning\|NaW\|ClW" leap.log | head -40
cpptraj -p test.prmtop <<< "parminfo"           # nº de moléculas de soluto: esperado 181

# 4) MD-05/MD-06: máscaras sobre la topología real (sin dinámica)
cpptraj -p test.prmtop <<< $'mask @CA,C,N,O\nmask @GN,GO\nmask :*&!@H='
# esperado: 0 átomos · ~58 000 · TODO el sistema (confirma MD-05 y MD-09)

# 5) [GPU] Humo de 1 000 pasos con el protocolo SIRAH correcto (tutorial/5) en vez de heat*
for s in em1 em2; do pmemd.cuda -O -i sirah_x2.3_24-07.amber/tutorial/5/${s}_WT4.in -p test.prmtop -c test.ncrst -ref test.ncrst -o ${s}.out -r ${s}.ncrst; done
sed 's/nstlim = 250000/nstlim = 1000/; s/:1-46/:1-29117/' sirah_x2.3_24-07.amber/tutorial/5/eq1_WT4.in > eq1_smoke.in
pmemd.cuda -O -i eq1_smoke.in -p test.prmtop -c em2.ncrst -ref em2.ncrst -o eq1_smoke.out
grep -E "TEMP\(K\)|EKtot|Density" eq1_smoke.out | tail -5          # ¿T estable ~300 K, sin NaN?
```

**Criterio de aceptación** para dar la MD por "bien montada": `parminfo` reporta 181
moléculas de soluto; `grep -c ' BPG '` = 3 494; `leap.log` sin `Added missing`; máscara
`@GN,GO` ≠ 0; `eq1_smoke.out` termina con T ≈ 300 K y sin `NaN`/`vlimit`. Solo entonces
tiene sentido lanzar 5 ns + 25 ns + ≥ 100 ns con `ig` **fijo y anotado**.

---

## 9. Qué pedir a Lucio (fuera del repo)

- Los `mdout` y `leap.log` de `packmanreplicas1/1_2` (origen del "heat1 → 17 666 K").
- Los `.in` reales que se lanzaron en el clúster (`prod-q_gpu.bsub` apunta a
  `capside-3_cg-WAT`); el `.pdb` CG y `.prmtop` de ese sistema.
- Qué ruta generó el CG: `convert_to_cg.sh` (con pdb2pqr) o `run_maestro.sh` (sin). El
  comparador `3J7L_cg.pdb` sugiere que para sustratinaitor se usó una ruta con hidrógenos.
- Si el barostato MC y `cut=9` fueron decisión consciente (CIENCIA-3) o herencia all-atom.

---

## 10. Cross-check contra `REVISION_MOTORES_hallazgos_sellados.md`

*(Leído después de cerrar las secciones 0–9. La pasada previa se limitó a leer código;
esta también midió los PDB y la distribución SIRAH.)*

### 10.1 Coincidencias (la pasada previa lo sospechaba; aquí queda confirmado con evidencia)

| Sospecha previa (sellado) | Estado en esta auditoría |
|---|---|
| `heat1..6` con parámetros all-atom (`dt=0.002`, SHAKE, `cut=9`, `@CA,C,N,O`); "los beads parecen llamarse GN/GC/GO" | **Confirmado y ampliado** (MD-04, MD-05): también `density_eq.in` y `final_eq.in`; la máscara selecciona 0 beads según censo de nombres en `amino.lib`/`solv.lib`/`ions.lib`, no "parece". |
| `prod_md_WT4.in` y `eq1_WT4.in` con `nstlim=500`, ¿stubs? | **Confirmado** (MD-01) y añadido `eq2_WT4.in` (también 500). Cuantificado: 240 ps totales vs 1,03 µs de referencia. |
| Comentario "0.15M NaCl" ≠ `addIonsRand NaW 0` | **Confirmado** (MD-12), con carga estimada −4 y comparación con `sustratinaitor` (caja 20 vs 12). |
| "Positivo: `prod/em/eq` coinciden con la referencia SIRAH" | **Solo parcialmente.** Física sí (`dt`, `cut`, `ntc/ntf`, `chngmask`), pero **`em1`, `eq1` y `eq2` tienen `ntr=0`** donde SIRAH exige 2,4 → 0,24 sobre `@GN,GO` (MD-06), y la frecuencia de salida es de prueba. No lo daría por "positivo". |

### 10.2 Dónde difiere mi juicio del previo

1. **El defecto más grave no está en los `.in`, está en la preparación del sistema.** La
   pasada previa no detectó que la ruta automatizada entrega a `cgconv.pl` un PDB **sin
   hidrógenos** (MD-02: 3 866 beads imposibles de mapear) y **sin `TER`** (MD-03: 181
   moléculas encadenadas). Cualquiera de los dos invalida la topología antes del primer
   paso de dinámica, independientemente de cómo se arreglen los `.in`. La explosión a
   17 666 K de `heat1` que el Studio registra como "el fallo real" se explica mejor por
   esto que por SHAKE.
2. **La verificación que propone el sellado ("mira si SHAKE tiró error en `*_heat*.out`")
   no encontraría nada.** `leaprc.sirah:10-11` asigna elemento `V` a los beads justamente
   para que `ntc=2` no actúe; SHAKE sobre SIRAH es un no-op, no un error. Lo que hay que
   mirar en esos `.out` es `matches 0 atoms` (MD-05), `Added missing heavy atom` en
   `leap.log` (MD-02) y el número de moléculas en `parminfo` (MD-03).
3. **Disulfuros de la enzima** (MD-07): no mencionados antes. SIRAH los exige explícitos
   (`CYX`→`sX` + `bond`).
4. **`configurar_simulacion.sh` no es "los `.in` correctos" sin más** (como afirma
   `ESTADO.md:117`): su `eq1` restringe todo el sistema incluido el solvente (MD-09), usa
   `gamma_ln=5` (tutorial 7) en vez de 50 (tutorial 5) y deja intactos los 8 `.in` all-atom
   que `run_MD.sh` sigue ejecutando (MD-10).
5. **Las cifras "reportadas" son sintéticas** (MD-08): el sellado no cruzó
   `nanocapsule-mvp/src/services/md.py` con PackMan. RMSD 2,8 Å, SASA 41 893 Å² y los
   r de RMSF son `math.sin`; no existe ningún `.dat`, `mdout` ni `.nc` en el repo.
6. **Análisis**: RMSF sin `rms` previo y `surf` LCPO sobre beads sin parámetros (MD-15);
   script orquestador llamando a un análisis inexistente (MD-16). No estaban en el sellado.
7. **Reproducibilidad de la ruta real**: `prod-q_gpu.bsub` apunta a un sistema
   (`capside-3_cg-WAT`) que ningún script genera (MD-18). El sellado no lo cubre.

### 10.3 Lo que el sellado dice y yo no puedo juzgar aquí

- sustratinaitor (resolución mixta), Poromania (HOLE sin `rseed`, eje del poro) y Packing
  del Studio (±1 Å) quedan fuera del alcance de esta auditoría (solo PackMan). Lo único que
  toqué de sustratinaitor fue usar su `gensystem.leap` y su `3J7L_cg.pdb` como comparadores,
  y ambos salen **mejor** que los de PackMan (caja 20 Å; CG con 180 `TER` y beads `BPG`).
