# Changelog — PackMan (dinámica molecular SIRAH)

Versionado independiente por motor. Formato: [Keep a Changelog]. Tags: `packman/vX.Y.Z`.

## [1.3.0] — 2026-10-05
Reparación del protocolo MD según `AUDITORIA_MD.md` (rama
`claude/audit-packman-dynamics-engine-52svym`) y `PLAN_REPARACION_MD.md` paso P5 (rama
`claude/packman-repair-plan-9c287t`). Cierra CIENCIA-3. Solo el protocolo; la preparación
del sistema (hidrógenos, `TER`, disulfuros; MD-02/03/07) sigue pendiente (plan, fases 1 y 3).
- **Eliminados** los 8 `.in` all-atom (`heat1..6`, `density_eq`, `final_eq`): `dt=2 fs`,
  SHAKE, `cut=9`, `gamma_ln=2` y máscaras `@CA,C,N,O` que no seleccionan ningún bead SIRAH
  (MD-04, MD-05). SIRAH no tiene etapa de calentamiento para proteínas: `eq1` arranca de 0 K.
- **Reescritos** los 5 `.in` copiando `sirah_x2.3_24-07.amber/tutorial/5` línea a línea.
  Duraciones reales: `eq1` 5 ns, `eq2` 25 ns, producción 10 ns por trozo (antes 10 ps cada
  una con títulos de 15 y 35 ns; MD-01). Restricciones posicionales de la referencia:
  `em1` 2.4 sobre `@GN,GO`, `eq1` 2.4 sobre todo el soluto, `eq2` 0.24 sobre `@GN,GO`
  (antes `ntr=0`; MD-06). Títulos ASCII ≤ 80 caracteres que dicen cuánto simula cada archivo.
- Desvíos respecto a la referencia, todos explícitos en `verificar_protocolo_md.py`:
  semillas fijas (`ig` 100001 / 100002 / 100100+k; MD-08), `skinnb=5` del tutorial 7 para
  GPU con ~400 k partículas (MD-14), máscara de `eq1` `!:WT4,NaW,ClW` en vez de `:1-46`
  (independiente del número de enzimas), y producción en trozos de 10 ns en vez de 1 µs.
- **`run_MD.sh`** reescrito: 5 etapas, `eq1` parte de `em2` (MD-11), producción en
  `NCHUNKS` trozos con `ig` propio y `SEMILLAS.txt`, reanudable, `DRY_RUN=1` para
  verificarlo sin AMBER. `prod-q_gpu.bsub` lanza `run_MD.sh` en vez de un `pmemd.cuda`
  suelto sobre un sistema que ningún script generaba (MD-18).
- **Retirado `configurar_simulacion.sh`**: generaba `eq1` con `':*&!@H='` (restringía
  también WT4 e iones; MD-09), `gamma_ln=5` y no borraba los `.in` all-atom (MD-10). Los 5
  `.in` estáticos son la única fuente de verdad.
- **Nuevo `verificar_protocolo_md.py`** (stdlib, sin AMBER): compara cada `.in` parámetro
  por parámetro con su referencia SIRAH y falla ante cualquier divergencia no listada;
  además comprueba marcadores all-atom, coherencia título↔`nstlim·dt`, que los nombres de
  las máscaras existan en las librerías SIRAH y la cadena `-c/-ref` de `run_MD.sh`. Corre
  en el job `engines` del CI.

## [1.2.0] — 2026-09-17
Versión heredada del nombre de carpeta (`.v.1.2`), ahora en archivo.
- Sin cambios de código esta sesión.
- Motor de la puerta "Sobrevive": empaquetado → CG SIRAH → tleap → pmemd.cuda → cpptraj.
  El subsistema `analisis/` produce los `.dat` (frame, valor) que consume la pestaña MD.
- Estado: solo el empaquetado tiene evidencia de ejecución; la MD NO se ha corrido.
- Decisión pendiente (CIENCIA-3, ESTADO §4b): los `heat*.in` estáticos son all-atom
  sobre topología CG; `configurar_simulacion.sh` ya genera los correctos en CG.
