# ⚠️ SELLADO — hallazgos de una pasada previa (NO LEER todavía)

> **PARA EL REVISOR:** este archivo contiene **sospechas SIN VERIFICAR** de una auditoría
> previa. **No lo leas hasta haber completado tu propia auditoría independiente** de los
> motores (ver `REVISION_MOTORES.md`). Es solo para **cross-check al final** — comparar tu
> juicio contra el de la pasada anterior.
>
> **PUEDEN ESTAR EQUIVOCADAS. NO SON NORMA.** Lucio pidió expresamente una revisión desde
> cero, no confirmar esto. Si tu pasada contradice algo de aquí, tu evidencia manda —
> reporta la discrepancia.
>
> Todo lo de abajo se derivó SOLO leyendo el código del repo (no de resultados externos).
> Cada punto trae dónde mirar; **verifícalo tú, no lo asumas.**

---

## sustratinaitor — sospecha: resolución mixta (all-atom en sistema CG)

- `2_ligando_GYE/GYE_cg_manual.pdb` = **17 beads** (CG). Pero `GYE.pdb` (la que usa
  `3_empaquetado_packmol/packmol_input.inp`) = **144 átomos** (all-atom). El resultado
  `3J7L-GYE.pdb` tiene 144 átomos por GYE.
- `4_ensamblaje_y_simulacion/gensystem.leap`: `source leaprc.sirah` + `source leaprc.gaff2`
  + `loadmol2 GYE.mol2` (all-atom) + `solvateOct ... WT4BOX` (agua CG).
- **Verificar:** ¿es un multiescala intencional y válido, o se cableó la rama all-atom por
  error? El GYE de 17 beads parece construido-pero-no-usado. Comprobar si la MD arranca.
- Menor: comentario dice "0.15M NaCl" pero `addIonsRand NaW 0` solo neutraliza.

## Poromania — sospechas

- `scripts/1run_hole.sh`: la llamada a HOLE **no tiene `rseed`**. **Verificar:** corre HOLE
  dos veces sobre el mismo input; ¿da el mismo radio? (HOLE puede ser no-determinista.)
- `pore_analyzer.py` (`calculate_pore_vector`, ~línea 485): el eje del poro =
  `centroide − primer_residuo_seleccionado`. **Verificar** si eso es el eje de simetría real
  o un heurístico que puede caer fuera del canal.
- `scripts/3analizar_hole.py`: toma el mínimo global del radio sin validar canal degenerado.
- `calculate_pentamer_center` está definida dos veces y no se usa (código muerto).
- `5docking.sh`: `found_any` ya parece arreglado (~línea 123, VLP-02).
- Contexto: el Studio (`nanocapsule-mvp/src/services/pore.py`) es una versión más nueva de
  este análisis — compara ambas y verifica cuál generó los resultados en los que te apoyas.

## PackMan — sospechas

- **Calentamiento** (`archivos_dm_cg/heat1_0to50.in` … `heat6_250to300.in`): parecen
  parámetros all-atom en un sistema CG — `dt=0.002` (SIRAH usa 0.020), `ntc=2/ntf=2` (SHAKE
  en H, pero CG no tiene H), `cut=9.0` (SIRAH usa 12.0), `restraintmask='@CA,C,N,O'` (los
  beads SIRAH parecen llamarse GN/GC/GO, no CA/C/N/O → la máscara podría no restringir nada).
  `run_MD.sh` (~línea 128 y 176) los invoca. **Verificar:** compara contra los `.in` de
  referencia en `sirah_x2.3.../tutorial/`, y mira los `*_heat*.out`: ¿SHAKE tiró error?,
  ¿la estructura se mantuvo sana?
- `prod_md_WT4.in` tiene `nstlim=500` (10 ps, título "fast test"); `eq1_WT4.in` igual.
  **Verificar** si son stubs de prueba y cuál `nstlim` se usó de verdad.
- Positivo (verifícalo igual): `prod/em/eq` parecen coincidir con la referencia SIRAH
  (`dt=0.020`, `ntc=1/ntf=1`, `cut=12`, `chngmask=0`).
- Menor: mismo comentario "0.15M NaCl" ≠ código que en sustratinaitor.

## Packing (Studio) — sospechas (menores)

- `src/core/capsid.py`: el código hace `radio_colision + 1.0` (~línea 146) pero el docstring
  (~líneas 57-59) dice que el cambio importante fue pasar a `−1.0`. **Código ≠ docstring**
  (CIENCIA-1). Además el radio *reportado* (`radio_interno.txt`) es `+1`, mientras que
  `src/packing/parallel_packer.py` usa `packing_radius = internal_radius − collision_margin`
  (margin=2.0) → radio efectivo `−1`. **Verificar** la intención y reconciliar reporte vs uso.
- Positivo (de-riesga; verifícalo): PACKMOL incluye la cápside como estructura **fija**
  (`parallel_packer.py` ~260-263, tolerancia 2.0) → las enzimas quedan acotadas por la pared
  real aunque la esfera sea aproximada. Réplicas con semillas aleatorias = metodología correcta.
- `exclusion_radius=5.0` (`config/default.yaml`) es la perilla principal de capacidad —
  documéntala/valídala.

---

*Fin del archivo sellado. Recuerda: tu evidencia manda sobre esto.*
