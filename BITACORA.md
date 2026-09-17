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
