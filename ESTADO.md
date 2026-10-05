# Estado de VLP Studio (PAC-ZYME)

> Mapa auditable del proyecto. Describe lo que **existe y funciona hoy**, no lo que
> se planeó. Si algo aquí contradice al README, CLAUDE.md, DEVELOPMENT_PLAN.md o
> TECHNICAL_IMPROVEMENTS.md, **manda este documento**: esos son planes fósiles de
> una versión anterior del proyecto.
>
> Última revisión: 2026-10-05 (fusión en `main` de las auditorías del 2026-10-04 y de las dos
> reparaciones: packing y protocolo MD) · Repo: github.com/najera-maldonado/vlp-studio
> (público desde 2026-09-18)
>
> **Aviso de revisión.** El 2026-10-04 se auditaron los cuatro motores desde cero (9 informes,
> consolidados en `HOJA_DE_RUTA.md`; todos en `main` desde el 2026-10-05). Varias afirmaciones
> de este documento quedaron desmentidas y se corrigen abajo, marcadas **[AUDITORÍA
> 2026-10-04]**; lo que ya se reparó va marcado **[REPARADO 2026-10-05]**. La lista completa de
> correcciones, con evidencia, está en `CORRECCIONES_DOCUMENTACION.md`; el estado real tras las
> reparaciones, en `HOJA_DE_RUTA.md §0`. Las secciones §4–§6 conservan el diagnóstico del
> 2026-09-17 donde sigue vigente.

---

## 1. Qué es el proyecto

Una plataforma para diseñar **nanocápsulas VLP con enzimas terapéuticas**, organizada
como un **embudo de 4 filtros** que un sustrato debe superar:

| Puerta | Pregunta | Motor real | Estado |
|--------|----------|------------|--------|
| A través | ¿Entra el sustrato por el poro? | Poromania (HOLE + idock + PyMOL) / Studio (HOLE + Vina) | Motor cableado de punta a punta; **resultado en revisión** [AUDITORÍA 2026-10-04]: el único perfil commiteado (1,92 Å) es del WT sin mutar, medido con `cpoint` a 7,6 Å del eje y `cvect` 19° desviado (`INVALIDO.md` en la carpeta). El Studio tiene el eje correcto en C5 pero su cribado falla en el pentámero y el eje está mal condicionado en trímeros |
| Dentro | ¿Cabe la enzima en la cavidad? | Studio (Packmol + PyMOL) | Motor corre; **capacidad todavía en revisión**. [AUDITORÍA 2026-10-04] criterio de aceptación muerto + fallback ciego (con un doble de PACKMOL reportaba 100 enzimas, σ 0, con 0 colocadas), semillas aleatorias, sin tests. [REPARADO 2026-10-05] criterio real (línea correcta del log, conteo de copias, rechazo de `_FORCED`, enzimas dentro de la cápside), semilla fija `seed_base + i`, config leída, 39 tests con doble en CI. **Pendiente:** ninguna corrida con PACKMOL real desde la reparación (PK-1); `best` sigue siendo el titular (DC-6); radio ±1 Å (CIENCIA-1). Resto ilustrativo |
| Fuera | ¿Evita la respuesta inmune? | — (NetMHCIIpan/FEP no integrados) | **Ilustrativo** |
| Sobrevive | ¿Aguanta la dinámica molecular? | PackMan (SIRAH + AMBER) | **MD sin correr; nunca hubo corridas de 15 ni 35 ns.** [AUDITORÍA 2026-10-04] `eq1/eq2/prod` eran stubs de 10 ps con esos títulos (≈ 240 ps en total), 8 de 13 `.in` all-atom, y `run_maestro.sh` entrega a `cgconv.pl` un PDB sin H y sin `TER`. [REPARADO 2026-10-05, v1.3.0] protocolo de 5 etapas de `tutorial/5` (5 + 25 + 10 ns/trozo), semillas fijas, verificador estático en CI. **Pendiente:** la preparación del sistema sigue produciendo una topología inválida (MD-1…MD-5), así que el protocolo no puede correr de punta a punta |

