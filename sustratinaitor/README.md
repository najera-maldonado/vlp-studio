# sustratinaitor

Construye el **sustrato glucosilceramida (GYE)** en representación coarse-grained (SIRAH)
y lo **distribuye alrededor de la cápside** (3J7L) para preparar una simulación de
dinámica molecular. Complementa la [puerta 4](../README.md) aportando el sistema
cápside-más-sustrato.

> **Estado:** etapas 1–3 hechas (`3J7L-GYE`, cápside CG rodeada de 200 copias de GYE);
> **etapa 4 (solvatar + correr MD) NO ejecutada.** Ver `EXPLICACION.md` para el detalle
> completo. Los archivos de parametrización genéricos de SIRAH **no** se incluyen (son la
> librería del force field, no algo generado para este sistema).

## Etapas (carpetas numeradas)

1. **`1_capside/`** — cápside 3J7L ya convertida a CG (`3J7L_cg.pdb`, ~131.820 beads).
   Se mantiene fija durante el empaquetado.
2. **`2_ligando_GYE/`** — construcción del sustrato: GYE no tenía parámetros CG en SIRAH,
   así que se mapeó a mano a 17 beads (glucosa + enlace + esfingosina + ácido graso) y se
   parametrizó con antechamber/GAFF2/AM1-BCC (`GYE.mol2`, `GYE.frcmod`).
3. **`3_empaquetado_packmol/`** — Packmol coloca 200 copias de GYE alrededor de la cápside
   → sistema `3J7L-GYE`.
4. **`4_ensamblaje_y_simulacion/`** — solvatación, ionización y MD (pendiente de correr).

## Requisitos

- **Packmol**, **antechamber/AmberTools**, y el **campo de fuerza SIRAH** (no incluido; su
  propia licencia — ver [`THIRD_PARTY.md`](../THIRD_PARTY.md)).

## Notas de reproducibilidad

Cabo suelto conocido (ver `CIENCIA-2` en [`ESTADO.md`](../ESTADO.md) §4b): el empaquetado
mezcla all-atom y CG en algunos pasos; decidir la resolución (CG vs all-atom) al correr la
MD. Detalle completo en `EXPLICACION.md`.
