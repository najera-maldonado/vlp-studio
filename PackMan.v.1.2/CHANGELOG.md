# Changelog — PackMan (dinámica molecular SIRAH)

Versionado independiente por motor. Formato: [Keep a Changelog]. Tags: `packman/vX.Y.Z`.

## [1.2.0] — 2026-09-17
Versión heredada del nombre de carpeta (`.v.1.2`), ahora en archivo.
- Sin cambios de código esta sesión.
- Motor de la puerta "Sobrevive": empaquetado → CG SIRAH → tleap → pmemd.cuda → cpptraj.
  El subsistema `analisis/` produce los `.dat` (frame, valor) que consume la pestaña MD.
- Estado: solo el empaquetado tiene evidencia de ejecución; la MD NO se ha corrido.
- Decisión pendiente (CIENCIA-3, ESTADO §4b): los `heat*.in` estáticos son all-atom
  sobre topología CG; `configurar_simulacion.sh` ya genera los correctos en CG.
