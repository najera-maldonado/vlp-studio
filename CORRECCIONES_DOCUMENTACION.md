# Correcciones a la documentación pública — VLP Studio

> **Qué es.** El inventario de cada afirmación de la documentación pública del repositorio que
> las auditorías independientes de los cuatro motores (2026-10-04) desmienten, con el archivo
> y la línea donde estaba, la evidencia (informe de auditoría + comando reproducible desde el
> propio repo), y el texto honesto que la sustituye. Todas las correcciones de esta lista
> **ya están aplicadas** en los archivos; este documento es el registro de por qué.
>
> **Motivo.** El repo es público y había una rama con el paquete de envío a JOSS
> (`origin/claude/prepare-joss-submission-29k493`) escrita **antes** de que concluyeran las
> auditorías. Afirmaba cosas que los informes ahora refutan. El objetivo es que nadie —ni un
> revisor de JOSS ni un usuario— lea en este repositorio una afirmación que el propio
> repositorio puede refutar.
>
> **Fuentes** (todas del 2026-10-04, un commit sobre `40f4b03`, sin fusionar en `main`):
> - `HOJA_DE_RUTA.md` — rama `claude/consolidate-audit-roadmap-k82rek` (consolida las 9)
> - `AUDITORIA_PACKING.md` — rama `claude/audit-packing-engine-wwph45` (motor ejecutado con doble)
> - `AUDITORIA_MD.md` — rama `claude/audit-packman-dynamics-engine-52svym`
> - `AUDITORIA_PORO.md` — rama `claude/audit-poro-engine-giea7e`
> - y las complementarias citadas en `HOJA_DE_RUTA.md §9`.
>
> Las líneas citadas son las del archivo **antes** de la corrección; tras aplicar las
> correcciones el texto se movió. Los números de línea de *código* (`.py`, `.sh`, `.in`) son
> los del código vivo y no cambian con este pase (la reparación del código es otra tarea; ver
> `HOJA_DE_RUTA.md`).

---

## 0. Resumen por archivo

| Archivo de documentación | Afirmaciones corregidas | Severidad máxima |
|---|---|---|
| `README.md` (raíz) | puertas 1 y 2 "reales"; "deterministic packing, fixed seed"; golden test; SIRAH no redistribuido | CRÍTICA |
| `nanocapsule-mvp/README.md` | packing "real (multi-replica)"; config que el código no lee; golden test cubre el packing; determinismo | CRÍTICA |
| `Poromania.v.1.2./README.md` | "most mature — real and end to end"; parámetros "tuned"; `1run_hole_old.sh` es código muerto | CRÍTICA |
| `PackMan.v.1.2/README.md` | "protocol complete"; "runnable"; heating en 6 etapas; `configurar_simulacion.sh` genera los `.in` correctos | CRÍTICA |
| `sustratinaitor/README.md` | "17 beads por centro de masa"; "compatible con SIRAH"; etapa 4 ejecutable | ALTA |
| `paper.md` | "reproducible / deterministic seed base"; "gates 1 and 2 real measurements"; "complete, runnable protocol" | CRÍTICA |
| `JOSS_CHECKLIST.md` | "Reproducibility DONE"; "gates 1 and 2 real"; "licence clearly stated"; "no git tags" | CRÍTICA |
| `docs/usage.md`, `docs/installation.md` | determinismo; seed base; golden test; timeout 300 s | ALTA |
| `CONTRIBUTING.md`, `THIRD_PARTY.md`, `CITATION.cff` | SIRAH no redistribuido; "needs a simulation to decide" | ALTA |
| `PENDIENTES.md`, `ESTADO.md`, `BITACORA.md` (internos) | "packing terreno firme"; "PAC-PORE real de punta a punta"; "motor listo" | CRÍTICA |
| Documentos fósiles (`CLAUDE.md` ×2, `PLAN_POROMANIA.md`, `SESION_STUDIO.md`, …) | 1.92 Å; cpoint fijo; scripts inexistentes; endpoints inexistentes | CRÍTICA |

