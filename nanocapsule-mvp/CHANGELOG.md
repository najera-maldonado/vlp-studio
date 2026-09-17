# Changelog — Studio (nanocapsule-mvp)

Versionado independiente por motor. Formato: [Keep a Changelog]. Tags: `studio/vX.Y.Z`.

## [0.1.0] — 2026-09-17
Línea base de la fase de cimientos (ver ESTADO.md §6).
- Infra reproducible: `requirements.txt` con versiones reales + RDKit; `/api/health`;
  Docker py3.12 (VLP-01).
- Backend modular: `packing_service.py` (1225 líneas) partido en 6 módulos por puerta
  + fachada (VLP-03).
- Frontend externalizado: CSS y JS de `studio.html` movidos a `static/` (VLP-04a).
- Red de tests de humo: 17 tests en `tests/test_smoke.py` (VLP-06).
- Nota: `capsid.py` radio ±1 Å pendiente de decisión (CIENCIA-1).
