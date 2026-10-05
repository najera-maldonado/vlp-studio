# Changelog — Studio (nanocapsule-mvp)

Versionado independiente por motor. Formato: [Keep a Changelog]. Tags: `studio/vX.Y.Z`.

## [Unreleased]
Reparación del motor de packing tras las dos auditorías independientes
(`AUDITORIA_PACKING.md` ×2, `HOJA_DE_RUTA.md` PK-2…PK-5). Detalle y decisiones en
`REPARACION_PACKING.md`.
- **Corregido:** el criterio de aceptación de PACKMOL parsea la línea real
  `Maximum violation of target distance:` (último valor), exige `Success!`, rechaza
  `ENDED WITHOUT PERFECT PACKING` y `<output>_FORCED` aunque el exit sea 0, y cuenta las
  copias de enzima colocadas (`átomos_cápside + N × átomos_enzima`). Retirado el fallback
  "≥ 10 000 líneas" (`packing.min_lines_threshold`), que la cápside sola cumplía.
- **Corregido:** la cápside entra en el `.inp` con `center` + `fixed`; el centrado es
  Python puro (sin PyMOL, conserva `TER`) y escribe en el directorio del experimento; el
  runner aborta si el centrado falla o si el radio es el valor de reserva. Verificación
  geométrica del output: las enzimas deben quedar dentro de la cápside.
- **Corregido:** `engines.packmol.seed_base`, `use_random_seeds`, `timeout`,
  `packing.collision_margin` y `experiments.n_replicas` se leen del YAML. Semilla fija por
  defecto (`seed_base + réplica`); cada causa de rechazo (timeout, exit, `_FORCED`,
  violación, conteo, geometría) queda en `metadata.json` y `report.txt`.
- **Añadido:** `engines.packmol.max_workers`; `n_replicas_at_best`, `warnings`,
  `run_config` y `rejection_reasons` en `statistics.json` y en `/api/experiment/run`;
  `stdev` es `null` con < 2 réplicas; un experimento sin réplicas aceptadas responde
  `status: failed` (la UI ya no lo pinta en verde).
- **Tests:** 39 tests nuevos del motor y del runner con un doble de PACKMOL
  (`tests/packmol_double.py`) y los dos logs reales como fixtures; 28/30 fallan contra el
  código anterior. Marcador `engine` para el test con PACKMOL real.

## [0.1.0] — 2026-09-17
Línea base de la fase de cimientos (ver ESTADO.md §6).
- Infra reproducible: `requirements.txt` con versiones reales + RDKit; `/api/health`;
  Docker py3.12 (VLP-01).
- Backend modular: `packing_service.py` (1225 líneas) partido en 6 módulos por puerta
  + fachada (VLP-03).
- Frontend externalizado: CSS y JS de `studio.html` movidos a `static/` (VLP-04a).
- Red de tests de humo: 17 tests en `tests/test_smoke.py` (VLP-06).
- Nota: `capsid.py` radio ±1 Å pendiente de decisión (CIENCIA-1).
