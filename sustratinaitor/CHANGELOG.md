# Changelog — sustratinaitor (sustrato GYE alrededor de la cápside)

Versionado independiente por motor. Formato: [Keep a Changelog]. Tags: `sustratinaitor/vX.Y.Z`.

## [0.1.0] — 2026-09-17
Línea base (antes sin versión explícita).
- Construye GYE (glucosilceramida) y empaqueta 200 copias alrededor de la cápside 3J7L.
- Ejecutado hasta el empaquetado; la etapa 4 (MD) no se ha corrido.
- Bug confirmado / decisión pendiente (CIENCIA-2, ESTADO §4b): mismatch de resolución —
  Packmol empaquetó el GYE all-atom (144 átomos), no los 17 beads CG; el sistema
  resultante (cápside CG + ligando all-atom + agua CG) es incoherente para SIRAH.