El **Studio** (`nanocapsule-mvp`) es la fachada web única; los otros tres proyectos
son los motores científicos.

---

## 2. Los cuatro subproyectos

### `nanocapsule-mvp/` — el Studio (fachada web)
- App Flask. Arranca: `FLASK_DEBUG=0 python3 src/web/app.py` → http://localhost:5000
- Backend en capas (bien trazado): `app.py` (adaptador HTTP delgado) → `services/` (un módulo por puerta tras VLP-03; `packing_service.py` es la fachada) → `core/` (dominio) + `core/paths.py` (rutas centralizadas, incluye el puente a Poromania).
- Frontend: `src/web/templates/studio.html` (solo estructura tras VLP-04a/b) + `static/js/` (un módulo por pestaña), NGL + Chart.js por CDN. 5 pestañas.
- `/classic` sirve `index.html`: interfaz **legada redundante** (duplica el núcleo de packing). Candidata a retirar.

### `Poromania.v.1.2./` — análisis de poros (motor de la puerta "A través")
- Pipeline: detección de residuos del poro → mutagénesis PyMOL → HOLE2 → APBS → docking iDock → figuras.
- El Studio lo consume directamente (lee `modelos/` y `mutants/*/hole/`).
- Herramientas instaladas: `hole`, `pymol`, `vina`, `idock`, `obabel`, RDKit.
- [AUDITORÍA 2026-10-04] Centro del canal = media de CA de **una** subunidad; eje = cuerda de 4,4 Å; sin `rseed`; sin verificación de que la mutación se aplicó; `1run_hole.sh` perdió la validación de canal que tenía `1run_hole_old.sh`. El mutante commiteado es el WT. Ver README de Poromania, "Audit findings".

### `sustratinaitor/` — sustrato GYE alrededor de la cápside
- Construye glucosilceramida (GYE) y empaqueta 200 copias alrededor de la cápside 3J7L (= BMV) con Packmol.
- Ejecutado hasta el empaquetado; etapa 4 (MD) no corrida y **no ejecutable** (busca un `prmtop` que tleap no produce; faltan los `.in`). **Tiene un bug de resolución** (ver §4).
- [AUDITORÍA 2026-10-04] La conversión CG de la cápside (`1_capside/3J7L_cg.pdb`) **está bien** y es reproducible byte a byte: es la receta que PackMan debe copiar. La salida de Packmol pierde los 180 `TER` y tiene seriales hexadecimales. 40 de 200 GYE quedan en el lumen.

### `PackMan.v.1.2/` — dinámica molecular (motor de la puerta "Sobrevive")
- MD coarse-grained SIRAH de enzima-en-cápside: empaquetado → conversión CG → tleap → pmemd.cuda → cpptraj → gráficas.
- El subsistema `analisis/` (cpptraj) produce los `.dat` (frame, valor) que la pestaña "Análisis MD" del Studio sabe leer (con bugs propios: máscaras por `resSeq`, RMSF sin `rms` previo, LCPO sin parámetros CG).
- Solo el empaquetado tiene evidencia de ejecución (1 corrida, n = 1). **MD sin correr** (no hay trayectorias, `mdout`, `leap.log` ni `.dat`). Nunca existió una corrida de 15 ni 35 ns: eran títulos sobre stubs de 10 ps.
- [AUDITORÍA 2026-10-04] **No podía correr con lo commiteado:** `.in` stubs de 10 ps rotulados 15/35 ns; 8 all-atom; topología sin H ni `TER` por `run_maestro.sh`; `gensystem.leap` sin disulfuros ni sal; scripts de setup que invocan plantillas inexistentes. Las cifras de MD del Studio (`md.py`: RMSD 2,8 Å, SASA 41 893 Å², 17 666 K) son sintéticas.
- [REPARADO 2026-10-05, v1.3.0] Los `.in`: 5 etapas copiadas de `tutorial/5` (em1, em2, eq1 5 ns, eq2 25 ns, prod 10 ns/trozo), sin los 8 all-atom ni `configurar_simulacion.sh`; `run_MD.sh` reanudable con semillas fijas; `verificar_protocolo_md.py` en CI. **Sigue roto:** la preparación del sistema (sin H, sin `TER`, seriales hex, `gensystem.leap`, scripts de setup con plantillas inexistentes, `run_maestro.sh` llamando a un script de análisis que no existe) y los defectos del análisis cpptraj. Ver `PackMan.v.1.2/README.md`.

