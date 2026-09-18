# Bitácora de VLP Studio — avances por sesión

> **Propósito:** dar continuidad entre sesiones. Aquí va lo que hay que saber de un
> vistazo: qué se hizo, qué se decidió y qué queda pendiente. **No** repite el
> detalle del código (eso está en `git log`) ni el diagnóstico técnico (eso está en
> `ESTADO.md`).
>
> **Para la IA:** al terminar cada sesión, agrega una entrada ARRIBA (más reciente
> primero) con la fecha real. Sé breve: 1) qué se hizo, 2) decisiones tomadas, 3) qué
> quedó pendiente. Marca ✅ hecho · 🚧 en progreso · ⬜ pendiente. Fechas absolutas.

---

## 2026-09-17 (16) — VLP-05: /classic oculta+deprecated → FASE B COMPLETA ✅

- ✅ **VLP-05 resuelto** (decisión de Lucio: conservar pero ocultar). `/classic` sigue
  funcional pero: enlace del footer quitado (0 enlaces UI), route/arranque marcados
  DEPRECATED, nota en README, comentario del test actualizado. 17 tests verdes.
- ✅ **FASE B ("confiable") COMPLETA:** LICENSE MIT + THIRD_PARTY + CI verde + pinning
  (lock) + VLP-09 (entry point) + VLP-05 (fósiles/classic). Falta solo, opcional: borrar
  `_temp_backup` local (770 MB, no está en git; decisión de Lucio con `rm -rf`).
- ⬜ **Siguiente = FASE C (citable):** README real (el actual sigue siendo el fósil de
  abril con parches; reescribirlo de verdad) + `CITATION.cff`. Opcional: golden file, JOSS.
- DECISIÓN AÚN ABIERTA para Fase C: ¿release normal de GitHub o apuntar a JOSS (DOI + paper)?

---

## 2026-09-17 (15) — Fase B: pinning + cierre VLP-09; falta decidir /classic (VLP-05)

- ✅ **Pinning (requirements.lock):** 17 paquetes con versión exacta (incl. transitivas
  antes sueltas). Dockerfile y CI instalan desde el lock → build/CI reproducibles.
  Verificado: build Docker OK, lock instala limpio en venv aislado, 17 tests verdes, CI verde.
- ✅ **VLP-09 cerrado:** retirado el entry point roto `nanocapsule=cli.main:cli` (apuntaba
  a src/cli inexistente, solo __init__ vacío) + borrado el paquete cli vacío. No hay CLI;
  el punto de entrada real es `python src/web/app.py`.
- 🔎 **VLP-05 (fósiles) — hallazgos:**
  - `_temp_backup/` (770 MB) **NO está trackeado en git** → no es basura del repo, es local.
    Lucio puede `rm -rf nanocapsule-mvp/_temp_backup` para recuperar disco (opcional, su decisión).
  - **`/classic`** (interfaz NGL antigua) SÍ está viva y con test de humo que exige 200.
    Retirarla es una DECISIÓN DE PRODUCTO (cambia comportamiento), no limpieza mecánica →
    NO se tocó unilateralmente. PENDIENTE de que Lucio decida si se retira o se conserva.
- ⬜ **Siguiente:** decidir /classic; luego Fase C (README real + CITATION.cff).

---

## 2026-09-17 (14) — VLP-08: CI en GitHub Actions ✅ VERDE

- ✅ **CI hecho y verde al primer intento** (run 35303445371, success en 31s).
  `.github/workflows/ci.yml`: en push/PR a main → Python 3.12, deps pip, lint crítico
  (flake8 E9/F63/F7/F82, solo errores reales sin ruido de estilo) + 17 tests de humo.
- **Decisión de alcance:** CI solo instala deps pip (NO motores). Verificado que los
  imports de pymol en src/ son lazy (dentro de funciones) y app.py/conftest no importan
  motores al tope → los tests de humo colectan y pasan sin pymol/hole/gromacs. Mirror del
  principio de la investigación: CI valida cableado, no ciencia.
- Cubre solo `nanocapsule-mvp/` (el Studio). Los otros 3 motores (Poromania/PackMan/
  sustratinaitor) no tienen tests aún → fuera de CI por ahora.
- Pre-validado local antes del push: lint 0 errores, 17 tests verdes.
- ⬜ **Siguiente Fase B:** pinning de deps (pip-tools/uv), retirar fósiles (VLP-05),
  cerrar VLP-09 (entry point cli roto).

---

