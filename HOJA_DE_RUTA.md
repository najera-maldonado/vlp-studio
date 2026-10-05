# Hoja de ruta de reparación — VLP Studio

> **Qué es.** La consolidación de las nueve auditorías del 2026-10-04 en una sola lista de
> trabajo. Deduplica los hallazgos repetidos, resuelve las contradicciones entre informes y
> ordena las tareas por lo que desbloquean. Está pensada para trabajar desde aquí sin
> volver a los informes originales; solo en dos sitios (contenido literal de los `.in` de
> SIRAH y scripts de validación CG) conviene abrir el original, y se dice dónde.
>
> **Fecha de corte:** 2026-10-04, sobre `main` en `40f4b03`. Ninguna reparación está hecha
> todavía; los informes viven en ramas (§9) y no están fusionados en `main`.
>
> **Convenciones de las tablas.**
> *Tipo:* **SW** = software (el código no hace lo que dice) · **CIENCIA** = decisión o
> corrida científica que solo el autor puede cerrar · **SW+CIENCIA** = arreglo de código que
> fija de paso una definición científica.
> *Severidad:* **CRÍTICO** (invalida un resultado o una afirmación publicada) · **ALTO**
> (resultado incorrecto o no reproducible) · **MEDIO** (reporte/interpretación/pérdida de
> datos) · **BAJO** (higiene).
> *Esfuerzo:* horas (h) o días (d) de trabajo humano; el cómputo va aparte.
> *JOSS:* **SÍ** = mientras siga así, una afirmación del README, `paper.md` o
> `JOSS_CHECKLIST.md` es falsa, o un revisor que corra el software obtiene un resultado
> incorrecto. **SÍ\*** = igual, salvo que se reetiquete la puerta como "en revisión" (DC-1).
> **NO** = no afecta a lo que se afirma.
> *GPU:* si la tarea exige GPU. "Herramientas" lista los motores externos que hacen falta
> en CPU (packmol, PyMOL, HOLE, AmberTools…); "—" significa Python puro.

---

## 0. Empieza aquí (los primeros diez pasos, en orden)

| # | ID | Tarea | Esfuerzo | GPU |
|---|---|---|---|---|
| 1 | **DC-1** | Decidir la estrategia JOSS: reparar antes de enviar (recomendado) o reetiquetar las puertas 1 y 2 como "en revisión" y enviar | 1 h | no |
| 2 | **RP-1** | Fusionar los informes y scripts de las 9 ramas en `main`; corregir las frases falsas en README / PENDIENTES / BITACORA / ESTADO / `JOSS_CHECKLIST.md` | 2–3 h | no |
| 3 | **PO-1** | Retirar de circulación el "1.92 Å" (el mutante es el WT): `INVALIDO.md` en la carpeta, corregir docs | 2 h | no |
| 4 | **T1** | Utilidad única de normalización de PDB: reinsertar `TER`, renumerar seriales sin hexadecimal ni desbordamiento | 1 d | no |
| 5 | **PK-1** | Medir PACKMOL real: código de salida al no converger, versión (en la máquina de Lucio) | 0,5 d | no |
| 6 | **PK-2** | Reescribir el criterio de aceptación del packing (regex muerta, fallback ciego) y contar las enzimas colocadas | 1 d | no |
| 7 | **PK-3** | `center` en el `.inp`; sin fallback silencioso de 90 Å; error explícito sin PyMOL | 0,5 d | no |
| 8 | **PK-4** | Que el código lea la configuración que ya existe (semilla, timeout, margen, radio de la UI) | 0,5–1 d | no |
| 9 | **PK-5** | Tests del packing con un doble de PACKMOL, en CI | 1,5 d | no |
| 10 | **PO-3** | Verificar cada mutación tras aplicarla (Poromania y Studio) y dejar de silenciar errores | 1–2 d | no |

Con esos diez, el envío a JOSS deja de apoyarse en afirmaciones falsas. El resto de la lista
(§4) sigue en orden de dependencia.

---

## 1. Veredicto consolidado

### 1.1 Por motor

| Motor | Puerta | Lo que se afirma hoy | Lo que las auditorías encontraron | Severidad |
|---|---|---|---|---|
| **Packing (Studio)** | 2 · Dentro | "real, multi-réplica, determinista, con golden test" (README, PENDIENTES §15, BITACORA §24) | El criterio de aceptación busca una frase que PACKMOL nunca escribe; el fallback acepta cualquier salida (la cápside sola ya supera el umbral); con un doble de PACKMOL el motor reporta **100 enzimas, σ = 0** con **cero** enzimas colocadas. Semillas aleatorias (la config que promete semilla fija no se lee). Sin PyMOL, radio 90 Å para todo y cápside sin centrar → enzimas empaquetadas **en el vacío** a 360 Å (BMV). Cero tests del motor. | **CRÍTICO** |
| **Poro (Poromania + Pac-Pore)** | 1 · A través | "real de punta a punta" (README, ESTADO) | El único resultado real del repo (1.92 Å) está mal atribuido tres veces: el "mutante" es **byte-idéntico al WT**; la estructura usada no es la que cargan los scripts commiteados; la semilla de HOLE cae a 7.6 Å del eje (dentro de la pared) y el eje va 19° desviado. El Studio tiene el eje correcto (0.00° en C5) pero su cribado falla sobre el pentámero y su eje está mal condicionado en trímeros. | **CRÍTICO** |
| **PackMan (MD SIRAH)** | 4 · Sobrevive | "protocolo completo, MD sin correr" | Nunca corrió y **no puede correr**: la ruta automatizada entrega a `cgconv.pl` un PDB sin hidrógenos (faltan 3 866 beads) y sin `TER` (181 moléculas encadenadas). 8 de 13 `.in` son all-atom sobre topología CG; los 3 SIRAH son stubs de 10 ps rotulados 15/35 ns. Las cifras de MD del Studio son `math.sin`. | **CRÍTICO** (pero ya rotulado honestamente) |
| **sustratinaitor** | 1/4 · sustrato | "ejecutado hasta el empaquetado; bug de resolución" | La conversión CG de la cápside **está bien** y es reproducible byte a byte (es la receta que PackMan debe copiar). Pero la salida de Packmol pierde los 180 `TER`, el GYE empaquetado es all-atom bajo un protocolo de 20 fs sin SHAKE (no integrable), el GYE "CG" de 17 beads no tiene topología ni geometría CG, y la etapa 4 busca un `prmtop` que tleap no produce. 40 de 200 sustratos quedan en el lumen. | **ALTO** |
| **Repo / JOSS** | — | `JOSS_CHECKLIST.md`: "Reproducibility DONE (fixed seeds, golden test)", "gates 1 and 2 real", "licence clearly stated" | Las tres afirmaciones son falsas con la evidencia de arriba. Además `THIRD_PARTY.md` dice que SIRAH no se redistribuye y el repo versiona 146 ficheros de SIRAH (con `tools/` GPL). | **ALTO** |

### 1.2 Los seis hechos que cambian la estrategia

1. **El packing no es "terreno firme".** Era la premisa para enviar a JOSS mientras se
   auditaba la MD. Dos auditorías independientes, sin leerse entre sí, llegaron a los mismos
   dos defectos bloqueantes (regex muerta + fallback ciego) y los demostraron contra los logs
   reales commiteados y ejecutando el motor con un doble. La pasada "sellada" previa los
   calificó de "menores" porque solo leyó código.
2. **El único resultado de poro publicable describe el tipo salvaje.** `cmp` lo demuestra.
   Si ese 1.92 Å llegó a la tesis o a una figura, hay que emitir una corrección.
3. **La MD no puede correr con lo commiteado**, pero la receta correcta ya existe en el
   propio repo (`sustratinaitor/1_capside/3J7L_cg.pdb` = `pdb2pqr --ff=AMBER` → `cgconv.pl`
   sobre la cápside sola, con `TER`). Portarla es medio día.
4. **Un solo defecto mecánico cruza los cuatro motores:** PDB con más de 99 999 átomos
   (seriales hexadecimales de Packmol, desbordamiento de columnas en `fix_pdb_serial.py` y
   en el preview del Studio) y pérdida de `TER` (PyMOL `save` 180→3, Packmol →0). Una
   utilidad (T1) lo cierra en todos.
5. **El patrón de fondo es el fallo silencioso:** fallbacks numéricos presentados como
   mediciones (90 Å, `cpoint 0 0 0`), `except: continue`, códigos de salida ignorados, y
   motores externos que declaran éxito porque cumplieron exactamente la restricción
   equivocada. Cada tarea de abajo que diga "que falle, no que avise" ataca esto.
6. **Las tres decisiones científicas aplazadas (CIENCIA-1/2/3) ya tienen evidencia
   suficiente para decidirse** sin correr nada (§3). Mantenerlas abiertas bloquea trabajo.

### 1.3 Ciencia frente a software, en una línea

- **Software (la mayoría del trabajo, ~20 días):** hacer que el código haga lo que la
  documentación ya afirma. No cambia ninguna definición científica.
- **Ciencia (decisiones de horas + corridas de días):** CIENCIA-1 (radio), CIENCIA-2
  (resolución del sustrato), CIENCIA-3 (protocolo de heat), qué estadístico publica el
  packing, qué estructura y qué eje mide el poro, qué motor de docking, y las corridas
  reales (MD en GPU, barridos de sensibilidad, recribado de mutantes).

---

## 2. Contradicciones entre informes, resueltas

| # | Tema | Informe A | Informe B | Resolución y evidencia |
|---|---|---|---|---|
| C1 | **Dónde quedó el sustrato de sustratinaitor** | `HALLAZGOS` §7.1: 199 de 200 fuera, cápside a 360 Å del origen | Ambas auditorías CG: cápside en el origen, 40–49 GYE en el lumen | **Ganan las auditorías CG.** Medido aquí sobre `3_empaquetado_packmol/3J7L-GYE.pdb`: centroide de la cápside (0, 0, 0); GYE con COM en lumen/cáscara/exterior = **40 / 36 / 124**; 18 íntegramente dentro. `HALLAZGOS` midió el centroide sobre `1_capside/3J7L_cg.pdb` (ese sí está en 207,9³), no sobre el fichero empaquetado. Su §12 incluso registra que "una pasada previa contó 18 dentro": esa pasada tenía razón. |
| C2 | **Por qué la topología de PackMan es inválida** | `AUDITORIA_MD`: sin H y sin `TER` en la ruta automatizada | `AUDITORIA_SUSTRATO_Y_CG` (e9h0rt): "veredicto correcto, causas no": `pdb2pqr` pone H y reconstruye `TER`; lo que rompe son los seriales hexadecimales | **Ambos tienen razón sobre rutas distintas.** `run_maestro.sh:58-62` (la ruta automatizada) llama a `cgconv.pl` directo y "salta pdb2pqr" (verificado): MD-02/MD-03 se sostienen ahí. `convert_to_cg.sh` (que `run_maestro.sh` no invoca) sí protonaría y repondría `TER`, pero aborta con `ValueError` en los seriales hex de Packmol (las dos auditorías CG lo ejecutaron). Conclusión operativa: invertir el orden (convertir cada componente con sus `TER`, empaquetar después) resuelve todo a la vez. |
| C3 | **`fix_pdb_serial.py` ¿funciona?** | CG rfst1e: "probado, viable" | CG e9h0rt + `HALLAZGOS` §11.1: desplaza una columna a partir del átomo 100 000 (`{atom_serial:5d}` → 6 caracteres) | **Ganan e9h0rt y HALLAZGOS.** rfst1e lo probó sobre un extracto (una copia de cadena C + enzima, < 100 000 átomos), por debajo del umbral donde falla. Y ningún script lo invoca. |
| C4 | **Severidad del packing** | Sellado: "sospechas (menores)" | `AUDITORIA_PACKING` ×2: dos hallazgos bloqueantes | **Ganan las auditorías**: regex ejecutada contra dos logs reales (0 coincidencias) y motor ejecutado con doble (100 enzimas, σ 0, 0 colocadas). El sellado solo leyó código. |
| C5 | **Código de salida de PACKMOL al no converger** | vdvq69 (leyó el fuente de PACKMOL): las versiones con `exit_codes.f90` devuelven 173 | wwph45 (sin acceso al fuente): desconocido; si es 0, la capacidad es el techo del bucle (100) | **Pendiente de medir** en la versión instalada (PK-1). Los dos coinciden en que, incluso con exit ≠ 0, el fichero intermedio que PACKMOL deja en `<output>` puede aceptarse como válido. PK-2 no depende de la respuesta. |
| C6 | **CIENCIA-1: ±1 Å** | Sellado y ESTADO: "la IA recomienda restar" | vdvq69, wwph45, `HALLAZGOS` §9.6: convergen en restar y añaden que el debate es ruido | **Sin contradicción; decidido (§3).** Evidencia: +1 reporta un radio ≈ 2,7 Å *dentro* del átomo de la pared (vdvq69); la esfera resultante (88 Å en BMV) deja una holgura mínima de 0,5 Å, por debajo de cualquier radio de vdW (wwph45), y queda 1,5 Å por dentro de la superficie interna (HALLAZGOS). El radio lo fija el 0,14 % de los átomos (una Arg); la incertidumbre conceptual es de 7–13 Å, no de 1 Å. |
| C7 | **Eje del Studio en trímeros** | `AUDITORIA_PORO` PORO-07: 6,14° de error, mal condicionado (separación de autovalores 21 %) | `HALLAZGOS` §4.7: mismas cifras, "puede ser mi referencia; no lo cuento" | **Gana PORO-07 en lo esencial:** la separación de autovalores es una propiedad del método, independiente de la referencia, y los trímeros no son C3 exactos (2,0 Å). La magnitud exacta del error sí es incierta. Acción: guarda de degeneración, no "corregir el número". |
| C8 | **`1run_hole_old.sh`** | ESTADO §4 y sellado: código muerto a borrar | PORO-04: es la versión que **tenía la validación de canal** (líneas 118-151) | **Gana PORO-04.** Portar la validación a `pore.py` antes de borrar. |
| C9 | **`skinnb=5`** | `PLAN_REPARACION_MD`: añadirlo | `HALLAZGOS` §12: no está en los tutoriales 5 y 8 (los aplicables) | **No es defecto;** es ajuste opcional de GPU para sistemas grandes (tutorial 7). Añadirlo no hace daño; su ausencia no es error. |
| C10 | **Cuántos `.in` carecen de `&ewald chngmask=0`** | `AUDITORIA_MD`: 11 de 13 | `HALLAZGOS` §8.1: 10 de 13 | **10** (em1, em2, heat1–6, density_eq, final_eq; eq1/eq2/prod lo tienen). Irrelevante tras MD-6, que deja 5 ficheros todos con el bloque. |
| C11 | **Estado JOSS** | `JOSS_CHECKLIST.md`: "Reproducibility DONE", "gates 1 and 2 real", "licence clearly stated DONE" | Todas las auditorías de motor + `HALLAZGOS` §6.8 (SIRAH redistribuido) | **Ganan las auditorías.** La checklist se escribió desde la documentación, no desde el código. RP-1 la corrige. |
| C12 | **Carga neta de la enzima** | `AUDITORIA_MD`: −4 | `HALLAZGOS` §12: −1 | Irrelevante hasta tleap: se lee en `leap.log` (`charge protein`) en MD-5 y de ahí salen NaW/ClW. |
| C13 | **Beads `BPG` esperados en el CG de cápside + 1 enzima** | `AUDITORIA_MD`: 3 494 | `PLAN_REPARACION_MD`: 3 490 | **3 490**: las 4 Cys de los dos puentes disulfuro pasan a `CYX`→`sX`, sin `BPG`. Para la cápside sola: 3 420 (las dos auditorías CG coinciden). |
| C14 | **Causa de que el mutante no se mutara** | `HALLAZGOS` §1.1: falta `cmd.refresh_wizard()` + ambigüedad de `segi` | PORO-09: ambigüedad de `segi`; mecanismo exacto **[requiere PyMOL]** | **Compatibles.** La acción es la misma sea cual sea la causa: verificar `resn` tras `apply()` y abortar si no cambió (PO-3). |