Las dos frases falsas que el encargo citaba como ejemplo son C-01 (packing determinista con
golden test) y C-20 (MD de 15/35 ns). Todo lo demás se encontró revisando los mismos
archivos contra los informes.

---

## 1. Packing (puerta 2 · "Dentro")

### C-01 — "El packing es geométrico, determinista (semilla fija, golden test)" — FALSA

- **Dónde:** `README.md` (raíz) "Reproducibility: Deterministic packing — Packmol runs with a
  fixed seed base … repeats bit for bit"; `nanocapsule-mvp/README.md` "Packing is geometric
  and deterministic under a fixed seed base, which makes it the most trustworthy numerical
  output"; `PENDIENTES.md:15-16`; `BITACORA.md` entrada (23); `docs/usage.md` "geometric,
  deterministic and covered by a golden test".
- **Por qué es falsa (dos mitades, ninguna se sostiene):**
  1. **No hay semilla fija en la ruta de producción.** `experiment_runner.py:160` llama a
     `run_parallel_replicas` **sin** `seed_base`; entonces `parallel_packer.py:118` usa
     `random.randint(1, 1000000)` sobre el RNG global sin sembrar. Las claves
     `engines.packmol.seed_base` y `use_random_seeds` del YAML **no las lee ningún módulo**.
  2. **El golden test no es del packing.** `tests/test_golden_science.py` importa y prueba
     `substrate_section` (puerta 1, poro), no el radio, ni el input de Packmol, ni el criterio
     de aceptación. Cobertura del motor de packing: cero.
- **Evidencia** (`AUDITORIA_PACKING.md` P-05, G-01; `HOJA_DE_RUTA.md` C4, C11):
  ```bash
  grep -rn "seed_base\|use_random_seeds" nanocapsule-mvp/src/      # solo parallel_packer lo acepta como arg; nadie lo pasa
  grep -n "random.randint\|seed_base" nanocapsule-mvp/src/core/experiment_runner.py   # no aparece seed_base
  grep -n "substrate_section\|parallel_packer\|capsid" nanocapsule-mvp/tests/test_golden_science.py  # solo substrate_section
  ```
- **Sustituida por:** descripción del estado real (semillas aleatorias en producción, la
  semilla usada queda en `metadata.json`; el golden test cubre solo `substrate_section`; el
  packing no tiene tests). Ver `README.md` §Reproducibility, `nanocapsule-mvp/README.md`
  §Configuration/§Reproducibility notes, `docs/usage.md`.

### C-02 — "Puerta 2: real (empaquetamiento multi-réplica)" — ENGAÑOSA (el número no es una medición)

- **Dónde:** `README.md` (raíz) tabla del embudo, puerta 2 "Real (multi-replica packing)";
  `nanocapsule-mvp/README.md` tabla "STUDIO 3D … Real"; `ESTADO.md:20`; `docs/usage.md:34`.
- **Por qué:** el criterio que decide cuántas enzimas caben **no mide el empaquetamiento**.
  1. **Criterio primario muerto:** `parallel_packer.py:35,192` busca `Maximum distance
     violation:`; PACKMOL escribe `Maximum violation of target distance:`. Contra los dos
     logs reales del repo, la regex del motor da **0 coincidencias**.
  2. **Fallback ciego:** al no casar, `parallel_packer.py:303` acepta si el PDB tiene ≥ 10 000
     líneas atómicas; las cápsides tienen 168 480–216 780 átomos, así que la **cápside sola**
     lo cumple.
  3. **`n_packed` no se cuenta:** es el `n` que se pidió. Con un doble de PACKMOL que coloca 0
     enzimas, el motor reporta **100 enzimas, media 100, σ 0, 2/2 réplicas**.
