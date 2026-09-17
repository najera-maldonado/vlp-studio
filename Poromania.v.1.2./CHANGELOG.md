# Changelog — Poromania (análisis de poros)

Versionado independiente por motor. Formato: [Keep a Changelog]. Tags: `poromania/vX.Y.Z`.

## [1.2.0] — 2026-09-17
Versión heredada del nombre de carpeta (`.v.1.2`), ahora en archivo.
- Fix: `5docking.sh` ponía `found_any=1` nunca → `exit 1` siempre; corregido (VLP-02).
- Motor real de la puerta "A través" del Studio (HOLE + cribado + docking), consumido
  vía `paths.POROMANIA_DIR`.
- Deuda conocida (ver ESTADO.md §4): código muerto (`pore_analyzer_backup.py`,
  `1run_hole_old.sh`, `test_*.pml`), motor HOLE duplicado por mutante, 3 definiciones
  del eje del poro. Pendiente de limpieza (VLP-05).