---

## 3. Decisiones que solo Lucio puede tomar

Cada una viene con la recomendación de las auditorías y con lo que bloquea mientras siga
abierta. Ninguna exige correr nada.

| ID | Decisión | Recomendación (y por qué) | Bloquea |
|---|---|---|---|
| **DC-1** | **Estrategia JOSS.** ¿Reparar packing y poro antes de enviar, o reetiquetar las puertas 1 y 2 como "motor listo, resultado en revisión" y enviar describiendo solo lo verificado? | **Reparar primero** (PK-1…PK-5 y PO-1, PO-3, PO-6: ~6 días). JOSS revisa que la funcionalidad coincida con lo descrito; hoy no coincide. Si hay prisa, reetiquetar es honesto y JOSS lo admite (ya se hizo con la MD). | RP-1 (qué frases escribir), el marcado "JOSS" de toda la lista |
| **DC-2** | **CIENCIA-1 — radio interno.** | **Restar** (docstring, README, CLAUDE.md), o mejor: sustituir el bucle de PyMOL por `d_min` exacto con NumPy y publicar **dos números con nombre**: *radio interno físico* = `d_min − r_vdW` y *radio de la esfera de empaquetado* = físico − margen. Disuelve el ±1, elimina PyMOL de esta ruta y permite testear el radio en CI. | PK-6 |
| **DC-3** | **CIENCIA-2 — resolución de sustratinaitor.** | **Opción B: sacar el GYE de la MD CG.** El híbrido commiteado está descartado por física (17 800 H explícitos a 20 fs sin SHAKE no integran; sin parámetros cruzados GAFF2×SIRAH; sin `TER`). La Puerta 4 corre cápside + enzima en SIRAH (PackMan reparado); la física del sustrato (cruce del poro, sitio activo) se hace all-atom en sistemas pequeños, como ya figura en PENDIENTES. La opción A (parametrizar GYE en SIRAH) es un subproyecto de 2–4 semanas y `GYE_cg_manual.pdb` **no** sirve de punto de partida. | SU-2, SU-3 |
| **DC-4** | **CIENCIA-3 — protocolo de calentamiento de PackMan.** | **Eliminar `heat1..6`, `density_eq`, `final_eq`** y usar las 5 etapas de `tutorial/5` (em1 → em2 → eq1 → eq2 → md; SIRAH arranca `eq1` de 0 K bajo NPT con Langevin, sin rampa). `gamma_ln = 50`, 300 K, Berendsen, `ig` fijo por etapa, ≥ 100 ns en trozos de 10 ns. `configurar_simulacion.sh` no es "los `.in` correctos": su `eq1` restringe también el solvente y usa `gamma_ln = 5`; retirarlo. | MD-6 |
| **DC-5** | **Licencia de SIRAH.** El repo redistribuye 146 ficheros de SIRAH 2.3 (3,9 MB) incluyendo `tools/` bajo GPLv2, mientras `THIRD_PARTY.md` dice lo contrario. | Verificar los términos de SIRAH (académica) y **o** quitar el bundle del repo (y que `fetch_data.sh` lo descargue) **o** corregir `THIRD_PARTY.md` y declararlo. GPLv2+ de `cgconv.pl` es compatible con AGPLv3; el problema es la declaración falsa. | RP-1, Zenodo |
| **DC-6** | **Qué estadístico publica el packing.** Hoy se muestra `best` (máximo sobre réplicas, que crece con el número de réplicas que elija el usuario) junto a media/σ como si fueran física. | Titular = **máximo observado en N réplicas** (etiquetado así, con semillas) + **fracción de réplicas que alcanzan el máximo** (es lo que demuestra convergencia) + mediana/IQR como dispersión del buscador. Y la curva `best(N réplicas)`. | PK-7 |
| **DC-7** | **Motor de docking.** Poromania usa idock sin semilla y con `threads=$(nproc)`; el Studio usa Vina con `--seed 1`. Las afinidades no son comparables. | **Vina** (reproducible; ya es el camino del Studio). Retirar `5docking.sh` del camino vivo o fijarle semilla y `threads`. No mezclar afinidades de ambos en una figura. | PO-9 |
| **DC-8** | **Qué poro se mide.** La carpeta de resultados dice 5-fold de BMV, los scripts commiteados cargan el trímero de CCMV, y `_AXIS_MIN` guarda el 1.9 como 3-fold. | Fijar por escrito la estructura y el eje de referencia; **`BMV/poro5fold`** es la mejor condicionada (C5 exacta, eje recuperado a 0,00°). Usarla para el golden. | PO-7, PO-8 |

---

## 4. Orden de trabajo completo

Ordenado por dependencia: cada tarea desbloquea las que la citan. Dentro de cada ola, las
de software van antes que las de ciencia. Las olas 0–4 se hacen íntegras sin GPU.

### Ola 0 — Congelar afirmaciones falsas (horas)

| # | ID | Tarea | Motor | Tipo | Sev | Esfuerzo | Depende de | JOSS | GPU | Herramientas |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | DC-1 | Estrategia JOSS | repo | CIENCIA | — | 1 h | — | SÍ | no | — |
| 2 | RP-1 | Fusionar ramas de auditoría; corregir afirmaciones en README/PENDIENTES/BITACORA/ESTADO/JOSS_CHECKLIST | repo | SW | ALTO | 2–3 h | DC-1 | SÍ | no | — |
| 3 | PO-1 | Invalidar el 1.92 Å y lo derivado | poro | SW | CRÍTICO | 2 h | — | SÍ | no | — |
| 4 | DC-5 | Licencia SIRAH | repo | CIENCIA | ALTO | 1 h + consulta | — | SÍ | no | — |

### Ola 1 — Transversal (desbloquea los cuatro motores)

| # | ID | Tarea | Motor | Tipo | Sev | Esfuerzo | Depende de | JOSS | GPU | Herramientas |
|---|---|---|---|---|---|---|---|---|---|---|
| 5 | T1 | Normalizador de PDB: `TER` + seriales | todos | SW | ALTO | 1 d | — | SÍ\* | no | — |
| 6 | T2 | Guarda geométrica antes de Packmol: la región de empaque debe intersecar la estructura | packing, PackMan, sustratinaitor | SW | ALTO | 2 h | — | SÍ\* | no | — |
| 7 | T3 | Política "que falle, no que avise" (lista concreta por motor) | todos | SW | ALTO | se reparte en PK-3, PO-3, PO-5, MD-3, SU-1, RP-3 | — | SÍ\* | no | — |

### Ola 2 — Packing, Fase 0 (lo mínimo para que la puerta 2 sea defendible)

| # | ID | Tarea | Motor | Tipo | Sev | Esfuerzo | Depende de | JOSS | GPU | Herramientas |
|---|---|---|---|---|---|---|---|---|---|---|
| 8 | PK-1 | Medir PACKMOL real: exit code, versión, `_FORCED` | packing | SW | CRÍTICO | 0,5 d | — | SÍ\* | no | packmol |
| 9 | PK-2 | Criterio de aceptación nuevo + contar `n_packed` | packing | SW | CRÍTICO | 1 d | PK-1 (informa, no bloquea) | SÍ\* | no | — |
| 10 | PK-3 | `center`; sin fallback 90 Å; error sin PyMOL; API distingue calculado/por defecto; caché por cápside | packing | SW | CRÍTICO | 0,5–1 d | — | SÍ\* | no | — |
| 11 | PK-4 | Leer la config: `seed_base`, `use_random_seeds`, `timeout`, `collision_margin`; radio de la UI; `success=False` visible | packing | SW | ALTO | 0,5–1 d | — | SÍ\* | no | — |
| 12 | PK-5 | Tests del motor con doble de PACKMOL (T1–T6 / R-5) en CI | packing | SW | ALTO | 1,5 d | PK-2, PK-3, PK-4 | SÍ\* | no | — |

### Ola 3 — Poro, lo mínimo defendible

| # | ID | Tarea | Motor | Tipo | Sev | Esfuerzo | Depende de | JOSS | GPU | Herramientas |
|---|---|---|---|---|---|---|---|---|---|---|
| 13 | PO-2 | Sello de procedencia por corrida de HOLE/docking | poro | SW | ALTO | 1 d | — | NO | no | — |
| 14 | PO-3 | Verificar mutaciones tras `apply()`; `check=True`; sin `except: continue`; `refresh_wizard`; `segi` | poro (ambos) | SW | CRÍTICO | 1–2 d | — | SÍ\* | no | PyMOL (para probar) |
| 15 | PO-4 | Una sola definición del canal (`pore.py`); guarda de degeneración; residuos por `segi`; validación de canal portada de `1run_hole_old.sh` | poro (ambos) | SW | ALTO | 5–8 d | PO-3 | SÍ\* | no | HOLE (para probar) |
| 16 | PO-5 | Parser de HOLE delimitado por cabecera; quitar `radio > 0.5`; detectar `Unrecognized`; `MIN_RAD`; códigos de salida de los `.sh` | poro (ambos) | SW | ALTO | 1–2 d | — | NO | no | — |
| 17 | PO-6 | Divulgación de lo ilustrativo: badge, sin gaussiana por defecto, sin veredicto PASA con dos lados ilustrativos, `_AXIS_MIN` | Studio | SW | ALTO | 1 d | — | SÍ | no | — |

### Ola 4 — PackMan: preparación del sistema y protocolo (sin GPU)

