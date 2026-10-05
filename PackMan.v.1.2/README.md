# PackMan v1.3

Motor de la **puerta 4 ("¿sobrevive?")** de [VLP Studio](../README.md): preparación y
protocolo de **dinámica molecular coarse-grained (SIRAH)** del sistema enzima-dentro-de-
cápside. Prepara el sistema (empaquetado + conversión a CG + generación con LEaP) y define
el protocolo MD completo (minimización → equilibración restringida → producción), tomado
de los `.in` oficiales de SIRAH.

> **Estado:** el protocolo `.in` está **verificado estáticamente** contra la referencia
> SIRAH (`python3 verificar_protocolo_md.py`), pero la **MD aún no se ha corrido** (no hay
> trayectorias ni `.dat` de análisis en el repo). Requiere AMBER + el campo de fuerza
> SIRAH instalados. La preparación del sistema (hidrógenos, `TER`, disulfuros) sigue
> pendiente: ver `PLAN_REPARACION_MD.md` fases 1 y 3 (rama
> `claude/packman-repair-plan-9c287t`). Es "publicable como ciencia" solo tras ejecutar
> y validar la MD.

## Flujo

1. **Empaquetado** (`archivos_dm_cg/empaquetador/`): calcula el radio interno de la
   cápside (`1calcula_radio_interno.py`) y coloca la enzima dentro
   (`2Empaquetador_Manual.py` / `2Empaquetador_Maximo.py`).
2. **Conversión a coarse-grained** (`convert_to_cg.sh`): all-atom → CG con el protocolo
   SIRAH. Uso: `./convert_to_cg.sh N_ENZIMAS`.
3. **Generación del sistema** (`gensystem.leap`): LEaP construye el sistema solvatado.
4. **Protocolo MD** (5 archivos `.in`, patrón `sirah_x2.3_24-07.amber/tutorial/5`):

   | Etapa | Archivo | Simula | Restricción posicional |
   |---|---|---|---|
   | Minimización 1 | `em1_WT4.in` | 5000 ciclos | 2.4 kcal/mol/Å² sobre `@GN,GO` |
   | Minimización 2 | `em2_WT4.in` | 5000 ciclos | ninguna |
   | Equilibración 1 (NPT, 0→300 K) | `eq1_WT4.in` | 5 ns | 2.4 sobre todo el soluto (`!:WT4,NaW,ClW`) |
   | Equilibración 2 (NPT) | `eq2_WT4.in` | 25 ns | 0.24 sobre `@GN,GO` |
   | Producción (NPT) | `prod_md_WT4.in` | 10 ns por trozo; `run_MD.sh` encadena 10 → 100 ns | ninguna |

   Todas las etapas: `dt = 20 fs`, `cut = 12 Å`, sin SHAKE, Langevin `gamma_ln = 50`,
   300 K, `chngmask = 0`, `skinnb = 5`. No hay etapa de calentamiento: SIRAH arranca
   `eq1` desde 0 K bajo Langevin, como en el tutorial oficial.
5. **Orquestación**: `run_MD.sh` (las 5 etapas, reanudable, semillas en `SEMILLAS.txt`),
   `prod-q_gpu.bsub` (lo lanza en cola LSF), `run_maestro.sh` (workflow completo),
   `setup_universal_md.sh`, `copy_md_files.sh`, `fix_pdb_serial.py` (corrige numeración PDB).
6. **Verificación estática**: `python3 verificar_protocolo_md.py` compara cada `.in`
   parámetro por parámetro con la referencia SIRAH y falla si divergen fuera de la lista
   de desvíos documentados (semillas fijas, `skinnb`, máscara de `eq1`, trozos de
   producción). Corre en CI. Si se cambia un `.in`, hay que cambiar esa lista a la vez.

## Requisitos

- **AMBER** (o motor equivalente para correr los `.in`) y **tLeaP**.
- **Campo de fuerza SIRAH** (no incluido; su propia licencia — ver
  [`THIRD_PARTY.md`](../THIRD_PARTY.md)).

## Documentación adicional

- `diagrama_archivos_dm.md` — estructura detallada de archivos.
- `texto_tesis_archivos_dm.md` — descripción en prosa (tesis).
- `CHANGELOG.md` / `VERSION` — versionado del motor (v1.3.0).

## Notas de reproducibilidad

- Semillas fijas: `ig = 100001` (eq1), `100002` (eq2), `100100 + k` para el trozo `k` de
  producción. `run_MD.sh` las anota en `SEMILLAS.txt`.
- La duración de producción se fija con `NCHUNKS` (trozos de 10 ns; 10 por defecto).
- La decisión `CIENCIA-3` (protocolo de calentamiento) quedó resuelta en v1.3.0: no hay
  etapa de calentamiento; se sigue el tutorial 5 de SIRAH. Diagnóstico en
  `AUDITORIA_MD.md` (rama `claude/audit-packman-dynamics-engine-52svym`) y plan en
  `PLAN_REPARACION_MD.md` (rama `claude/packman-repair-plan-9c287t`).