## 2026-09-17 (13) — Fase B: LICENSE MIT aplicada (VLP-09 parte 1)

- ✅ **LICENSE MIT** en la raíz del monorepo. Titular: **najera-maldonado** (nombre de
  Lucio en publicaciones científicas, confirmado por él), año 2026. Cubre el código propio
  de los 4 proyectos.
- ✅ **THIRD_PARTY.md**: lista las licencias de cada motor externo, separando los
  redistribuibles (packmol/pymol/obabel/vina/rdkit) de los que NO se distribuyen y aporta
  el usuario (HOLE, idock, NetMHCIIpan, GROMACS, SIRAH). Deja explícito que MIT del código
  es compatible con motores GPL/LGPL que se INVOCAN (no se enlazan).
- ✅ **setup.py**: añadido `license='MIT'`, author → najera-maldonado, URLs placeholder
  `yourusername/nanocapsule-mvp` → `najera-maldonado/vlp-studio`. (El clasificador MIT ya
  estaba.)
- ⚠️ **Pendiente de VLP-09:** el entry point `nanocapsule=cli.main:cli` sigue roto (no hay
  módulo cli; CLAUDE.md ya lo notaba). No rompe el install, pero el comando fallaría.
  Arreglarlo o quitarlo en una pasada aparte.
- ⬜ **Siguiente Fase B:** CI (VLP-08), pinning de deps, retirar fósiles (VLP-05).

---

## 2026-09-17 (12) — Fase A arrancada: la imagen Docker YA CONSTRUYE Y ARRANCA ✅

- ✅ **Docker daemon verificado disponible** (v29.8.0) → se atacó la Fase A (el riesgo real).
- 🐛 **2 bugs de build encontrados y arreglados en caliente:**
  1. **Sin `.dockerignore`** → build context de **2.4 GB** (Output 1.3G, _temp_backup 770M,
     Input 337M). Creado `nanocapsule-mvp/.dockerignore` → context a **564 kB**. (Input/
     Output van por volumen, no en la imagen; _temp_backup es fósil.)
  2. **`libgl1-mesa-glx` no existe en Debian 13 (trixie)**, que es lo que `python:3.12-slim`
     rastrea ahora → apt exit 100. Cambiado a **`libgl1`** en el Dockerfile. Los demás apt
     (packmol/pymol/openbabel/autodock-vina) SÍ resuelven.
- ✅ **Imagen construida** (`nanocapsule-mvp:latest`, 298 MB) **y verificada en vivo:**
  `docker compose up` → contenedor **healthy**, `/api/health` = `status ok`. Deps OK
  (flask/numpy/rdkit/yaml). Motores DENTRO: packmol/pymol/obabel/vina ✅.
- ⚠️ **Confirmado lo esperado (NO son bugs):** dentro del contenedor faltan **hole**,
  **idock** (no están en apt; + hole no es redistribuible) y **gmx/GROMACS** (Puerta 4).
  → Pac-Pore y Puerta 4 MD no funcionan en el contenedor tal cual. Se resuelve aparte
  (capa/volumen para hole/idock bajo licencia del usuario; decisión de cómo proveer GROMACS).
- ⬜ **Siguiente:** decidir cómo proveer hole/idock/GROMACS (sin hornear los no
  redistribuibles), luego Fase B (CI, LICENSE MIT, pinning, fósiles). Cambios de hoy
  (.dockerignore + Dockerfile) SIN commitear aún.

---

## 2026-09-17 (11) — Investigación enfocada: reproducibilidad para un dev único

- ✅ **Cerrado el vacío del eje (e).** 2ª deep-research enfocada solo en reproducibilidad
  realista para VLP Studio mantenido por una persona. Reporte en
  **`INVESTIGACION_REPRODUCIBILIDAD_2026-09-17.md`** (23 fuentes, 23/25 claims confirmados).
  Nota: el paso de síntesis automática falló por límite de sesión → sintetizado a mano
  sobre los claims verificados (cada recomendación cita fuente).
- **Plan de acción priorizado (mínimo viable, por retorno/esfuerzo):**
  1. **conda-lock por motor** (pinning exacto de HOLE/Vina/GROMACS/RDKit) — mayor retorno.
  2. **Log de provenance por corrida** (params + versiones junto a cada output; push-based,
     sin refactor).
  3. **VLP-08 (CI) como stub-run + lint** — pytest de humo + linting en Actions; NO correr
     motores pesados en CI (el estándar nf-core es stub que genera outputs vacíos).
  4. **Golden file + numpy.allclose** para un perfil de poro de referencia — red contra
     regresiones científicas (no solo bugs de código).
  5. **Quedarse en Makefile/scripts**; Snakemake solo si hace falta paralelismo/reanudar/
     barridos (y ahí da provenance gratis en .snakemake/metadata).