| # | ID | Tarea | Motor | Tipo | Sev | Esfuerzo | Depende de | JOSS | GPU | Herramientas |
|---|---|---|---|---|---|---|---|---|---|---|
| 18 | MD-1 | Confirmar en local C1–C7 (cgconv sin H, tleap encadena, máscaras vacías, pdb2pqr con numeración repetida) | PackMan | SW | — | 2–4 h | — | NO | no | AmberTools, pdb2pqr, perl |
| 19 | MD-2 | Protonar por componente (`pdb2pqr --ff=AMBER --ffout=AMBER [+propka]`) → `capside_H.pdb`, `enzima_H.pdb` con `CYX` | PackMan | SW | CRÍTICO | 2–4 h | MD-1 | NO | no | pdb2pqr |
| 20 | MD-3 | Empaquetar conservando H e insertando `TER`; arreglar `ls` lexicográfico, `N_ENZIMAS="1o"`, recentrado saltado, radio hardcodeado | PackMan | SW | CRÍTICO | 3–5 h | T1, MD-2 | NO | no | packmol |
| 21 | MD-4 | `cgconv.pl` sobre el PDB correcto; `run_maestro.sh` y scripts rotos; validación CG automática | PackMan | SW | CRÍTICO | 1–2 h | MD-3 | NO | no | perl |
| 22 | MD-5 | `gensystem.leap`: `bond` S–S, caja 20 Å, 0,15 M NaCl, sin `mbondi3`; dos pasadas | PackMan | SW | ALTO | 2–3 h + tleap | MD-4 | NO | no | AmberTools |
| 23 | MD-6 | Cinco `.in` SIRAH + `run_MD.sh` + semillas fijas; borrar los 8 all-atom; retirar `configurar_simulacion.sh` | PackMan | SW+CIENCIA | CRÍTICO | 3–4 h | DC-4 (redactable sin MD-5; validable con) | NO | no | sander (sintaxis) |
| 24 | SU-1 | sustratinaitor: higiene (`TER`, nombres `-WAT`, `.in`, `set -e`, log truncado, README) | sustratinaitor | SW | ALTO | 3–4 h | T1 | NO | no | — |

### Ola 5 — Corridas y ciencia (exigen motores o GPU)

| # | ID | Tarea | Motor | Tipo | Sev | Esfuerzo | Depende de | JOSS | GPU | Herramientas |
|---|---|---|---|---|---|---|---|---|---|---|
| 25 | MD-7 | Humo en GPU: em1, em2, eq1 de 1 000 pasos | PackMan | CIENCIA | — | 1–2 h + 15–40 min GPU | MD-5, MD-6 | NO | **sí** | pmemd.cuda |
| 26 | MD-9 | Análisis: índices absolutos de residuo, `rms` antes de `atomicfluct`, SASA, eje temporal, bugs bash | PackMan | SW | ALTO | 1 d | MD-7 (para probar) | NO | no | cpptraj |
| 27 | MD-8 | Producción 5 + 25 + ≥ 100 ns, semillas fijas, manifiesto | PackMan | CIENCIA | — | 2 h + 1–3 d GPU | MD-7 verde | NO | **sí** | pmemd.cuda, LSF |
| 28 | PK-6 | Radio interno redefinido (CIENCIA-1): NumPy, `d_min − r_vdW`, dos números, test golden del radio | packing | SW+CIENCIA | MEDIO | 1–2 d | DC-2 | NO | no | — |
| 29 | PK-7 | Estadístico publicable + barrido de sensibilidad `N_max(radius, timeout)` + cotas de cordura | packing | CIENCIA | ALTO | 2 d + CPU-horas | PK-2…PK-5, DC-6 | NO | no | packmol |
| 30 | PO-7 | Recribado real: regenerar el mutante bien, HOLE sobre `poro5fold` con el eje correcto, docking | poro | CIENCIA | CRÍTICO | 1 d + cómputo | PO-3, PO-4, DC-8 | SÍ\* | no | HOLE, PyMOL, Vina |
| 31 | PO-8 | Golden de perfil de poro sobre `poro5fold` + test de simetría de entrada | poro | SW | ALTO | 2–3 d | PO-4, PO-7 | NO | no | HOLE (fuera de CI) |
| 32 | PO-9 | Un solo motor de docking; semilla; `threads` fijo; correlación con n e IC | poro | SW+CIENCIA | MEDIO | 2–3 d | DC-7 | NO | no | Vina |
| 33 | PO-10 | `substrate_section` con radios de vdW; unificar escala con `_SUBSTRATES`; tolerancia del golden | Studio | SW+CIENCIA | ALTO | 1 d | — | NO | no | RDKit |
| 34 | SU-2 | Ejecutar CIENCIA-2 (opción B: sacar el GYE de la MD CG; o abrir subproyecto GYE-SIRAH) | sustratinaitor | CIENCIA | ALTO | 1 h (B) / 2–4 sem (A) | DC-3 | NO | no | — |
| 35 | SU-3 | Geometría del sustrato: `outside sphere` (Puerta 1) o `inside sphere` (encapsulado); documentar el 200 | sustratinaitor | CIENCIA | MEDIO | 2 h + packmol | DC-3, T2 | NO | no | packmol |

### Ola 6 — Resto (higiene, infra, documentación)

| # | ID | Tarea | Motor | Tipo | Sev | Esfuerzo | Depende de | JOSS | GPU | Herramientas |
|---|---|---|---|---|---|---|---|---|---|---|
| 36 | PK-8 | Provenance del packing: carpetas con timestamp, no escribir en `Input/`, restaurar GCase, limpiar `packed_*.pdb`, 7 vs 10 réplicas, metadata con versión/exit/tiempo | packing | SW | MEDIO | 1,5 d | — | NO | no | — |
| 37 | PK-9 | Preview: seriales > 99 999, `END` en medio, IDs de cadena colapsados; determinismo | Studio | SW | ALTO | 0,5 d | T1 | NO | no | — |
| 38 | PO-11 | Higiene de Poromania (APBS, cámara, pH, mejor score, `sort` lexicográfico, `DEL`, duplicados) | poro | SW | MEDIO/BAJO | 1–2 d | PO-4 | NO | no | — |
| 39 | MD-10 | Documentación de PackMan + Studio `md.py` (quitar anclajes sintéticos; `md_prepare` emite SIRAH; SMILES ignorado) | PackMan, Studio | SW | MEDIO | 2–3 h | MD-6 | NO | no | — |
| 40 | RP-3 | Infra: `setup.py`, `ruff` sin pin, puerto 5001, `salud.sh`, `vlpstudio.kdl`, `fetch_data.sh`, `/api/result/pdb`, `/api/files/cleanup` | repo | SW | MEDIO | 1 d | — | parcial | no | — |
| 41 | RP-4 | Tests que comprueben algo (`pore_channels`, preview, rutas sin cobertura) | repo | SW | MEDIO | 0,5 d | PK-5 | NO | no | — |
| 42 | RP-5 | JOSS, solo Lucio: nombre/ORCID/afiliación, tag, Zenodo, DOIs de `paper.bib`, cronología | repo | — | — | 2 h | RP-1 | SÍ | no | — |
| 43 | RP-6 | Retirar documentos fósiles y código muerto (al final, con cuidado: `1run_hole_old.sh` solo tras PO-4) | repo | SW | BAJO | 1 d | PO-4 | NO | no | — |

**Totales aproximados.** Software: ~30–35 días-persona (la mitad es el poro). Ciencia: decisiones de horas +
2–4 días de corridas (packing, poro) + 1–3 días de GPU (MD) + opcionalmente 2–4 semanas
(GYE-SIRAH). Sin GPU se completa todo salvo MD-7 y MD-8.

---

## 5. Fichas de tarea

Cada ficha: qué hacer, dónde, cómo saber que está hecho, y qué hallazgos de los informes
cierra (para no volver a ellos).

### 5.1 Transversal

#### T1 — Normalizador de PDB (`TER` + seriales) · SW · ALTO · 1 d · sin GPU

**Problema.** Tres convenciones de serial conviven: Packmol escribe hexadecimal a partir
del átomo 100 000 (`186A0`), `fix_pdb_serial.py` desplaza todas las columnas una posición
desde ese mismo átomo (`{atom_serial:5d}` produce 6 caracteres) y además pone el elemento en
las columnas 73-74, el preview del Studio hace lo mismo desde la copia 23 de GCase, y
`3J7L_cg.pdb` reinicia en 1. En paralelo, PyMOL `save` colapsa 180 `TER` en 3 y Packmol
escribe 0, de modo que tLeaP encadenaría 181 moléculas con enlaces de 26–217 Å y 358
residuos terminales quedarían con carga de residuo interno.

**Qué hacer.** Una sola utilidad Python (sin dependencias) en `herramientas/` o en
`nanocapsule-mvp/src/io/`, usada por los cuatro motores:
- Inserta `TER` cuando el número de residuo no avanza **o** cambia la clase de molécula **o**
  la distancia C–N (all-atom) / GO–GN (CG) supera 2,5 Å. Medido: en el PDB empaquetado de
  PackMan los 180 saltos de numeración coinciden exactamente con los 180 cortes C–N; en
  `3J7L-GYE.pdb` la regla devuelve los 379 esperados (179 + 1 + 199).
- Renumera seriales con desbordamiento controlado (reinicio en 0 al pasar de 99 999, como
  hace `cgconv.pl`) o hybrid-36; nunca 6 caracteres.
- Reescribe solo las columnas que toca; conserva el resto byte a byte.
- Opcional: asigna un ID de cadena o un `segi` distinto a cada copia de la enzima.
- Sustituye a `fix_pdb_serial.py` (o lo corrige) y se invoca desde `run_maestro.sh`,
  `convert_to_cg.sh`, sustratinaitor etapa 3 y el preview del Studio.

**Hecho cuando.** `grep -c '^TER'` = 180 + N en el PDB empaquetado de PackMan y 379 en
`3J7L-GYE.pdb`; ningún serial con letras; `pdb2pqr` y `cgconv.pl` leen el fichero sin
error; un test unitario con un PDB sintético de 100 010 átomos.

**Cierra.** MD-03, PK-11, P-22, CG-e9h0rt #1/#3/#4, HALLAZGOS §2.1, §11.1–§11.4; PLAN P2
(`3insertar_TER.py`).

#### T2 — Guarda geométrica antes de Packmol · SW · ALTO · 2 h

**Problema.** Tres motores especifican `inside sphere 0 0 0 R` o `inside box` respecto al
origen mientras la estructura puede vivir a 360 Å de él (las cápsides de la biblioteca
traen centroide (207,9; 207,9; 207,9); QB en (73,9; 0; 0)). Packmol cumple la restricción
pedida y declara `Success!`.

**Qué hacer.** Antes de escribir cualquier `.inp`: calcular el centroide de la estructura
fija y comprobar que el centro de la región de empaque cae dentro de ella (distancia <
radio interno). Si no, error. Y escribir `center` bajo `fixed` (lo hace ya
`sustratinaitor/3_empaquetado_packmol/packmol_input.inp:8` y `md.py:159`; no lo hace
`parallel_packer.py:262`).

**Hecho cuando.** Un test con `capside.pdb` sin centrar lanza; con `capside_centered.pdb`
pasa. En el PDB resultante, la separación entre centroide de cápside y de enzimas es < 40 Å.

**Cierra.** PK-02 (parte), HALLAZGOS §2.4, §14.2.

#### T3 — Política "que falle, no que avise" · SW · ALTO · repartida

No es una tarea aparte: es la lista de sitios concretos que las demás fichas corrigen.
Se anota aquí para que nadie los cierre "avisando":

- Radio 90 Å por defecto cuando falta PyMOL, cuando el bucle se agota (> 199 Å, caso P22)
  o ante cualquier excepción (`capsid.py:72-77, 139-142, 163-168`); el endpoint lo rotula
  "calculado" → PK-3.
- `experiment_runner.py:114-117` captura el fallo de centrado y sigue con el PDB sin
  centrar → PK-3.
- `app.py:303-320` responde 200 `completed` con `success: False` y sin `error` → PK-4.
- `1run_hole.sh:12-22` usa `cpoint 0 0 0` / `cvect 0 0 1` si faltan los ficheros; `:49-66`
  sale 0 cuando HOLE falla; `rm -f` del resultado anterior antes de correr → PO-5.
- `pore.py:371, 550` `except Exception: continue`; `:247` ignora el `returncode` de PyMOL
  → PO-3.
- `run_maestro.sh:74` llama a un script inexistente y "continúa"; `setup_*.sh` crean
  ficheros vacíos y declaran `✓ Configurado`; `run_MD.sh:134-139` "continúa con los inputs
  disponibles" → MD-4.
- sustratinaitor `run_MD.sh` sin `set -e` y sin producción → SU-1.
- `salud.sh:36-40` pinta verde con tests fallando → RP-3.

### 5.2 Packing (Studio, `nanocapsule-mvp`)

#### PK-1 — Medir PACKMOL real · SW · CRÍTICO · 0,5 d · packmol (máquina de Lucio)

**Qué.** Un caso imposible (p. ej. 200 × GCase en esfera de 88 Å, o 40 en 30 Å con
`nloop 5`) y leer: `echo $?`, si existe `<output>` además de `<output>_FORCED`, cuántas
líneas `ATOM` tiene `<output>`, y las cadenas exactas del bloque final
(`ENDED WITHOUT PERFECT PACKING`, `Maximum violation of target distance:`). Registrar
`packmol | grep -i version` (el log de PackMan dice 20.14.3; el de sustratinaitor 21.0.1).
También: `python3 -c "from pymol import cmd"` con el intérprete que arranca Flask (el
`/api/health` comprueba el binario, no el módulo).