- **Evidencia** (`AUDITORIA_PACKING.md` P-01, P-02, P-04, §1):
  ```bash
  grep -c "Maximum distance violation" PackMan.v.1.2/archivos_dm_cg/empaquetador/log_packmol_*.txt \
     sustratinaitor/3_empaquetado_packmol/packmol_run.log          # 0 y 0
  grep "Maximum violation" PackMan.v.1.2/archivos_dm_cg/empaquetador/log_packmol_*.txt | head -1
  #   -> "Maximum violation of target distance:   0.000000"  (otro orden de palabras)
  ```
- **Sustituida por:** "engine runs; capacity number under review", con los tres defectos
  nombrados, en `README.md`, `nanocapsule-mvp/README.md` (§Audit findings y la tabla de
  endpoints), `paper.md` y `docs/usage.md` (bloque "Read this before trusting the numbers").

### C-03 — "Fallback radius 90 Å" presentado como radio calculado — ENGAÑOSA

- **Dónde:** `nanocapsule-mvp/README.md` tabla de config "internal_radius_default … Fallback
  radius"; `ESTADO.md:110` "el radio casi siempre es el fallback 90 Å" (como si fuera
  anecdótico).
- **Por qué:** `capsid.py:72-77,139-142,163-168` devuelve 90.0 cuando falta PyMOL, cuando el
  bucle `range(5,200)` se agota, o ante cualquier excepción, y `/api/capsid/radius` lo rotula
  "Radio interno calculado: 90.0 Å". Para BMV el valor correcto redondea a 90, así que ningún
  resultado commiteado permite saber si PyMOL llegó a correr.
- **Evidencia:** `AUDITORIA_PACKING.md` P-11; `HOJA_DE_RUTA.md` PK-3.
- **Sustituida por:** nota explícita de que el 90 Å se devuelve en silencio y rotulado como
  calculado (tabla de config y §Known limitations del README del Studio; caveat en la fila
  `/api/capsid/radius`).

### C-04 — Tabla de parámetros de config como si el código los leyera — FALSA en 5 claves

- **Dónde:** `nanocapsule-mvp/README.md` tabla "Configuration" (`collision_margin`,
  `max_violation_threshold`, `seed_base`, `use_random_seeds`, `timeout`); `docs/usage.md` y
  `docs/installation.md` ("timeout 300 s", "use_random_seeds must be false").
- **Por qué:** `collision_margin` (hardcodeado 2.0 en `:268`), `timeout` (hardcodeado 90 en
  `:283`), `max_violation_threshold` (sin efecto por C-02), `seed_base`/`use_random_seeds`
  (no leídos) no hacen lo que la tabla dice.
- **Evidencia:** `AUDITORIA_PACKING.md` P-12, P-19, P-01, P-05; `HALLAZGOS §2.3,§2.5-2.7`.
- **Sustituida por:** tabla con columna "Effective today" que dice de cada clave si se lee o
  no y dónde está hardcodeada (README del Studio); correcciones en los troubleshooting de
  `docs/installation.md` y en `docs/usage.md`.

### C-05 — "exclusion_radius 10 Å" vs código — INCONSISTENTE

- **Dónde:** `nanocapsule-mvp/README.md` decía 10 Å; el YAML dice 5.0; el packer usa 5.0 (que
  en PACKMOL es radio por átomo → 10 Å entre enzimas, 6 Å enzima-cápside).
- **Evidencia:** `AUDITORIA_PACKING.md` P-13, P-20.
- **Sustituida por:** fila de la tabla con la semántica correcta (radio por átomo, suma de
  radios) y nota de que la capacidad depende fuertemente de esta perilla.

---

## 2. Poro (puerta 1 · "A través")

### C-10 — "Poromania: the most mature engine — real and end to end" — FALSA

- **Dónde:** `Poromania.v.1.2./README.md` bloque Status; `README.md` (raíz) puerta 1 "Real,
  end to end"; `nanocapsule-mvp/README.md` "PAC-PORE … Real, end to end"; `ESTADO.md:19,57`
  "PAC-PORE real de punta a punta … la parte más madura"; `docs/usage.md:33`.