---

## 3. Estado real por puerta del Studio

- **BIBLIOTECA** — real. Tablas de cápsides/enzimas con datos calculados (`/api/library/detail`). Pendiente: radio interno solo cacheado para BMV; tabla de sustratos.
- **STUDIO 3D** — mitad real. Packing Packmol + preview reales como ejecución; **el número de capacidad todavía no es una medición validada**. [AUDITORÍA 2026-10-04] criterio de aceptación muerto, fallback ciego, `n_packed` no se contaba, semillas aleatorias, timeout 90 s y `collision_margin` hardcodeados, radio 90 Å por defecto rotulado "calculado". [REPARADO 2026-10-05] todo lo anterior salvo: `best` sigue siendo el titular (DC-6), `/api/capsid/radius` sigue devolviendo 90 Å rotulado "calculado" (aunque el runner ya se niega a empaquetar con ese valor), y no hay ninguna corrida con PACKMOL real posterior a la reparación (PK-1). "Sustrato alrededor" por SMILES (RDKit) y preparador de DM generan geometría/inputs pero **no ejecutan** (y `md_prepare` emite ff19SB + TIP3P all-atom para un motor SIRAH).
- **PAC-PORE** — cableado de punta a punta; **no validado** [AUDITORÍA 2026-10-04]. Aciertos: eje por tensor de segundo momento (0,00° en C5), `rseed 1`, `vdwradii.lib` compartido, `substrate_section` con golden. Defectos: `_pore_residues` deja 1 residuo sobre `poro5fold` (las 5 subunidades comparten `chain A`), eje mal condicionado en trímeros (≈ 6°), mutagénesis sin verificar, `except: continue` en cribado y docking, `_AXIS_MIN` guarda el 1,92 (pentámero) como 3-fold con el orden invertido, el badge "(ilustrativo)" se vació en `40f4b03` mientras `/api/pore/profile` sigue siendo una gaussiana. Los "2,47 / 1,68 Å" solo existen en prosa, sin artefacto.
- **DE-INMUNIZACIÓN** — ilustrativo. Diccionario estático (`_DEIMMUNO`). Marcado "(ilustrativo)" en la UI.
- **ANÁLISIS MD** — ilustrativo. Curvas sintéticas (`math.sin`) con anclajes numéricos ("RMSD final 2.8 Å", "heat1 → 17.666 K · el fallo real", `source: packmanreplicas1/1_2`) que **no corresponden a ninguna corrida del repo**. El motor real (PackMan) existe pero su MD no se ha corrido.

**Nota de arquitectura:** el Studio **reimplementó en Python** la lógica de poro/cribado/docking
que ya vive en Poromania (`pore_analyzer.py` + los `.sh`). Funciona, pero la misma ciencia
existe en dos sitios que pueden divergir. Cualquier corrección debe decidirse en un solo lado.

---

## 4. Bugs y deuda conocidos (verificado 2026-09-17; ampliado por la auditoría 2026-10-04)