**Hecho cuando.** Queda anotado en `nanocapsule-mvp/docs/` o en el CHANGELOG: versión,
exit code al no converger, y si el fichero regular queda escrito.

**Cierra.** PK-01 (parte REQUIERE CORRER), P-03, P-13, PK-14.

#### PK-2 — Criterio de aceptación y conteo de enzimas · SW · CRÍTICO · 1 d

**Problema.** `parallel_packer.py:34-36,191-193` busca `Maximum distance violation:`;
PACKMOL escribe `Maximum violation of target distance:` (verificado contra los dos logs
reales del repo: cero coincidencias; heredado de `2Empaquetador_Maximo.py:87`). Al no casar,
`:300-310` acepta si el PDB tiene ≥ 10 000 líneas atómicas, que la cápside sola cumple
(168 480–216 780). `n_packed` no se mide: es el `n` pedido. Con un doble de PACKMOL que
coloca 0 enzimas, el motor reporta 100 / σ 0 / 2 de 2 réplicas.

**Qué hacer.** En `parallel_packer.py`:
1. Regex `Maximum violation of target distance:\s*([-+\d.eE]+)` sobre el **último** bloque,
   exigir `Success!`, rechazar si aparece `ENDED WITHOUT PERFECT PACKING` o existe
   `<output>_FORCED`, y **retirar** el fallback por líneas.
2. Contar enzimas: `(líneas_output − líneas_cápside) / líneas_enzima` debe ser exactamente
   `n`; si no, rechazar. (El script original de la tesis ya calculaba `lineas_por_enzima`.)
3. Registrar la causa de cada rechazo (timeout, exit ≠ 0, `_FORCED`, violación, conteo) en
   `metadata.json`; `except (TimeoutExpired, Exception)` deja de tragar todo como "no cabe".
4. Aplicar lo mismo a `PackMan.v.1.2/archivos_dm_cg/empaquetador/2Empaquetador_Maximo.py`
   (hoy su bucle no tiene criterio de parada: incrementa `n` indefinidamente).

**Hecho cuando.** Con los dos logs reales como fixtures, `_read_max_violation` devuelve
0.0 y 0.0 (hoy devuelve `None`). Con el doble de PACKMOL "sin enzimas", el resultado es
`success=False`. Un `N_max` fuera de las cotas de PK-7 es un fallo.

**Cierra.** PK-01, P-01, P-02, P-03, P-04, P-07, HALLAZGOS §9.1.

#### PK-3 — Centrado, radio y fallbacks silenciosos · SW · CRÍTICO · 0,5–1 d

**Qué hacer.**
- `parallel_packer.py:260-263`: `center` bajo `fixed 0. 0. 0. 0. 0. 0.` (T2).
- `capsid.py`: sin PyMOL → **error**, nunca 90.0; quitar el techo de `range(5, 200)` o
  derivarlo del tamaño (P22 devolvería 90 Å para una cavidad > 200 Å); excepciones
  propagadas. Mejor aún: centroide y `d_min` con NumPy (sin PyMOL): el bucle entero de
  PyMOL es exactamente `ceil(d_min − 0,5)` y se reproduce en milisegundos; eso además
  permite testearlo en CI (PK-6 lo completa).
- `experiment_runner.py:97-117`: separar el `try` del radio y del centrado; si el centrado
  falla, abortar.
- `/api/capsid/radius` responde `calculado` o `por_defecto`, nunca "Radio interno
  calculado: 90.0 Å" sin haber calculado.
- Caché del radio **por cápside** (`Input/Capsides/<nombre>/radio.json` o un JSON
  indexado), no `radio_interno.txt` global en el CWD que `library.py:85` muestra siempre
  como BMV.
- `/api/health`: comprobar `import pymol` en el intérprete, no `which pymol`.

**Hecho cuando.** Con `PYMOL_AVAILABLE=False`, `run_maximum_packing` lanza (test T6). El
`.inp` generado contiene `center`. Calcular el radio de QB no cambia la fila de BMV en la
Biblioteca.

**Cierra.** PK-02, PK-07, PK-10, PK-13, PK-14, P-11, P-18, HALLAZGOS §2.4, §3.1, §3.2, §3.3.

#### PK-4 — Leer la configuración que ya existe · SW · ALTO · 0,5–1 d

**Problema.** `default.yaml` declara `seed_base: 1234567`, `use_random_seeds: false`,
`engines.packmol.timeout: 300`, `packing.collision_margin: 2.0`; ninguna se lee.
`experiment_runner.py:160-170` no pasa `seed_base` → `random.randint` por réplica (dos
corridas idénticas dieron semillas distintas). `timeout=90` hardcodeado
(`parallel_packer.py:283`): un timeout cuenta como "no cabe" y 7 procesos compiten por CPU,
así que la capacidad depende del hardware. `collision_margin = 2.0` hardcodeado (`:268`).
El campo "Radio interno" de la UI va al preview pero no al experimento (`packing.js:56`).
`n_replicas` = 7 en `experiment_manager.py:47` y 10 en el YAML/UI. Un experimento
totalmente fallido se muestra en verde (`app.py:303-320`, `packing.js:61`).

**Qué hacer.** Un solo punto de lectura de parámetros; `experiment_runner` pasa
`seed_base` y honra `use_random_seeds`; la semilla de cada réplica va al `report.txt`;
`timeout` de config y registro de cada timeout como causa; `max_workers` configurable (y
documentar que afecta a los tiempos); el radio de la UI llega a `run_experiment`;
`success`/`error` se propagan a la respuesta y la UI los muestra.

**Hecho cuando.** Dos corridas con `use_random_seeds: false` dan semillas
`seed_base+1…+N` idénticas (test T4). Subir el timeout en el YAML cambia el comportamiento.
Un experimento con 0 réplicas exitosas se ve en rojo.

**Cierra.** PK-03, PK-04, PK-05 (parte), PK-08 (parte), P-05, P-12, P-19, P-20,
HALLAZGOS §2.3, §2.5, §2.6, §2.7, §2.9.

#### PK-5 — Tests del motor de packing · SW · ALTO · 1,5 d

**Problema.** `tests/test_golden_science.py` prueba `substrate_section` (puerta 1), no el
packing; `test_smoke.py` ejercita el preview aleatorio. Cobertura del motor: cero. Los 22
tests pasan con todos los defectos de arriba. La frase "packing con golden test" es falsa.

**Qué hacer.** Con un doble de PACKMOL que emita las cadenas reales (los dos logs
commiteados son la mejor especificación): acepta con violación baja; rechaza con violación
alta, sin enzimas, con `ENDED WITHOUT PERFECT PACKING`; el `.inp` generado se congela
carácter a carácter (`center`, `inside sphere 0 0 0 <R−margen>`, `radius`, `seed`); la
búsqueda incremental se detiene donde debe; semillas reproducibles; `_consolidate_results`
con réplicas fallidas y n = 1 (`stdev` "no definida", no 0); modo degradado lanza. Más el
golden del radio (PK-6). Marcar `@pytest.mark.engine` el test lento real (dos corridas con
`max_workers=1` y semilla fija → listas idénticas).

**Hecho cuando.** CI verde con los tests nuevos y **rojo** si se reintroduce la regex
vieja.

**Cierra.** PK-09, G-01, HALLAZGOS §6.4 (parte).

#### PK-6 — Radio interno redefinido (CIENCIA-1) · SW+CIENCIA · MEDIO · 1–2 d

**Evidencia.** Réplica NumPy del algoritmo sobre las cuatro cápsides: `d_min` = 89,47
(BMV), 92,79 (CCMV), 103,63 (MS2), 105,94 (QB); el código reporta `d_min + 1` redondeado
(90 para BMV, igual al valor por defecto, así que nunca se supo si PyMOL corrió). El átomo
que define la esfera es la punta de una Arg (BMV: NH1 de Arg26 cadena C); dentro de 2 Å
del mínimo hay 300 átomos de 216 780. El `vdw` del pseudoátomo y `rebuild()` son
decorativos: `within` mide centro a centro.

**Qué hacer** (según DC-2). Calcular `d_min` exacto; reportar *radio físico* =
`d_min − r_vdW(átomo)` y *radio de empaque* = físico − margen (config); documentar que la
esfera inscrita la fija el residuo más móvil y que la verdadera cota estérica la pone
`radius`/`tolerance` de PACKMOL, no la esfera. Alinear código, docstring, README y
CLAUDE.md. Golden del radio: BMV 89,47 → tolerancia 0,01 Å.

**Cierra.** PK-06, PK-12, P-08, P-09, P-10, MD-17 (parte), HALLAZGOS §9.6, ESTADO CIENCIA-1.

#### PK-7 — Estadístico publicable y sensibilidad · CIENCIA · ALTO · 2 d + CPU

**Evidencia.** `radius 5.0` es radio **por átomo**; PACKMOL exige la suma de radios: 10 Å
entre átomos de enzimas distintas y 6 Å enzima–cápside. README dice 10, config 5, packer 10.
La capacidad escala con `(R_cav / (R_enz + radius))³`: ±30 % entre 2,5 y 10 Å. Cotas para
GCase en BMV (esfera 88 Å): ≈ 6 (esferas circunscritas, φ 0,64) a ≈ 20 (volumen vdW
dilatado); el "100" actual está fuera de toda cota. No hay ningún `statistics.json` ni
`report.txt` commiteado: la "condición de 6 enzimas" no tiene respaldo.

**Qué hacer** (según DC-6). Barrido `N_max(radius ∈ {2, 3, 4, 5})` y `N_max(timeout)` con
`max_workers=1` y semilla fija; publicar la curva; reportar máximo observado + fracción de
réplicas que lo alcanzan + mediana/IQR + `best(N réplicas)`; test de cordura permanente
contra las cotas. Justificar por escrito el `radius` elegido.

**Cierra.** PK-05 (ciencia), PK-08, P-06, P-13, P-14, R-11, R-12, R-14.

#### PK-8 — Provenance e higiene de datos · SW · MEDIO · 1,5 d

`Output/<cápside>/<enzima>` sin timestamp sobrescribe experimentos (CLAUDE.md promete
`[timestamp]`); `center_structure` escribe `*_centered.pdb` dentro de `Input/` (versionado);
3 de 4 enzimas ya fueron sobrescritas con `.original` y **GCase no tiene respaldo**;
`packed_*.pdb` intermedios suman decenas de GB sin limpieza; `metadata.json` no guarda
versión de PACKMOL, exit code ni tiempo; `experiment_manager.py` tiene consolidación muerta
con lógica distinta. Hacer: timestamp, centrados a `Output/` o caché, restaurar/documentar
`Input/Enzimas/`, limpiar intermedios, metadata completa, borrar el código muerto.

**Cierra.** P-16, P-17, P-21, PK-13 (parte), HALLAZGOS §2.8, §2.9, §5.6.

#### PK-9 — Preview del Studio · SW · ALTO · 0,5 d

`services/packing.py:138` desborda el serial en la copia 23 de GCase (el deslizador llega a
50); `:120, :147-148` meten el `END` de la cápside en medio y copian `CRYST1`/`TER`/`END`
dentro de cada `MODEL` (Biopython ve 11 471 átomos de 224 726; la cápside se pierde);
`:130` trunca los IDs de cadena a un carácter. NGL lo tolera, PyMOL/MDAnalysis/AMBER no;
es el fichero del ZIP de descarga. Usar T1; test que compare número de `MODEL` con
`n_enzymes` y parsee con un lector estricto.

**Cierra.** HALLAZGOS §2.1, §2.2, §2.10, §6.4 (preview).

### 5.3 Poro (Poromania y Pac-Pore del Studio)

#### PO-1 — Invalidar el 1.92 Å · SW · CRÍTICO · 2 h

**Evidencia.** `mutants/mut_129HIS_132GLY/receptor.pdb` ≡ `mutants/WT.pdb` (md5
`d56a4e53…`; Ser129 y Val132 en las cinco subunidades). `mutants/WT.pdb` es
`modelos/BMV/poro5fold.pdb` centrado (5 735 átomos), no el `poronatural.pdb` (3 574, CCMV)
que `1crear_mutantes.pml:5` carga. El `cpoint` commiteado está a 7,59 Å del eje C5 y el
`cvect` 19,29° desviado; la constricción trazada a 11,76 Å del eje.

**Qué hacer.** `INVALIDO.md` en la carpeta (no borrar: es la evidencia). Corregir
`PLAN_POROMANIA.md:40-42`, `ESTADO.md:19,57`, `SESION_STUDIO.md:36-53`, `BITACORA.md:77`
y el README: ninguna dice "real de punta a punta" hasta tener un perfil validado.
**Preguntar a Lucio si el 1.92 Å llegó a la tesis o a una figura**; si sí, corrección.

**Cierra.** PORO-01, PORO-02, PORO-03, HALLAZGOS §1.1, §1.2, §1.5; R1.

#### PO-2 — Sello de procedencia · SW · ALTO · 1 d