- **Por qué:** el único resultado de poro del repo está mal atribuido en tres niveles.
  1. **El "mutante" no está mutado:** `mutants/mut_129HIS_132GLY/receptor.pdb` es
     byte-idéntico a `mutants/WT.pdb`; 129 = SER y 132 = VAL en las 5 subunidades.
  2. **No se regenera con los inputs del repo:** `1crear_mutantes.pml:5` carga
     `poronatural.pdb` (trímero CCMV, 3 574 át.), pero `WT.pdb` es `modelos/BMV/poro5fold.pdb`
     centrado (5 735 át.).
  3. **La geometría no apunta al poro:** `cpoint` a 7.59 Å del eje C5, `cvect` 19.29°
     desviado, constricción a 11.76 Å del eje.
- **Evidencia** (`AUDITORIA_PORO.md` PORO-01/02/03, §4):
  ```bash
  cmp "Poromania.v.1.2./mutants/WT.pdb" "Poromania.v.1.2./mutants/mut_129HIS_132GLY/receptor.pdb" && echo IDENTICOS
  grep -c '^ATOM' "Poromania.v.1.2./poronatural.pdb" "Poromania.v.1.2./modelos/BMV/poro5fold.pdb"  # 3574 / 5735
  ```
- **Sustituida por:** Status honesto en el README de Poromania (motor corre, resultado en
  revisión), tabla "Audit findings", `INVALIDO.md` en la carpeta del mutante, y "result under
  review" en README raíz, Studio, `paper.md`, `docs/`.

### C-11 — "Parameters tuned for the target structure" (presentado como limitación menor) — INSUFICIENTE

- **Dónde:** `Poromania.v.1.2./README.md` §Fixed parameters.
- **Por qué:** no es solo que estén fijos; los valores fijos **están mal** (C-10.3), y el eje
  del Studio está mal condicionado en trímeros (6.14°, degeneración 21 %) y su cribado deja 1
  residuo sobre el pentámero (las 5 subunidades comparten `chain A`).
- **Evidencia:** `AUDITORIA_PORO.md` PORO-07, PORO-08, PORO-09.
- **Sustituida por:** §Fixed parameters reescrita + tabla de audit findings.

### C-12 — "`1run_hole_old.sh` es código muerto a borrar" — FALSA (es la red de seguridad)

- **Dónde:** `ESTADO.md:86-87` (lista de código muerto); el README de Poromania lo listaba
  junto a los fósiles.
- **Por qué:** `1run_hole_old.sh:118-151` tenía la validación de canal (constricción a > 5 Å
  del centro → aviso) que la versión viva `1run_hole.sh` perdió; es justo la que habría
  detenido C-10.3.
- **Evidencia:** `AUDITORIA_PORO.md` PORO-04.
- **Sustituida por:** nota en `ESTADO.md §Código muerto` y en el Status del README de Poromania
  de que no se borra hasta portar su validación (PO-4).

### C-13 — Docking "real end to end" sin distinguir motores — ENGAÑOSA

- **Dónde:** `ESTADO.md:19` y `SESION_STUDIO.md:50-53` presentan el docking como una capacidad
  real única; el README de Poromania no advertía de la no-reproducibilidad.
- **Por qué:** Poromania usa idock sin semilla y con `threads=$(nproc)`; el Studio usa Vina
  con `--seed 1`; idock y Vina **no son comparables**.
- **Evidencia:** `AUDITORIA_PORO.md` PORO-14.
- **Sustituida por:** nota de "Known defects" en el bloque de docking del README de Poromania
  y fila PORO-14 de su tabla.

---

## 3. Dinámica molecular (puerta 4 · "Sobrevive")

### C-20 — "Corridas de MD de 15 ns y 35 ns" / "protocolo completo y ejecutable" — FALSA

