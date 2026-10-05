# Hallazgos verificados — depuración de `HALLAZGOS_NO_DOCUMENTADOS_2026-10-04.md`

> **Qué es esto.** La rama `claude/find-undocumented-errors-4ssuye` dejó un informe de "99
> hallazgos" sobre los cuatro motores, producto de una sola pasada. Este documento **no lo
> amplía**: verifica cada hallazgo contra el código real de `main` (`40f4b03`), lo marca como
> **CONFIRMADO**, **DUDOSO** o **FALSO POSITIVO** con la evidencia que lo decide, elimina
> duplicados, lo cruza con los seis informes de las otras ramas de auditoría y ordena lo que
> sobrevive por severidad real, separando lo que bloquea el envío a JOSS de lo cosmético.
>
> **Fecha:** 2026-10-05. **Entorno:** Python 3.11 + numpy/flask/pytest/biopython, bash, ruff,
> node. **Sin** PyMOL, HOLE, Packmol, AMBER, RDKit ni Docker: lo que exige esos binarios se
> marca como DUDOSO salvo que el código sea inequívoco por sí mismo. Ningún fichero de los
> motores se modificó. Toda cifra de este documento se recalculó aquí o se cita del informe
> del verificador correspondiente; las líneas citadas son las reales de `main`, no las del
> informe original (que en algunos casos estaban desplazadas).

---

## 0. Resumen

**Sobre el número 99.** El informe tiene **98 secciones numeradas**, de las cuales **§4.7 es
un "verificado correcto"**, no un hallazgo. El universo real son **97 hallazgos**. Cuatro de
ellos (§1.20, §6.14, §8.9, §9.10) agrupan 16 viñetas menores; se verificaron una a una (113
afirmaciones atómicas) pero se cuentan como sus 97 cabeceras.

| Resultado | Hallazgos |
|---|---|
| CONFIRMADOS (hecho reproducido) | 92 |
| CONFIRMADO el hecho, DUDOSO el mecanismo o la magnitud | 3 (§4.2, §8.1, §10.1) |
| **FALSOS POSITIVOS** | **2** (§7.1, §8.4) |
| Eliminados por estar ya documentados en ESTADO/PENDIENTES/sellado | 3 (§8.6, §8.8, §9.6) |
| Fusionados como duplicados de otro hallazgo del mismo informe | 7 (§2.10→2.1, §3.2→3.1, §3.7→4.1, §7.3→7.2, §7.4→7.2, §10.3→10.2, §10.6→10.5) |
| **Sobreviven** | **85** de 97 |

De los 85 supervivientes, **8 bloquean el envío a JOSS**, **42 son defectos reales de severidad
media** que conviene corregir antes de publicar resultados, y **35 son cosméticos o de
robustez**. **35 de los 85 ya estaban en alguna de las otras seis auditorías**; 50 son
aportación neta de este informe (sobre todo los scripts shell de Poromania, la API/CI del
Studio y el pipeline de análisis de PackMan).

**El informe acierta en los hechos y falla en la calibración.** 92 de 97 hechos se
reproducen. Pero de sus 26 "ALTA", solo **8 se sostienen como ALTA**; 14 bajan a MEDIA y 4 a
BAJA. Y de "los siete que importan" de su resumen, **uno es un falso positivo de medición
(§7.1, el segundo del ranking)** y otros dos están sobrevalorados (§2.1 y §9.1 en su
consecuencia).

### Los siete del informe, reevaluados

| # informe | Hallazgo | Veredicto | Severidad real |
|---|---|---|---|
| 1 | §1.1 El mutante de Poromania es el WT byte a byte | **CONFIRMADO** (md5 idéntico; SER129/VAL132 en los 5 segi). La causa "falta `refresh_wizard`" es **falsa**; la causa real es la selección múltiple por `chain` (ver §1.1) | **ALTA — bloquea** |
| 2 | §7.1 199 de 200 sustratos fuera de la cápside | **FALSO POSITIVO.** La cápside del fichero de salida está en el origen (centroide 0.0). El informe midió el centroide del fichero de *entrada* (207.9) y lo aplicó al GYE de *salida*. Reparto real: 18 dentro / 86 fuera / 96 en la pared, que es justo lo que el informe descartó como "pasada previa" | eliminado |
| 3 | §1.2 Centro/eje del poro sobre una subunidad | **CONFIRMADO** y agravado: el `cvect` forma 19° con el eje C5 real y las esferas de HOLE están a 12 Å del eje | **ALTA — bloquea** |
| 4 | §2.1 PDB del preview corrupto con ≥23 enzimas | **CONFIRMADO** (9 325 líneas rotas desde la copia 23), pero afecta al *preview* aleatorio, no al packing de Packmol | MEDIA |
| 5 | §2.3 Packing no reproducible | **CONFIRMADO** (`seed_base`/`use_random_seeds` no los lee nadie; `random.randint`). La semilla sí queda en `metadata.json`. Lo grave es que PENDIENTES afirma un determinismo falso | MEDIA (corregir PENDIENTES) |
| 6 | §2.4 Si falla el centrado, enzimas en el vacío | **CONFIRMADO** el mecanismo (`fixed` sin `center`; `except` traga el fallo). Requiere PyMOL ausente con Packmol presente | **ALTA condicionada — bloquea** |
| 7 | §10.1 El análisis MD mide 164 residuos | **CONFIRMADO** el mecanismo (resi → máscara `:N` sin mapeo); **DUDOSAS** las cifras (medidas sobre `capside.pdb`, no sobre el PDB de tleap que el script lee) | **ALTA — bloquea** la MD |

---

## 1. Criterios

- **CONFIRMADO**: la evidencia (comando, recálculo, test client, sandbox bash) reproduce lo
  afirmado. **DUDOSO**: hecho de código cierto pero mecanismo o magnitud no decidible sin el
  motor. **FALSO POSITIVO**: el código no hace lo que dice el informe, o el defecto afirmado
  no es un defecto.
- **Severidad real** (la de este documento, no la del informe): **ALTA** = produce o ha
  producido resultados científicos falsos sin aviso, o impide instalar/publicar (JOSS:
  instalabilidad, licencias); **MEDIA** = bug real que rompe un flujo, engaña al usuario o
  está latente con disparador plausible; **BAJA** = robustez, estilo, código muerto, inocuo hoy.
- **Bloquea JOSS**: ALTA que afecta a lo que un revisor verá o ejecutará (artefactos
  versionados falsos, `pip install`, licencias) o al único pilar que sostiene el envío (el
  packing). Lo demás, por grave que sea para la tesis, no bloquea el *software paper*.
- **Duplicado**: mismo defecto en el mismo código listado dos veces. Dos defectos distintos
  en el mismo fichero **no** se fusionan.
- **Ya documentado**: aparece en `ESTADO.md §4/§4b`, `PENDIENTES.md` o
  `REVISION_MOTORES_hallazgos_sellados.md`, que el informe prometía excluir.

Fuentes del cruce (todas leídas íntegras):

| Clave | Rama | Fichero |
|---|---|---|
| MD | `audit-packman-dynamics-engine-52svym` | `AUDITORIA_MD.md` (MD-01…20, S-1…8) |
| PK-A | `audit-packing-engine-wwph45` | `AUDITORIA_PACKING.md` (P-01…22, G-01…03) |
| PK-B | `audit-packing-engine-vdvq69` | `AUDITORIA_PACKING.md` (PK-01…14) |
| PORO | `audit-poro-engine-giea7e` | `AUDITORIA_PORO.md` (PORO-01…18) |
| CG-A | `audit-coarse-grained-conversion-rfst1e` | `AUDITORIA_SUSTRATO_Y_CG.md` |
| CG-B | `audit-sirah-coarse-grain-conversion-e9h0rt` | `AUDITORIA_SUSTRATO_Y_CG.md` (hallazgos 1-10) |
| SELL / EST | `main` | `REVISION_MOTORES_hallazgos_sellados.md`, `ESTADO.md` |

---

## 2. Eliminados

### 2.1 Falsos positivos (2)

**§7.1 — "199 de 200 sustratos fuera de la cápside" (el informe lo rotula ALTA y lo pone
segundo en su ranking).** Recalculado con numpy sobre
`sustratinaitor/3_empaquetado_packmol/3J7L-GYE.pdb` (160 620 átomos = 131 820 cápside +
200×144 GYE):

```
cápside: centroide (−0.0, 0.0, −0.0), distancia al origen 0.0 Å, r_int 89.5, r_ext 142.6
GYE:     centroide (3.0, −0.2, 8.7)
moléculas con todos sus átomos en la cavidad: 18 · todos fuera: 86 · atravesando la pared: 96
centros de masa: 40 en el lumen · 36 en la corona · 124 fuera
distancia mínima GYE–cápside: 2.00 Å (= tolerance)
```

