# Pendientes — VLP Studio

> Lista viva. Formato: `- [ ]` pendiente, `- [x]` hecho. Detalle de tareas grandes en
> `ESTADO.md §6`; investigaciones en `INVESTIGACION_*.md`; historial en `BITACORA.md`.
> Actualizado 2026-09-17 tras cumplir la meta "publicable como software" + release v0.1.0.

## 🎯 Meta cumplida: PUBLICABLE COMO SOFTWARE (release v0.1.0)
- [x] **Fase A — instalable:** Docker construye/arranca (.dockerignore, fix libgl1), engines documentados.
- [x] **Fase B — confiable:** LICENSE MIT + THIRD_PARTY · CI verde (VLP-08) · pinning requirements.lock · VLP-09 (entry point) · VLP-05 (/classic oculta+deprecated).
- [x] **Fase C — citable:** README de plataforma (raíz) · CITATION.cff · **release v0.1.0 en GitHub**.

## Para dejarlo "bien bien" ANTES de publicar (pulido recomendado)
- [ ] **README de PackMan y sustratinaitor** (hoy SIN README; Studio y Poromania sí tienen). Cada motor debería explicarse.
- [ ] **VLP-11 — `fetch_data.sh`**: bajar las estructuras pesadas gitignoreadas (sobre todo la cápside P22 5UU5 >100 MB). Sin esto, un clone limpio corre el Studio con la biblioteca por defecto (BMV/CCMV/MS2/QB sí viajan) pero NO con P22.
- [ ] **Golden file + numpy.allclose**: test de regresión científica (p.ej. perfil de poro BMV ≈2.47 Å reproducible). Red contra romper la ciencia, no solo el código.
- [ ] **VLP-10 — Linter/formatter con config** (black + flake8/ruff completos; hoy CI solo hace lint crítico E9/F* sin ruido). Opcional pre-commit.
- [ ] **CI para los otros motores** (hoy CI solo cubre el Studio; Poromania tiene 1 test sin correr en CI).
- [ ] **VLP-04b — Partir `studio.js`** (830 líneas) por pestaña. Mantenibilidad; ya con red de navegador.

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
