# 🧬 Pipeline Automatizado de Análisis de Poros Proteicos y Docking Molecular

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org)
[![PyMOL](https://img.shields.io/badge/PyMOL-2.5%2B-green)](https://pymol.org)
[![License](https://img.shields.io/badge/License-AGPLv3-blue.svg)](../LICENSE)

Pipeline completo automatizado para el análisis de poros proteicos, generación sistemática de mutantes, análisis geométrico con HOLE2 y docking molecular desde códigos SMILES.

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Instalación](#-instalación)
- [Uso Rápido](#-uso-rápido)
- [Pipeline Completo](#-pipeline-completo)
- [Estructura de Archivos](#-estructura-de-archivos)
- [Ejemplos](#-ejemplos)
- [Documentación](#-documentación)
- [Contribuciones](#-contribuciones)
- [Citas](#-citas)

## ✨ Características

### 🎯 **Análisis Interactivo de Poros**
- Interfaz PyMOL interactiva para identificación de poros
- Selección automática de residuos por distancia radial
- Detección de posiciones comunes en todas las cadenas proteicas
- Visualización en tiempo real con esferas ajustables

### 🧬 **Generación Sistemática de Mutantes**
- Mutagénesis automatizada basada en análisis de poro
- Generación de mutantes aleatorios o dirigidos
- Aplicación simultánea en todas las cadenas proteicas
- Estructuras PDB optimizadas listas para análisis

### 📊 **Análisis Cuantitativo HOLE2**
- Cálculo automático de perfiles de poro
- Métricas geométricas (radio mínimo, constriccioness)
- Gráficos publication-ready
- Procesamiento en paralelo de múltiples mutantes

### 🧪 **Docking Molecular desde SMILES**
- Conversión automática SMILES → estructura 3D → PDBQT
- Optimización geométrica robusta para moléculas complejas
- Docking automatizado en todos los mutantes
- Análisis comparativo de afinidades

### 📈 **Visualización y Reportes**
- Gráficos de correlación poro-afinidad
- Imágenes de superficies electrostáticas
- Trípticos comparativos automáticos
- Exportación en múltiples formatos

## 🛠️ Instalación

### Requisitos del Sistema

```bash
# Sistema operativo: Linux/macOS
# Python: 3.8 o superior
# Memoria: 8 GB RAM mínimo, 16 GB recomendado
# Espacio: 5 GB disponibles
```

### Dependencias Principales

```bash
# PyMOL (interfaz gráfica y mutagénesis)
conda install -c conda-forge pymol

# RDKit (procesamiento de SMILES)
conda install -c conda-forge rdkit

# OpenBabel (conversión de formatos químicos)
sudo apt-get install openbabel

# HOLE2 (análisis de poros)
# Descargar de: http://www.holeprogram.org/

# iDock (docking molecular)
# Compilar desde: https://github.com/HongjianLi/idock
```

### Paquetes Python Adicionales

```bash
pip install pandas matplotlib numpy pathlib
```

### Verificación de Instalación

```bash
python -c "import pymol, rdkit, pandas; print('✅ Todas las dependencias instaladas')"
which hole && echo "✅ HOLE2 disponible"
which idock && echo "✅ iDock disponible"
```

## 🚀 Uso Rápido

### Pipeline Completo en 3 Comandos

```bash
# 1. Análisis de poro y generación de mutantes
python visualize_pore.py

# 2. Docking con ligando desde SMILES
python smiles_docking_pipeline.py 'CC(=O)OC1=CC=CC=C1C(=O)O' --ligand-name aspirina

# 3. Visualización de resultados
ls mutants/*/docking/estructuras/ligand_best_*.pdb
```

### Ejemplo con Glucosilceramida

```bash
# SMILES de glucosilceramida (ligando complejo de 125 átomos)
python smiles_docking_pipeline.py 'CCCCCCCCCCCCCCC(C(=O)N[C@@H](CO[C@H]1[C@@H]([C@H]([C@@H]([C@H](O1)CO)O)O)O)[C@@H](/C=C/CC/C=C/CCCCCCCCC)O)O' --ligand-name glucosilceramida
```

## 📋 Pipeline Completo

### Paso 0: Análisis de Poro
```bash
# Interactivo con GUI PyMOL
python visualize_pore.py
# Selecciona radio de esfera → identifica residuos → genera mutantes

# Automatizado (para pruebas)
python automated_test.py  # 9Å radius, 5 mutantes aleatorios
```

### Paso 1: Generación de Mutantes
```bash
pymol -cq 1crear_mutantes.pml
# Genera: mutants/mut_*/receptor.pdb + scripts
```

### Paso 2-4: Análisis Estructural
```bash
./2cargarsuperficies.sh     # Superficies moleculares
./3copiar_scripts.sh        # Scripts auxiliares (opcional)
./4generarhole.sh          # Análisis HOLE2 paralelo
```

### Paso 5: Docking Molecular
```bash
# Desde SMILES (recomendado)
python smiles_docking_pipeline.py 'SMILES_CODE' --ligand-name nombre

# Manual
python generate_ligand_from_smiles.py 'SMILES_CODE' -o ligando.pdbqt
cp ligando.pdbqt ligand.pdbqt
./5docking.sh
```

### Paso 6-7: Visualización y Reportes
```bash
./5imagenescargasporo.sh    # Imágenes APBS
./6generador_triptico.sh    # Trípticos finales
```

### Pipeline Automático Completo
```bash
./clickaqui.sh  # Ejecuta pasos 1-7 (sin docking)
```

## 📁 Estructura de Archivos

```
SOFTWARE-ubicador poro/
├── 📄 poronatural.pdb              # Estructura proteica inicial
├── 🔧 Scripts principales
│   ├── pore_analyzer.py            # Analizador interactivo
│   ├── visualize_pore.py           # Launcher con opciones
│   ├── generate_ligand_from_smiles.py  # Generador de ligandos
│   └── smiles_docking_pipeline.py  # Pipeline completo
├── 📜 Scripts de pipeline
│   ├── 1crear_mutantes.pml         # Generación de mutantes
│   ├── 2cargarsuperficies.sh       # Superficies
│   ├── 3copiar_scripts.sh          # Distribución scripts
│   ├── 4generarhole.sh             # Análisis HOLE
│   ├── 5docking.sh                 # Docking molecular
│   ├── 5imagenescargasporo.sh      # Visualización APBS
│   ├── 6generador_triptico.sh      # Reportes finales
│   └── clickaqui.sh                # Pipeline automático
├── 📂 mutants/                     # Resultados mutantes
│   ├── WT.pdb                      # Wild-type
│   └── mut_*/                      # Cada mutante
│       ├── receptor.pdb            # Estructura mutante
│       ├── scripts/                # Scripts análisis
│       ├── hole/resultados/        # Resultados HOLE
│       │   ├── hole_profile.tsv    # Datos cuantitativos
│       │   └── perfil_*.png        # Gráficos
│       └── docking/                # Resultados docking
│           ├── Results/poses.txt   # Scores afinidad
│           └── estructuras/        # Poses 3D
└── 📂 scripts/                     # Scripts base
    ├── 1run_hole.sh                # Ejecución HOLE
    ├── 2out_tsv.py                 # Conversión datos
    ├── 3analizar_hole.py           # Análisis perfiles
    └── vdwradii.lib                # Parámetros HOLE
```

## 🧪 Ejemplos

### Ejemplo 1: Análisis Interactivo

```bash
# Iniciar análisis
python visualize_pore.py
# Seleccionar: 1 (PyMOL GUI)

# En el prompt:
# Ingrese radio: 8.0
# Comando: mutantes
# Tipo: 2 (aleatoria)
# Número de mutantes: 5
# Mutaciones por mutante: 2
```

### Ejemplo 2: Ligandos de Ejemplo

```bash
# Ver ejemplos disponibles
python test_smiles_example.py

# Aspirina
python smiles_docking_pipeline.py 'CC(=O)OC1=CC=CC=C1C(=O)O' --ligand-name aspirina

# Ibuprofeno
python smiles_docking_pipeline.py 'CC(C)CC1=CC=C(C=C1)C(C)C(=O)O' --ligand-name ibuprofeno

# Cafeína
python smiles_docking_pipeline.py 'CN1C=NC2=C1C(=O)N(C(=O)N2C)C' --ligand-name cafeina
```

### Ejemplo 3: Análisis de Resultados

```bash
# Ver mejores scores
grep "🏆" mutants/*/mut_*.log

# Visualizar mejores poses
pymol mutants/mut_*/docking/estructuras/ligand_best_*.pdb

# Analizar correlaciones
python -c "
import pandas as pd
import matplotlib.pyplot as plt

# Cargar datos de ejemplo (implementar según necesidades)
# datos = pd.read_csv('resultados_compilados.csv')
# plt.scatter(datos['radio_min'], datos['mejor_score'])
# plt.xlabel('Radio mínimo HOLE (Å)')
# plt.ylabel('Score docking (kcal/mol)')
# plt.show()
"
```

## 📚 Documentación

### Parámetros Principales

| **Parámetro** | **Descripción** | **Valores típicos** |
|---------------|-----------------|-------------------|
| `radio_esfera` | Radio análisis poro | 5-15 Å |
| `num_mutantes` | Número mutantes | 5-20 |
| `muts_por_mutante` | Mutaciones por estructura | 1-5 |
| `ph` | pH protonación | 7.4 (fisiológico) |
| `max_conformaciones` | Poses docking | 100-1000 |

### Formatos de Entrada

- **Estructura proteica**: PDB format
- **Ligandos**: Códigos SMILES
- **Configuración**: Archivos .conf para parámetros avanzados

### Formatos de Salida

- **Estructuras**: PDB, PDBQT
- **Datos**: TSV, CSV
- **Gráficos**: PNG, PDF
- **Reportes**: HTML, Markdown

## 🤝 Contribuciones

### Cómo Contribuir

1. **Fork** el repositorio
2. **Crear** branch para nueva funcionalidad
3. **Implementar** cambios con tests
4. **Documentar** nuevas funciones
5. **Enviar** pull request

### Áreas de Desarrollo

- 🔬 Nuevos algoritmos de análisis de poro
- 🧬 Integración con más herramientas de docking
- 📊 Análisis estadístico avanzado
- 🖥️ Interfaz web/GUI standalone
- 🚀 Optimización de rendimiento

### Reportar Issues

- 🐛 **Bugs**: Descripción detallada + logs
- 💡 **Sugerencias**: Casos de uso + beneficios
- 📖 **Documentación**: Secciones confusas/faltantes

## 📄 Licencia

Parte de VLP Studio, bajo **GNU AGPLv3 o posterior**. Ver [LICENSE](../LICENSE) (raíz del
monorepo) y [THIRD_PARTY.md](../THIRD_PARTY.md). Copyright (C) 2026 najera-maldonado.

## 📚 Citas

Si usas este pipeline en tu investigación, por favor cita:

```bibtex
@software{pipeline_poros_2024,
  title={Pipeline Automatizado de Análisis de Poros Proteicos y Docking Molecular},
  author={[Tu nombre]},
  year={2024},
  url={https://github.com/[usuario]/pipeline-poros},
  note={Herramienta integrada para mutagénesis sistemática y docking desde SMILES}
}
```

### Referencias de Herramientas Utilizadas

- **HOLE**: Smart, O.S., et al. *J. Mol. Graph.* **14**, 354-360 (1996)
- **PyMOL**: Schrödinger, LLC. *PyMOL Molecular Graphics System*
- **RDKit**: Landrum, G. *RDKit: Open-source cheminformatics*
- **AutoDock**: Morris, G.M., et al. *J. Comput. Chem.* **30**, 2785-2791 (2009)

## 🚀 Roadmap

### Versión Actual (v1.0)
- ✅ Pipeline básico funcional
- ✅ Integración SMILES → Docking
- ✅ Análisis HOLE automatizado
- ✅ Mutantes sistemáticos

### Próximas Versiones

#### v1.1 (2-3 meses)
- 🔄 Interfaz web Flask/Django
- 📊 Dashboard interactivo de resultados
- 🧪 Validación con datos experimentales
- 📈 Análisis estadístico integrado

#### v1.2 (6 meses)
- ☁️ Implementación en la nube
- 🤖 Machine learning para predicciones
- 🔗 APIs REST para integración
- 📱 Aplicación móvil para visualización

#### v2.0 (1 año)
- 🧬 Soporte para complejos proteína-proteína
- 🔬 Integración con AlphaFold
- 🚀 Optimización GPU/CPU paralela
- 📚 Base de datos de resultados públicos

---

## 💬 Soporte y Contacto

- **Issues**: [GitHub Issues](https://github.com/[usuario]/pipeline-poros/issues)
- **Documentación**: [Wiki completa](https://github.com/[usuario]/pipeline-poros/wiki)
- **Email**: [tu-email@universidad.edu]
- **ORCID**: [0000-0000-0000-0000]

---

*Desarrollado para la investigación en biología estructural computacional y descubrimiento de fármacos* 🧬💊