Los números que el informe atribuye a "la cápside del fichero de salida" —centroide
(207.9, 207.9, 207.9), caja (68.3, 71.9, 66.4)–(347.5, 343.9, 349.4)— son exactamente los de
`1_capside/3J7L_cg.pdb`, el fichero de **entrada**. `center` + `fixed 0. 0. 0. 0. 0. 0.`
(`packmol_input.inp:8-9`) sí trasladó la cápside al origen; la salida es una traslación pura
de −207.9 Å. La "nota de discrepancia" del informe (§12) descarta la medición correcta
(18/86/96) por la incorrecta. Lo que queda de real —que la caja de ±150 Å llena esquinas y
lumen, con ~20 % de los centros de masa dentro de la cápside— está documentado como
intencional en `sustratinaitor/EXPLICACION.md §3` y ya lo discuten CG-A §3.2 y CG-B §8.2
como decisión científica, no como bug. La recomendación §14.2 del informe para
sustratinaitor se apoya en este falso positivo.

**§8.4 — "`eq1` descarta 7 etapas de dinámica previa" (MEDIA-ALTA).** El hecho es cierto
(`eq1_WT4.in:3` `ntx=1, irest=0`, `tempi=300.0`; `run_MD.sh:264-269` le pasa
`_density.ncrst`), pero la conclusión no: con `ntx=1` AMBER lee coordenadas **y caja** del
restart y solo resortea velocidades Maxwell a la misma temperatura, otra muestra del mismo
ensamble canónico. Las coordenadas y la densidad, que es donde vive el efecto de la rampa y de
`density_eq`, se conservan. La propia referencia SIRAH hace lo mismo entre dos etapas a 300 K:
`tutorial/5/eq2_WT4.in:3` `ntx=1, irest=0`. El caso realmente malo es el `tempi = 0.0` del
generador, que está en §8.3.

### 2.2 Ya documentados (3) — el informe prometía no repetirlos

| § | Hallazgo | Dónde estaba ya |
|---|---|---|
| §9.6 | `1calcula_radio_interno.py` reporta +1 Å sobre la colisión | CIENCIA-1 (`ESTADO.md §4b`), `SELL:58-62` ("radio reportado +1 / efectivo −1"), MD-17. Además el +1 es intención documentada (`README.txt:59`, print de la línea 40) y Packmol lo resuelve con la cápside `fixed` + `tolerance 2.0`: sin efecto medible |
| §8.8 | `ntpr=ntwx=ntwr=50` en eq1/eq2/prod | Es la misma faceta del stub `nstlim=500` ya sellado (`SELL:50-51`, MD-01). 500/50 = 10 fotogramas es el escalado de un test; el generador recalcula ambos a la vez (`configurar_simulacion.sh:263-266`) |
| §8.6 | `gamma_ln` 2.0 en heat/density/final vs 50 en eq/prod | Reformulación de CIENCIA-3 ("parámetros all-atom en un sistema CG", `SELL:43-46`, MD §3.2 pt 6). El 5.0 del generador es un valor que SIRAH sí usa (tutoriales 6/7) y `gamma_ln` no cambia el ensamble de equilibrio: la frase "el estado al que llega eq1 no es el del protocolo" no se sostiene |

### 2.3 Duplicados fusionados (7)

| Absorbido | En | Por qué es el mismo defecto |
|---|---|---|
| §2.10 (IDs de cadena colapsan) | §2.1 | Mismo bucle de `preview()` (`services/packing.py:128-149`), mismo disparador (>22 copias); además la franja afectada ya tiene la columna 22 desplazada por §2.1 |
| §3.2 (ruta relativa de `radio_interno.txt`) | §3.1 | Mismo fichero único y global; el arreglo (clave por cápside en una ruta absoluta) cierra ambos |
| §3.7 (radios ilustrativos → PASA/NO PASA) | §4.1 | Son los dos lados de la misma comparación (`pac-pore.js:242-245`): poro ilustrativo vs sustrato ilustrativo. PORO-15 los trata como uno |
| §7.3 (carpeta sin dependencias), §7.4 (sin producción ni `$?`) | §7.2 | Los tres dicen "la etapa 4 de sustratinaitor no puede ejecutarse tal como está" sobre los mismos dos ficheros (`gensystem.leap`, `run_MD.sh`) |
| §10.3 (`wait` sobre PID no hijo) | §10.2 | Dos causas del mismo efecto único: el monitor paralelo marca ERROR en todo. Se corrigen juntas |
| §10.6 (`tick_labels` ≥ matplotlib 3.9) | §10.5 | Mismo script (`compara_enzimas_misma_capside.py`), mismo ocultamiento (`> /dev/null 2>&1`), misma severidad |

---

## 3. Lo que sobrevive, por severidad real

### 3.1 BLOQUEA EL ENVÍO A JOSS (8)

| # | § | Hallazgo | Evidencia decisiva | Cruce |
|---|---|---|---|---|
| A1 | **§1.1** | El único mutante versionado de Poromania (`mutants/mut_129HIS_132GLY/receptor.pdb`) es byte-idéntico a `mutants/WT.pdb`; todo lo derivado (HOLE 1.915 Å, APBS, figuras) describe el WT con etiqueta de mutante | `md5sum` → `d56a4e53…` ambos; CA 129 = SER y 132 = VAL en los 5 `segi` (A_6…A_10). **Causa**: `1crear_mutantes.pml:126` `w.do_select(f"/{tag}//{chain}/{pos}/")` casa 5 residuos porque las 5 subunidades comparten `chain A`; en el fuente del wizard de PyMOL (`mutagenesis.py`) `do_library()` exige `count_atoms(name N)==1`, si no hace `clear()` → `status=0` → `apply()` es un no-op silencioso. La hipótesis "falta `cmd.refresh_wizard()`" **es falsa**: `set_mode`/`do_select` ya lo llaman. Nada compara `resn` tras `apply()` | PORO-01 (idéntico), PORO-09 (causa) |
| A2 | **§1.2** | El centro y el eje del poro se calculan sobre la primera subunidad (`stored.temp_coords[0]`): el perfil HOLE versionado no recorre el poro C5 | `pore_analyzer.py:428`. Emulando el bucle con numpy se reproduce **exactamente** `pore_center.txt` (9.18, −3.88, 2.22) y `pore_vector.txt` desde los 4 CA de A_10. Centroide de las 5 subunidades: a 7.59 Å. Eje C5 real (normal al plano de los 5 centroides): el `cvect` versionado forma **19.4°**; las 175 esferas de HOLE están a mediana 12.2 Å del eje y la mínima (r = 1.920) a 11.8 Å | PORO-03, PORO-09; SELL:32-34 solo anotaba el heurístico del vector |
| A3 | **§4.2** | El Studio (`pore.py:238-240`) reimplementa la mutagénesis con el mismo selector `/{tag}//{ch}/{pos}/`, ignora el `returncode` de PyMOL (`pore.py:247`) y solo comprueba `pdb.exists()` (`:356`): un mutante no mutado da `delta = 0.00` sin alarma | Sobre `modelos/BMV/poro5fold.pdb`: `_chain_ids` → `['A','B']`, 10 `segi`, **5 CA con `chain A` y `resi 129`** → misma ambigüedad que A1. **DUDOSO el efecto** (sin PyMOL aquí), pero el mecanismo está en el fuente del wizard. Para los trímeros (un `segi` por cadena) el selector casa 1 residuo y funcionaría | PORO-16, PORO-09, PORO-08 |
| A4 | **§2.4** | Si falla el centrado, las enzimas se empaquetan en el vacío: `parallel_packer.py:260-263` escribe `fixed 0. 0. 0. 0. 0. 0.` **sin `center`** y `experiment_runner.py:97-117` traga la excepción de `center_structure()` dejando `capsid_file` sin centrar | Reproducido vía test client sin PyMOL: el `.inp` apunta a `Input/Capsides/QB_1QBE/capside.pdb` crudo con `inside sphere 0. 0. 0. 88.0`. Geometría: BMV `capside.pdb` centroide a 360.1 Å del origen, átomo más cercano a 221.4 Å → la esfera de 88 Å no toca la cápside; QB a 73.9 Å → la esfera pisa la pared. `md.py:158-159` sí escribe `center`. No hay otra guarda. **Condicionado** a PyMOL ausente/roto con Packmol presente; `ESTADO §4b` admite que "el radio casi siempre es el fallback 90 Å", es decir, que PyMOL ha fallado a menudo | PK-B PK-02 (idéntico, derivado de `cenmass.f90`); contradice SELL:63-65 |
| A5 | **§9.1** | La regex `Maximum\s+distance\s+violation:` (`2Empaquetador_Maximo.py:87`) no casa nunca con Packmol (que escribe `Maximum violation of target distance:`): el criterio de colisión documentado (0.10 Å) no existe y el fallback `< 10000 líneas` lo satisface la cápside sola | Regex ejecutada sobre los dos logs reales del repo → `None`. El bucle es `while True` (`:140`) sin tope; el único freno real es `returncode == 0 and exists(output)` (`:79`). **La consecuencia del informe está exagerada**: Packmol 20.x devuelve ≠0 y escribe `_FORCED` al no converger, así que el bucle para; "indefinidamente hasta agotar disco" y "~133 s por corrida" (ese dato es del log de sustratinaitor; el de PackMan dice 2.1 s) no se sostienen. **Pero** el N "máximo" pasa a depender del exit code de Packmol, que ningún informe pudo verificar sin el binario, y el mismo regex está heredado en el Studio (`parallel_packer.py:34-36`), que es el pilar del envío | PK-A P-01/P-02/P-03 y PK-B PK-01 (lo tratan como BLOQUEANTE para el Studio, con doble de Packmol) |
| A6 | **§10.1** | `generar_analisis_individual.py:43-44,73-78` usa `int(resi)` del PDB como máscara cpptraj `:N-M`, que se refiere al índice secuencial de la topología, sin ningún mapeo | Mecanismo inequívoco: 8 máscaras emitidas tal cual (`:270,273,289,305,308,330,346,349`), `set()` colapsa las 180 copias que repiten `resSeq` 26-189, `n_enzimas = total // 497`. **DUDOSAS las cifras** del informe (164 residuos, `n_enzimas = 1`): están medidas sobre `capside.pdb`, pero el script prefiere `*_cg-WAT.pdb` (`:112-119`), el PDB de tleap, cuya numeración es la secuencial de LEaP (y en 4 columnas por encima de 9999). Con ~29 000 residuos el mapeo no puede ser la identidad en ningún caso. Además `not resn WT4` no excluye los iones `NaW`. Latente mientras la MD no corra; cpptraj no avisará porque siempre selecciona *algo* | MD S-4 solo lo califica de "frágil" |
| A7 | **§6.1** | `pip install nanocapsule-mvp/` deja un paquete inútil: `find_packages(where='src')` + `package_dir={'': 'src'}` instala `core/engines/io/services/web` sin el prefijo `src.` que usa todo el código, y `src/packing/` no tiene `__init__.py`, así que `parallel_packer` ni se distribuye | Reproducido en venv limpio: `import src.core` → `ModuleNotFoundError`; `import core.experiment_runner` → `No module named 'packing'`. **Adicional**: instala un top-level `io` que colisiona con la stdlib. Desde el repo funciona por `pytest.ini pythonpath = .` y `app.py:15 sys.path.insert`. Criterio JOSS: instalabilidad | Distinto de `ESTADO §4` (entry point `cli/main.py`, ya retirado) |
| A8 | **§6.8** | `THIRD_PARTY.md:4-5,33` afirma que SIRAH "NO se distribuye", y el repo versiona **146 ficheros (3.6 MB)** de SIRAH 2.3 en `PackMan.v.1.2/archivos_dm_cg/sirah_x2.3_24-07.amber/` | `git ls-files … | wc -l` → 146. `tools/COPYING` = GPLv2; `cgconv.pl:16-18` GPL-2.0-or-later (compatible con AGPLv3, sin conflicto). El `0README` del bundle solo trae un "Legal declaimer: Copyright (c) 2014" **sin licencia para los ficheros del campo de fuerza**: "verificar términos" sigue sin hacerse. `ci.yml:53-54` y `PENDIENTES.md:32` muestran que el proyecto sabe que el bundle está ahí. Criterio JOSS/Zenodo: declaración de terceros falsa | MD-19 solo anota la versión |