- **Sobre-ingeniería a EVITAR (refutado o desaconsejado):** repo separado de test-data
  (refutado 0-3); metadatos FAIR con ontologías/DOIs; WMS "porque sí"; tratar el testing
  automatizado como dogma universal (refutado 0-3).
- **Regla de oro:** subir un nivel de madurez cuesta 5-10× más esfuerzo → elegir el mínimo
  nivel necesario.
- ⬜ **Siguiente:** ejecutar el plan (empezar por conda-lock y/o VLP-08 con lo aprendido).

---

## 2026-09-17 (10) — Investigación externa: qué se nos está pasando (deep-research)

- ✅ **Investigación profunda recuperada y terminada.** La sesión (9) se cortó (apagón)
  con una deep-research corriendo ("ver proyectos similares, qué se nos pasa"); no dejó
  resultados rescatables, así que se relanzó. Resultado completo en
  **`INVESTIGACION_2026-09-17.md`** (24 fuentes, 24/25 claims confirmados por verificación
  adversarial). Nota de proceso: el primer relanzamiento falló (args demasiado largo →
  el agente de scope agotó reintentos de salida estructurada); se recortó el args y corrió.
- **Hallazgos clave por puerta:**
  - 🔴 **Puerta 1 (poro) es el punto frágil:** HOLE2 + cribado geométrico estático
    subestima el transporte (cadenas laterales dominan, poros "respiran", ignora gating
    hidrofóbico <5 Å). Fix barato de mayor impacto: **CHAP** (proxy de agua desde MD corta).
    Escalables: CAVER/MOLE, CaverDock (puente HOLE2↔Vina), PMF por umbrella sampling+WHAM.
  - 🟡 **Puerta 3 (de-inmunización) puede dejar de ser maqueta YA:** **NetMHCIIpan-4.3**
    es standalone descargable (MHC-II/CD4+, lo relevante para enzimas). Plantilla de motor:
    King et al. PNAS 2014 (SVM+Rosetta).
  - 🟢 **Puerta 2:** P22 es el precedente experimental directo; ojo, la carga es
    enzima-dependiente (no asumir protocolo fijo). **Puerta 4:** SIRAH confirmado apto.
  - ⚠️ **Reproducibilidad (eje e): SIN respuesta verificada** — ningún claim sobrevivió.
    Es el mayor hueco; merece una 2ª búsqueda enfocada solo en ese eje.
- ⬜ **Siguiente:** decidir si se actúa sobre Puerta 1 (CHAP) / Puerta 3 (NetMHCIIpan), y/o
  relanzar deep-research solo sobre reproducibilidad. Cimientos aún pendientes: VLP-04b, 05, 08.

---

## 2026-09-17 (9) — VLP-07: versionado por motor + plan ampliado (best practices)

- ✅ **VLP-07 hecho:** `VERSION` + `CHANGELOG.md` en cada motor, independientes —
  Studio 0.1.0, Poromania 1.2.0, PackMan 1.2.0, sustratinaitor 0.1.0. Convención de
  tags con prefijo por motor (`studio/vX.Y.Z`, etc.); tags baseline creados. La versión
  vive en archivo, NO en el nombre de carpeta (que es frágil, rompe rutas).
- ✅ **Plan ampliado tras revisar buenas prácticas** (ESTADO §6): añadidos VLP-08 (CI
  GitHub Actions — lo más valioso pendiente), VLP-09 (LICENSE + arreglar setup.py),
  VLP-10 (linter/formatter), VLP-11 (script de datos). Gaps confirmados: sin LICENSE,
  sin CI, sin config de lint, sin CHANGELOG (este último ya resuelto por VLP-07).
- Fuera de alcance por ahora (documentado): mypy, logging real, tests de integración de
  motores, endurecer seguridad, Makefile.
- ⬜ **Siguiente:** cerrar cimientos (VLP-04b, 05) y luego VLP-08 (CI).

---

## 2026-09-17 (8) — Portada EMBUDO descartada (revertida)

