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
│   ├── archivos de entrada de simulación:
│   │   ├── em1_WT4.in, em2_WT4.in         # Minimización de energía
│   │   ├── eq1_WT4.in, eq2_WT4.in         # Equilibración del sistema
│   │   ├── heat1_0to50.in ... heat6_250to300.in # Calentamiento gradual
│   │   ├── density_eq.in                   # Equilibración de densidad
│   │   ├── final_eq.in                     # Equilibración final
│   │   └── prod_md_WT4.in                  # Producción MD
│   ├── gensystem.leap                       # Script LEaP para generación del sistema
│   ├── run_MD.sh                           # Script maestro de ejecución MD
│   └── setup_universal.sh                  # Configuración universal del sistema
├── ReplicaExtra/                           # Simulaciones adicionales/réplicas
│   └── 1_1/                               # Réplica específica (sistema 1, réplica 1)
│       └── empaquetador/
│           └── enzimas_individuales/       # Enzimas separadas para análisis
├── Scripts de configuración general:
│   ├── configurar_simulacion.sh            # Configurador principal
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
2. **Minimización**: Dos etapas (em1, em2) para relajación inicial
3. **Calentamiento**: Gradual 0→300K en 6 etapas de 50K
4. **Equilibración**: Densidad, presión y equilibración final
5. **Producción**: Simulación MD de alta precisión

### 3. Sistema de Réplicas
- **Organización**: Estructura jerárquica para estudios estadísticos
- **Escalabilidad**: Soporte para múltiples condiciones y parámetros
- **Consistencia**: Mismos protocolos en todas las réplicas

## Flujo de Trabajo Principal

```
Estructuras PDB → Empaquetador → LEaP → Minimización → Calentamiento → Equilibración → Producción MD
```

Este sistema proporciona una plataforma automatizada para el estudio de sistemas de encapsulación enzimática mediante simulaciones de dinámica molecular coarse-grained.