### 3.2 Defectos reales de severidad MEDIA — corregir antes de publicar resultados (42)

Agrupados por motor. "Sev. inf." es la severidad que daba el informe.

**Poromania (11)**

| § | Hallazgo | Veredicto y evidencia | Sev. inf. → real | Cruce |
|---|---|---|---|---|
| 1.3 | `2out_tsv.py:22-23` descarta radios ≤ 0.5 Å: un poro ocluido se reporta como abierto; `ax.plot` une el hueco | CONFIRMADO, **latente**: 347/347 puntos sobreviven hoy (mínimo 1.915). Mismo filtro en `pore.py:111` y `_constriction_point` (`:201`) del Studio | ALTA → ALTA latente | PORO-10 |
| 1.4 | `foto_poro.pml:33-39` y `2cargarsuperficies.sh:82-88` tienen la cámara en (220.4, 169.1, 316.4), marco sin centrar; la molécula está en el origen (421 Å de distancia, slab 80 Å) | CONFIRMADO con prueba directa: `imagenes/mut_82TRP…/surf.png` muestra solo las barras del ramp, sin molécula. Coincide con el `cpoint` fósil de `CLAUDE.md:59` | ALTA → MEDIA | — |
| 1.5 | `1crear_mutantes.pml:14` `chains=['A','B']` no cubre la cadena C del `poronatural.pdb` versionado | CONFIRMADO y agravado: `poronatural.pdb` de la raíz es md5-idéntico a `modelos/CCMV/poronatural.pdb` (ASN129/ASP132), mientras `WT.pdb` es BMV (SER/VAL) = `modelos/BMV/poro5fold.pdb` centrado. Re-ejecutar hoy mutaría **otra proteína**, en 2 de 3 cadenas | ALTA → MEDIA (nada versionado afectado; irreproducibilidad) | PORO-02 |
| 1.7 | `1run_hole.sh:11-23`: sin `pore_center.txt` → `CPOINT="0 0 0"`, sin vector → `"0 0 1"`, solo un `⚠️` y continúa | CONFIRMADO; latente (el `.pml` escribe siempre ambos) | MEDIA → MEDIA latente | PORO-04 (cercano) |
| 1.8 | `1run_hole.sh` sale 0 si HOLE falla (rama `else` sin `exit 1`) y `rm -f` las esferas previas **antes** de correr | CONFIRMADO en sandbox sin `hole`: exit 0, `hole_spheres.pdb` anterior destruido; `clickautomatico.sh` sin `set -e` sigue | MEDIA | — |
| 1.9 | `4generarhole.sh:4 set -e` + `exit(1)` legítimo de `3analizar_hole.py` → el lote muere en el primer mutante degenerado | CONFIRMADO en sandbox con dos mutantes: el segundo nunca se procesa, sin mensaje | MEDIA | — |
| 1.10 | `6generador_triptico.sh:20` `find` sobre `hole/resultados` inexistente + `set -euo pipefail` → aborta; la rama "Se omite" (23-26) es inalcanzable | CONFIRMADO en sandbox | MEDIA | — |
| 1.12 | APBS `cglen 80 80 80` (`2cargarsuperficies.sh:30`) frente a una molécula de 107.5×83.4×102.6 Å | CONFIRMADO desde `log_apbs.txt:88-90` e `io.mc:66-67`: 13.75 Å fuera por lado en X, 11.3 en Z; **845 átomos (7.4 %) fuera de la malla gruesa**; APBS no avisa; el `.dx` se usa tal cual | MEDIA | — |
| 1.13 | `5docking.sh:95` `sort -n` sin `-k2` ordena por nº de pose; `smiles_docking_pipeline.py:134-137` lee la primera línea y la rotula "Mejor score"; `except:` desnudo | CONFIRMADO: con scores −7.5/−9.9/−8.1 el pipeline informa −7.5 | MEDIA | — |
| 1.14 | `5docking.sh:45` troza `hole_spheres.pdb` por espacios; en 93 de 268 líneas el centinela va pegado (`S-888`) | CONFIRMADO, latente: hoy esas líneas tienen `$10 = 0.00` y se descartan; la numeración de esferas va de −70 a 103, a 30 esferas de que aparezca `S-100` y el centro de la caja se corrompa | MEDIA latente | PORO §3.4 ("frágil, da lo mismo hoy") |
| 1.18 | `pore_analyzer.py:359-371`: mutantes aleatorios sin control de unicidad, `random.choice` puede devolver el silvestre, `'DEL'` entra en el sorteo; `mkdir(exist_ok=True)` sobrescribe | CONFIRMADO con la semilla real (`random.seed(42)`, que el informe omite): 19 tags únicos de 20, 1 deleción | MEDIA | PORO §8 pt 5 (solo `DEL`) |

**Studio — packing, biblioteca y preview (10)**