Junto a cada salida de HOLE/docking: md5 del PDB de entrada, `cpoint`, `cvect`, `sample`,
`rseed`, versión de HOLE (`2.2.005` es la única registrada hoy), commit, fecha, radio de
sonda y posiciones elegidas (hoy el flujo interactivo de `pore_analyzer.py:598-672` no las
registra). Ya era la acción 2 de `INVESTIGACION_REPRODUCIBILIDAD_2026-09-17.md`.

**Cierra.** PORO-02, PORO-16 (parte), §8 punto 4; R2.

#### PO-3 — Que la mutagénesis haga lo que dice · SW · CRÍTICO · 1–2 d · PyMOL para probar

**Qué hacer.** En `1crear_mutantes.pml:122-129` y `pore.py:238-247`: `cmd.refresh_wizard()`
tras `cmd.wizard('mutagenesis')`; selección por `segi` (en `poro5fold` las 5 subunidades
comparten `chain A` y `/tag//A/129/` casa con 5 residuos); **releer el PDB de salida y
comprobar `resn` en todas las subunidades; abortar si no cambió**; `check=True` y
`returncode` de PyMOL; quitar `except Exception: continue` de `screen_mutants` (`:371`) y
`dock_correlate` (`:550`) y mostrar la fila como fallida; `pac-pore.js:104` y `:210` dejan
de reventar o tragar errores. Documentar que el wizard no relaja el entorno (el Δradio por
mutación es un efecto de rotámero). Decidir `DEL`.

**Hecho cuando.** Un test con PyMOL: mutar 129→GLY y verificar `resn` en 5 `segi`.
Un mutante no mutado produce error, no `delta = 0.00`.

**Cierra.** PORO-01 (causa), PORO-08 (parte), PORO-09, PORO-16, HALLAZGOS §1.1, §4.2,
§4.4, §4.5; R8, R9, R10.

#### PO-4 — Una sola definición del canal · SW · ALTO · 5–8 d

**Evidencia.** Hay cuatro rutas que definen centro y eje. Poromania: centro = media de los
CA de los residuos seleccionados de **una** subunidad (`stored.temp_coords[0]` descarta 4
de 5), eje = cuerda de 4,4 Å del primer CA al centroide (menos fiable cuanto mejor se
eligen los residuos). Studio: centroide (0,000 Å del eje) y eigenvector del valor propio
no degenerado del tensor de segundo momento (0,00° en C5), **pero** sin guarda de
degeneración (trímeros: separación 21 %, error ≈ 6°) y con `_pore_residues` exigiendo
residuos en todas las `chain`, que en el pentámero deja 1 residuo a 11,5 Å de la
constricción. `_hole_on` valida solo `len(rs) < 30` (canal degenerado, no equivocado);
`1run_hole_old.sh:118-151` sí validaba distancia constricción–centro > 5 Å y se perdió.

**Qué hacer.** `pore.py` es la única implementación: `1run_hole.sh` consume
`pore_center.txt`/`pore_vector.txt` generados por `pore.py`; retirar `calculate_pore_vector`
y `calculate_pore_center_for_structure` del generador del `.pml`. Guarda de degeneración
(`min(|w1−w0|,|w2−w1|)/max(w)` > 1e-3 → error y exigir eje explícito o usar eje por
centroides de subunidad). `_chain_ids`/`_pore_residues` por `segi` (columnas 73-76).
Portar la validación de canal: distancia constricción–eje > 2–3 Å → **error**. Mantener
`len(rs) < 30`. Unificar `sample` (0,2 vs 0,25) y declarar el paso junto al radio.
Corregir "tensor de inercia" → "segundo momento". Las copias de `scripts/` por mutante
(`3copiar_scripts.sh`) dejan de existir o se regeneran siempre.

**Hecho cuando.** Sobre `poro5fold` el `cpoint` queda a < 0,1 Å del eje y la
constricción a < 3 Å; sobre un trímero el código pide eje explícito en vez de adivinar.

**Cierra.** PORO-03, PORO-04, PORO-06, PORO-07, PORO-08, PORO-11, PORO-17 (parte),
HALLAZGOS §1.2, §1.15; R3, R4, R5, R6.

#### PO-5 — Parser, filtro y shell de HOLE · SW · ALTO · 1–2 d

`2out_tsv.py:22` y `pore.py:111` descartan todo punto con radio ≤ 0,5 Å (es lo que les
permite parsear, porque hacen `float()` sobre cualquier línea): un poro **ocluido se
reporta abierto** (en `hole_spheres.pdb` 93 de 268 registros tienen r ≤ 0,5). Lo mismo en
`_constriction_point` (centra la caja de docking). `1run_hole.sh:55` nunca imprime el
radio (`$NF` = `angstroms.`; es `$(NF-1)`); `:12-22` fallbacks `0 0 0`/`0 0 1`; sale 0 si
HOLE falla; `rm -f` previo. `4generarhole.sh` aborta el lote con `set -e`;
`6generador_triptico.sh:20` idem; `2cargarsuperficies.sh:59` escribe en `/`. `gmacro`/`quit`
rechazados por HOLE sin que nadie mire `Unrecognized`. `5docking.sh:45,50` trocea por
espacios un PDB de ancho fijo (hoy funciona por suerte).

**Qué hacer.** Delimitar la tabla por la cabecera `cenxyz.cvec`; quitar el filtro;
detectar `***Unrecognized line read` y fallar; `$(NF-1)`; `exit 1` real; sin fallbacks;
columnas fijas en awk.

**Cierra.** PORO-10, PORO-12, PORO-13, PORO-14 (awk), HALLAZGOS §1.3, §1.6–§1.11, §1.14,
§4.3; R7, R17.

#### PO-6 — Divulgación de lo ilustrativo · SW · ALTO · 1 d

El commit `40f4b03` vació el badge "(ilustrativo)" del perfil de poro mientras
`/api/pore/profile` sigue devolviendo una gaussiana sintética (`_AXIS_MIN` + desplazamiento
derivado del **nombre** de la cápside) con `illustrative: True` que el frontend ignora. El
veredicto PASA/OCLUIDO compara ese mínimo contra radios de sustrato "ilustrativos". Y
`_AXIS_MIN = {3-fold: 1.9, 5-fold: 3.2}` guarda el 1.92 (medido sobre un **pentámero**)
como 3-fold, con el orden invertido respecto a la medición del propio Studio (3-fold ≈ 2,47,
5-fold ≈ 1,68; sin artefacto que las respalde).

**Qué hacer.** No mostrar la gaussiana por defecto (panel vacío: "Corre HOLE"); ningún
veredicto cuando ambos lados son ilustrativos; sustituir `_AXIS_MIN` por valores medidos
con procedencia o eliminarlo.

**Cierra.** PORO-15, HALLAZGOS §3.7, §4.1; R15.

#### PO-7 — Recribado real · CIENCIA · CRÍTICO · 1 d + cómputo · HOLE, PyMOL, Vina

Con PO-3/PO-4 hechos y DC-8 decidida: generar de verdad el mutante 129HIS/132GLY (y los
del cribado automático), correr HOLE sobre `poro5fold` con el eje correcto y `rseed`,
docking con Vina, y guardar los artefactos (`Output/hole_runs/`, `Output/cribado/`) con
sello de procedencia. Medir también la dispersión de HOLE sin `rseed` (N corridas) para
cerrar PORO-05. Solo entonces se puede volver a decir "real de punta a punta".

**Cierra.** PORO-05 (dispersión), lo "[REQUIERE CORRER]" de la auditoría de poro.

#### PO-8 — Golden de perfil y guardia de simetría · SW · ALTO · 2–3 d

Golden file (`numpy.allclose`, tolerancia declarada) sobre `BMV/poro5fold` (C5 exacta), no
sobre un trímero; asserts de sanidad (radio > 0, ≥ 30 puntos, constricción dentro del
umbral del eje). Test de simetría de entrada: rotación de 360/n sobre el eje candidato,
desviación de centroides de subunidad (los trímeros dan 2,0 Å: debe aparecer en el informe
de la corrida). Fuera de CI (`@pytest.mark.engine`), necesita HOLE.

**Cierra.** PORO-05, PORO-06 (regresión), PORO-07 (detección); R13, R14.

#### PO-9 — Docking · SW+CIENCIA · MEDIO · 2–3 d

Según DC-7. Si Vina: retirar `5docking.sh` o fijarle semilla y `threads`; `poses.txt` se
ordena con `sort -n` sin `-k` y `smiles_docking_pipeline.py:135-137` toma la primera línea
como "mejor score" (reproducido: informa −7,5 cuando el mínimo es −9,9); `except:` desnudo.
`_pearson` devuelve `{r, n, p}`; con n ≤ 5 no se afirma "abrir el poro debilita la unión"
(`r ≈ 0,9` con n = 5 roza el cero en el IC). Protonación consistente (hoy APBS a pH 4,5,
docking a 7,4). `generate_ligand_from_smiles.py`: el fallback a UFF es inalcanzable
(MMFF devuelve −1 sin excepción) y `-o x.sdf` borra la salida.

**Cierra.** PORO-14, HALLAZGOS §1.13, §1.17, §1.19, §1.20 (sdf); R11, R12.

#### PO-10 — `substrate_section` con radios de vdW · SW+CIENCIA · ALTO · 1 d

Es la pieza mejor hecha del módulo (ETKDGv3, semilla 42, PCA por SVD, test golden y de
determinismo) **pero mide semiejes de centros atómicos sin vdW**: glucosa 1,95 Å frente a
3,49 Å físico (×1,8); etanol ×2,2. La tabla `_SUBSTRATES` del mismo módulo lleva radios de
literatura de 3,5–5,1 Å: dos escalas distintas, y la puerta 1 compara contra una u otra
según el camino. La tolerancia ±0,2 Å del golden está sin usar (variación real entre dos
versiones mayores de RDKit: 0,000). Hacer: incluir vdW, remedir los golden, unificar escala,
tolerancia ±0,05 Å. Mientras, documentar en el test que no es una sección física.

**Cierra.** G-02, G-03; R16, R17.

#### PO-11 — Higiene de Poromania · SW · MEDIO/BAJO · 1–2 d

APBS: `cglen 80` menor que la molécula (107 × 83 × 103 Å), ~14 Å de proteína fuera de
la malla; `foto_poro.pml` con cámara a 421 Å del centro (los PNG salen vacíos; matriz
duplicada en `2cargarsuperficies.sh`); `center_structures.py` centra `receptor.pdb` pero no
`pore_center.txt`/`pore_vector.txt` ni `WT.pdb`; mutantes aleatorios duplicados o iguales
al WT (`random.sample` sin unicidad, `mkdir exist_ok` sobrescribe), `DEL` en el sorteo;
`sorted()` lexicográfico de `resi` (tags `mut_132GLY_9ALA`); umbrales 1,4 vs 2,0 Å en la
misma figura; "anchura" de zona estrecha calculada sobre puntos no contiguos;
`calculate_pentamer_center` ×2 sin usar; `pore_analyzer_backup.py`, `test_*.pml`,
`glucosilceramida.pdbqt` ≡ `ligand.pdbqt`; `CLAUDE.md` de Poromania con `cpoint`
"optimizado" que no corresponde a ninguna corrida y cita ficheros inexistentes;
`os.system` ignorando el retorno. `1run_hole_old.sh` **solo** se borra tras PO-4.

**Cierra.** PORO-17, PORO-18 (informativo), HALLAZGOS §1.4, §1.12, §1.15, §1.16, §1.18,
§1.20; R16.

### 5.4 PackMan (MD coarse-grained SIRAH)

> El `PLAN_REPARACION_MD.md` (rama `claude/packman-repair-plan-9c287t`) tiene el contenido
> literal de los cinco `.in` y los checklists detallados de cada paso. Es el único informe
> al que conviene volver, para copiar y pegar. Las fichas de aquí resumen lo que decide y
> lo que verifica, y añaden lo que los otros informes aportaron después.

#### MD-1 — Confirmar en local antes de tocar nada · 2–4 h · AmberTools, pdb2pqr, perl

Siete comprobaciones (C1–C7 del plan): `cgconv.pl` sobre el PDB empaquetado sin H → 0
`BPG`/`BPE` (las auditorías CG ya lo midieron sobre extractos: faltan 57 BPG + 6 BPE por
cada 3 cadenas); `tleap` sobre ese CG → miles de `Added missing heavy atom`; `parminfo` →
1 molécula de soluto en vez de 181; `mask @CA,C,N,O` = 0 y `:*&!@H=` = todo el sistema;
`pdb2pqr` sobre el empaquetado → aborta por seriales hex (ya confirmado por dos auditorías;
`ValueError: '349F5'`); `charge protein`; `surf` LCPO sin parámetros para beads.
Ya confirmado estáticamente y no hace falta repetir: 180/3/0 `TER`, 0 H, 2 puentes S–S en la
enzima (Cys4–Cys16, Cys18–Cys23 a 2,04 Å), 88 altlocs, bloques A×60/B×60/C×60.

#### MD-2 — Protonar por componente · SW · CRÍTICO · 2–4 h · pdb2pqr

