# Pendientes — VLP Studio

> Lista viva. El pane "pendientes" del tablero zellij la muestra; edítala ahí con
> la tecla `e`, o con cualquier editor. Formato: `- [ ]` pendiente, `- [x]` hecho.
> El detalle y el orden de las tareas grandes vive en `ESTADO.md §6` (VLP-01…06);
> aquí solo el recordatorio de lo inmediato y lo que depende de ti (humano).

## Ahora
- [ ] **VLP-01 — Infra reproducible** (siguiente commit): RDKit en `requirements.txt`, healthcheck `/api/health` real, Docker que instale hole/vina/obabel. Ver ESTADO §6.
- [ ] Confirmar que el Studio arranca hoy (`cd nanocapsule-mvp && FLASK_DEBUG=0 python3 src/web/app.py`).

## Backlog (detalle en ESTADO.md §6)
- [ ] VLP-02 — Corregir los 4 bugs conocidos (5docking.sh, mismatch CG, capsid ±1 Å, heat*.in).
- [ ] VLP-03 — Partir `packing_service.py` por puerta.
- [ ] VLP-04 — Partir `studio.html` + portada EMBUDO.
- [ ] VLP-05 — Retirar fósiles (/classic, prototipos muertos, código muerto).
- [ ] VLP-06 — Tests de humo sobre las rutas reales.

## Humano (solo Lucio — la IA no puede)
- [ ] Instalar/verificar binarios científicos en el sistema: `hole`, `vina`, `idock`, `obabel`, `pymol`, `packmol` + `rdkit` (Python). Ver ESTADO §7.
- [ ] Decisión científica: en `sustratinaitor`, ¿el sistema va todo coarse-grained (rehacer el empaquetado con `GYE_cg_manual.pdb`, 17 beads) o todo all-atom? Hoy es híbrido incoherente.
- [ ] Decisión científica: en `capsid.py`, el radio interno ¿es colisión +1 Å o −1 Å? (el código y el docstring se contradicen).

## Hecho
- [x] Git inicial + monorepo publicado en GitHub (privado, cuenta najera-maldonado).
- [x] ESTADO.md: mapa auditable del proyecto real (diagnóstico, bugs, plan VLP-01…06).
- [x] Sistema de trabajo estilo residente: PENDIENTES.md + BITACORA.md + layout zellij `vlpstudio`.