| § | Hallazgo | Veredicto y evidencia | Sev. inf. → real | Cruce |
|---|---|---|---|---|
| 2.1 (+2.10) | `services/packing.py:126,138`: serial con `:5d` desde 10 000 → desborda en la copia 23 (GCase) / 47 (EGFP), dentro del deslizador (max 50); columna 22 pasa a `' '`; `chain_ids[...][0]` trunca a un carácter | CONFIRMADO en vivo con `n_enzymes=25`: 9 325 líneas ilegibles por columnas, idéntico al informe. Afecta solo al **preview** aleatorio (sin Packmol), que se guarda en `Output/Generated_PDBs/` y viaja en el ZIP | ALTA → MEDIA | — (PK-A P-22 solo menciona que el preview asigna cadenas) |
| 2.2 | El PDB del preview lleva el `END` de la cápside en medio y un `CRYST1`/`TER`/`END` por `MODEL` | CONFIRMADO (224 726 / 11 471 / 3 613 reproducidos). **Atribución corregida**: Biopython colapsa el `capside.pdb` crudo a 3 613 átomos **antes** del preview (IDs A/B/C y `resSeq` repetidos 180 veces, §3.6): la "pérdida de la cápside" es de los PDB de entrada. "Inválido para cualquier parser" es exagerado: Biopython lo lee | ALTA → MEDIA | PK-A P-22 (TER/hex, el entregable real) |
| 2.3 | `seed_base: 1234567` / `use_random_seeds: false` del YAML no los lee nadie; `experiment_runner.py:160-170` no pasa semilla → `random.randint` (`parallel_packer.py:118`); el preview tampoco es repetible | CONFIRMADO (`.inp` real generado: `seed 275409`). La semilla sí queda en `metadata.json` (`:357`). `PENDIENTES.md:15-16` afirma "semilla fija, golden test": el golden test es del radio RDKit, no del packing | ALTA → MEDIA (y corregir PENDIENTES) | PK-A P-05, PK-B PK-03; contradice SELL:65 |
| 2.5 | `parallel_packer.py:384-390` devuelve `success: False` + `error`; `app.py:303-320` responde 200 `status: completed` sin el `error`; `packing.js:61` nunca mira `d.success` → "Packing real OK: 0 enzimas · 0/N" en verde | CONFIRMADO vía test client sin Packmol | MEDIA | — |
| 2.6 | El campo "Radio interno (Å)" se envía en el preview (`packing.js:8`) pero no en `doRun` (`:58`); `run_experiment()` no tiene parámetro de radio y recalcula o cae a 90 | CONFIRMADO. Además el preview usa `radius × 0.8` (`packing.py:47`): preview y experimento son incomparables incluso con el mismo radio | MEDIA | — |
| 2.7 | `engines.packmol.timeout: 300` ignorado → `timeout=90` cableado (`parallel_packer.py:283`); el timeout cuenta como "no cabe" (`:312-320`) | CONFIRMADO. La fila `seed_base` es §2.3; `collision_margin` cableado vale lo mismo que el YAML (2.0): latente | MEDIA (timeout) | PK-A P-19, PK-B PK-04 |
| 2.8 | `experiment_manager.py:69` `Output/<capside>/<enzima>` sin timestamp: cada corrida pisa `replica_*/`, `summary/`, `statistics.json`; `CLAUDE.md:104` promete `[timestamp]` | CONFIRMADO; además mezcla artefactos de corridas con N distinto en la misma carpeta | MEDIA | PK-A P-16 |
| 3.1 (+3.2) | `capsid.py:152-155` escribe un `radio_interno.txt` único y relativo al CWD; `library.py:63,84-85` lo lee desde `PROJECT_ROOT` y lo muestra `if name.startswith("BMV")` | CONFIRMADO con monkeypatch: un 131.0 "de CCMV" aparece como radio de BMV. El arranque fósil de `CLAUDE.md:31` (`cd src/web`) dejaría el fichero donde nadie lo lee; Docker y `ESTADO §7` arrancan desde `PROJECT_ROOT` | ALTA → MEDIA | PK-A P-18, PK-B PK-10; `ESTADO §3` lo da por limitación |
| 3.3 | `/api/capsid/radius` sin PyMOL responde `status: success`, `"Radio interno calculado: 90.0 Å"` con el default (`capsid.py:72-77`, `app.py:252-268`) | CONFIRMADO vía test client (`/api/health` sí dice `pymol: false`). También cae al mismo default si no hay colisión en 5..200 Å | MEDIA | PK-A P-11, PK-B PK-07; `ESTADO §4b` admite el fallback |
| 3.4 | La columna "Volume(Å³)" que sirve `library.py:53` es `(n_atoms × 11.5 + grid) / 2` (`fast_vdw_volume.py:104-107,157,211`), bajo un título "VAN DER WAALS VOLUMES" | CONFIRMADO al Å³ con las funciones del propio script: grid implícito = grid recalculado en las 4 enzimas (71 464 / 19 811 / 42 422 / 43 215); sesgo +2.8 % a +5.9 % al alza. Luciferasa, que el informe dejó sin cerrar, también cierra | MEDIA | — |

**Studio — PAC-PORE, preparador DM, tests y datos (8)**

| § | Hallazgo | Veredicto y evidencia | Sev. inf. → real | Cruce |
|---|---|---|---|---|
| 4.1 (+3.7) | El commit `40f4b03` vació el badge "(ilustrativo)" del gráfico del perfil (`studio.html:183`, `pac-pore.js:71`); `/api/pore/profile` sigue devolviendo una gaussiana con mínimo cableado por eje y offset derivado del **nombre** de la cápside (`pore.py:32,625`), con `illustrative: True` que el frontend ignora (0 ocurrencias en JS). El pie "PASA/NO PASA" (`pac-pore.js:242-245`) compara ese mínimo con un radio de sustrato también ilustrativo (`_SUBSTRATES`) salvo que el usuario dé un SMILES | CONFIRMADO. **Matiz**: el cuadro de estado contiguo sigue diciendo "Perfil ilustrativo — usa Correr HOLE" (`pac-pore.js:75-76`, `studio.html:179`); el badge se quitó a propósito (mensaje del commit). Además `_AXIS_MIN` tiene el orden 3-fold/5-fold invertido respecto a la medición del propio Studio (PORO §4) | ALTA → MEDIA | PORO-15 |
| 4.4 | `screen_mutants` puede devolver `mutants: []` (`pore.py:355-357,371-372` `continue` silenciosos) y `pac-pore.js:104` hace `d.mutants[0].name` → `TypeError` en vez de "ningún mutante abrió el poro" | CONFIRMADO en node. Además sin `pymol` instalado `subprocess.run` lanza `FileNotFoundError` → `app.py` lo mapea a **404** | MEDIA | PORO-16 (los `except: continue`) |
| 4.5 | `loadHoleStructures()` tiene `catch (e) {}` (`pac-pore.js:205-211`); tres botones (`runHole`, `runScreen`, `runDock`) salen en silencio si el `<select>` está vacío, `runManualMutant` da un mensaje erróneo | CONFIRMADO (3 silenciosos + 1 engañoso, no 4 silenciosos) | MEDIA | — |
| 5.3 | `md_prepare(capsid, n_substrate, smiles)` (`md.py:146-184`) solo devuelve el SMILES; el bloque Packmol dice siempre `structure sustrato.pdb`, fichero que nunca se produce; `studio-core.js:163` pinta `# SMILES …` | CONFIRMADO. Docstring del módulo: "inputs reales"; cabecera de la sección (`md.py:126`): "(ILUSTRATIVO)" | MEDIA | `ESTADO §3` ("genera inputs pero no ejecuta") |
| 5.4 | El preparador emite `ff19SB` + `gaff2` + `TIP3P` + `solvateOct … TIP3PBOX 10` (`md.py:166-176`) para un proyecto cuyo único motor de MD es SIRAH CG (`gensystem.leap`: `leaprc.sirah`, `WT4BOX`) | CONFIRMADO el núcleo. **Dudosos** dos detalles: son ~2×10⁶ átomos de agua, no "decenas de millones"; y tleap sí añade H a residuos estándar, el obstáculo real serían altlocs/TER | MEDIA | MD S-6 |
| 6.4 | `test_smoke.py:69-78` solo exige `isinstance(…, list)`; `pore_channels()`/`hole_structures()` devuelven `[]` si falta `POROMANIA_DIR` → verde con la puerta muerta. `test_smoke.py:136` `"END" in body` es tautológico (`"END" in "ENDMDL"`); `n_enzymes=2` no alcanza §2.1 | CONFIRMADO; 22 tests, rutas sin cobertura confirmadas por `grep`. Los tests se autodeclaran "de forma, no de valor científico" | MEDIA | PK-A G-01, PK-B PK-09 (cero tests del packing) |
| 6.5 | `salud.sh:36-40` `case "$res" in *passed*)` → verde con `"1 failed, 21 passed"` | CONFIRMADO con la salida real de este entorno: pintaría `✓ 9 failed, 13 passed` | MEDIA | — |
| 6.7 | `fetch_data.sh:21-28`: `wget -O` crea y trunca el destino antes de la petición; con 404 deja 0 bytes (exit 8) y `[ -f "$dest" ]` dice "ya existe" para siempre; `list_available_capsides` solo mira `.exists()` → `_pdb_centroid` = (0,0,0), `_max_radius` = 0, `box_half` = 0 | CONFIRMADO con un servidor HTTP local en 404 (también queda un `.gz` huérfano); `curl -f` no crea nada | MEDIA | — |

**sustratinaitor (1)**

| § | Hallazgo | Veredicto y evidencia | Sev. inf. → real | Cruce |
|---|---|---|---|---|
| 7.2 (+7.3, 7.4) | La etapa 4 no puede ejecutarse: `gensystem.leap:20` escribe `3J7L-GYE_cg.{prmtop,ncrst}` y `run_MD.sh:5-6,9` pide `3J7L-GYE_cg-WAT.prmtop` **y** `3J7L-GYE_cg-WAT.ncrst` (el informe solo vio el prmtop); faltan en la carpeta los 4 `.in`, el bundle SIRAH (excluido a propósito según README), `GYE.mol2/frcmod` y `3J7L-GYE.pdb`; no hay `set -e` ni `$?` ni etapa de producción | CONFIRMADO. "Termina con código 0" es **dudoso/incorrecto**: bash devuelve el estado del último `pmemd.cuda`, que sale ≠0 al no encontrar el prmtop (reproducido con stub). Etapa declarada "no ejecutada" en ESTADO/README | ALTA → MEDIA | CG-A §4.3, CG-B §8.3 y hallazgo 7 |