- **Dónde:** títulos de `PackMan.v.1.2/archivos_dm_cg/eq1_WT4.in` ("15ns equilibración NPT"),
  `eq2_WT4.in` ("35ns"), `prod_md_WT4.in` ("0.01ns producción (fast test)");
  `PackMan.v.1.2/README.md` "the scripts and the protocol are complete"; `README.md` (raíz) y
  `docs/` "Protocol complete"; `paper.md` "a complete, runnable protocol";
  `texto_tesis_archivos_dm.md:17` y `diagrama_archivos_dm.md` (producción, `ReplicaExtra`).
- **Por qué:** los tres `.in` SIRAH tienen `nstlim = 500` a `dt = 0.020` ps = **10 ps cada
  uno**; las 13 etapas suman **≈ 240 ps** (la referencia SIRAH ≈ 1.03 µs). Nunca corrieron (no
  hay `mdout`, `.nc`, `leap.log` ni `.dat`). Además la ruta automatizada construye una
  topología inválida (sin H, sin `TER`).
- **Evidencia** (`AUDITORIA_MD.md` MD-01, MD-02, MD-03, §2.1):
  ```bash
  cd PackMan.v.1.2/archivos_dm_cg
  for f in eq1_WT4 eq2_WT4 prod_md_WT4; do head -1 $f.in; grep -o 'nstlim *= *[0-9]*' $f.in; done
  grep -c '^TER' empaquetador/capside.pdb empaquetador/capside_1enzimas_*.pdb   # 180 y 0
  ```