- ❌ **VLP-04c revertida a petición de Lucio** ("no me gusta, no le veo utilidad").
  Se había construido (portada en `/`, Studio en `/studio`) pero se descartó. `git revert`
  del commit → `/` vuelve a ser el Studio directo, `/studio` y los archivos embudo
  eliminados, 17 tests verdes. **No reconstruir la portada** (ESTADO §6 VLP-04c = ❌).
- Nota de proceso: la construí por un malentendido — Lucio dijo "el layout" refiriéndose
  al layout de ZELLIJ (que ya estaba hecho), y lo leí como layout web. El de zellij ya
  está completo y validado (KDL parsea, comando `vlpstudio` se genera en shell interactiva).
- ⬜ **Siguiente:** VLP-04b (partir studio.js por pestaña) o VLP-05.

---

## 2026-09-17 (7) — VLP-04a: studio.html externalizado (CSS+JS a static/)

- ✅ **`studio.html` 1190 → 281 líneas** (solo estructura): CSS inline → `static/css/
  studio.css` (77), JS inline → `static/js/studio.js` (830). Extracción byte-idéntica
  con script Python; rutas `/static/...` planas (sin Jinja). Orden de carga preservado
  (studio.js al final del body).
- ✅ **Verificado a fondo** (frontend, sin red de tests propia): `node --check` del JS OK,
  servido con content-type correcto, 17 tests backend verdes, y **en navegador real**
  (claude-in-chrome): render con CSS, badge "PACKMOL LISTO" (JS corrió /api/health),
  biblioteca con datos reales, cambio a pestaña PAC-PORE con gráfica Chart.js y dropdown
  de canales poblado, CERO errores de consola.
- **Decisión de alcance:** VLP-04 se dividió en 04a (externalizar, HECHO), 04b (partir
  studio.js por pestaña, pendiente) y 04c (portada EMBUDO, pendiente). La externalización
  ya da el grueso de la editabilidad; el split fino y la portada van aparte.
- ⬜ **Siguiente:** VLP-04b (studio.js por pestaña) o VLP-04c (portada EMBUDO).

---

## 2026-09-17 (6) — VLP-03: monolito partido por puertas (estrangulador)

- ✅ **`packing_service.py` (1225 líneas) → 6 módulos** por responsabilidad:
  `common.py` (infra+helpers PDB), `library.py`, `pore.py` (526, Pac-Pore completo),
  `deimmuno.py`, `md.py`, `packing.py` (Studio 3D).
- ✅ **Fachada:** `packing_service.py` quedó en 71 líneas re-exportando la API pública
  (24 nombres, incl. `_config`). `app.py` y los tests NO cambiaron → estrangulador puro.
- ✅ **Verificado:** 17 tests verdes tras el swap + boot real del Flask con una ruta por
  puerta (health/library/pore/deimmuno/md) → todas 200, sin errores.
- **Cómo crecer ahora:** puerta nueva = módulo nuevo + una línea de re-export en la fachada.
- **Nota:** el nombre `packing_service.py` quedó legacy (ya es fachada, no "packing");
  renombrarlo tocaría app.py+tests → opcional para VLP-05.
- ⬜ **Siguiente:** VLP-04 (partir `studio.html` + portada EMBUDO).

---

## 2026-09-17 (5) — VLP-06 adelantado: red de tests de humo antes de trocear

- ✅ **Decisión:** hacer VLP-06 ANTES de VLP-03, para tener red al partir el monolito.
- ✅ **`tests/test_smoke.py`** (17 tests, ~1.5s, pytest): boot + páginas, /api/health,
  biblioteca (Input real), Pac-Pore rutas rápidas, sección RDKit (válido→radio, inválido
  →400), profile/deimmuno/md ilustrativos, md_box, preview de enzimas, y funciones de
  servicio (substrate_section, md_prepare). NO ejercen HOLE/PyMOL/Vina/Packmol (lentos).
- ✅ `pytest.ini` (pythonpath) + `tests/conftest.py` (fixture client). pytest en requirements.
- ✅ Comando `test` añadido al pane manual del layout; `salud.sh` muestra el resultado.
- ⬜ **Siguiente:** VLP-03 (partir `packing_service.py` por puerta) — ya con red verde.

---

## 2026-09-17 (4) — VLP-02: bug mecánico corregido, 3 "bugs" eran ciencia

- ✅ **`Poromania/5docking.sh` corregido:** `found_any=1` dentro del loop (antes nunca
  se ponía a 1 → `exit 1` siempre, aunque el docking funcionara). Verificado en aislado.