**PackMan — inputs AMBER/SIRAH (4)**

| § | Hallazgo | Veredicto y evidencia | Sev. inf. → real | Cruce |
|---|---|---|---|---|
| 8.1 | Falta `&ewald chngmask=0` en 10 de 13 inputs (`em1`, `em2`, `heat1..6`, `density_eq`, `final_eq`); todos los de referencia (`tutorial/5,8`) lo llevan | CONFIRMADO el hecho (`grep`: solo eq1/eq2/prod lo tienen). **DUDOSO el mecanismo**: SIRAH lo comenta como "Only required to avoid SANDER error" (`tutorial/7/heat_Prot-Lip.in:28`); no hay soporte para "electrostática incorrecta en pmemd.cuda". Lo seguro: con el motor `sander` que `run_MD.sh:85-87` ofrece, `em1` aborta. **Corrige al sellado**, que daba em1/em2 por conformes (`SELL:52-53`) | ALTA → MEDIA | MD-14, MD §3.2 pt 8 ("con pmemd.cuda no importa") |
| 8.2 | `configurar_simulacion.sh:353` `restraintmask=':*&!@H='` con `restraint_wt=2.4`: en SIRAH no hay ningún nombre de átomo que empiece por H | CONFIRMADO: 92 nombres de átomo únicos en los 15 `.lib` del bundle, inicial B/C/G/K/L/M/N/O/P/W/Z, **ninguno H** → la máscara es todo el sistema, WT4 e iones incluidos, atado a `_density.ncrst` con `ntp=1`. Contradice la frase de `ESTADO §4b CIENCIA-3` "el generador ya genera los .in correctos" | ALTA → MEDIA (eq2 y prod vienen detrás sin esa máscara) | MD-09 |
| 8.3 | El generador escribe `em1/em2/eq1/eq2/prod` (`:300,319,334,365,396`) pero no `heat1..6`, `density_eq` ni `final_eq`, que `run_MD.sh:128` sigue ejecutando con `temp0=300` cableado; elegir 310 K produce una discontinuidad térmica | CONFIRMADO con **agravante**: el `eq1` generado lleva `ntx=1, irest=0` **y `tempi = 0.0`** (`:337,345`): tras calentar, eq1 arranca con velocidades a 0 K para cualquier temperatura | ALTA → MEDIA | MD-10 (incluye el `tempi=0.0`) |
| 8.7 | `validate_positive` acepta `310.5` y la interpolación `temp0 = $TEMP.0` (`:345,376,407`) produce `310.5.0`, namelist inválido | CONFIRMADO reproduciendo el script (`TEMP='310.5' → temp0 = 310.5.0`; `'310.' → 310..0`). Error inmediato de pmemd, entrada poco habitual | MEDIA (caso borde) | — |

**PackMan — orquestación y análisis (8)**

| § | Hallazgo | Veredicto y evidencia | Sev. inf. → real | Cruce |
|---|---|---|---|---|
| 9.2 | `2Empaquetador_Manual.py:14` `radio_interno = 90` cableado; `run_maestro.sh:35` calcula el radio y la 38 ejecuta el Manual, que lo ignora; `README.txt:103-104` promete lo contrario | CONFIRMADO; hoy indistinguible (el fichero dice 90). Con otra cápside la esfera sería incorrecta, pero la cápside `fixed` + `tolerance 2.0` impide colocar enzimas *dentro de la pared*: esfera mal dimensionada, no resultados falsos | ALTA → MEDIA latente | MD-17, MD S-8 |
| 9.3 | `setup_1_1o.sh:31,34` y `setup_universal_md.sh:41,44` hacen `sed … *_template.* > destino` sobre plantillas que **no existen** en el repo → `gensystem.leap` y `run_MD.sh` de 0 bytes, `chmod +x`, "✓ Configurado"; la salvaguarda `grep -q DIRNAME` pasa precisamente porque el fichero está vacío | CONFIRMADO (`find -iname '*template*'` → solo `templates/` de Flask; sandbox reproduce los 0 bytes). Scripts de una generación anterior (`gensystem.leap` real usa `AUTO_DETECT_*`), pero `README.md:24` los lista como vigentes | ALTA → MEDIA | MD-16, CG-A §2.1 |
| 9.4 | `run_maestro.sh:41` `ls capside_${N}enzimas_*.pdb | head -1` ordena lexicográficamente; la línea 28 copia `empaquetador/`, que trae versionado `capside_1enzimas_20260324_212620.pdb` → para N=1 se propaga el PDB de marzo a cgconv → tleap → MD. `2Empaquetador_*.py:34-38` tampoco recentra si `*_recentrada.pdb` existe (y están versionados) | CONFIRMADO en sandbox (`ls | head -1` → marzo; `ls -t` → hoy). **Solo para N=1**; latente mientras la MD no corra | ALTA → ALTA condicionada / MEDIA | — |
| 9.5 | `run_maestro.sh:74` invoca `ejecutar_analisis_cpptraj.sh`, que no existe en ningún sitio; además `generar_analisis_individual.py` (que crea los `.cpptraj`) no lo invoca nadie y es interactivo (`input()`); el maestro imprime "⚠️ Análisis falló, pero continuando" y termina con "🎉 completado" | CONFIRMADO (`grep -rn` → única aparición) | ALTA → MEDIA | MD-16, MD §5, CG-A §2.1 |
| 9.7 | El glob `[0-9]*_[0-9]*` (`run_maestro.sh:11`) casa `1_1o` (nombre que crea `setup_1_1o.sh:6`) → `N_ENZIMAS="1o"` → `int()` lanza, `ls` vacío, `cp ""` falla | CONFIRMADO en sandbox; latente (no hay `1_1o` versionado) | MEDIA | MD-16 |
| 10.2 (+10.3) | El monitor paralelo (`ejecutar_todo_paralelo_progreso.sh`) reporta "Exitosos: 0" aunque todo vaya bien, por dos causas: `local status=…` en el cuerpo principal (`:265,278`) → "`local: can only be used in a function`", `$status` vacío; y `wait $cpptraj_pid` desde un subshell nieto (`:59`) → `rc=127` → escribe `ERROR`/`-1` siempre | CONFIRMADO ambas (reproducidas con scripts mínimos). Los `.dat` de cpptraj quedan intactos | ALTA → MEDIA | — |
| 10.4 | `plot_ryg.py:12,29`, `plot_rmsd.py:18-19`, `plot_sasa.py:40` cablean 0.1 ns/fotograma (`ntwx=5000` de referencia) y `xlim(0, 1000)`; con `prod_md_WT4.in` (`dt=0.020`, `ntwx=50`) son 0.001 ns/fotograma: eje temporal 100× mal; `plot_sasa.py:40` normaliza al último fotograma = 1000 ns sea cual sea la trayectoria | CONFIRMADO. Vecino del stub `nstlim=500` ya sellado, pero el acoplamiento `dt×ntwx` → gráfica es un defecto propio | MEDIA | SELL:50 (stub) |
| 11.1 | `fix_pdb_serial.py:36` `f"{atom_serial:5d}"` desborda en el átomo 100 000 y desplaza una columna todo el registro; `capside.pdb` tiene 216 780 átomos | CONFIRMADO sobre una línea real: serial 100 000 → 77 caracteres, x `'  197.21'`, y `'6 198.95'`. Mismo defecto que §2.1 en otro fichero. **Latente**: nadie lo invoca (§11.3); CG-B lo convierte en bloqueo real de la ruta `convert_to_cg.sh` | ALTA → ALTA si se ejecuta / MEDIA latente | CG-B hallazgo 4 y §5.3 |

### 3.3 Cosmético, robustez o latente sin disparador realista (35)

