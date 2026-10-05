# Diagrama de Estructura del Proyecto PackMan v.1.2 - Simulaciones de Dinámica Molecular

## Estructura General del Proyecto

```
PackMan.v.1.2/
├── archivos_dm_cg/                          # Archivos principales de dinámica molecular coarse-grained
│   ├── empaquetador/                        # Sistema de empaquetamiento molecular
│   │   ├── capside.pdb                      # Estructura del cápside viral
│   │   ├── capside_recentrada.pdb          # Cápside con centro ajustado
│   │   ├── enzima.pdb                       # Estructura de la enzima
│   │   ├── enzima_recentrada.pdb           # Enzima con centro ajustado
│   │   ├── 1calcula_radio_interno.py       # Cálculo del radio interno del cápside
│   │   ├── 2Empaquetador_Manual.py         # Empaquetamiento manual controlado
│   │   └── 2Empaquetador_Maximo.py         # Empaquetamiento óptimo automático
│   ├── archivos de entrada de simulación (patrón SIRAH tutorial/5):
│   │   ├── em1_WT4.in, em2_WT4.in         # Minimización (esqueleto restringido / libre)
│   │   ├── eq1_WT4.in                      # 5 ns NPT, todo el soluto restringido (2.4)
│   │   ├── eq2_WT4.in                      # 25 ns NPT, esqueleto GN,GO restringido (0.24)
│   │   └── prod_md_WT4.in                  # Producción NPT, trozos de 10 ns (10 → 100 ns)
│   ├── gensystem.leap                       # Script LEaP para generación del sistema
│   ├── run_MD.sh                           # Orquestador de las 5 etapas (reanudable)
│   ├── prod-q_gpu.bsub                     # Lanzador LSF de run_MD.sh
│   └── setup_universal.sh                  # Configuración universal del sistema
├── ReplicaExtra/                           # Simulaciones adicionales/réplicas
│   └── 1_1/                               # Réplica específica (sistema 1, réplica 1)
│       └── empaquetador/
│           └── enzimas_individuales/       # Enzimas separadas para análisis
├── Scripts de configuración general:
│   ├── verificar_protocolo_md.py           # Verificación estática de los .in vs referencia SIRAH
│   ├── convert_to_cg.sh                    # Conversor all-atom → CG
│   ├── copy_md_files.sh                    # Distribuidor de archivos MD
│   ├── fix_pdb_serial.py                   # Corrector de numeración PDB
│   ├── run_maestro.sh                      # Controlador maestro de simulaciones
│   ├── setup_1_1o.sh                       # Configuración sistema 1-objeto
│   └── setup_universal_md.sh               # Configuración MD universal
```

## Descripción de Componentes Principales

### 1. Sistema de Empaquetamiento Molecular
- **Propósito**: Posicionamiento óptimo de enzimas dentro del cápside viral
- **Algoritmos**: Manual (controlado) y automático (máximo empaquetamiento)
- **Geometría**: Cálculo preciso del radio interno para optimización espacial

### 2. Pipeline de Simulación MD
1. **Preparación**: LEaP genera topología y coordenadas del sistema
2. **Minimización**: Dos etapas (em1 con esqueleto restringido, em2 libre)
3. **Equilibración NPT**: eq1 (5 ns, todo el soluto restringido; arranca de 0 K bajo
   Langevin, sin etapa de calentamiento separada, como SIRAH) y eq2 (25 ns, esqueleto)
4. **Producción NPT**: trozos reiniciables de 10 ns con semilla propia (10 → 100 ns)

### 3. Sistema de Réplicas
- **Organización**: Estructura jerárquica para estudios estadísticos
- **Escalabilidad**: Soporte para múltiples condiciones y parámetros
- **Consistencia**: Mismos protocolos en todas las réplicas

## Flujo de Trabajo Principal

```
Estructuras PDB → Empaquetador → cgconv → LEaP → em1 → em2 → eq1 (5 ns) → eq2 (25 ns) → prod (10 × 10 ns)
```

Este sistema proporciona una plataforma automatizada para el estudio de sistemas de encapsulación enzimática mediante simulaciones de dinámica molecular coarse-grained.