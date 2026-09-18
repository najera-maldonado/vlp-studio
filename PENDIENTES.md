# Pendientes — VLP Studio

> Lista viva. Formato: `- [ ]` pendiente, `- [x]` hecho. Detalle de tareas grandes en
> `ESTADO.md §6`; investigaciones en `INVESTIGACION_*.md`; historial en `BITACORA.md`.
> Actualizado 2026-09-17 tras cumplir la meta "publicable como software" + release v0.1.0.

## 🎯 Meta cumplida: PUBLICABLE COMO SOFTWARE (release v0.1.0)
- [x] **Fase A — instalable:** Docker construye/arranca (.dockerignore, fix libgl1), engines documentados.
- [x] **Fase B — confiable:** LICENSE MIT + THIRD_PARTY · CI verde (VLP-08) · pinning requirements.lock · VLP-09 (entry point) · VLP-05 (/classic oculta+deprecated).
- [x] **Fase C — citable:** README de plataforma (raíz) · CITATION.cff · **release v0.1.0 en GitHub**.

## Para dejarlo "bien bien" ANTES de publicar (pulido recomendado)
- [x] **README de PackMan y sustratinaitor** (2026-09-17): los 4 motores documentados con estado honesto.
- [x] **VLP-11 — `fetch_data.sh`** (2026-09-17): baja P22 5UU5 de RCSB; biblioteca por defecto ya viaja en el repo. Sintaxis validada, RCSB 200.
- [x] **Golden test de regresión científica** (2026-09-17): `tests/test_golden_science.py`, radio de sección RDKit (seed fijo) con tolerancia; corre en CI. 5 tests.
- [x] **VLP-10 — Linter/formatter** (2026-09-17): ruff (pyproject.toml), 39 fixes + format; CI usa ruff check + format --check.
- [x] **CI para los otros motores** (2026-09-18): job `engines` corre compileall sobre Poromania/PackMan/sustratinaitor (verifican que su Python parsea; excluye bundle SIRAH). Verde.
- [x] **VLP-04b — Partir `studio.js`** (2026-09-18): 830 líneas → 6 archivos por puerta (studio-core/library/analisis-md/deinmunizacion/pac-pore/packing). Byte-idéntico, verificado en navegador (PAC-PORE con Chart.js, 0 errores consola).

## Bloqueante para PUBLICAR de verdad (decisión + acción humana)
- [ ] **Hacer el repo PÚBLICO** (hoy privado). Necesario para que otros lo usen y para JOSS. — Solo Lucio.

## Siguiente objetivo acordado: publicación en JOSS
- [ ] `paper.md` (metadata + *statement of need* + resumen + referencias).
- [ ] Docs de instalación/uso completas (JOSS las exige explícitas).
- [ ] Archivar en Zenodo → DOI (añadir a README y CITATION.cff).
- [ ] Repo público (ver arriba).

## Diferido / cosmético (no bloquea publicar)
- [ ] Renombrar `nanocapsule-mvp/` → `studio/` (nombre fósil). RIESGOSO: toca rutas, build-context de Docker, imports → hacerlo con red y verificación.
- [ ] Borrar `_temp_backup/` local (770 MB, NO está en git). Recupera disco. — Solo Lucio, `rm -rf`.

## Humano — ciencia (fuera de "publicable como software"; es "publicable como ciencia", meses)
- [ ] **CIENCIA-1** — `capsid.py` radio ±1 Å (IA recomienda restar). Ver ESTADO §4b.
- [ ] **CIENCIA-2** — resolución de `sustratinaitor` (CG vs all-atom), al correr esa MD.
- [ ] **CIENCIA-3** — protocolo de heat de `PackMan`, al correr esa MD.
- [ ] Robustecer Puerta 1 (CHAP/PMF; HOLE geométrico subestima transporte — ver INVESTIGACION_2026-09-17.md).
- [ ] Motor real de Puerta 3 (de-inmunización: NetMHCIIpan-4.3). Correr la MD de Puerta 4 (hoy sin trayectorias).

## Descartado
- [x] ~~VLP-04c — Portada EMBUDO~~ (Lucio: "no le veo utilidad"). No reconstruir.