> [AUDITORÍA 2026-10-04] Esta sección es el diagnóstico de septiembre. La lista completa y
> actual de defectos, con severidad, evidencia y tarea de reparación, es `HOJA_DE_RUTA.md`
> (§4 y §5). Los hallazgos que cambian este documento:
> - **Packing (CRÍTICO → reparado en software el 2026-10-05, `REPARACION_PACKING.md`):** regex
>   de aceptación muerta, fallback por líneas ciego, `n_packed` asumido, semillas no leídas de
>   la config, `timeout=90` y `collision_margin=2.0` hardcodeados, cápside sin `center` en el
>   `.inp`, primera pérdida de `TER` (180→3) por el centrado con PyMOL, cero tests del motor:
>   **todo eso está corregido** (líneas de código citadas en la auditoría ya no aplican).
>   **Sigue abierto:** fallback de 90 Å rotulado "calculado" en `/api/capsid/radius` (el
>   runner ya lo rechaza), pérdida de `TER` y seriales hex por PACKMOL (T1), `radio_interno.txt`
>   global atribuido a BMV, experimentos sin timestamp que se sobrescriben, `Input/Enzimas/`
>   mutado antes de la reparación (GCase sin respaldo), PK-1 (PACKMOL real).
> - **Poro (CRÍTICO):** mutante commiteado = WT; estructura usada ≠ cargada por el script;
>   `cpoint`/`cvect` fuera del canal; sin `rseed` en Poromania; filtro `radio > 0.5` oculta
>   oclusión; `1run_hole.sh:55` nunca imprime el radio; idock sin semilla.
> - **MD (CRÍTICO; protocolo reparado el 2026-10-05, preparación del sistema no):** ver §2
>   PackMan. Además `fix_pdb_serial.py` desplaza columnas desde el átomo 100 000 y ningún
>   script lo invoca.
> - **Transversal:** PDB > 99 999 átomos (seriales hex de Packmol) y pérdida de `TER` cruzan
>   los cuatro motores → una utilidad única (T1).
> - **Repo:** `THIRD_PARTY.md` decía que SIRAH no se redistribuye y el repo versiona 146
>   ficheros de SIRAH 2.3 (`tools/` GPL). `setup.py` con `version='1.0.0'` y
>   `python_requires>=3.7`. `salud.sh` en verde con tests fallando.

### Bugs reales
- **`Poromania/5docking.sh`**: `found_any` se inicializa en 0 y **nunca se pone a 1** → el script termina siempre con `exit 1` aunque el docking funcione, y eso hace fallar a `smiles_docking_pipeline.py`.
- **`sustratinaitor` — mismatch de resolución (confirmado)**: Packmol empaquetó el GYE **all-atom de 144 átomos** (160.620 = 131.820 + 200×144), no los 17 beads CG. La versión CG (`GYE_cg_manual.pdb`) quedó huérfana. El sistema resultante (cápside-CG + ligando-atomístico + agua-CG) es físicamente incoherente para SIRAH.
- **`nanocapsule-mvp/src/core/capsid.py`**: el código **suma** `+1.0 Å` al radio de colisión, pero su docstring y el CLAUDE.md dicen **restar** 1 Å. Una de las dos es un bug; hay que decidir cuál.
- ~~**`PackMan` — `heat1..6*.in` son all-atom** (`dt=0.002`, SHAKE, `@CA,C,N,O`) aplicados a topología CG SIRAH.~~ **Resuelto el 2026-10-05 (v1.3.0):** eliminados; el protocolo sigue `tutorial/5` de SIRAH sin etapa de calentamiento (CIENCIA-3 cerrada).

### Infraestructura desincronizada (diagnóstico de 2026-09-17; corregido en VLP-01/VLP-09, se deja como registro)
- ~~**Docker roto para el producto real**: los healthchecks pegan a `/api/health`, endpoint que no existe; el Dockerfile no instala RDKit, Vina ni obabel.~~ Corregido en VLP-01 (`/api/health` real; imagen py3.12 con obabel/vina/RDKit; HOLE e idock siguen siendo del usuario).
- ~~**`requirements.txt` no declara RDKit.**~~ Corregido en VLP-01 (+ `requirements.lock`).
- ~~**`setup.py`** apunta a `cli/main.py` inexistente.~~ Corregido en VLP-09.