- **Sustituida por:** Status del README de PackMan ("MD never run, and not runnable as
  committed") con la tabla de duraciones y las dos causas de topología inválida; "MD never
  run; committed inputs are stubs" en README raíz, `docs/`, `paper.md`; banner en
  `diagrama_archivos_dm.md` y `texto_tesis_archivos_dm.md`.

### C-21 — "Gradual heating in six stages" como parte del protocolo — ENGAÑOSA

- **Dónde:** `PackMan.v.1.2/README.md` pipeline ("gradual heating in six stages"); `ESTADO.md`
  §4b CIENCIA-3 "configurar_simulacion.sh ya genera los `.in` correctos".
- **Por qué:** `heat1..6`, `density_eq`, `final_eq` son **all-atom** (`dt=0.002`, SHAKE,
  `cut=9`, `gamma_ln=2`, máscara `@CA,C,N,O` que selecciona 0 beads SIRAH) aplicados a una
  topología CG. Y `configurar_simulacion.sh` **no** es el reemplazo correcto: su `eq1`
  restringe el solvente (`':*&!@H='`), usa `gamma_ln=5` y no borra los 8 all-atom.
- **Evidencia:** `AUDITORIA_MD.md` MD-04, MD-05, MD-09, MD-10; `HOJA_DE_RUTA.md` DC-4.
- **Sustituida por:** pipeline del README de PackMan reescrito (los 8 all-atom marcados como
  tales), §Orchestration con el estado de `configurar_simulacion.sh`, y `ESTADO.md §4b`
  CIENCIA-3 con la recomendación (5 etapas de `tutorial/5`).

### C-22 — Cifras de MD en el Studio presentadas como medidas — FALSA

- **Dónde:** `nanocapsule-mvp/src/services/md.py` anclajes "RMSD final 2.8 Å", "SASA ~41.893
  Å²", "heat1 → 17.666 K · el fallo real", `source: packmanreplicas1/1_2`; reflejadas en la
  pestaña Análisis MD.
- **Por qué:** son curvas `math.sin`; no existe ningún `.dat`/`mdout`/`.nc` en el repo.
- **Evidencia:** `AUDITORIA_MD.md` MD-08, §5.
- **Sustituida por:** nota en el README raíz (la pestaña MD lleva captions numéricos que no
  vienen de simulación), tabla del README del Studio y `ESTADO.md §3`. La limpieza del código
  (`md.py`) queda como tarea MD-10 (no es documentación).

---

## 4. sustratinaitor (sustrato CG)

### C-30 — "17 beads por centro de masa, compatible con SIRAH" — FALSA

- **Dónde:** `sustratinaitor/README.md` "Each bead's coordinates come from the centre of mass
  of the corresponding all-atom group"; `2_ligando_GYE/README_conversion_gye_cg.md:50`
  "Compatible with SIRAH force field topology generation".
- **Por qué:** `GYE_cg_manual.pdb` tiene beads sobre átomos individuales (1.4 Å entre sí), no
  centros de masa; sin `.lib`, con nombres `GC`/`GO` que chocan con el esqueleto proteico,
  `resSeq` inválido, un salto `BCT–BF1` de 39 Å. No es un modelo CG utilizable.
- **Evidencia:** `AUDITORIA_SUSTRATO_Y_CG.md` (e9h0rt #2, #5; rfst1e §4); `HOJA_DE_RUTA.md` SU-2.
- **Sustituida por:** stage 2 del README reescrito ("partition sketch, not a coarse-grained
  model") con la corrección explícita; §Resolution mismatch con la recomendación.

### C-31 — "Stages 1–3 done, stage 4 would then simulate" — INSUFICIENTE

- **Dónde:** `sustratinaitor/README.md` Status; stage 4.
- **Por qué:** stage 4 no solo "no corrió": no puede arrancar (`run_MD.sh` busca
  `3J7L-GYE_cg-WAT.prmtop` que `gensystem.leap` no escribe; faltan los `.in`; sin `set -e`;
  sin producción). El empaquetado pierde los 180 `TER` y el GYE es all-atom a 20 fs.
- **Evidencia:** `AUDITORIA_SUSTRATO_Y_CG.md` (e9h0rt #1,#7,#8; rfst1e §3); `HOJA_DE_RUTA.md` SU-1.
- **Sustituida por:** Status del README con los cinco defectos; stage 3 (0 `TER`, seriales
  hex, reparto lumen/cáscara/exterior) y stage 4 ("not run, not runnable as is") reescritos.

---

## 5. JOSS y licencia

### C-40 — "Reproducibility DONE (fixed Packmol seeds, golden regression test)" — FALSA

- **Dónde:** `JOSS_CHECKLIST.md §3` tabla reviewer checklist.
- **Por qué:** ver C-01. Corregida a **OPEN** (PK-4, PK-5).
- **Evidencia:** `AUDITORIA_PACKING.md` P-05, G-01; `HOJA_DE_RUTA.md` C11.

### C-41 — "Functionality works as described / Gates 1 and 2 are real" — FALSA

- **Dónde:** `JOSS_CHECKLIST.md §3` Functionality; `§5.1`.
- **Por qué:** ver C-02 y C-10. Corregida a **OPEN**, con la decisión DC-1 (reparar antes o
  reetiquetar) explícita.

### C-42 — "Licence is clearly stated DONE" — FALSA

- **Dónde:** `JOSS_CHECKLIST.md §2`; `THIRD_PARTY.md`.
- **Por qué:** `THIRD_PARTY.md` listaba SIRAH entre "los que NO se distribuyen", pero el repo
  **versiona** 146 ficheros de SIRAH 2.3, incluido `tools/` bajo GPLv2.
- **Evidencia** (`HALLAZGOS §6.8`; `HOJA_DE_RUTA.md` DC-5):
  ```bash
  git ls-files PackMan.v.1.2/archivos_dm_cg/sirah_x2.3_24-07.amber | wc -l         # 146
  git ls-files PackMan.v.1.2/archivos_dm_cg/sirah_x2.3_24-07.amber/tools | head
  ```
- **Sustituida por:** nota en `README.md` (raíz) §License, fila ampliada en `THIRD_PARTY.md`,
  fila "with an open item (DC-5)" en `JOSS_CHECKLIST.md §2`, mención en `CONTRIBUTING.md`.

### C-43 — "No git tags exist in this clone" — INEXACTA

- **Dónde:** `JOSS_CHECKLIST.md §1.2`.
- **Por qué:** los tags **sí** existen en el remoto (`v0.1.0`, `studio/v0.1.0`,
  `poromania/v1.2.0`, `packman/v1.2.0`, `sustratinaitor/v0.1.0`); el clon desde el que se
  escribió la checklist no los había traído.
- **Evidencia:** `git ls-remote --tags origin`.
- **Sustituida por:** §1.2 reescrita a "partly done" (falta decidir qué tag se archiva).

### C-44 — "each needs a simulation to be run before a choice is defensible" (CIENCIA-1/2/3) — INEXACTA

- **Dónde:** `CONTRIBUTING.md`; `ESTADO.md §4b`; READMEs.
- **Por qué:** las auditorías concluyen que las tres decisiones tienen ya evidencia para
  decidirse **sin correr nada** (restar el margen; sacar el GYE de la MD CG; 5 etapas de
  `tutorial/5`).
- **Evidencia:** `HOJA_DE_RUTA.md §3` DC-2/DC-3/DC-4.
- **Sustituida por:** recomendación concreta para cada una en `ESTADO.md §4b`, README de
  PackMan y de sustratinaitor, y `CONTRIBUTING.md`.

---

## 6. Documentos fósiles (marcados, no reescritos)

Se les añadió un banner "DOCUMENTO FÓSIL / NO NORMATIVO" que remite a `ESTADO.md` y a este
archivo, en lugar de reescribirlos, porque son registro histórico y no documentación pública
viva. Afirmaciones que contienen y que el repo refuta:

| Archivo | Afirmación fósil | Refutada por |
|---|---|---|
| `nanocapsule-mvp/PLAN_POROMANIA.md:41` | "radio mín 1.92 Å … de aquí salió el 1.9 Å de la maqueta" | C-10 (`INVALIDO.md`) |
| `nanocapsule-mvp/SESION_STUDIO.md:39,48` | "3-fold ≈2.47 Å, 5-fold ≈1.68 Å, reproducibles"; "TRP cierra el poro −1.97 Å" | sin artefacto; `AUDITORIA_PORO.md §4`, PORO-07 |
| `nanocapsule-mvp/CLAUDE.md` | endpoints inexistentes; licencia MIT; "subtract 1 Å"; tests en `_temp_backup/` | `ESTADO.md §4`; CIENCIA-1 |
| `Poromania.v.1.2./CLAUDE.md` | `cpoint (219.21,171.38,312.96)` fijo; `automated_test.py`, `clickaqui.sh` | `AUDITORIA_PORO.md` PORO-17 |
| `nanocapsule-mvp/TECHNICAL_IMPROVEMENTS.md` | siete módulos marcados hechos que nunca se crearon | `ESTADO.md §4` |
| `nanocapsule-mvp/DEVELOPMENT_PLAN.md`, `BACKEND_FRONTEND_ARCHITECTURE.md` | planes/endpoints anteriores a la auditoría | `ESTADO.md` |

`HOJA_DE_RUTA.md` RP-6 propone retirarlos del todo al final; hasta entonces el banner evita
que se lean como estado del proyecto.

---

## 7. Qué queda fuera de este pase (es código, no documentación)

Estas correcciones **no** se hacen aquí porque tocan el comportamiento del software, no la
documentación; están en `HOJA_DE_RUTA.md` con su tarea. Se listan para que quede claro que la
documentación corregida ya las describe como pendientes, no como hechas:

- Criterio de aceptación del packing, conteo de `n_packed`, lectura de la config, semillas
  (PK-1…PK-5).
- Verificación de la mutagénesis, una sola definición del canal, validación de canal,
  recribado real (PO-1…PO-8).
- Preparación del sistema de MD y los 5 `.in` correctos (MD-1…MD-8).
- Anclajes sintéticos de `md.py` y el badge "(ilustrativo)" vaciado en `40f4b03` (MD-10, PO-6).
- Decisión y aplicación de DC-1 (estrategia JOSS) y DC-5 (bundle de SIRAH).
