# PackMan v1.2

Motor de la **puerta 4 ("¿sobrevive?")** de [VLP Studio](../README.md): preparación y
protocolo de **dinámica molecular coarse-grained (SIRAH)** del sistema enzima-dentro-de-
cápside. Prepara el sistema (empaquetado + conversión a CG + generación con LEaP) y define
el protocolo MD completo (minimización → calentamiento → equilibración → producción).

> **Estado:** scripts y protocolo **completos**; la **MD aún no se ha corrido** (no hay
> trayectorias ni `.dat` de análisis en el repo). Requiere AMBER + el campo de fuerza
> SIRAH instalados. Es "publicable como ciencia" solo tras ejecutar y validar la MD.

## Flujo

1. **Empaquetado** (`archivos_dm_cg/empaquetador/`): calcula el radio interno de la
   cápside (`1calcula_radio_interno.py`) y coloca la enzima dentro
   (`2Empaquetador_Manual.py` / `2Empaquetador_Maximo.py`).
2. **Conversión a coarse-grained** (`convert_to_cg.sh`): all-atom → CG con el protocolo
   SIRAH. Uso: `./convert_to_cg.sh N_ENZIMAS`.
3. **Generación del sistema** (`gensystem.leap`): LEaP construye el sistema solvatado.
4. **Protocolo MD** (archivos `.in`): minimización (`em1/em2`), calentamiento gradual
   (`heat1_0to50` … `heat6_250to300`), equilibración (`eq1/eq2`, `density_eq`,
   `final_eq`) y producción (`prod_md_WT4`).
5. **Orquestación**: `configurar_simulacion.sh` (configurador interactivo),
   `setup_universal_md.sh`, `run_maestro.sh` (workflow completo), `copy_md_files.sh`,
   `fix_pdb_serial.py` (corrige numeración PDB).

## Requisitos

- **AMBER** (o motor equivalente para correr los `.in`) y **tLeaP**.
- **Campo de fuerza SIRAH** (no incluido; su propia licencia — ver
  [`THIRD_PARTY.md`](../THIRD_PARTY.md)).

## Documentación adicional

- `diagrama_archivos_dm.md` — estructura detallada de archivos.
- `texto_tesis_archivos_dm.md` — descripción en prosa (tesis).
- `CHANGELOG.md` / `VERSION` — versionado del motor (v1.2.0).

## Notas de reproducibilidad

Antes de correr la MD queda por decidir el **protocolo de calentamiento** (ver
`CIENCIA-3` en [`ESTADO.md`](../ESTADO.md) §4b).
