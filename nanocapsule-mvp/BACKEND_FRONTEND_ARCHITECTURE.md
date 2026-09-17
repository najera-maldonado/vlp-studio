# Arquitectura de Comunicación Backend-Frontend

## Resumen General

El sistema utiliza una arquitectura REST tradicional con Flask (backend) y JavaScript vanilla (frontend). No hay WebSockets ni polling, toda la comunicación es mediante llamadas HTTP síncronas request-response.

## Stack Tecnológico

### Backend (Flask)
- **Framework**: Flask 2.3.2
- **Puerto**: 5000
- **Host**: 0.0.0.0 (accesible desde toda la red)
- **Modo**: Debug habilitado en desarrollo
- **CORS**: Habilitado (`Access-Control-Allow-Origin: *`)

### Frontend
- **Tecnología**: HTML5 + JavaScript vanilla (sin frameworks)
- **Visualización 3D**: NGL.js v2.0.0-dev.37
- **Comunicación**: Fetch API nativa
- **UI**: CSS personalizado estilo científico

## Endpoints API y Flujo de Datos

### 1. Carga de Biblioteca de Estructuras

#### GET `/api/library/combinations`
**Frontend → Backend:**
- Llamada al cargar la página (`loadLibrary()`)

**Backend → Frontend:**
```json
{
  "capsides": ["MS2", "CCMV", "BMV", "QB"],
  "enzymes": ["1OGS", "2XYZ", ...],
  "total_combinations": 16
}
```

**Uso en Frontend:**
- Popula los selectores `<select>` de cápsides y enzimas
- Actualiza contador de combinaciones disponibles

---

### 2. Información de Estructura Individual

#### GET `/api/structure/{type}/{name}`
**Frontend → Backend:**
- Se llama cuando el usuario selecciona una cápside o enzima
- Parámetros: `type` = "capside" o "enzima", `name` = nombre del archivo

**Backend → Frontend:**
```json
{
  "name": "MS2",
  "type": "capside",
  "path": "/api/file/capside/MS2",
  "atoms": 15420,
  "size_bytes": 1048576,
  "size_mb": 1.0
}
```

**Uso en Frontend:**
- Muestra info en los divs `capsid-info` y `enzyme-info`
- Formato: nombre, número de átomos, tamaño en MB

---

### 3. Cálculo de Radio Interno

#### POST `/api/capsid/radius`
**Frontend → Backend:**
```json
{
  "capsid": "MS2"
}
```

**Backend → Frontend:**
```json
{
  "status": "success",
  "capsid": "MS2",
  "internal_radius": 89.5,
  "radius_file": "radio_interno.txt",
  "message": "Radio interno calculado: 89.5 Å"
}
```

**Proceso Backend:**
1. Invoca PyMOL para calcular radio
2. Centra la cápside en origen
3. Detecta colisión con pseudoátomo
4. Resta 1Å de margen de seguridad
5. Guarda en `radio_interno.txt`

**Uso en Frontend:**
- Almacena en variable global `calculatedRadius`
- Habilita botón de vista previa
- Muestra resultado en `radius-result` div

---

### 4. Vista Previa con Enzimas (Generación Rápida)

#### POST `/api/preview/enzymes`
**Frontend → Backend:**
```json
{
  "capsid": "MS2",
  "enzyme": "1OGS",
  "n_enzymes": 10,
  "radius": 89.5,
  "save_file": true
}
```

**Backend → Frontend:**
- Retorna archivo PDB completo como text/plain
- Headers incluyen nombre de archivo sugerido

**Proceso Backend:**
1. Lee estructuras originales de `Input/`
2. Genera posiciones aleatorias respetando `exclusion_radius` (5Å)
3. Asigna chain IDs únicos a cada enzima
4. Combina cápside + enzimas en un solo PDB
5. Opcionalmente guarda en `Output/Generated_PDBs/`

**Uso en Frontend:**
- Carga el PDB directamente en NGL viewer
- Renderiza cápside como superficie transparente
- Colorea cada enzima con color único

---

### 5. Experimento con Réplicas (Packmol)

#### POST `/api/experiment/run`
**Frontend → Backend:**
```json
{
  "capsid": "MS2",
  "enzyme": "1OGS",
  "n_replicas": 10,
  "n_enzymes": null,  // null = máximo, número = manual
  "run_packing": true
}
```

**Backend → Frontend (si run_packing=true):**
```json
{
  "status": "completed",
  "success": true,
  "best_result": 25,
  "mean": 23.5,
  "stdev": 1.2,
  "n_replicas_success": 9,
  "n_replicas_total": 10,
  "experiment_dir": "Output/Experiments/2024...",
  "best_file": "replica_3/packed.pdb",
  "message": "Experimento completado con sistema optimizado. Mejor resultado: 25 enzimas"
}
```

**Proceso Backend:**
1. Crea directorio de experimento con timestamp
2. Ejecuta 7-10 réplicas en paralelo
3. Cada réplica usa Packmol con semilla diferente
4. Algoritmo incremental busca máximo empaquetamiento
5. Selecciona mejor resultado (más enzimas)
6. Genera estadísticas consolidadas

---

### 6. Descarga de Resultados

#### POST `/api/download/experiment-zip`
**Frontend → Backend:**
```json
{
  "capsid": "MS2",
  "enzyme": "1OGS",
  "experiment_type": "manual" | "maximum"
}
```