| § | Hallazgo | Veredicto y nota | Sev. inf. → real | Cruce |
|---|---|---|---|---|
| 1.6 | `1run_hole.sh:55` toma `$NF` (= `angstroms.`) → `MIN_RAD` vacío, el `echo` nunca sale | CONFIRMADO (`MIN_RAD=[]`); solo se pierde un mensaje, el mínimo lo calcula `3analizar_hole.py` | MEDIA → BAJA | PORO-12 |
| 1.11 | `2cargarsuperficies.sh:59` heredoc fuera del bucle → `cat > "/foto_poro.pml"` sin mutantes | CONFIRMADO con matiz: `outdir` solo queda vacío si **todas** las iteraciones hacen `continue`; `5imagenescargasporo.sh:28` copia el `.pml` de todos modos | MEDIA → BAJA | — |
| 1.15 | `center_structures.py` reescribe `receptor.pdb` in place sin tocar `pore_center/vector.txt` y no centra `WT.pdb` | CONFIRMADO el código; **huérfano** (ningún invocador) y hoy todo está en el mismo marco (`pore_center.txt` se reproduce desde las coordenadas actuales) | MEDIA → BAJA | PORO-02 (parcial) |
| 1.16 | `3analizar_hole.py:33-38` llama "anchura" a `max−min` de todos los puntos < 2 Å y "continua" a una zona que no comprueba | CONFIRMADO; los 12 puntos < 2 Å son contiguos hoy (anchura 1.10 Å correcta por casualidad) | MEDIA → BAJA | PORO-11 (parcial) |
| 1.17 | `generate_ligand_from_smiles.py:94-109`: `MMFFOptimizeMolecule` devuelve −1 sin excepción; el fallback UFF está en el `except` y es inalcanzable | CONFIRMADO por lectura (sin RDKit aquí); la geometría ETKDG sigue siendo razonable | MEDIA → BAJA | — |
| 1.19 | pdb2pqr a pH 4.5 para APBS (`2cargarsuperficies.sh:19`) vs obabel a 7.4 para docking (`5docking.sh:34`) y ligando a 7.4 | CONFIRMADO; es una decisión científica sin documentar (del tipo CIENCIA-x), no un bug | MEDIA → BAJA | — |
| 1.20 (a-h) | `sorted()` lexicográfico sobre `resi` str (`mut_132GLY_9ALA`); umbral 1.4 Å en gráfica vs 2.0 en métrica; filtros no-op de `2out_tsv.py:16` (cabecera real `cenxyz.cvec` en minúsculas; `except` descartó 1 812 líneas sin contarlas); `gmacro`/`quit` rechazados por HOLE (`***Unrecognized line read`); `chmod +x` dentro del `if [ -x ]`; `-o algo.sdf` → `unlink()` borra la salida (`with_suffix('.sdf')` es identidad); `3copiar_scripts.sh` sin shebang/`set -e`; `os.system` sin leer el código de retorno | CONFIRMADAS las 8 | BAJA | 1.20b PORO-11; 1.20c PORO-10; 1.20d PORO-13 |
| 2.9 | `experiment_manager.py:47` `n_replicas = 7` cableado: crea 7 directorios y escribe `n_replicas: 7` en metadata aunque se pidan 1 o 10; `consolidate_results`/`get_replica_dir` del gestor son código muerto en el flujo vivo; `_generate_report` numera solo las exitosas | CONFIRMADO (corrida de 1 réplica → metadata dice 7, 6 directorios vacíos) | MEDIA → BAJA | PK-A P-16, PK-B PK-08 |
| 3.5 | `fast_vdw_volume.py:26` solo `ATOM`; los otros tres scripts `ATOM`+`HETATM` → EGFP pierde los 22 átomos del cromóforo CRO (1926 vs 1948) | CONFIRMADO; Rg 16.98 vs 16.89 Å; las otras tres enzimas no tienen HETATM | MEDIA → BAJA | — |
| 3.6 | `common.py:33-37` cuenta IDs de cadena únicos (3) y `library.py:83` deriva "T=3" de esa cuenta | CONFIRMADO: las 4 cápsides reutilizan A/B/C para 180 subunidades (BMV 180 TER/180 segid; CCMV/MS2/QB 3 TER/1 segid); el "T=3" es correcto por coincidencia. Es la causa real del colapso de §2.2 | BAJA | — |
| 4.3 | `_constriction_point` devuelve `None` si ninguna esfera tiene r > 0.5 y `_pore_residues` hace `p − None` → `TypeError` 500 | CONFIRMADO (reproducido), pero `_hole_on` ya lanza `RuntimeError` antes si el perfil tiene < 30 puntos: hace falta inconsistencia entre `hole_out.txt` y `hole_spheres.pdb` | MEDIA → BAJA | — |
| 4.6 | `paths.py:25` `POROMANIA_DIR = PROJECT_ROOT.parent / "Poromania.v.1.2."` cableado con el punto final; `pore_channels()`/`hole_structures()` devuelven `[]` sin error si falta | CONFIRMADO el acoplamiento; **FALSA la mitad del argumento**: renombrar `nanocapsule-mvp/` (VLP-05) **no** cambia `PROJECT_ROOT.parent`, y `ESTADO.md:178` lo dice literalmente; versionar en el nombre de carpeta está descartado por VLP-07. Disparador real: Docker (`Dockerfile:11-12` deja Poromania fuera) | MEDIA → BAJA | — |
| 5.1 | `app.py:371-373` valida con `str(target).startswith(str(OUTPUT_DIR))`: un hermano `Output_leak/` pasa | CONFIRMADO (test client: 200 `SECRET LEAKED`); servidor local de un usuario, hermano inexistente; arreglo trivial (`is_relative_to`) | MEDIA → BAJA | — |
| 5.2 | `/api/files/cleanup` toma `days_old` sin validar: `0` o negativo borra todos los PDB generados; `n_enzymes`/`radius` sin rango | CONFIRMADO (test client borró el fichero de prueba). Solo salidas gitignored; la única llamada está en la UI `index.html` deprecated con 7 fijo | MEDIA → BAJA | — |
| 5.5 | `renderPDB` (`studio-core.js:34`) usa `mdBoxData` sin comparar `mdBoxCapsid` con la cápside actual → pinta el box de BMV sobre MS2 | CONFIRMADO en código (no ejecutado en navegador); se corrige al remarcar el checkbox | BAJA | — |
| 5.6 | `capsid.py:189-190` y `cargo.py:81-82` escriben `*_centered.pdb` junto al input, dentro de `Input/` versionado (8 ficheros ya versionados) | CONFIRMADO | BAJA | PK-A P-17 (añade: 3 de 4 enzimas ya sobrescritas) |
| 5.7 | `common.py:20-21` instancia `StructureFetcher` al importar y su constructor hace `mkdir(exist_ok=True)` sin `parents` | CONFIRMADO (reproducido con tmp) | BAJA | — |
| 6.2 | `config.py:104` fallback `"port": 5001` (y sin `debug`) vs `EXPOSE 5000` y healthchecks a 5000 | CONFIRMADO; requiere un bind mount `./config` vacío. Distinto de lo de ESTADO (`ngl-viewer.html`) | MEDIA → BAJA | — |
| 6.3 | `ci.yml:37` `pip install ruff` sin pin, ausente del lock, bajo un comentario que promete reproducibilidad | CONFIRMADO | MEDIA → BAJA/MEDIA | — |
| 6.6 | `vlpstudio.kdl:32` define `test(){…}` y lo exporta: cualquier bash hijo hereda un `test` que siempre devuelve 0 | CONFIRMADO el mecanismo (reproducido); **ningún script del repo usa `test`** (todos usan `[`) | MEDIA → BAJA | — |
| 6.9 | `setup.py:33` `version='1.0.0'` vs `VERSION`/`CITATION.cff`/release `0.1.0`; `python_requires='>=3.7'` vs lock/Docker/CI en 3.12 | CONFIRMADO (release `v0.1.0` confirmado vía API). Matiz: Flask 3.1 exige ≥3.9, no ≥3.10. Visible para JOSS (versión citable ≠ paquete) | BAJA | — |
| 6.10 | El job `engines` del CI compila Python y `sustratinaitor` tiene 0 `.py`; no hay `bash -n` | CONFIRMADO | BAJA | — |
| 6.11 | Pane "Plan" de `salud.sh:47`: omite VLP-10/11, no transforma VLP-04a/b/c, con `LC_CTYPE=POSIX` no transforma nada, el `|| echo` cuelga del `sed` | CONFIRMADAS las 4 sub-afirmaciones (reproducidas) | BAJA | — |
| 6.12 | `/home/luciernaga/Escritorio/Pac-Zyme/uno solo` ×5 en `vlpstudio.kdl` | CONFIRMADO; herramienta personal, y el propio kdl lo declara | BAJA | `ESTADO:178` manda actualizarlo |
| 6.13 | Claves muertas de `default.yaml`: `engines.pymol.*`, `io.*` (6), `logging.*`, `experiments.{output_base_dir,keep_temp_files,auto_generate_reports}`, `web.cors_enabled`, `library.*` | CONFIRMADO por grep de todas las lecturas de config. Las de `engines.packmol.*` están en §2.7 | BAJA | `ESTADO:188` (solo `logging`) |
| 6.14 (a-c) | `library.js:33` deja `tb-enz` en "Cargando…" ante un error; `studio.css:26` no cubre `input[type=text]`; `.status.load` no está definida | CONFIRMADAS; "cargando visualmente idéntico a neutro" exagerado: el `.spinner` sí se muestra | BAJA | — |
| 8.5 | `heat1..6` y `density_eq` definen `ntwx` pero `run_MD.sh:177-250` no pasa `-x`: las 7 etapas escriben `mdcrd` y se sobrescriben | CONFIRMADO; se pierden trayectorias de diagnóstico de etapas destinadas a retirarse (CIENCIA-3) | MEDIA → BAJA | — |
| 8.9 (a-c) | `taup=2.0` con `barostat=2` (MC) es inerte; `set default PBradii mbondi3` sin `igb` es inerte; `ioutfm=1`/`ntxo=2` omitidos en heat/density/final | CONFIRMADAS las tres omisiones, las tres **sin efecto**: `ioutfm=1`/`ntxo=2` son default desde Amber 16 y el restart se autodetecta | BAJA → COSMÉTICA | MD §3.2 pt 7, MD-20 |
| 9.8 | Siete `cd` sin verificar en `run_maestro.sh`; un `cd analisis` fallido descompensaría la pila | CONFIRMADO el patrón; `analisis/` siempre existe porque la línea 28 lo copia: sin disparador | MEDIA → BAJA | — |
| 9.9 | `prod-q_gpu.bsub` apunta a `/tmpu/scunam/…`, a `capside-3_cg-WAT.*` (convención `_cg` que ningún script produce; `setup_universal.sh:16` usa `-cg-WAT`) y arranca desde `_eq2` saltando `final_eq`; sin shebang ni `-W` | CONFIRMADO; plantilla de clúster que el usuario debe editar; falla ruidosamente | MEDIA → BAJA | MD-18 |
| 9.10 (a-b) | `radio_colision` sin definir si no hay colisión en 5..199 → `NameError`; `run_MD.sh:134-139` sigue con inputs ausentes y la etapa siguiente falla en AMBER con un diagnóstico confuso | CONFIRMADAS | BAJA | — |
| 10.5 (+10.6) | `compara_enzimas_misma_capside.py:190` define `zone_colors` dentro de `if backbone_data_found` y la 230 lo usa bajo otra guarda → `NameError` posible; `:354` `tick_labels=` exige matplotlib ≥ 3.9 (sin pin); ambos ocultos por `> /dev/null 2>&1` en `ejecutar_todos_graficos.sh:213,219` | CONFIRMADO (el `NameError` exige que falte `*_rmsf_backbone.dat` y exista `*_rmsf_all.dat`, que salen del mismo `.cpptraj`: improbable) | MEDIA → BAJA | — |
| 11.2 | `fix_pdb_serial.py:36` deja el elemento en las columnas 73-74 (campo segID), no 77-78 | CONFIRMADO midiendo columnas; las herramientas infieren el elemento por nombre | MEDIA → BAJA | — |
| 11.3 | Nadie invoca `fix_pdb_serial.py` (solo `README.md:25` y `diagrama_archivos_dm.md:34`); tres convenciones de serial conviven: módulo 100 000 (`3J7L_cg.pdb`), saturado en 99999 (`capside.pdb`), hexadecimal (`186A0`, salidas de Packmol) | CONFIRMADO; tleap, cpptraj, cgconv y Packmol ignoran la columna de serial. **Pero** CG-B demostró que `pdb2pqr` **aborta** con los hexadecimales, lo que sí bloquea `convert_to_cg.sh` (hallazgo de CG-B, no de este informe) | MEDIA → BAJA (como está formulado) | CG-B hallazgos 3-4, CG-A §2.1, PK-A P-22 |
| 11.4 | `fix_pdb_serial.py` renumera `ATOM`/`HETATM` y copia los `CONECT` sin tocar | CONFIRMADO; ningún PDB del repo tiene `CONECT` | BAJA | — |