- ✅ **Reclasificación honesta:** los otros 3 "bugs" de §4 resultaron ser decisiones
  científicas, no fixes de una línea. Movidos a ESTADO §4b como CIENCIA-1/2/3:
  - CIENCIA-1: capsid.py ±1 Å (Lucio decide luego; IA recomienda restar).
  - CIENCIA-2: sustratinaitor CG vs all-atom (aplazado hasta correr esa MD).
  - CIENCIA-3: PackMan protocolo heat (aplazado hasta correr esa MD).
- **Decisión de Lucio:** no tocar los 3 científicos ahora (coherente con la filosofía:
  no tocar ciencia sin red y sin necesidad inmediata; ni esas MDs se han corrido).
- ⬜ **Siguiente:** VLP-03 (partir `packing_service.py` por puerta).

---

## 2026-09-17 (3) — VLP-01 hecho: infra reproducible

- ✅ **`requirements.txt` reescrito** a las versiones que realmente funcionan (Flask
  3.1.3, numpy 1.26.4, py3.12) + **RDKit 2025.9.1** (antes ausente → irreproducible).
  Motores externos documentados como no-pip; deps no usadas marcadas para VLP-05.
- ✅ **Endpoint `/api/health` real** en `app.py`: reporta qué motores (which) y deps
  (import) están presentes. Antes no existía → el healthcheck de Docker daba unhealthy.
- ✅ **`debug` respeta config** (web.debug=false por defecto + override FLASK_DEBUG);
  antes estaba `debug=True` hardcodeado.
- ✅ **Dockerfile** base py3.12 (no 3.9), instala obabel+vina, healthcheck por urllib
  (no requests/curl). **compose** healthcheck por python (no curl).
- ✅ **Verificado en vivo:** boot del Flask + `/api/health` → 200 con los 6 motores y 4
  deps presentes; debug off.
- 🚧 **Caveat honesto:** la imagen Docker NO se construyó (sin daemon aquí); `hole`/
  `idock` no están en apt → documentado como límite. Pendiente humano: `docker compose build` una vez.
- ⬜ **Siguiente:** VLP-02 (los 4 bugs).

---

## 2026-09-17 (2) — Filosofía aclarada: cimientos para editar la ciencia, no congelarla

- ✅ **Corrección de alcance (ESTADO §5b):** la ciencia NO está fuera de alcance ni
  congelada para siempre. Esta fase de cimientos existe **para poder pulir/reconstruir
  la ciencia real con seguridad en el futuro**. Hoy no se toca solo porque falta la red
  (modularidad + tests); esos cimientos son la licencia para editarla luego.
- ✅ **Frontera permanente reducida a:** datos crudos pesados, el otro proyecto/cuenta,
  y las tripas de motores de terceros (HOLE/Vina/AMBER/SIRAH se llaman, no se forkean).
  Todo lo demás —incluida la ciencia propia— es editable a futuro con red.
- Contexto: Lucio construyó toda la ciencia solo; el conocimiento vive en su cabeza y el
  código. Los cimientos (ESTADO/bitácora/modularidad/tests) también sirven para que ese
  conocimiento deje de depender solo de su memoria.

---

## 2026-09-17 — Fundación: git, diagnóstico y sistema de trabajo

- ✅ **Git iniciado** y monorepo (los 4 proyectos) publicado en GitHub privado:
  `github.com/najera-maldonado/vlp-studio`. Cuenta dedicada `najera-maldonado`
  (identidad repo-local; la global sigue siendo la de otro proyecto).
- ✅ **Lectura completa del código** (Studio + Poromania + PackMan + sustratinaitor +
  docs) → volcada en `ESTADO.md`: qué es el proyecto, estado por puerta, bugs
  verificados (§4) y plan de ejecución VLP-01…06 (§6).
- ✅ **Decisión estratégica registrada:** NO reescribir de cero; patrón "estrangulador"
  (extraer pieza por pieza en commits verificables, el Studio nunca deja de arrancar).
- ✅ **Sistema de trabajo estilo residente** montado: `PENDIENTES.md` (lista viva),
  esta `BITACORA.md`, IDs de tarea en ESTADO, y layout zellij `vlpstudio`
  (`~/.config/zellij/layouts/vlpstudio.kdl`, comando `vlpstudio`).
- 🚧 **Diagnóstico:** ningún paso del plan ejecutado todavía. `requirements.txt` sin
  RDKit, los 4 bugs vivos, monolitos sin partir.
- ⬜ **Siguiente:** VLP-01 (infra reproducible). Empezar por ahí porque desbloquea
  todo y es imposible de romper.