### Documentación fósil
- README/CLAUDE describen ~4 endpoints que no existen (`/api/structures`, `/api/generate_pdb`, `/api/radius/{capsid}`, `/api/download/{exp_id}`) y **ninguno** de los ~20 reales.
- `TECHNICAL_IMPROVEMENTS.md` marca como `[x] hechos` siete módulos que nunca se crearon (`src/api/`, `health_service`, etc.).
- `SESION_STUDIO.md` cita `LO_APRENDIDO.md` como "la visión" — ese archivo **no existe**.
- Prototipos muertos: `vlp-enzyme-brutalista.html` (maqueta sin backend), `ngl-viewer.html` (apunta a un backend puerto 5001 que ya no existe).

### Código muerto (Poromania)
- `pore_analyzer_backup.py` (versión vieja divergente), `test_*.pml`, funciones definidas dos veces (`calculate_pentamer_center`), motor HOLE duplicado a mano en cada `mutants/*/scripts/`.
- **`1run_hole_old.sh` NO es basura** [AUDITORÍA 2026-10-04, PORO-04]: es la versión que tenía la validación de canal (líneas 118-151: constricción a > 5 Å del centro → aviso) y la vigente la perdió. Portar esa validación a `pore.py` antes de borrarlo (PO-4).

---

## 5. Rumbo recomendado (sin features nuevas)

1. **No reescribir desde cero.** La arquitectura (app → services → core) es correcta y auditable, y las piezas buenas existen (eje del poro del Studio, `substrate_section`, la conversión CG de sustratinaitor). [AUDITORÍA 2026-10-04] Pero ya no vale decir que "la ciencia que funciona ya está hecha": ningún resultado está validado y el patrón de fondo es el fallo silencioso (fallbacks presentados como mediciones, `except: continue`, códigos de salida ignorados). La reparación es "que falle, no que avise" (T3 de la hoja de ruta), no una reescritura.
2. **Partir los dos monolitos por sus costuras existentes**: `packing_service.py` → un módulo por puerta (`services/pore.py`, `services/md.py`, ...); `studio.html` → un módulo JS por pestaña. Convierte "agregar sección" en "crear archivo".
3. **Portada EMBUDO** como raíz (hoy `/` entra directo a Biblioteca). Cuenta la visión que no está escrita en ningún lado.
4. **Corregir los bugs de §4** y sincronizar la infraestructura (RDKit en requirements, healthcheck real, Docker que instale los motores).
5. **Sincronizar los documentos** con el código; retirar los fósiles.
6. Servidor web **local de un solo usuario** por ahora. Contenerizado + cola de trabajos el día que lo usen otros. **Nunca app de escritorio** (perdería los motores binarios/GPU).

---

## 4b. Decisiones científicas pendientes (las decide Lucio, no la IA)

Cosas que parecían "bugs" pero son elecciones de ciencia. Las decide Lucio. [AUDITORÍA
2026-10-04] **Las tres tenían ya evidencia suficiente para decidirse sin correr nada**
(`HOJA_DE_RUTA.md §3`, DC-2/DC-3/DC-4). CIENCIA-3 quedó cerrada el 2026-10-05 (MD-6);
CIENCIA-1 y CIENCIA-2 siguen abiertas y bloquean PK-6 y SU-2/SU-3.

- **CIENCIA-1 — `capsid.py` radio interno ±1 Å.** El código suma +1 Å; el docstring dice
  restar 1 Å. Recomendación con evidencia: **restar**. Con `+1` la esfera de empaque
  (88 Å en BMV) deja una holgura mínima de 0,5 Å frente al átomo más interno, por debajo
  de cualquier radio de vdW; con `−1` son ≥ 2,5 Å. Y el debate es ruido: el radio lo fija el
  0,14 % de los átomos (la punta de una Arg26, cadena C en BMV) y la incertidumbre
  conceptual es de 7–13 Å. Mejor: `d_min` exacto con NumPy (el bucle de PyMOL equivale a
  `ceil(d_min − 0,5)`) y publicar *radio físico* = `d_min − r_vdW` y *radio de empaque* =
  físico − margen. Nota corregida: "impacto real bajo porque el radio casi siempre es el
  fallback 90 Å" es justamente el problema: para BMV el valor correcto redondea a 90, así
  que ningún resultado commiteado permite saber si PyMOL llegó a correr.
