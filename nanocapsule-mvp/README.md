# Nanocapsule Designer MVP

Sistema profesional para el diseño y empaquetamiento de enzimas terapéuticas en cápsides virales mediante optimización computacional.

## Arquitectura del Sistema

### Estructura Modular
```
nanocapsule-mvp/
├── src/
│   ├── core/           # Lógica de negocio principal
│   │   ├── capsid.py   # Manejo de cápsides y cálculo de radio
│   │   ├── cargo.py    # Manejo de enzimas y preparación
│   │   ├── config.py   # Gestión centralizada de configuración
│   │   └── experiment.py # Sistema de réplicas experimentales
│   ├── io/
│   │   └── structure_fetcher.py # Gestión de estructuras PDB
│   ├── packing/
│   │   └── packmol_engine.py    # Motor de empaquetamiento
│   └── web/
│       ├── app.py       # Backend Flask
│       └── templates/
│           └── index.html # Interface web con NGL.js
├── config/
│   └── default.yaml     # Configuración del sistema
├── Input/               # Estructuras de entrada
│   ├── Capsides/       # Cápsides virales
│   └── Enzimas/        # Enzimas terapéuticas
└── Output/             # Resultados generados
    ├── Experiments/    # Experimentos con réplicas
    └── Generated_PDBs/ # Estructuras empaquetadas
```

## Características Principales

### 1. Sistema de Empaquetamiento Molecular
- **Motor Packmol**: Optimización de posiciones moleculares con restricciones geométricas
- **Cálculo Automático de Radio Interno**: Análisis PyMOL para determinar espacio disponible
- **Validación de Colisiones**: Prevención de superposición molecular con exclusión de 10Å
- **Sistema de 7 Réplicas**: Múltiples intentos con selección del mejor resultado

### 2. Interfaz Web Interactiva
- **Visualización 3D en Tiempo Real**: Motor NGL.js integrado
- **Control de Transparencia**: Ajuste dinámico de opacidad de cápside
- **Visualización Interior**: Sistema de clipping para explorar el interior
- **Panel de Secuencias**: Visualización estilo PyMOL de cadenas y residuos

### 3. Gestión de Estructuras
- **Carga Dinámica**: Soporte para cualquier combinación cápside-enzima
- **Detección Automática**: Escaneo de directorios Input para estructuras disponibles
- **Asignación de Cadenas**: IDs únicos para diferenciación visual por colores

### 4. Sistema de Archivos
- **Anti-Basura**: Limpieza automática de archivos temporales
- **Descargas ZIP**: Empaquetado de resultados para el usuario
- **Organización Jerárquica**: Estructura clara de experimentos y réplicas

## Configuración del Sistema

### Parámetros de Empaquetamiento (config/default.yaml)
```yaml
packing:
  internal_radius_default: 90.0  # Radio interno por defecto
  collision_margin: 2.0          # Margen de colisión
  exclusion_radius: 10.0         # Distancia mínima entre enzimas
  tolerance: 2.0                 # Tolerancia Packmol
  max_violation_threshold: 0.05  # Umbral máximo de violación
```

### Parámetros de Motores
```yaml
engines:
  packmol:
    executable: 'packmol'
    timeout: 300
  pymol:
    headless: true
    quiet: true
```

## Flujo de Trabajo

### 1. Preparación de Estructuras
```python
# Cálculo de radio interno
capsid = Capsid("capside.pdb")
radius = capsid.calculate_internal_radius()

# Preparación de enzima
cargo = Cargo("enzima.pdb")
cargo.center_structure()
```

### 2. Empaquetamiento con Réplicas
```python
# Sistema de 7 réplicas
experiment = ExperimentManager("Output/Experiments")
best_result = experiment.run_experiment(
    capsid_file="capside.pdb",
    enzyme_file="enzima.pdb",
    n_replicas=7
)
```

### 3. Visualización Web
- Acceder a http://localhost:5001
- Seleccionar cápside y enzima
- Ajustar número de enzimas a empaquetar
- Visualizar resultado con controles interactivos

## Controles de Visualización

### Panel Principal
- **Carga de Estructuras**: Selección de cápside y enzima
- **Número de Enzimas**: Control deslizante (1-50)
- **Generar PDB**: Creación de estructura empaquetada

### Visualización Interior
- **Profundidad de Corte**: Control deslizante (0-100%)
- **Transparencia**: Ajuste de opacidad de cápside
- **Rotación Automática**: Activación de giro continuo

### Panel de Secuencias
- **Mostrar/Ocultar**: Toggle superior estilo PyMOL
- **Separación por Enzima**: Cada enzima con color único
- **Información Detallada**: Residuos, átomos, rangos

## Mejoras Implementadas

### Correcciones Técnicas
- Radio interno con sustracción de 1Å para margen de seguridad
- Recentrado automático de estructuras antes del cálculo
- Secuencia correcta de comandos PyMOL para unidades biológicas
- Prevención de colisiones con validación de distancias

### Optimizaciones de UI
- Eliminación completa de emojis del sistema
- Colores únicos por cadena/enzima
- Panel de secuencias con separación clara
- Controles simplificados de visualización

## API REST

### Endpoints Principales
```
GET  /api/structures        # Lista estructuras disponibles
GET  /api/radius/{capsid}   # Calcula radio interno
POST /api/generate_pdb      # Genera PDB empaquetado
POST /api/experiment/run    # Ejecuta experimento con réplicas
GET  /api/download/{exp_id} # Descarga resultados en ZIP
```

## Requisitos del Sistema

### Dependencias Python
- Flask >= 2.0
- PyMOL (pymol-open-source)
- NumPy
- BioPython
- PyYAML

### Software Externo
- Packmol (instalación del sistema)
- PyMOL (para cálculos geométricos)

## Instalación

```bash
# Clonar repositorio
git clone <repository>

# Instalar dependencias
pip install -r requirements.txt

# Instalar Packmol
sudo apt-get install packmol  # Linux
brew install packmol           # macOS

# Ejecutar servidor
cd src/web
python app.py
```

## Uso Básico

1. **Preparar Estructuras**:
   - Colocar cápsides en `Input/Capsides/`
   - Colocar enzimas en `Input/Enzimas/`

2. **Iniciar Servidor**:
   ```bash
   python src/web/app.py
   ```

3. **Acceder a Interface**:
   - Abrir navegador en http://localhost:5001

4. **Generar Empaquetamiento**:
   - Seleccionar estructuras
   - Ajustar parámetros
   - Generar y visualizar resultado

## Estadísticas del Sistema

- **Líneas de Código**: ~2,500 (refactorizado desde 1,113)
- **Módulos**: 8 componentes independientes
- **Cobertura**: Cápsides virales y enzimas terapéuticas
- **Performance**: 7 réplicas en <5 minutos típicamente

## Notas Técnicas

### Cálculo de Radio Interno
El sistema utiliza PyMOL para calcular el radio interno disponible:
1. Recentra la cápside en origen
2. Calcula centro de masa
3. Encuentra radio máximo de átomos
4. Resta 1Å de margen de seguridad

### Sistema de Réplicas
Cada experimento ejecuta 7 réplicas independientes:
- Diferentes semillas aleatorias
- Selección automática del mejor resultado
- Estadísticas de convergencia

### Prevención de Colisiones
- Exclusión radius: 10Å entre enzimas
- Validación pre-empaquetamiento
- Detección de superposiciones

## Licencia

MIT License - Software de investigación académica

## Autores

Sistema desarrollado para investigación en nanocápsulas terapéuticas.