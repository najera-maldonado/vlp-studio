# Software de terceros (motores externos)

VLP Studio (el código propio) se distribuye bajo licencia **GNU AGPLv3 o posterior**
(ver `LICENSE`). Ese código **invoca** motores científicos de terceros como procesos
externos; NO los incorpora ni los redistribuye. Cada motor conserva su propia licencia.
Este archivo las lista para transparencia y para dejar claro qué debes obtener por tu cuenta.

Llamar a un binario externo por línea de comandos no crea obra derivada, por lo que la
licencia AGPLv3 del código propio no impone obligaciones sobre esos motores ni ellos sobre
él; AGPLv3 es además compatible con GPL/LGPL.

## Motores incluidos en la imagen Docker (redistribuibles)

| Motor | Uso | Licencia | Fuente |
|-------|-----|----------|--------|
| Packmol | Empaquetamiento molecular | libre (MIT-like) | https://m3g.github.io/packmol/ |
| PyMOL (open-source) | Geometría, mutagénesis | permisiva (BSD-like, Schrödinger) | https://github.com/schrodinger/pymol-open-source |
| Open Babel | Preparación de ligandos | GPL-2.0 | https://openbabel.org/ |
| AutoDock Vina | Docking | Apache-2.0 | https://vina.scripps.edu/ |
| RDKit | Química (SMILES, geometría 3D) | BSD-3-Clause | https://www.rdkit.org/ |

## Motores que NO se distribuyen (los aporta el usuario)

Su licencia **no permite redistribuirlos** o requiere aceptación individual. Obténlos tú
mismo bajo sus términos y móntalos en el contenedor / ponlos en el PATH (ver README).

| Motor | Uso | Licencia | Fuente |
|-------|-----|----------|--------|
| **HOLE** | Perfil de poro (Pac-Pore) | **académica, no comercial, NO redistribuible** | https://www.holeprogram.org/ |
| **idock** | Docking alternativo | verificar términos antes de usar | (fuente del autor) |
| **NetMHCIIpan** | De-inmunización (Puerta 3) | **académica DTU, no comercial, NO redistribuible** | https://services.healthtech.dtu.dk/services/NetMHCIIpan-4.3/ |
| **GROMACS** | MD (Puerta 4) | LGPL-2.1 | https://www.gromacs.org/ |
| **SIRAH** | Campo de fuerza CG (Puerta 4) | académica; verificar términos | http://www.sirahff.com/ |

> Sin HOLE no funciona la puerta Pac-Pore; sin GROMACS/SIRAH no corre la Puerta 4
> (Análisis MD); NetMHCIIpan es opcional (de-inmunización). El resto del Studio
> (empaquetamiento, docking con Vina) funciona sin ellos.