- **CIENCIA-2 — `sustratinaitor` resolución CG vs all-atom.** El híbrido commiteado queda
  **descartado por física** (17 800 H explícitos a 20 fs sin SHAKE no integran; sin
  parámetros cruzados GAFF2×SIRAH; sin `TER`). Recomendación: **opción B, sacar el GYE de
  la MD CG**: la Puerta 4 corre cápside + enzima en SIRAH (PackMan reparado) y la física
  del sustrato se hace all-atom en sistemas pequeños reutilizando `GYE.mol2/.frcmod` (que
  están bien). La opción A (parametrizar GYE en SIRAH) es un subproyecto de 2–4 semanas y
  **`GYE_cg_manual.pdb` no sirve de punto de partida** (beads sobre átomos individuales,
  nombres que colisionan con el esqueleto, sin `.lib`).
- **CIENCIA-3 — `PackMan` protocolo.** **Resuelta (2026-10-05, PackMan v1.3.0)** siguiendo
  la recomendación DC-4: eliminados los 8 `.in` all-atom (`heat1..6`, `density_eq`,
  `final_eq`: `dt=0.002`, SHAKE, `cut=9`, máscara `@CA,C,N,O` que no selecciona ningún bead
  SIRAH) y `configurar_simulacion.sh` (su `eq1` restringía también el solvente con
  `':*&!@H='`, usaba `gamma_ln = 5` y no borraba los all-atom). Los 5 `.in` copian
  `tutorial/5` de SIRAH (em1 → em2 → eq1 5 ns → eq2 25 ns → prod en trozos de 10 ns; sin
  rampa de calentamiento, `eq1` arranca de 0 K bajo Langevin; `gamma_ln = 50`; restricciones
  2,4 → 0,24 sobre `@GN,GO`; `ig` fijo por etapa) y `verificar_protocolo_md.py` falla en CI
  si divergen de la referencia. Ver `PackMan.v.1.2/CHANGELOG.md`. **Sigue pendiente** la
  preparación del sistema (hidrógenos, `TER`, disulfuros, iones; MD-1…MD-5) antes de poder
  correr nada: el protocolo reparado no tiene todavía una topología válida que simular.

---

## 5b. Filosofía y alcance (leer antes de decidir qué tocar)

**El proyecto NO está muerto ni congelado. Estamos poniendo cimientos.** La ciencia
la construyó Lucio solo; el conocimiento vive en su cabeza y en el código. El objetivo
de esta fase (estructura, auditabilidad, editar-sin-romper) es **habilitar** que en el
futuro se pueda pulir, parchear y reconstruir la ciencia real **con seguridad** — no
sustituirla.

Por qué hoy no tocamos la ciencia: ahora no hay red (monolito, cero tests). La
modularidad (VLP-03/04) + los tests de humo (VLP-06) SON la licencia para editar la
ciencia después con marcha atrás y verificación.

**Fronteras (qué significa "no tocar"):**
- **Permanente — nunca:** los datos crudos pesados (los produce un motor, van en
  `.gitignore`); el otro proyecto/cuenta (`mexicanoresidente-ux`, residente-mx); y las
  **tripas de los motores de terceros** — HOLE, Vina, AMBER, campo de fuerza SIRAH se
  **llaman**, no se reescriben ni se forkean.
