# Estado de VLP Studio (PAC-ZYME)

> Mapa auditable del proyecto. Describe lo que **existe y funciona hoy**, no lo que
> se planeó. Si algo aquí contradice al README, CLAUDE.md, DEVELOPMENT_PLAN.md o
> TECHNICAL_IMPROVEMENTS.md, **manda este documento**: esos son planes fósiles de
> una versión anterior del proyecto.
>
> Última revisión: 2026-09-17 · Repo: github.com/najera-maldonado/vlp-studio (privado)

---

## 1. Qué es el proyecto

Una plataforma para diseñar **nanocápsulas VLP con enzimas terapéuticas**, organizada
como un **embudo de 4 filtros** que un sustrato debe superar:

| Puerta | Pregunta | Motor real | Estado |
|--------|----------|------------|--------|
| A través | ¿Entra el sustrato por el poro? | Poromania (HOLE + Vina + PyMOL) | **Real, de punta a punta** |
| Dentro | ¿Cabe la enzima en la cavidad? | Studio (Packmol + PyMOL) | Real (packing); resto ilustrativo |
| Fuera | ¿Evita la respuesta inmune? | — (NetMHCIIpan/FEP no integrados) | **Ilustrativo** |
| Sobrevive | ¿Aguanta la dinámica molecular? | PackMan (SIRAH + AMBER) | Motor listo, **MD sin correr** |

El **Studio** (`nanocapsule-mvp`) es la fachada web única; los otros tres proyectos
son los motores científicos.

---

## 2. Los cuatro subproyectos

### `nanocapsule-mvp/` — el Studio (fachada web)
- App Flask. Arranca: `FLASK_DEBUG=0 python3 src/web/app.py` → http://localhost:5000
- Backend en capas (bien trazado): `app.py` (adaptador HTTP delgado) → `services/packing_service.py` (toda la lógica, 1225 líneas) → `core/` (dominio) + `core/paths.py` (rutas centralizadas, incluye el puente a Poromania).
- Frontend: `src/web/templates/studio.html` (1190 líneas, todo el JS inline, NGL + Chart.js por CDN). 5 pestañas.
- `/classic` sirve `index.html`: interfaz **legada redundante** (duplica el núcleo de packing). Candidata a retirar.

### `Poromania.v.1.2./` — análisis de poros (motor de la puerta "A través")
- Pipeline: detección de residuos del poro → mutagénesis PyMOL → HOLE2 → APBS → docking iDock → figuras.
- El Studio lo consume directamente (lee `modelos/` y `mutants/*/hole/`).
- Herramientas instaladas: `hole`, `pymol`, `vina`, `idock`, `obabel`, RDKit.

### `sustratinaitor/` — sustrato GYE alrededor de la cápside
- Construye glucosilceramida (GYE) y empaqueta 200 copias alrededor de la cápside 3J7L con Packmol.
- Ejecutado hasta el empaquetado; etapa 4 (MD) no corrida. **Tiene un bug de resolución** (ver §4).

### `PackMan.v.1.2/` — dinámica molecular (motor de la puerta "Sobrevive")
- MD coarse-grained SIRAH de enzima-en-cápside: empaquetado → conversión CG → tleap → pmemd.cuda → cpptraj → gráficas.
- El subsistema `analisis/` (cpptraj) produce exactamente los `.dat` (frame, valor) que la pestaña "Análisis MD" del Studio sabe leer.
- Solo el empaquetado tiene evidencia de ejecución. **MD sin correr** (no hay trayectorias ni `.dat`).

---

## 3. Estado real por puerta del Studio

- **BIBLIOTECA** — real. Tablas de cápsides/enzimas con datos calculados (`/api/library/detail`). Pendiente: radio interno solo cacheado para BMV; tabla de sustratos.
- **STUDIO 3D** — mitad real. Packing Packmol + preview reales. "Sustrato alrededor" por SMILES (RDKit) y preparador de DM generan geometría/inputs reales pero **no ejecutan**.
- **PAC-PORE** — **real de punta a punta**. HOLE con eje de simetría correcto, sección de sustrato (RDKit), cribado de mutantes (PyMOL), docking (Vina) + correlación radio/afinidad. Es la parte más madura.
- **DE-INMUNIZACIÓN** — ilustrativo. Diccionario estático (`_DEIMMUNO`). Marcado "(ilustrativo)" en la UI.
- **ANÁLISIS MD** — ilustrativo. Curvas sintéticas (`math.sin`). El motor real (PackMan) existe pero su MD no se ha corrido.

**Nota de arquitectura:** el Studio **reimplementó en Python** la lógica de poro/cribado/docking
que ya vive en Poromania (`pore_analyzer.py` + los `.sh`). Funciona, pero la misma ciencia
existe en dos sitios que pueden divergir. Cualquier corrección debe decidirse en un solo lado.

---

## 4. Bugs y deuda conocidos (verificado 2026-09-17)

### Bugs reales
- **`Poromania/5docking.sh`**: `found_any` se inicializa en 0 y **nunca se pone a 1** → el script termina siempre con `exit 1` aunque el docking funcione, y eso hace fallar a `smiles_docking_pipeline.py`.
- **`sustratinaitor` — mismatch de resolución (confirmado)**: Packmol empaquetó el GYE **all-atom de 144 átomos** (160.620 = 131.820 + 200×144), no los 17 beads CG. La versión CG (`GYE_cg_manual.pdb`) quedó huérfana. El sistema resultante (cápside-CG + ligando-atomístico + agua-CG) es físicamente incoherente para SIRAH.
- **`nanocapsule-mvp/src/core/capsid.py`**: el código **suma** `+1.0 Å` al radio de colisión, pero su docstring y el CLAUDE.md dicen **restar** 1 Å. Una de las dos es un bug; hay que decidir cuál.
- **`PackMan` — `heat1..6*.in` son all-atom** (`dt=0.002`, SHAKE, `@CA,C,N,O`) aplicados a topología CG SIRAH (`dt=0.020`, `@GN,GO`). El calentamiento está pensado para otra resolución.