**Receta validada** (reproducida byte a byte: `pdb2pqr --ff=AMBER capside.pdb` →
`cgconv.pl` da exactamente `sustratinaitor/1_capside/3J7L_cg.pdb`, md5
`1d038b4b…`). Para la enzima añadir `--ffout=AMBER` (sin él las 4 Cys de los puentes salen
como `sC` incompletas y no hay puente; con él salen `CYX`→`sX`). Opcional
`--titration-state-method=propka --with-ph=7.0` (cambia 4 Asp/Glu y 1 His; documentar).
Hacerlo sobre `capside.pdb` (180 `TER`) y `enzima.pdb` por separado, nunca sobre el
empaquetado (60 copias de "A 41" y seriales hex). No usar `h_add` de PyMOL (nombra `H01…`
y cgconv no los reconoce).

**Hecho cuando.** `capside_H.pdb`: 180 `TER`, 28 620 residuos, 1 980 `HG SER`, 1 260
`HG1 THR`, 360 `HE1 TRP`; `enzima_H.pdb`: 1 `TER`, 497 residuos, `CYX` en 4, 16, 18, 23.
Decidir y anotar la política de His (todas `sHe` sin `--ffout`; HID/HIE con él): afecta a
540 His de la cápside.

**Cierra.** MD-02, MD-07 (parte), MD-13, CG-rfst1e §1.6–1.7, §2.2 pasos 1–2; PLAN P1.

#### MD-3 — Empaquetar conservando H e insertando `TER` · SW · CRÍTICO · 3–5 h · packmol

`2Empaquetador_Manual.py` / `_Maximo.py`: entradas `*_H.pdb`; `recentrar()` por
traslación NumPy que conserve `TER` (no PyMOL `save`), o `center` de Packmol (T2); tras
Packmol, T1 inserta `TER` (180 + N) y normaliza seriales; `radio_interno = 90` hardcodeado
en `Manual.py:14` → leer `radio_interno.txt`; `run_maestro.sh:41` usa `ls | head -1`
lexicográfico y recoge el PDB **de marzo versionado** en vez del recién generado (`ls -t`
o invalidar por mtime; lo mismo con `*_recentrada.pdb` versionados, que hacen que el
recentrado se salte siempre); `run_maestro.sh:20` produce `N_ENZIMAS="1o"` para `1_1o`;
`cd` sin verificar. Decidir si empaquetar en all-atom y convertir después (hoy) o convertir
cada componente a CG y empaquetar los CG (recomendado por e9h0rt: nunca desborda el serial
y la tolerancia se mide en la resolución real); con T1 ambas funcionan.

**Hecho cuando.** `grep -c '^TER'` = 181 (N = 1); átomos = cápside_H + N × enzima_H;
Packmol "Success", 0 violaciones; el fichero usado es el recién generado (mtime).

**Cierra.** MD-03, MD-17, HALLAZGOS §9.2, §9.4, §9.7, §9.8, §9.10 (parte); PLAN P2.

#### MD-4 — cgconv sobre el PDB correcto y scripts rotos · SW · CRÍTICO · 1–2 h

`run_maestro.sh:58-62`: quitar "salta pdb2pqr", alimentar `cgconv.pl` con el PDB de MD-3;
`:74` llama a `ejecutar_analisis_cpptraj.sh` (no existe; es
`ejecutar_analisis_individual.sh`, que además exige correr antes el generador interactivo).
`setup_1_1o.sh:31-34` y `setup_universal_md.sh:41-44` usan `gensystem_template.leap` y
`run_MD_template.sh` (no existen) → generan ficheros de 0 bytes y declaran `✓ Configurado`:
retirarlos. `convert_to_cg.sh` queda como ruta legacy con T1 delante o se retira. Cablear
como validación previa a tleap los chequeos de `herramientas/auditoria_cg.py` (rama rfst1e)
/ `herramientas/auditoria_cg/auditar_cg.py` (rama e9h0rt): beads por residuo = `amino.lib`,
BPG/BPE al 100 %, `TER` = 180 + N, GC–GC 3,78 ± 0,07 Å, GO–GN 2,24 Å, 0 pares consecutivos
sin `TER` > 4,5 Å.

**Hecho cuando.** En `capside-<dir>-cg.pdb` (N = 1): 29 117 residuos, `BPG` = 3 490,
`BPE` = 372, `sX` = 4, `TER` ≥ 181, 0 avisos de cgconv; la parte de cápside coincide con
`3J7L_cg.pdb` (180 `TER`, 3 420 `BPG`).

**Cierra.** MD-02 (ruta), MD-16, CG-rfst1e §2.1–2.2, CG-e9h0rt §7, HALLAZGOS §9.3, §9.5;
PLAN P3.

#### MD-5 — `gensystem.leap` · SW · ALTO · 2–3 h + tleap · AmberTools

`bond` de los dos puentes por copia de enzima (índices tleap = 28 620 + 497·(k−1) + i;
para N = 1: 28624–28636 y 28638–28643); `solvateOct protein WT4BOX 20 0.7` (hoy 12; el
tutorial y sustratinaitor usan 20); iones explícitos a 0,15 M (`addIonsRand protein NaW n
ClW n`; hoy `NaW 0` solo neutraliza y la cápside tiene carga neta 0 → no añade ningún ion
pese al comentario); quitar `set default PBradii mbondi3` (radios GB all-atom sin sentido
para beads). Dos pasadas en `setup_universal.sh` (contar WT4 y leer `charge`, luego
calcular NaW/ClW). Exportar `AUTO_NRES` (29 117 para N = 1) para la máscara de `eq1`.

**Hecho cuando.** `leap.log`: 0 `Added missing heavy atom`, 0 `Created a new atom`;
`parminfo`: 181 moléculas de soluto; `printBonds @BSG`: 2 enlaces ≈ 2 Å; `mask @GN,GO` =
58 234; `mask @CA,C,N,O` = 0; ≈ 362 residuos terminales (`nX`/`cX`), no 2; carga total 0.

**Cierra.** MD-07, MD-12, CG-e9h0rt #8, HALLAZGOS §8.9 (mbondi3); PLAN P4.

#### MD-6 — Los cinco `.in` SIRAH y `run_MD.sh` · SW+CIENCIA · CRÍTICO · 3–4 h

**Evidencia.** `eq1`/`eq2`/`prod` tienen `nstlim = 500` (10 ps) con títulos "15 ns",
"35 ns", "fast test": 240 ps totales frente a 1,03 µs de referencia. `heat1..6`,
`density_eq`, `final_eq` son all-atom (`dt = 0.002`, SHAKE, `cut = 9`, `gamma_ln = 2`,
`restraintmask='@CA,C,N,O'` que selecciona 0 beads). `em1`/`eq1`/`eq2` con `ntr = 0`
(referencia: 2,4 y 0,24 kcal·mol⁻¹·Å⁻² sobre `@GN,GO`). `eq1` con `ntx=1, irest=0` tira las
velocidades de 110 ps previos. Sin `&ewald chngmask=0` en 10 de 13 (con `sander` falla; con
`pmemd.cuda` regenera exclusiones). `ntpr=ntwx=ntwr=50` (con 100 ns serían 1 000 000 de
fotogramas). 7 etapas con `ntwx` sin `-x` → todas escriben a `mdcrd` y se sobrescriben.
`configurar_simulacion.sh`: `eq1` restringe todo el sistema (`':*&!@H='`; no hay H en
SIRAH), `gamma_ln = 5` (tutorial 7, membrana), no borra los 8 all-atom, `temp0 = 310.5.0`
con temperatura decimal, y si se elige 310 K el calentamiento queda a 300 K. `ig = -1` en
todo y ningún `mdout` commiteado: la semilla es irrecuperable.

**Qué hacer** (según DC-4). `git rm` de los 8 all-atom. Los 5 restantes = `tutorial/5` con
exactamente estos cambios: `em1` añade `ntr=1, restraint_wt=2.4, restraintmask='@GN,GO'`;
`eq1` `restraintmask=':1-29117'` (o `'!:WT4,NaW,ClW'`) e `ig` fijo; `eq2` `ig`; `prod`
`nstlim = 500000` por trozo (10 ns) con `ig = 100100+k` sustituido por `run_MD.sh`;
todos con `ntpr=ntwx=ntwr=5000, ioutfm=1, ntxo=2`, `dt=0.020`, `cut=12`, `ntc=ntf=1`,
`gamma_ln=50`, `chngmask=0`; `skinnb=5` opcional. `run_MD.sh`: 5 etapas, `eq1` arranca de
`em2.ncrst`, bucle de trozos, `SEMILLAS.txt`. `prod-q_gpu.bsub` parametrizado
(hoy apunta a `capside-3_cg-WAT`, que ningún script genera, y salta `final_eq`).
`configurar_simulacion.sh`: retirar (recomendado) o dejarlo idéntico a los estáticos.

**Hecho cuando.** `diff` normalizado contra `tutorial/5` muestra solo las líneas previstas;
`ls *.in | wc -l` = 5; `grep -l "dt = 0.002\|ntc = 2\|cut *= *9" *.in` vacío;
`grep -L chngmask *.in` vacío; `sander` sobre 1CRN con `nstlim=10` termina sin error;
`MD_EXE=echo bash run_MD.sh` imprime em1 → em2 → eq1 → eq2 → prod_k1..k10 con los
`-c/-ref` correctos.

**Cierra.** MD-01, MD-04, MD-05, MD-06, MD-08 (semilla), MD-09, MD-10, MD-11, MD-14, MD-18,
MD-20, HALLAZGOS §8.1–§8.9, §9.9, §9.10; ESTADO CIENCIA-3; PLAN P5.

#### MD-7 — Humo en GPU · CIENCIA · 1–2 h + 15–40 min GPU · pmemd.cuda

em1, em2 completos; `eq1` con `nstlim = 1000`. Verde si: `matches` ≠ 0 (58 234 para
`@GN,GO`), sin `NaN`/`vlimit`, T sube de 0 y se estabiliza en 290–310 K, densidad finita,
RMSD de esqueleto < 1 Å a 20 ps con restricción 2,4, disulfuros ≈ 2 Å, y anotar `ns/day`
(estimado 50–150 en V100 para ~400 k partículas). Si falla: máscara → MD-6; `NaN` en em1 →
MD-2/4/5; `Added missing` → MD-2. **No pasar a MD-8 sin esto.**

**Cierra.** PLAN P6; lo "[REQUIERE CORRER]" de MD-05/MD-06.

#### MD-8 — Producción con manifiesto · CIENCIA · 2 h + 1–3 d GPU

5 + 25 + ≥ 100 ns con `ig` fijos. Nuevo `MANIFIESTO_CORRIDA.md` por corrida: host,
`module list`, versión SIRAH (`x2.3_24-07`; `leaprc` "2.3 Nov 2023"; `0README` "March 2025"),
md5 de `prmtop`/`ncrst`, etapa → `ig` → pasos → `mdout`, pdb2pqr/propka/pH, N_WT4, NaW,
ClW, q. Commitear `leap.log`, los `.in` usados, los `mdout`, `SEMILLAS.txt`; `.gitignore`
para `.nc`/`.ncrst`/`.prmtop`. Aceptación: `NSTEP` = `nstlim` en cada `mdout`, T 300 ± 3 K,
enzima dentro (COM < 90 Å), RMSD acotado (3–6 Å típico a 100 ns; una deriva que no satura
se reporta, no se oculta).

**Cierra.** MD-08, MD-19; PLAN P7; PENDIENTES "Correr la MD".

#### MD-9 — Análisis · SW · ALTO · 1 d · cpptraj (con la trayectoria de MD-7)

`generar_analisis_individual.py:43-44` emite `resSeq` del PDB como máscara cpptraj
(`:26-189`): analiza los primeros 164 residuos de la topología (0,6 % de la cápside), y
`n_enzimas = 497 // 497 = 1` siempre; las máscaras de cápside y enzima se solapan → **la
enzima nunca se analiza**. Usar índices absolutos (cápside 1–28 620; enzima k:
28 621 + 497(k−1)…). `atomicfluct` sin `rms` previo (RMSF contaminado por movimiento
global; coincide con el "r = 0,12, el bug de hoy" del Studio). `surf` LCPO sin parámetros
para beads → `molsurf` con radios del `prmtop` o "no disponible en CG". Graficadores con
0,1 ns/fotograma hardcodeado (100× de error con `ntwx=50`; con MD-6 pasa a ser correcto,
pero derivar de `dt × ntwx`); `plot_sasa.py:40` normaliza mal; `set_xlim(0,1000)`.
`ejecutar_todo_paralelo_progreso.sh:265,278` usa `local` fuera de función (resumen 100 %
errores) y `:59` hace `wait` de un PID que no es hijo (`rc=127` siempre, marca ❌ todo).
`zone_colors` definido en una rama; `tick_labels` exige matplotlib ≥ 3.9.
Correlación RMSF–B-factor como script en `analisis/`.

**Hecho cuando.** Sobre `eq1_smoke.nc`: `.dat` no vacíos, RMSF alineado < sin alinear,
sin warnings LCPO, el monitor marca ✓ en trabajos que terminaron bien,
`bash run_maestro.sh` en seco llega al paso 6.