---

## 4. Veredicto hallazgo a hallazgo (los 97)

| § | Veredicto | Sev. informe | Sev. real | Destino |
|---|---|---|---|---|
| 1.1 | CONFIRMADO (causa `refresh_wizard` FALSA) | ALTA | ALTA | A1 |
| 1.2 | CONFIRMADO | ALTA | ALTA | A2 |
| 1.3 | CONFIRMADO (latente) | ALTA | ALTA latente | B |
| 1.4 | CONFIRMADO | ALTA | MEDIA | B |
| 1.5 | CONFIRMADO (+ agravante CCMV/BMV) | ALTA | MEDIA | B |
| 1.6 | CONFIRMADO | MEDIA | BAJA | C |
| 1.7 | CONFIRMADO | MEDIA | MEDIA latente | B |
| 1.8 | CONFIRMADO | MEDIA | MEDIA | B |
| 1.9 | CONFIRMADO | MEDIA | MEDIA | B |
| 1.10 | CONFIRMADO | MEDIA | MEDIA | B |
| 1.11 | CONFIRMADO (matiz) | MEDIA | BAJA | C |
| 1.12 | CONFIRMADO | MEDIA | MEDIA | B |
| 1.13 | CONFIRMADO | MEDIA | MEDIA | B |
| 1.14 | CONFIRMADO (latente) | MEDIA | MEDIA latente | B |
| 1.15 | CONFIRMADO (huérfano) | MEDIA | BAJA | C |
| 1.16 | CONFIRMADO | MEDIA | BAJA | C |
| 1.17 | CONFIRMADO (lectura) | MEDIA | BAJA | C |
| 1.18 | CONFIRMADO | MEDIA | MEDIA | B |
| 1.19 | CONFIRMADO (decisión científica) | MEDIA | BAJA | C |
| 1.20 a-h | CONFIRMADAS (8/8) | BAJA | BAJA | C |
| 2.1 | CONFIRMADO | ALTA | MEDIA | B (absorbe 2.10) |
| 2.2 | CONFIRMADO (atribución corregida) | ALTA | MEDIA | B |
| 2.3 | CONFIRMADO | ALTA | MEDIA | B |
| 2.4 | CONFIRMADO (condicionado) | ALTA | ALTA cond. | A4 |
| 2.5 | CONFIRMADO | MEDIA | MEDIA | B |
| 2.6 | CONFIRMADO | MEDIA | MEDIA | B |
| 2.7 | CONFIRMADO (seed = 2.3; margin latente) | MEDIA | MEDIA | B |
| 2.8 | CONFIRMADO | MEDIA | MEDIA | B |
| 2.9 | CONFIRMADO | MEDIA | BAJA | C |
| 2.10 | CONFIRMADO | BAJA | BAJA | fusionado en 2.1 |
| 3.1 | CONFIRMADO | ALTA | MEDIA | B (absorbe 3.2) |
| 3.2 | CONFIRMADO (alcance exagerado) | MEDIA | BAJA | fusionado en 3.1 |
| 3.3 | CONFIRMADO | MEDIA | MEDIA | B |
| 3.4 | CONFIRMADO (al Å³) | MEDIA | MEDIA | B |
| 3.5 | CONFIRMADO | MEDIA | BAJA | C |
| 3.6 | CONFIRMADO | BAJA | BAJA | C |
| 3.7 | CONFIRMADO | BAJA | BAJA | fusionado en 4.1 |
| 4.1 | CONFIRMADO (matiz: estado sigue marcado) | ALTA | MEDIA | B (absorbe 3.7) |
| 4.2 | CONFIRMADO hecho / DUDOSO efecto | ALTA | ALTA | A3 |
| 4.3 | CONFIRMADO (camino difícil) | MEDIA | BAJA | C |
| 4.4 | CONFIRMADO | MEDIA | MEDIA | B |
| 4.5 | CONFIRMADO (3+1) | MEDIA | MEDIA | B |
| 4.6 | CONFIRMADO hecho / FALSO el disparador VLP-05 | MEDIA | BAJA | C |
| 4.7 | "Verificado correcto": CONFIRMADO para el pentámero (0.00°); DUDOSO para los trímeros (10-11° vs eje Kabsch; tensor no degenerado) | — | — | no es hallazgo; PORO-07 lo convierte en uno |
| 5.1 | CONFIRMADO | MEDIA | BAJA | C |
| 5.2 | CONFIRMADO | MEDIA | BAJA | C |
| 5.3 | CONFIRMADO | MEDIA | MEDIA | B |
| 5.4 | CONFIRMADO núcleo / DUDOSOS 2 detalles | MEDIA | MEDIA | B |
| 5.5 | CONFIRMADO (código) | BAJA | BAJA | C |
| 5.6 | CONFIRMADO | BAJA | BAJA | C |
| 5.7 | CONFIRMADO | BAJA | BAJA | C |
| 6.1 | CONFIRMADO (+ `io` vs stdlib) | MEDIA | ALTA (JOSS) | A7 |
| 6.2 | CONFIRMADO (latente) | MEDIA | BAJA | C |
| 6.3 | CONFIRMADO | MEDIA | BAJA/MEDIA | C |
| 6.4 | CONFIRMADO | MEDIA | MEDIA | B |
| 6.5 | CONFIRMADO | MEDIA | MEDIA | B |
| 6.6 | CONFIRMADO (sin víctima) | MEDIA | BAJA | C |
| 6.7 | CONFIRMADO | MEDIA | MEDIA | B |
| 6.8 | CONFIRMADO | MEDIA | ALTA (JOSS) | A8 |
| 6.9 | CONFIRMADO | BAJA | BAJA | C |
| 6.10 | CONFIRMADO | BAJA | BAJA | C |
| 6.11 | CONFIRMADO (4/4) | BAJA | BAJA | C |
| 6.12 | CONFIRMADO | BAJA | BAJA | C |
| 6.13 | CONFIRMADO | BAJA | BAJA | C |
| 6.14 a-c | CONFIRMADAS (3/3) | BAJA | BAJA | C |
| 7.1 | **FALSO POSITIVO** | ALTA | — | eliminado |
| 7.2 | CONFIRMADO ("exit 0" dudoso) | ALTA | MEDIA | B (absorbe 7.3, 7.4) |
| 7.3 | CONFIRMADO (SIRAH excluido a propósito) | MEDIA | BAJA | fusionado en 7.2 |
| 7.4 | CONFIRMADO | MEDIA | BAJA | fusionado en 7.2 |
| 8.1 | CONFIRMADO hecho / DUDOSO mecanismo | ALTA | MEDIA | B |
| 8.2 | CONFIRMADO | ALTA | MEDIA | B |
| 8.3 | CONFIRMADO (+ `tempi=0.0`) | ALTA | MEDIA | B |
| 8.4 | hecho sí / **FALSO POSITIVO** en la conclusión | MEDIA-ALTA | — | eliminado |
| 8.5 | CONFIRMADO | MEDIA | BAJA | C |
| 8.6 | CONFIRMADO hecho, efecto exagerado | MEDIA | — | eliminado: reformulación CIENCIA-3 |
| 8.7 | CONFIRMADO (reproducido) | MEDIA | MEDIA | B |
| 8.8 | CONFIRMADO hecho | MEDIA | — | eliminado: stub ya sellado |
| 8.9 a-c | CONFIRMADAS, inertes | BAJA | COSMÉTICA | C |
| 9.1 | CONFIRMADO (consecuencia exagerada; "133 s" falso) | ALTA | ALTA cond. | A5 |
| 9.2 | CONFIRMADO | ALTA | MEDIA latente | B |
| 9.3 | CONFIRMADO | ALTA | MEDIA | B |
| 9.4 | CONFIRMADO (solo N=1) | ALTA | ALTA cond. / MEDIA | B |
| 9.5 | CONFIRMADO | ALTA | MEDIA | B |
| 9.6 | CONFIRMADO hecho | MEDIA | — | eliminado: CIENCIA-1 |
| 9.7 | CONFIRMADO (latente) | MEDIA | MEDIA | B |
| 9.8 | CONFIRMADO (sin disparador) | MEDIA | BAJA | C |
| 9.9 | CONFIRMADO | MEDIA | BAJA | C |
| 9.10 a-b | CONFIRMADAS | BAJA | BAJA | C |
| 10.1 | CONFIRMADO mecanismo / DUDOSAS cifras | ALTA | ALTA | A6 |
| 10.2 | CONFIRMADO | ALTA | MEDIA | B (absorbe 10.3) |
| 10.3 | CONFIRMADO (reproducido) | ALTA | MEDIA | fusionado en 10.2 |
| 10.4 | CONFIRMADO | MEDIA | MEDIA | B |
| 10.5 | CONFIRMADO | MEDIA | BAJA | C (absorbe 10.6) |
| 10.6 | CONFIRMADO (sin ejecutar) | BAJA | BAJA | fusionado en 10.5 |
| 11.1 | CONFIRMADO (reproducido) | ALTA | ALTA si se usa / MEDIA | B |
| 11.2 | CONFIRMADO | MEDIA | BAJA | C |
| 11.3 | CONFIRMADO | MEDIA | BAJA | C |
| 11.4 | CONFIRMADO | BAJA | BAJA | C |