- **Protegido AHORA, editable DESPUÉS (con red):** toda la ciencia propia — análisis de
  poro, cribado de mutantes, protocolos de MD, empaquetado. Candidata a pulir/reconstruir
  una vez existan los cimientos. Durante VLP-03 se **mueve tal cual, no se reescribe**;
  reescribirla ahora reintroduce bugs ya resueltos (eje de simetría, rseed, centrado).
- **Aplazado hasta que haya razón real (no "nunca"):** deploy en nube, multiusuario,
  cola de trabajos, endurecer seguridad. Tiene sentido el día que lo use alguien más.
- **Ampliación futura, no ahora:** De-inmunización real (NetMHCIIpan/FEP).

---

## 6. Decisión estratégica: refundar por dentro, no reescribir de cero

**Decidido (2026-09-17): NO se reescribe desde cero.** La arquitectura es correcta y
hay piezas que funcionan y hay que conservar (eje del poro del Studio, `rseed 1`,
`substrate_section`, la conversión CG de sustratinaitor). [AUDITORÍA 2026-10-04] La
premisa "la ciencia difícil ya funciona (Pac-Pore end-to-end)" se retira: Pac-Pore corre,
pero no ha producido ningún resultado validado (§3). La decisión de no reescribir sigue
en pie por la misma razón: los defectos son concretos, localizados y tienen tarea asignada.

**Patrón a seguir: "estrangulador"** — el Studio sigue funcionando en todo momento;
en cada commit se extrae una pieza a su módulo y se verifica que arranca. No hay un
"gran día del rewrite": hay muchos commits pequeños, reversibles, que nunca dejan el
proyecto roto. Git es el vehículo: cada extracción es un commit auditable.

**"Empezar limpio" solo cabe** en lo que hoy es maqueta (De-inmunización, Análisis MD)
cuando se conecten de verdad, y en la etapa rota de `sustratinaitor` (bug de resolución).

### Plan de ejecución (ordenado; cada punto = uno o varios commits verificables)

> IDs de tarea: para trabajar una, di *"trabaja VLP-0N"*. Estado: ⬜ pendiente · 🚧 en progreso · ✅ hecho.