**Cierra.** MD-15, MD-16 (parte), HALLAZGOS §10.1–§10.6; PLAN P8.

#### MD-10 — Documentación y Studio · SW · MEDIO · 2–3 h

`CHANGELOG.md` 1.3.0; `README.md:17-24`, `diagrama_archivos_dm.md`,
`texto_tesis_archivos_dm.md:15-17,27` (sin 6 calentamientos; `ReplicaExtra` no existe);
`ESTADO.md` CIENCIA-3 decidida; `nanocapsule-mvp/src/services/md.py:20-122`: quitar los
anclajes numéricos de las curvas sintéticas ("RMSD final 2.8 Å", "SASA ~41.893 Å²",
"r = 0.81", "heat1 → 17.666 K · el fallo real") o etiquetarlos "sintético, no medido", y
cargar los `.dat` reales cuando existan; `md_prepare` (`md.py:146-184`) emite ff19SB +
TIP3P (all-atom, irrealizable para 216 780 átomos) para un motor SIRAH, e ignora el SMILES
que acepta. Pedir a Lucio los `mdout`/`leap.log` de `packmanreplicas1/1_2` (origen del
"17 666 K") y los `.in` reales de `capside-3_cg-WAT`.

**Cierra.** MD-08 (cifras sintéticas), S-6, HALLAZGOS §5.3, §5.4, §5.5; PLAN P9.

### 5.5 sustratinaitor

#### SU-1 — Higiene inmediata · SW · ALTO · 3–4 h

Independiente de CIENCIA-2. T1 sobre `3J7L-GYE.pdb` (0 `TER` → 379; 51 951 seriales hex);
`gensystem.leap` escribe `3J7L-GYE_cg.prmtop` y `run_MD.sh` busca `3J7L-GYE_cg-WAT.prmtop`
(nunca arranca; sin `set -e` las 4 etapas se lanzan igual y termina con 0); faltan en la
carpeta los 4 `.in`, el bundle SIRAH, `GYE.mol2/.frcmod` y el PDB (copiar o referenciar;
`addPath` falla); no hay etapa de producción; `addIonsRand NaW 0` vs comentario "0.15 M";
borrar `packmol.log` (truncado a mitad de optimización; el completo es `packmol_run.log`);
README: nombrar **BMV** (3J7L es la cápside de BMV, 149/149 idéntica a `BMV_IJS9`);
`README_conversion_gye_cg.md` afirma compatibilidad SIRAH y mapeo por centros de masa, ambas
falsas; documentar la receta de `3J7L_cg.pdb` (hoy solo estaba en el fichero).

**Cierra.** CG-e9h0rt #1, #7, #8, #9, #10; CG-rfst1e §3.1, §4.3, §6; HALLAZGOS §7.2–§7.4.

#### SU-2 — Ejecutar CIENCIA-2 · CIENCIA · ALTO · según DC-3

Opción B: retirar la etapa 4 de sustratinaitor como "MD del sustrato CG"; la MD de Puerta
4 es PackMan; los estudios del sustrato (cruce del poro con PMF/SMD, sitio activo) van
all-atom en sistemas pequeños reutilizando `GYE.mol2/.frcmod` (que están bien:
antechamber, GAFF2, AM1-BCC). Opción A: subproyecto GYE-SIRAH (cabeza con el patrón de 6
beads de los glicanos SIRAH, β-Gal `BL0` como proxy de β-Glc; cola 24:0 = 6 beads `xMY/xPA`;
esfingosina 18:1 = 5 beads con `xOL`; cargas efectivas; validar contra la MD all-atom del
GYE); `GYE_cg_manual.pdb` solo vale como boceto de partición (beads sobre átomos
individuales a 1,4 Å, nombres `GC`/`GO` que colisionan con el esqueleto proteico, `resSeq`
inválido, `BCT–BF1` a 39 Å, sin `.lib`). Registrar en `ESTADO.md §4b` que el híbrido queda
descartado por evidencia.

**Cierra.** CG-e9h0rt #2, #5, §9; CG-rfst1e §4, §5; ESTADO CIENCIA-2.

#### SU-3 — Geometría del sustrato · CIENCIA · MEDIO · 2 h + packmol

Medido (ver C1): 40 de 200 GYE con COM en el lumen, 36 en la cáscara, 124 fuera; 18
íntegramente dentro. La caja de Packmol (26 900 nm³) es el doble de la esfera externa de la
cápside y Packmol llena esquinas y lumen. Si la pregunta es el cruce del poro (Puerta 1):
`outside sphere 0 0 0 143` + caja, lumen vacío. Si es sustrato encapsulado: `inside sphere`
con el radio interno. Documentar el criterio del "200" (12,3 mM en la caja).

**Cierra.** CG-e9h0rt #6, CG-rfst1e §3.2; HALLAZGOS §7.1 (corregido).

### 5.6 Repositorio, infraestructura y JOSS

#### RP-1 — Fusionar las auditorías y corregir las afirmaciones · SW · ALTO · 2–3 h

1. Fusionar en `main` los 9 informes (todos parten de `40f4b03`, 1 commit cada uno, sin
   conflictos salvo los dos `AUDITORIA_PACKING.md`: renombrar con sufijo de rama) en una
   carpeta `auditorias/2026-10-04/`, más `herramientas/auditoria_cg.py` (rfst1e) y
   `herramientas/auditoria_cg/` (e9h0rt), que MD-4 reutiliza.
2. Fusionar la rama `claude/prepare-joss-submission-29k493` (`paper.md`, `paper.bib`,
   `docs/installation.md`, `docs/usage.md`, `CONTRIBUTING.md`, READMEs en inglés,
   `CITATION.cff`) y **a continuación** corregir en ella, según DC-1:
   - `JOSS_CHECKLIST.md` §3: "Reproducibility: fixed Packmol seeds, golden regression test"
     → no es cierto (PK-03/P-05, G-01); "Gates 1 and 2 are real" → en revisión hasta PK-5 y
     PO-7; "Licence clearly stated" → pendiente de DC-5.
   - `README.md` raíz: puerta 1 "✅ real, de punta a punta" y puerta 2 "✅ real
     (empaquetamiento multi-réplica)" → estado honesto.
   - `PENDIENTES.md:15-16` y `BITACORA.md:24-25`: "el packing es geométrico y determinista
     (semilla fija, golden test)" → retirar.
   - `ESTADO.md:19,57` ("real de punta a punta"), `:109-110`, §4b (CIENCIA-1/2/3 con las
     recomendaciones de §3), §4 (`1run_hole_old.sh` no es basura).
   - `paper.md`: la sección de alcance debe decir lo mismo que el README corregido.
3. Enlazar esta hoja de ruta desde `PENDIENTES.md` como lista de trabajo vigente.

**Cierra.** C4, C8, C11 de §2; HALLAZGOS §2.3 (contradicción documental); P-05 (doc);
JOSS_CHECKLIST §3 (estados falsos).

#### RP-3 — Infraestructura · SW · MEDIO · 1 d

`setup.py`: `version='1.0.0'` (todo lo demás dice 0.1.0), `python_requires>=3.7`
(imposible: lock con 3.12), `find_packages` no distribuye `src/packing/` (único subpaquete
sin `__init__.py`) y el código importa con prefijo `src.` (el paquete instalado no es
importable). `ci.yml:37` instala `ruff` sin pin. `config.py:104` fallback a puerto 5001
(Docker expone 5000: contenedor *unhealthy* si no carga el YAML). `salud.sh:36-40` verde con
tests fallando; `:47` pane Plan roto. `vlpstudio.kdl:32` define y exporta `test()` (pisa el
builtin en todo script hijo) y cablea `/home/luciernaga/...` ×5. `fetch_data.sh` con `wget`
deja un `capside.pdb` de 0 bytes en un 404 y luego "ya existe" para siempre (`_pdb_centroid`
→ `[0,0,0]` sin error). `app.py:372` valida `/api/result/pdb` con `startswith` (`Output_leak/`
pasa; usar `is_relative_to`). `app.py:482` `/api/files/cleanup` con `days_old: 0` borra todo;
`n_enzymes`, `n_replicas`, `radius` sin validar. `THIRD_PARTY.md` según DC-5. Claves
muertas de `default.yaml` (`logging`, `io.*`, `library`, `pymol.*`…): borrar o implementar.
`common.py:21` crea `Input/` al importar. Cosmética CSS/JS de HALLAZGOS §6.14.

**Cierra.** HALLAZGOS §5.1, §5.2, §5.7, §6.1–§6.3, §6.5–§6.9, §6.11–§6.14; JOSS_CHECKLIST
§4.4 (parte).

#### RP-4 — Tests que comprueben algo · SW · MEDIO · 0,5 d

`test_pore_channels_shape`/`test_pore_structures_shape` aceptan `[]` (que es lo que
devuelven si `POROMANIA_DIR` no existe: `paths.py:25` cablea `"Poromania.v.1.2."` con punto
final; subir a 1.3 o renombrar `nanocapsule-mvp/` los deja vacíos sin error y con la puerta
muerta en verde) → exigir las claves conocidas. `test_preview_enzymes_returns_pdb`:
`"END" in body` es tautológico (`ENDMDL`) → comparar `MODEL` con `n_enzymes` y parsear
estricto. Rutas sin cobertura: `/api/capsid/radius`, `/api/experiment/run`,
`/api/result/pdb`, `/api/files/*`, `/api/download/*`. El job `engines` del CI no verifica
sustratinaitor (0 ficheros `.py`): añadir `bash -n`.

**Cierra.** HALLAZGOS §4.6, §6.4, §6.10.

#### RP-5 — JOSS, solo Lucio · 2 h

De `JOSS_CHECKLIST.md` §1 (sigue vigente): nombre legal y ORCID en `paper.md` y
`CITATION.cff` (marcados `TODO`), afiliación y lista de autores; tag de release (los tags
`v0.1.0` y por motor **sí existen en el remoto**; la checklist decía que no porque no
estaban en aquel clon); Zenodo → DOI → README y `CITATION.cff`; verificar los 19 DOIs de
`paper.bib` contra Crossref (ojo a `smart1996` y `rose2018`); declarar la cronología real
(el git log son 2 días). Leer `paper.md` de principio a fin. Enviar solo tras DC-1 y RP-1.

#### RP-6 — Fósiles y código muerto · SW · BAJO · 1 d · al final

`nanocapsule-mvp/{CLAUDE.md, DEVELOPMENT_PLAN.md, TECHNICAL_IMPROVEMENTS.md,
SESION_STUDIO.md, BACKEND_FRONTEND_ARCHITECTURE.md, PLAN_POROMANIA.md}` (contradicen al
software), `vlp-enzyme-brutalista.html`, `ngl-viewer.html`, `/classic`, el código muerto de
Poromania (PO-11) **con `1run_hole_old.sh` solo después de PO-4**, `experiment_manager.py`
consolidación muerta (PK-8). Renombrar `nanocapsule-mvp/` → `studio/` sigue siendo
riesgoso (rutas en `paths.py:25`, `vlpstudio.kdl`, `salud.sh`, Docker).

**Cierra.** JOSS_CHECKLIST §4.4, ESTADO §4 "documentación fósil", VLP-05.

---

## 6. Lo que está bien y no hay que tocar

Para no tirar lo que funciona ni reintroducir bugs resueltos:

- **Studio, arquitectura** `app.py` → `services/` → `core/`: correcta y auditable.
- **Studio, eje del poro** `_pore_axis`: método correcto; sobre el pentámero exacto
  (0,00°). Solo le falta la guarda (PO-4).
- **Studio, `rseed 1`**, validación `len(rs) < 30`, `vdwradii.lib` compartido con
  Poromania, `substrate_section` (semilla 42, PCA por SVD, test golden y de determinismo;
  salvo PO-10), esferas de HOLE al visor por B-factor.
- **Los dos parsers de perfil y los dos extractores de constricción** dan el mismo
  resultado sobre los ficheros commiteados (1,915 Å en z = −15,382; r = 1,920 en
  (15,033; −12,215; 2,264)).
- **`sustratinaitor/1_capside/3J7L_cg.pdb`**: conversión CG impecable (0 fallas contra
  `amino.lib`, 180 `TER`, 100 % de BPG/BPE, GO–GN 2,24 Å) y reproducible byte a byte. Es la
  referencia para PackMan.
- **`GYE.mol2` / `GYE.frcmod`** (antechamber, GAFF2, AM1-BCC): parametrización all-atom
  ortodoxa.
- **El empaquetado de sustratinaitor** convergió de verdad (`Success`, violación 0,000,
  semilla 1234567 por defecto registrada) y la cápside sí está centrada (C1).
- **PackMan**: `eq1`/`eq2`/`prod` tienen la física SIRAH correcta salvo duración y
  restricciones; `gensystem.leap` carga SIRAH bien, closeness 0,7, `saveAmberParmNetcdf`;
  el empaquetado de 1 enzima (único paso con log real) es determinista y sin violaciones;
  las máscaras del análisis son CG-aware (`@GN,GO,GC`); la rampa de `heat1..6` es continua
  y los bloques `&wt` están bien formados (aunque se eliminen).
