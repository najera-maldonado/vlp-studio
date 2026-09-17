# Pendientes — VLP Studio

> Lista viva. El pane "pendientes" del tablero zellij la muestra; edítala ahí con
> la tecla `e`, o con cualquier editor. Formato: `- [ ]` pendiente, `- [x]` hecho.
> El detalle y el orden de las tareas grandes vive en `ESTADO.md §6` (VLP-01…06);
> aquí solo el recordatorio de lo inmediato y lo que depende de ti (humano).

## Ahora
- [x] **VLP-01 — Infra reproducible** (2026-09-17): requirements reescrito + RDKit, `/api/health` real, debug configurable, Dockerfile py3.12 + motores, compose sin curl. Verificado en vivo.
- [x] Confirmar que el Studio arranca hoy (verificado: boot + /api/health 200).
- [x] **VLP-02 — Bug mecánico** (2026-09-17): 5docking.sh `found_any` corregido y verificado. Los otros 3 eran decisiones científicas → CIENCIA-1/2/3 (aplazadas por decisión de Lucio).
- [x] **VLP-06 — Tests de humo** (2026-09-17, adelantado): 17 tests en `tests/test_smoke.py`, verdes en ~1.5s. La red para VLP-03.
- [ ] **VLP-03 — Partir `packing_service.py`** por puerta (siguiente, ya con red de tests). Ver ESTADO §6.
- [ ] (Humano, cuando puedas) construir la imagen Docker una vez para validarla: `cd nanocapsule-mvp && docker compose build`. Aquí no hubo daemon.

## Backlog (detalle en ESTADO.md §6)
- [ ] VLP-02 — Corregir los 4 bugs conocidos (5docking.sh, mismatch CG, capsid ±1 Å, heat*.in).
- [ ] VLP-03 — Partir `packing_service.py` por puerta.
- [ ] VLP-04 — Partir `studio.html` + portada EMBUDO.
- [ ] VLP-05 — Retirar fósiles (/classic, prototipos muertos, código muerto) + **renombrar `nanocapsule-mvp/` → `studio/`** (nombre engañoso; contiene el Studio vivo). Ver ESTADO §6.
- [ ] VLP-06 — Tests de humo sobre las rutas reales.

## Humano (solo Lucio — la IA no puede)
- [ ] Construir la imagen Docker una vez para validar VLP-01: `cd nanocapsule-mvp && docker compose build`.
- [ ] **CIENCIA-1** — decidir `capsid.py` radio ±1 Å (IA recomienda restar). Ver ESTADO §4b.
- [ ] **CIENCIA-2** — decidir resolución de `sustratinaitor` (CG vs all-atom), al correr esa MD. Ver ESTADO §4b.
- [ ] **CIENCIA-3** — decidir protocolo de heat de `PackMan`, al correr esa MD. Ver ESTADO §4b.

## Hecho
- [x] Git inicial + monorepo publicado en GitHub (privado, cuenta najera-maldonado).
- [x] ESTADO.md: mapa auditable del proyecto real (diagnóstico, bugs, plan VLP-01…06).
- [x] Sistema de trabajo estilo residente: PENDIENTES.md + BITACORA.md + layout zellij `vlpstudio`.