### Infraestructura desincronizada
- **Docker roto para el producto real**: los healthchecks (Dockerfile y compose) pegan a `/api/health`, **endpoint que no existe**. Y el Dockerfile **no instala RDKit, HOLE, Vina ni obabel** → Pac-Pore reventaría en el contenedor. El Docker solo sirve al MVP viejo.
- **`requirements.txt` no declara RDKit**, que es import duro de dos puertas.
- **`setup.py`** apunta a `cli/main.py` inexistente (entry point roto).

### Documentación fósil
- README/CLAUDE describen ~4 endpoints que no existen (`/api/structures`, `/api/generate_pdb`, `/api/radius/{capsid}`, `/api/download/{exp_id}`) y **ninguno** de los ~20 reales.
- `TECHNICAL_IMPROVEMENTS.md` marca como `[x] hechos` siete módulos que nunca se crearon (`src/api/`, `health_service`, etc.).
- `SESION_STUDIO.md` cita `LO_APRENDIDO.md` como "la visión" — ese archivo **no existe**.
- Prototipos muertos: `vlp-enzyme-brutalista.html` (maqueta sin backend), `ngl-viewer.html` (apunta a un backend puerto 5001 que ya no existe).

### Código muerto (Poromania)
- `pore_analyzer_backup.py` (versión vieja divergente), `1run_hole_old.sh`, `test_*.pml`, funciones definidas dos veces (`calculate_pentamer_center`), motor HOLE duplicado a mano en cada `mutants/*/scripts/`.

---

## 5. Rumbo recomendado (sin features nuevas)

1. **No reescribir desde cero.** La ciencia que funciona (Pac-Pore end-to-end, los pipelines) es la parte difícil y ya está hecha. Lo roto es organización, no diseño.
2. **Partir los dos monolitos por sus costuras existentes**: `packing_service.py` → un módulo por puerta (`services/pore.py`, `services/md.py`, ...); `studio.html` → un módulo JS por pestaña. Convierte "agregar sección" en "crear archivo".
3. **Portada EMBUDO** como raíz (hoy `/` entra directo a Biblioteca). Cuenta la visión que no está escrita en ningún lado.
4. **Corregir los bugs de §4** y sincronizar la infraestructura (RDKit en requirements, healthcheck real, Docker que instale los motores).
5. **Sincronizar los documentos** con el código; retirar los fósiles.
6. Servidor web **local de un solo usuario** por ahora. Contenerizado + cola de trabajos el día que lo usen otros. **Nunca app de escritorio** (perdería los motores binarios/GPU).

---

## 6. Decisión estratégica: refundar por dentro, no reescribir de cero

**Decidido (2026-09-17): NO se reescribe desde cero.** La ciencia difícil ya
funciona (Pac-Pore end-to-end; los pipelines). Reescribir tiraría lo valioso y
reintroduciría bugs ya resueltos (eje de simetría degenerado, `rseed` de HOLE,
centrado de enzimas). La arquitectura es correcta; el problema es que los archivos
crecieron sin partirse.

**Patrón a seguir: "estrangulador"** — el Studio sigue funcionando en todo momento;
en cada commit se extrae una pieza a su módulo y se verifica que arranca. No hay un
"gran día del rewrite": hay muchos commits pequeños, reversibles, que nunca dejan el
proyecto roto. Git es el vehículo: cada extracción es un commit auditable.

**"Empezar limpio" solo cabe** en lo que hoy es maqueta (De-inmunización, Análisis MD)
cuando se conecten de verdad, y en la etapa rota de `sustratinaitor` (bug de resolución).

### Plan de ejecución (ordenado; cada punto = uno o varios commits verificables)

> IDs de tarea: para trabajar una, di *"trabaja VLP-0N"*. Estado: ⬜ pendiente · 🚧 en progreso · ✅ hecho.

| ID | Estado | Tarea |
|----|--------|-------|
| **VLP-01** | ⬜ | **Infra reproducible** (empezar por aquí — desbloquea todo, imposible de romper): RDKit en `requirements.txt`, arreglar healthcheck `/api/health`, Docker que instale los motores (hole/vina/obabel). Sin esto nadie puede levantar el proyecto real. |
| **VLP-02** | ⬜ | **Corregir los 4 bugs de §4** (puntuales, alto valor): `5docking.sh` `found_any`, mismatch CG de sustratinaitor, `capsid.py` ±1 Å, `heat*.in` all-atom en PackMan. |
| **VLP-03** | ⬜ | **Partir `packing_service.py`** en un módulo por puerta (`services/pore.py`, `md.py`, `library.py`, `packing.py`). |
| **VLP-04** | ⬜ | **Partir `studio.html`** (un JS por pestaña) + **portada EMBUDO** como raíz. |
| **VLP-05** | ⬜ | **Retirar fósiles**: `/classic`, prototipos muertos, código muerto de Poromania, docs que mienten. |
| **VLP-06** | ⬜ | **Tests de humo** sobre las rutas reales → a partir de ahí cada cambio es seguro. |

---

## 7. Cómo arrancar hoy

```bash
cd nanocapsule-mvp
FLASK_DEBUG=0 python3 src/web/app.py
# http://localhost:5000
```

Requiere en el sistema: `packmol`, `pymol`, `hole`, `vina`, `obabel`, `idock` (binarios) y `rdkit`, `flask`, `numpy`, `pyyaml` (Python). Ver §4: `requirements.txt` está incompleto.