- **VLP-02** (`found_any`) está realmente corregido.
- **Sospechas que NO se sostuvieron** (HALLAZGOS §12), para no perseguirlas: path traversal
  en `/api/download/single`, `/classic` roto, desfase JS↔backend, tags git ausentes,
  `requirements.txt` vs lock, `ruff` fallando en CI, `2out_tsv.py` capturando tablas ajenas,
  sensibilidad del volumen a la rejilla, `md_prepare` con la caja mal puesta, `iwrap`/`nscm`,
  signo del contraión, `&end` como terminador de namelist (no comprobado, no contado).

---

## 7. Qué hace falta de fuera del repo

Nada de la lista exige esperar por esto, pero cierra hallazgos marcados "[requiere correr]":

| Qué | Para | Quién |
|---|---|---|
| `packmol` instalado: versión y exit code al no converger | PK-1 | Lucio (su máquina) |
| `python3 -c "from pymol import cmd"` en el intérprete de Flask | PK-1, PK-3 | Lucio |
| `statistics.json` / `report.txt` / `metadata.json` de experimentos ya corridos (gitignorados) y de dónde sale la "condición de 6 enzimas" | PK-7 | Lucio |
| HOLE, PyMOL, Vina, idock instalados con versión registrada; `Output/hole_runs/` y `Output/cribado/` de la workstation (respaldarían el 2,47 y el 1,68 Å) | PO-7, PO-8 | Lucio |
| Radio de sonda y posiciones de la sesión interactiva que produjo `1crear_mutantes.pml`; si el 1,92 Å está en la tesis o en una figura | PO-1, PO-2 | Lucio |
| AmberTools (`tleap`, `cpptraj`, `sander`, `pdb4amber`), `pdb2pqr` ≥ 3 (+`propka`), `perl` | MD-1…MD-6, MD-9 | cualquiera, CPU |
| `pmemd.cuda` (AMBER 22) + GPU (V100 16 GB basta) | MD-7, MD-8 | Lucio / clúster |
| `mdout` y `leap.log` de `packmanreplicas1/1_2`; `.in` reales de `capside-3_cg-WAT`; qué ruta generó `3J7L_cg.pdb` | MD-10 | Lucio |
| Términos de la licencia de SIRAH | DC-5 | Lucio |

---

## 8. Índice: de cada hallazgo original a su tarea

Para no volver a los informes. Un hallazgo que aparece en varios informes se lista una vez
por informe con la misma tarea.

**AUDITORIA_MD.md** (MD-01…20, S-1…8): MD-01 → MD-6 · MD-02 → MD-2, MD-4 · MD-03 → T1,
MD-3 · MD-04/05/06 → MD-6 · MD-07 → MD-2, MD-5 · MD-08 → MD-6 (semilla), MD-8, MD-10 ·
MD-09/10/11 → MD-6 · MD-12 → MD-5 · MD-13 → MD-2 · MD-14 → MD-6 · MD-15 → MD-9 · MD-16 →
MD-4, MD-9 · MD-17 → MD-3, PK-6 · MD-18 → MD-6 · MD-19 → MD-8 · MD-20 → MD-6 · S-6 → MD-10 ·
S-7 → MD-2 (altlocs: `pdb4amber` si hace falta).

**PLAN_REPARACION_MD.md** (C1–C7, P1–P9): C1–C7 → MD-1 · P1 → MD-2 · P2 → T1, MD-3 ·
P3 → MD-4 · P4 → MD-5 · P5 → MD-6 · P6 → MD-7 · P7 → MD-8 · P8 → MD-9 · P9 → MD-10.

**AUDITORIA_PACKING.md (rama vdvq69, PK-01…14, T1–T7)**: PK-01 → PK-1, PK-2 · PK-02 →
T2, PK-3 · PK-03/04 → PK-4 · PK-05 → PK-4 (valores), PK-7 (ciencia) · PK-06 → PK-6 ·
PK-07 → PK-3 · PK-08 → PK-4, PK-7 · PK-09 → PK-5 · PK-10 → PK-3 · PK-11 → T1 · PK-12 →
PK-6 · PK-13 → PK-3, PK-8 · PK-14 → PK-3 · tests T1–T7 → PK-5, PK-6.

**AUDITORIA_PACKING.md (rama wwph45, P-01…22, G-01…03, R-1…18)**: P-01/02/03/04/07 →
PK-2 · P-05 → PK-4 · P-06 → PK-7 · P-08/09/10 → PK-6 · P-11 → PK-3 · P-12 → PK-4 · P-13/14
→ PK-7 · P-16/17/21 → PK-8 · P-18 → PK-3 · P-19/20 → PK-4 · P-22 → T1 · G-01 → PK-5 ·
G-02/03 → PO-10 · R-1…5 → PK-1…PK-5 · R-6…10 → PK-6, PK-3, PK-4 · R-11…15 → PK-7, PK-8,
T1 · R-16/17 → PO-10 · R-18 → PENDIENTES "validación con datos experimentales" (fuera de
esta lista).

**AUDITORIA_PORO.md** (PORO-01…18, R1–R17): PORO-01 → PO-1, PO-3 · PORO-02 → PO-1, PO-2 ·
PORO-03 → PO-1, PO-4 · PORO-04 → PO-4 · PORO-05 → PO-7, PO-8 · PORO-06/07 → PO-4 ·
PORO-08/09 → PO-3, PO-4 · PORO-10 → PO-5 · PORO-11 → PO-4 · PORO-12/13 → PO-5 · PORO-14
→ PO-5 (awk), PO-9 · PORO-15 → PO-6 · PORO-16 → PO-2, PO-3 · PORO-17 → PO-11, RP-6 ·
PORO-18 → informativo · R1 → PO-1 · R2 → PO-2 · R3–R7 → PO-4, PO-5 · R8–R10 → PO-3 ·
R11/R12 → PO-9 · R13/R14 → PO-8 · R15 → PO-6 · R16 → PO-11, RP-6 · R17 → PO-5.

**AUDITORIA_SUSTRATO_Y_CG.md (rama rfst1e)**: §1 (conversión correcta) → §6 de esta hoja
· §1.6–1.7 (receta, `--ffout`, His) → MD-2 · §2.1–2.2 → MD-2, MD-3, MD-4, MD-5 · §3.1 →
T1, SU-1 · §3.2 → SU-3 · §4 → SU-2 · §5 → DC-3 · §6 → SU-1 · plan P0 → MD-2…MD-7 · P1 →
SU-1, SU-3 · P2 → SU-2 · P3 → MD-2 (política de His).

**AUDITORIA_SUSTRATO_Y_CG.md (rama e9h0rt, #1…10)**: #1 → T1, MD-3, SU-1 · #2 → DC-3,
SU-2 · #3/#4 → T1, MD-4 · #5 → SU-2 · #6 → SU-3 · #7 → SU-1 · #8 → MD-5, SU-1 · #9/#10
→ SU-1 · §5 (divergencia con AUDITORIA_MD) → C2 de §2.

**HALLAZGOS_NO_DOCUMENTADOS_2026-10-04.md**: §1.1 → PO-1, PO-3 · §1.2 → PO-4 · §1.3 →
PO-5 · §1.4 → PO-11 · §1.5 → PO-1 · §1.6–1.11 → PO-5 · §1.12 → PO-11 · §1.13 → PO-9 ·
§1.14 → PO-5 · §1.15/1.16/1.18 → PO-11 · §1.17 → PO-9 · §1.19 → PO-9 · §1.20 → PO-11,
PO-9 · §2.1/2.2/2.10 → PK-9 · §2.3 → PK-4, RP-1 · §2.4 → T2, PK-3 · §2.5/2.6/2.7/2.9 →
PK-4 · §2.8 → PK-8 · §3.1/3.2/3.3 → PK-3 · §3.4/3.5 (volumen "vdW" = media con n×11,5 Å³;
cuatro scripts con selección distinta) → PK-8 (documentar o recalcular; BAJO) · §3.6
(cadenas y T por conteo de IDs) → PK-8 · §3.7 → PO-6 · §4.1 → PO-6 · §4.2 → PO-3 · §4.3 →
PO-5 · §4.4/4.5 → PO-3 · §4.6 → RP-4 · §4.7 → C7 · §5.1/5.2/5.7 → RP-3 · §5.3/5.4/5.5 →
MD-10 · §5.6 → PK-8 · §6.1–6.3, 6.5–6.9, 6.11–6.14 → RP-3 · §6.4/6.10 → RP-4 · §7.1 →
**corregido** (C1), SU-3 · §7.2/7.3/7.4 → SU-1 · §8.1–8.9 → MD-6 (8.9 `mbondi3` → MD-5) ·
§9.1 → PK-2 · §9.2/9.4/9.7/9.8 → MD-3 · §9.3/9.5 → MD-4 · §9.6 → PK-6 · §9.9/9.10 → MD-6
· §10.1–10.6 → MD-9 · §11.1–11.4 → T1 · §12 → §6 de esta hoja · §13 → §7 · §14 → T2, T3,
PO-3.

**JOSS_CHECKLIST.md**: §1.1–1.4 → RP-5 · §2 "version-tagged release" → ya existe
(`v0.1.0`) · §3 "Reproducibility DONE" → **falso**, RP-1 · §3 "Functionality works as
described" → RP-1, PK-5, PO-7 · §3 "Licence" → DC-5 · §4.1 → RP-5 · §4.2 → sin cambios ·
§4.3 → RP-5 · §4.4 → RP-6 · §5.1 → DC-1 · §5.4 → PO-4 · §5.6 → MD-8 · §6 → RP-5.

**REVISION_MOTORES_hallazgos_sellados.md**: sustratinaitor → confirmado y ampliado (SU-2,
C1) · Poromania `rseed` → PO-7, PO-8 · eje heurístico → confirmado y cuantificado (PO-4) ·
mínimo global → PO-4, PO-5 · `calculate_pentamer_center` → PO-11 · PackMan `heat*` → MD-6 ·
stubs → MD-6 · "positivo: prod/em/eq coinciden" → solo en parte (`ntr=0`) · Packing
"menores" → **refutado** (C4) · "cápside fija de-riesga" → solo si llega centrada (PK-3) ·
"semillas aleatorias = correcto" → refutado como implementación (PK-4) ·
`exclusion_radius` → PK-7.

---

## 9. Fuentes

Todas del 2026-10-04, un commit cada una sobre `40f4b03`, sin fusionar en `main`:

| Informe | Rama | Alcance |
|---|---|---|
| `AUDITORIA_MD.md` | `claude/audit-packman-dynamics-engine-52svym` | PackMan: inputs, parámetros vs SIRAH, setup, reproducibilidad |
| `PLAN_REPARACION_MD.md` | `claude/packman-repair-plan-9c287t` | Plan paso a paso de PackMan, con los `.in` literales |
| `AUDITORIA_PACKING.md` | `claude/audit-packing-engine-vdvq69` | Packing: fuente de PACKMOL, réplica NumPy del radio, regex contra logs |
| `AUDITORIA_PACKING.md` | `claude/audit-packing-engine-wwph45` | Packing: motor ejecutado con doble de PACKMOL, radio por percentiles, golden |
| `AUDITORIA_PORO.md` | `claude/audit-poro-engine-giea7e` | Poro: dos implementaciones, HOLE, mutagénesis, docking |
| `AUDITORIA_SUSTRATO_Y_CG.md` + `herramientas/auditoria_cg.py` | `claude/audit-coarse-grained-conversion-rfst1e` | Conversión CG reproducida byte a byte; GYE; CIENCIA-2 |
| `AUDITORIA_SUSTRATO_Y_CG.md` + `herramientas/auditoria_cg/` | `claude/audit-sirah-coarse-grain-conversion-e9h0rt` | Conversión CG; `TER`; seriales hex; `fix_pdb_serial.py` |
| `HALLAZGOS_NO_DOCUMENTADOS_2026-10-04.md` | `claude/find-undocumented-errors-4ssuye` | 99 hallazgos nuevos en los 4 motores + repo; sospechas descartadas |
| `JOSS_CHECKLIST.md` + `paper.md`, `paper.bib`, `docs/`, `CONTRIBUTING.md`, READMEs en inglés | `claude/prepare-joss-submission-29k493` | Paquete de envío a JOSS |

Contexto ya en `main`: `REVISION_MOTORES.md` (briefing), `REVISION_MOTORES_hallazgos_sellados.md`
(pasada previa, solo lectura de código), `ESTADO.md`, `PENDIENTES.md`.

Medición propia de esta consolidación (Python puro, sin dependencias) para resolver C1:
centroide de la cápside en `sustratinaitor/3_empaquetado_packmol/3J7L-GYE.pdb` = (0, 0, 0);
r_min/r_max = 89,5/142,6 Å; GYE con COM en lumen/cáscara/exterior = 40/36/124; 18 copias
con todos sus átomos en el lumen; 86 con todos fuera.