**Backend → Frontend:**
- Retorna archivo ZIP como application/zip
- Contiene:
  - `inputs/`: Estructuras originales
  - `generated_pdbs/`: PDBs generados (manual)
  - `replica_*/`: Resultados de réplicas (maximum)
  - `README.txt`: Documentación del experimento

---

### 7. Gestión de Archivos Generados

#### GET `/api/files/generated`
**Backend → Frontend:**
```json
{
  "files": [
    {
      "name": "MS2_10enzimas_1OGS_20240408_143022.pdb",
      "size": 2097152,
      "size_mb": 2.0,
      "modified": "2024-04-08 14:30:22",
      "path": "Output/Generated_PDBs/..."
    }
  ],
  "count": 5,
  "total_size_mb": 10.5
}
```

#### POST `/api/files/cleanup`
**Frontend → Backend:**
```json
{
  "days_old": 7
}
```

**Backend → Frontend:**
```json
{
  "message": "Limpieza completada",
  "removed": 3,
  "removed_files": ["file1.pdb", "file2.pdb"],
  "cutoff_days": 7
}
```

---

## Flujo de Trabajo Típico del Usuario

1. **Inicialización**
   - Página carga → `loadLibrary()` → GET `/api/library/combinations`
   - Selectores poblados con estructuras disponibles

2. **Selección de Estructuras**
   - Usuario selecciona cápside → GET `/api/structure/capside/MS2`
   - Usuario selecciona enzima → GET `/api/structure/enzima/1OGS`
   - Se muestran detalles (átomos, tamaño)

3. **Cálculo de Radio**
   - Click "Calcular Radio" → POST `/api/capsid/radius`
   - PyMOL calcula radio interno
   - Resultado mostrado y guardado

4. **Vista Previa Rápida**
   - Click "Vista Previa" → POST `/api/preview/enzymes`
   - Backend genera PDB con posiciones aleatorias
   - NGL.js renderiza en 3D inmediatamente

5. **Experimento Completo**
   - Click "Ejecutar Experimento" → POST `/api/experiment/run`
   - Backend ejecuta 7-10 réplicas con Packmol
   - Muestra estadísticas del mejor resultado

6. **Descarga de Resultados**
   - Click "Descargar ZIP" → POST `/api/download/experiment-zip`
   - ZIP generado con todos los archivos relevantes

## Manejo de Estado

### Variables Globales Frontend
```javascript
// NGL.js
let stage;                  // Instancia del visualizador
let capsideComponent;       // Componente 3D de cápside
let enzymeComponent;        // Componente 3D de enzima

// Estado de selección
let currentCapsides = [];   // Lista de cápsides disponibles
let currentEnzymes = [];    // Lista de enzimas disponibles
let selectedCapsid = null;  // Cápside seleccionada
let selectedEnzyme = null;  // Enzima seleccionada
let calculatedRadius = null; // Radio interno calculado
```

### Estado Backend
- **Stateless**: Cada request es independiente
- **Archivos temporales**: Limpiados automáticamente
- **Configuración**: Cargada de `config/default.yaml` en cada request

## Visualización 3D (NGL.js)

### Representaciones de Cápside
```javascript
capsideComponent.addRepresentation("surface", {
    surfaceType: "sas",
    opacity: 0.3,
    colorScheme: "chainid",
    side: "double"
});
```

### Representaciones de Enzima
```javascript
enzymeComponent.addRepresentation("cartoon", {
    colorScheme: "chainid",
    opacity: 1.0
});
```

### Controles Interactivos
- **Transparencia**: Slider 0-100% opacidad
- **Clipping**: Corte por planos para ver interior
- **Rotación**: Manual con mouse o automática
- **Zoom**: Scroll del mouse
- **Pan**: Click derecho y arrastrar

## Optimizaciones y Consideraciones

### Performance
- **No hay polling**: Todo es request-response
- **Carga bajo demanda**: Estructuras solo cuando se seleccionan
- **Cacheo de radio**: Se guarda en `radio_interno.txt`
- **Réplicas en paralelo**: Uso de multiprocessing en backend

### Seguridad
- **CORS abierto**: `Access-Control-Allow-Origin: *` (desarrollo)
- **Sin autenticación**: Sistema abierto
- **Validación básica**: Límites en número de enzimas (1-100)

### Limitaciones
- **Sin WebSockets**: No hay actualizaciones en tiempo real
- **Sin progress bars**: Usuario no ve progreso de cálculos largos
- **Timeout potencial**: Operaciones largas (>5 min) pueden fallar
- **Memoria**: PDBs grandes pueden saturar el navegador

## Puntos de Extensión

### Para agregar WebSockets
1. Instalar `flask-socketio`
2. Emitir eventos de progreso desde backend
3. Escuchar en frontend con Socket.IO client

### Para agregar polling
1. Crear endpoint `/api/experiment/status/{id}`
2. Frontend hace polling cada 2-5 segundos
3. Actualizar UI con progreso

### Para mejorar UX
1. Agregar spinners/loaders durante operaciones
2. Implementar cola de trabajos con Celery
3. Cachear resultados de experimentos
4. Comprimir respuestas con gzip

## Debugging

### Logs Backend
```python
app.run(debug=True)  # Habilita logs detallados
```

### Logs Frontend
```javascript
console.log('API Response:', data);
console.error('API Error:', error);
```

### Network Inspector
- Chrome DevTools → Network tab
- Ver payloads y responses
- Identificar requests lentos

### NGL.js Debug
```javascript
stage.viewer.debug = true;
```