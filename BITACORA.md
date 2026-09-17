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