Las "sospechas que NO se sostienen" de §12 del informe se reverificaron: **todas correctas**
(profundidad de `../..`, columna `Rg[Max]`, signo de `NaW` con cargas recalculadas cápside
3000/3000 → 0 y enzima −1, rampa térmica continua, `ntb/ntp`, `skinnb`, 13 `.in`), **salvo la
"nota de discrepancia" 0/199/1**, que queda refutada (ver §7.1). El `&end` de §13 está bien
dejado fuera: gfortran, Intel y NVHPC lo aceptan y la propia referencia SIRAH pone `&end` y
`/` juntos.

---

## 5. Cruce con las otras seis auditorías

**35 de los 85 supervivientes ya estaban cubiertos** (idénticos, en lo esencial o en parte) en las ramas
de auditoría; en varios casos aquellas los cuantifican mejor o los agravan:

| Motor | Supervivientes ya cubiertos | Dónde |
|---|---|---|
| Poromania | 1.1, 1.2, 1.3, 1.5, 1.6, 1.14, 1.16, 1.20 (b, d), 4.1 | PORO-01/02/03/09/10/11/12/13/15 |
| Studio packing | 2.3, 2.4, 2.7, 2.8, 2.9, 3.1, 3.3, 5.6, 6.4, 9.1 | PK-A P-01/05/11/12/16/17/18/19, G-01; PK-B PK-01/02/03/04/07/08/09/10 |
| Studio PAC-PORE / DM | 4.2, 4.4, 5.4 | PORO-09/16; MD S-6 |
| sustratinaitor | 7.2 | CG-A §4.3, CG-B §8.3 |
| PackMan MD | 8.1, 8.2, 8.3, 8.9 | MD-09/10/14/20 |
| PackMan orquestación | 9.2, 9.3, 9.5, 9.7, 9.9, 10.1 (parcial), 11.1, 11.3 | MD-16/17/18, S-4; CG-A §2.1; CG-B 3-4 |

**Tres puntos donde este informe corrige a los demás**: §8.1 desmiente al sellado (em1/em2 no
tienen `chngmask=0`); §2.3 desmiente el "positivo" del sellado sobre semillas; §1.1 y §4.2
fijan el mecanismo exacto (selección múltiple por `chain`) que PORO dejaba como "[REQUIERE
CORRER]" y descartan la hipótesis del `refresh_wizard`.

**Los 50 restantes son aportación neta** del informe: los scripts shell de Poromania (1.4,
1.7-1.13, 1.18), el preview y la biblioteca del Studio (2.1, 2.2, 2.5, 2.6, 3.4-3.6), la
API/CI/tablero (4.3, 4.5, 4.6, 5.1-5.3, 5.5, 5.7, 6.1-6.3, 6.5-6.14), los inputs AMBER menores
(8.5, 8.7), el pipeline de análisis de PackMan (10.2, 10.4, 10.5) y `fix_pdb_serial.py`
(11.2, 11.4). Lo más valioso de ese bloque es 6.1 y 6.8 (JOSS), 10.2 y 10.4 (el análisis MD
reportaría 100 % de errores y ejes 100× mal) y 6.5/6.7 (la red de salud y la de datos mienten).

**Aviso sin ampliar el informe**: las otras auditorías contienen hallazgos de severidad igual
o mayor que **no** están en los 99 (pérdida de los 180 `TER` en toda salida de Packmol,
hidrógenos ausentes en la ruta `run_maestro.sh`, stubs de 10 ps en eq1/eq2/prod, `ntr=0` en las
etapas SIRAH, cribado del Studio que falla sobre el pentámero, `pdb2pqr` abortando con
seriales hexadecimales). Este documento no los incorpora; están en sus ramas.

---

## 6. Lo que no se pudo decidir aquí

Requiere los motores instalados; ninguna conclusión de §3.1 depende de ello salvo donde se indica:

- **§4.2** (A3): ejecutar PyMOL sobre `poro5fold.pdb` con el `.pml` que genera `pore.py` y
  comparar `resn` antes/después. El fuente del wizard predice el no-op; falta verlo.
- **§9.1** (A5): código de salida de Packmol (versión 20.14.3 del log) al terminar con
  `ENDED WITHOUT PERFECT PACKING`, y si deja `<output>` además de `<output>_FORCED`. Decide si
  el bucle de PackMan y el fallback del Studio aceptan estructuras no convergidas (PK-A R-1).
- **§10.1** (A6): las cifras hay que medirlas sobre el `*-cg-WAT.pdb` que escribe tleap, no
  sobre `capside.pdb`.
- **§8.1**: si `chngmask=1` altera algo en pmemd.cuda (todo indica que no).
- **§4.7** trímeros: efecto de los ~10° de desviación del eje sobre el radio mínimo de HOLE.
- **§1.17**, **§10.6**: comportamiento de RDKit/matplotlib (código inequívoco, no ejecutado).

---

## 7. Cuenta final

De los **99** hallazgos anunciados (**97** reales, más §4.7 que era un "verificado correcto"):

- **2 falsos positivos** (§7.1, §8.4), uno de ellos el segundo del ranking del informe.
- **3 eliminados por estar ya documentados** (§8.6, §8.8, §9.6).
- **7 fusionados** como duplicados de otro hallazgo del mismo informe.
- **85 sobreviven**: **8 bloquean JOSS**, **42 son MEDIA**, **35 son cosméticos**.
- De los 85, **35 ya estaban en las otras auditorías**; **50 son nuevos**.

El informe original es fiable en los hechos (92 de 97 reproducidos) y poco fiable en la
severidad (18 de 26 "ALTA" bajan de nivel) y en una medición clave (§7.1). Los ocho que
bloquean el envío son, en orden: el mutante que es el WT (§1.1), el eje del poro de una
subunidad (§1.2), la mutagénesis del Studio sin verificación (§4.2), `fixed` sin `center`
con el centrado tragado (§2.4), el criterio de Packmol que no existe (§9.1), las máscaras de
cpptraj sin mapeo (§10.1), el paquete pip no importable (§6.1) y la declaración falsa sobre
SIRAH en `THIRD_PARTY.md` (§6.8).