| ID | Estado | Tarea |
|----|--------|-------|
| **VLP-01** | ✅ | **Infra reproducible** (2026-09-17): `requirements.txt` reescrito a versiones que funcionan + RDKit; endpoint `/api/health` real (reporta motores/deps); `debug` respeta config (off por defecto); Dockerfile base py3.12 + motores apt (obabel/vina) + healthcheck urllib; compose sin curl. Verificado en vivo (boot + /api/health 200). **Caveat:** la imagen Docker no se pudo construir aquí (sin daemon); `hole`/`idock` no están en apt → documentado como límite conocido. |
| **VLP-02** | ✅ | **Bug mecánico corregido** (2026-09-17): `5docking.sh` `found_any` ahora se pone a 1 en el loop (antes `exit 1` siempre). Verificado. Los otros 3 "bugs" resultaron ser **decisiones científicas** → reclasificados abajo (CIENCIA-1/2/3), no se tocan ahora por decisión de Lucio. |
| **VLP-03** | ✅ | **`packing_service.py` partido** (2026-09-17, patrón estrangulador): el monolito de 1225 líneas → 6 módulos por responsabilidad — `common.py` (infra+helpers), `library.py`, `pore.py` (526), `deimmuno.py`, `md.py`, `packing.py`. `packing_service.py` quedó como **fachada** (71 líneas) que re-exporta la API; `app.py` y los tests no cambiaron. 17 tests verdes + boot en vivo (una ruta por puerta → 200). Para añadir puerta: nuevo módulo + re-exportar en la fachada. |
| **VLP-04a** | ✅ | **Externalizar `studio.html`** (2026-09-17): CSS y JS inline → `static/css/studio.css` (77) y `static/js/studio.js` (830); el template pasó de 1190 a 281 líneas (solo estructura). Extracción byte-idéntica (script Python). Verificado: node --check del JS, servido con content-type correcto, 17 tests backend verdes, y **en navegador** (render, badge PACKMOL LISTO, biblioteca real, cambio de pestaña a PAC-PORE con gráfica Chart.js, cero errores de consola). |
| **VLP-04b** | ✅ | **Partir `studio.js`** (2026-09-18): 830 líneas → 6 archivos por puerta en `static/js/`, byte-idéntico, verificado en navegador. |
| **VLP-04c** | ❌ | **Portada EMBUDO — DESCARTADA** (2026-09-17): se construyó y se revirtió a petición de Lucio ("no le veo utilidad"). `/` sigue entrando directo al Studio. NO reconstruir. |
| **VLP-05** | ⬜ | **Retirar fósiles**: `/classic`, prototipos muertos, código muerto de Poromania, docs que mienten. **+ Renombrar `nanocapsule-mvp/` → `studio/`** (el nombre es fósil; contiene el Studio vivo). OJO al renombrar: actualizar `herramientas/vlpstudio.kdl`, `herramientas/salud.sh`, PENDIENTES/BITACORA y docs que citen la ruta (paths.py se resuelve por `__file__`, no se rompe). |
| **VLP-06** | ✅ | **Tests de humo** (2026-09-17, ADELANTADO antes de VLP-03 para tener red al partir el monolito): `nanocapsule-mvp/tests/test_smoke.py`, 17 tests, ~1.5s. Cubren boot, páginas, biblioteca, Pac-Pore (rutas rápidas), sección RDKit, MD/deimmuno ilustrativos, preview y funciones de servicio. NO ejercen motores lentos (HOLE/PyMOL/Vina/Packmol). Correr: `cd nanocapsule-mvp && python3 -m pytest -q` (o `test` en el pane manual). El tablero `salud.sh` muestra el resultado. |
| **VLP-07** | ✅ | **Versionado por motor** (2026-09-17): `VERSION` + `CHANGELOG.md` en cada motor, independientes (Studio 0.1.0, Poromania 1.2.0, PackMan 1.2.0, sustratinaitor 0.1.0). Convención de tags git con prefijo por motor: `studio/vX.Y.Z`, `poromania/vX.Y.Z`, `packman/vX.Y.Z`, `sustratinaitor/vX.Y.Z`. Se versiona en archivo, NO en el nombre de carpeta (frágil). Tags baseline creados. |
| **VLP-08** | ✅ | **CI (GitHub Actions)** (2026-09-18): ruff + pytest del Studio desde `requirements.lock`; job `engines` con `compileall` de los otros motores y, desde 2026-10-05, `verificar_protocolo_md.py` de PackMan. Los binarios no van a CI. |
| **VLP-09** | ✅ | **LICENSE + `setup.py`** (2026-09-18): AGPLv3 (relicenciado desde MIT) + `THIRD_PARTY.md`; entry point arreglado. |
| **VLP-10** | ✅ | **Linter/formatter** (2026-09-17): ruff (`pyproject.toml`); CI corre `ruff check` + `ruff format --check`. |
| **VLP-11** | ✅ | **`fetch_data.sh`** (2026-09-17): baja la cápside P22 (5UU5) de RCSB; la biblioteca por defecto viaja en el repo. |

Deliberadamente FUERA del plan por ahora (se consideraron): tests de integración de los
motores (lentos, requieren binarios); type checking (mypy); logging real (sección de
default.yaml sin usar); endurecer seguridad de subprocess/SMILES (solo al exponer a
internet); Makefile (redundante con salud.sh + pane manual).

---

## 7. Cómo arrancar hoy

```bash
cd nanocapsule-mvp
FLASK_DEBUG=0 python3 src/web/app.py
# http://localhost:5000
```

Requiere en el sistema: `packmol`, `pymol`, `hole`, `vina`, `obabel`, `idock` (binarios) y las dependencias Python de `requirements.lock` (`pip install -r requirements.lock`). Tests: `python -m pytest -q` (60 + 1 saltado sin PACKMOL real).
