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
