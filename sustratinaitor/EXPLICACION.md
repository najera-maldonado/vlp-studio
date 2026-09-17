# sustratinaitor — colocación del sustrato (glucosilceramida) alrededor de la cápside

Recopilación de los archivos que intervinieron en el proceso de **construir el
ligando GYE (glucosilceramida) en representación coarse-grained y distribuirlo
alrededor de la cápside 3J7L** para el sistema `3J7L-GYE`. Deliberadamente
**no se incluyen los archivos de parametrización del campo de fuerzas SIRAH**
(`sirah_x2.3_24-07.amber/`, `leaprc.sirah`, `.lib`/`.frcmod` de la propia
fuerza SIRAH): esos son la librería genérica del force field, no algo
generado para este sistema en particular.

## Contexto general

El objetivo era generar una configuración inicial con la cápside viral 3J7L
(en CG/SIRAH) rodeada de 200 copias del sustrato glucosilceramida (GYE), para
después solvatar, ionizar y correr una simulación de MD coarse-grained. El
flujo tiene 4 etapas, reflejadas en las carpetas numeradas:

## 1_capside/

- **`3J7L_cg.pdb`**: estructura de la cápside 3J7L ya convertida a
  representación coarse-grained (131,820 átomos/beads). Es la molécula que
  se mantiene **fija** durante el empaquetado.

## 2_ligando_GYE/ — construcción del sustrato

La glucosilceramida no tenía parámetros CG predefinidos en SIRAH, así que se
hizo en dos pasos:

1. **Mapeo manual a CG** (`README_conversion_gye_cg.md`, `GYE_cg_manual.pdb`):
   como el script automático de SIRAH (`cgconv.pl`) falló por falta de
   parámetros para GYE, se mapeó la molécula a mano siguiendo las
   convenciones SIRAH (~4 carbonos por bead en cadenas alifáticas): 17 beads
   en total — 4 para la cabeza de glucosa (GC/GO), 2 de enlace (BGL/BCE), 5
   para la cadena de esfingosina (BC1–BCT) y 6 para el ácido graso
   (BF1–BF6). Las coordenadas de cada bead se derivaron del centro de masa
   de los átomos correspondientes en la estructura all-atom.

2. **Parametrización química con antechamber/GAFF2/AM1-BCC**
   (`sqm.in`, `sqm.out`, `sqm.pdb`, `ATOMTYPE.INF`, `ANTECHAMBER_AC.AC`,
   `ANTECHAMBER_AM1BCC.AC`): antechamber corre `sqm` para asignar cargas
   parciales AM1-BCC y tipos de átomo GAFF2 a la molécula. De ahí salen
   `GYE.mol2` (estructura + cargas) y `GYE.frcmod` (parámetros de enlaces/
   ángulos/diedros faltantes en GAFF2 estándar).

3. **Carga en tLeaP** (`convert.leap`, `GYE.log`): script que carga
   `GYE.mol2` + `GYE.frcmod` con `leaprc.gaff2`, y guarda la unidad como
   `GYE.off` (librería reutilizable) y `GYE.pdb` (coordenadas, la que
   realmente usa PACKMOL en el siguiente paso).

## 3_empaquetado_packmol/ — colocar el sustrato "alrededor"

Aquí está la pieza clave que responde a "cómo pusieron el sustrato alrededor
de la cápside":

- **`packmol_input.inp`**: input de PACKMOL.
  ```
  structure 3J7L_cg.pdb
    number 1
    center
    fixed 0. 0. 0. 0. 0. 0.
  end structure

  structure GYE.pdb
    number  200
    inside box -150.336 -147.174 -151.982 150.336 147.174 151.982
  end structure
  ```
  - La cápside se **centra en el origen y se fija** (no se mueve ni rota).
  - 200 copias de GYE se empaquetan dentro de una **caja cúbica** cuyas
    dimensiones (±150/147/152 Å) coinciden aproximadamente con el radio
    máximo de la cápside ya centrada (~142 Å). Es decir, la caja envuelve
    justo el volumen que ocupa la cápside.
  - PACKMOL optimiza las posiciones/orientaciones de las 200 moléculas de
    GYE para que **no se solapen** con los átomos fijos de la cápside
    (tolerancia de 2.0 Å), rellenando el espacio libre disponible dentro de
    esa caja — tanto en el exterior de la cápside como en su cavidad
    interna, según dónde haya hueco.
- **`packmol.log` / `packmol_run.log`**: bitácora de la optimización (número
  de moléculas, función de penalización por solapamiento bajando de
  ~61,000 a ~1,455 tras reubicar moléculas mal orientadas, etc.).
- **`3J7L-GYE.pdb`**: resultado final — cápside + 200 GYE ya distribuidos,
  sin agua ni iones todavía. Es el archivo que alimenta la siguiente etapa.

## 4_ensamblaje_y_simulacion/

- **`gensystem.leap`**: script de tLeaP que carga `3J7L-GYE.pdb` junto con
  el campo de fuerzas SIRAH (no incluido aquí) y GAFF2, calcula la carga
  del sistema, solvata con agua CG (WT4) en caja octaédrica truncada,
  añade contraiones (NaW), y guarda la topología/coordenadas finales
  (`3J7L-GYE_cg.prmtop`, `3J7L-GYE_cg.ncrst`).
- **`run_MD.sh`**: pipeline de minimización/equilibración con
  `pmemd.cuda` (em1 → em2 → eq1 → eq2) sobre el sistema ya solvatado.

## Resumen del truco

No hay un algoritmo "geométrico" sofisticado para poner el sustrato
alrededor de la cápside: se define una **caja del tamaño de la cápside**, se
**fija la cápside en el centro**, y se le pide a **PACKMOL** que acomode N
copias del ligando dentro de esa caja evitando choques con la cápside fija.
El resultado es una distribución empacada (no una capa/shell explícita)
limitada por la geometría de la propia cápside y el tamaño de caja elegido.
