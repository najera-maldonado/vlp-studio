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

## 4b. Decisiones científicas pendientes (las decide Lucio, no la IA)

Cosas que parecían "bugs" pero son elecciones de ciencia. No se tocan hasta que Lucio
decida la dirección y, en su caso, se corra la MD correspondiente (con la red de VLP-06).

- **CIENCIA-1 — `capsid.py` radio interno ±1 Å.** El código suma +1 Å; el docstring dice
  restar 1 Å (margen de seguridad). Contradicción. Recomendación de la IA: restar
  (alinea con intención + más seguro). **Estado: Lucio lo decide luego.** Impacto real
  bajo hoy (el radio casi siempre es el fallback 90 Å).
- **CIENCIA-2 — `sustratinaitor` resolución CG vs all-atom.** Hoy el sistema es híbrido
  incoherente (cápside CG + GYE all-atom de 144 átomos empaquetado + agua CG). Decidir:
  todo CG (rehacer empaquetado con `GYE_cg_manual.pdb`, 17 beads — coherente con PackMan,
  pero mapeo CG sin validar) o todo all-atom (inviable para cápside entera). **Estado:
  aplazado hasta correr esa MD.**
- **CIENCIA-3 — `PackMan` protocolo de heat.** Los `heat*.in` estáticos son all-atom
  (`dt=0.002`, SHAKE, `@CA,C,N,O`) sobre topología CG SIRAH. `configurar_simulacion.sh`
  ya genera los `.in` correctos en CG. Decidir protocolo y retirar los estáticos.
  **Estado: aplazado hasta correr esa MD.**

---

## 5b. Filosofía y alcance (leer antes de decidir qué tocar)

**El proyecto NO está muerto ni congelado. Estamos poniendo cimientos.** La ciencia
la construyó Lucio solo; el conocimiento vive en su cabeza y en el código. El objetivo
de esta fase (estructura, auditabilidad, editar-sin-romper) es **habilitar** que en el
futuro se pueda pulir, parchear y reconstruir la ciencia real **con seguridad** — no
sustituirla.

Por qué hoy no tocamos la ciencia: ahora no hay red (monolito, cero tests). La
modularidad (VLP-03/04) + los tests de humo (VLP-06) SON la licencia para editar la
ciencia después con marcha atrás y verificación.

**Fronteras (qué significa "no tocar"):**
- **Permanente — nunca:** los datos crudos pesados (los produce un motor, van en
  `.gitignore`); el otro proyecto/cuenta (`mexicanoresidente-ux`, residente-mx); y las
  **tripas de los motores de terceros** — HOLE, Vina, AMBER, campo de fuerza SIRAH se
  **llaman**, no se reescriben ni se forkean.
- **Protegido AHORA, editable DESPUÉS (con red):** toda la ciencia propia — análisis de
  poro, cribado de mutantes, protocolos de MD, empaquetado. Candidata a pulir/reconstruir
  una vez existan los cimientos. Durante VLP-03 se **mueve tal cual, no se reescribe**;
  reescribirla ahora reintroduce bugs ya resueltos (eje de simetría, rseed, centrado).
- **Aplazado hasta que haya razón real (no "nunca"):** deploy en nube, multiusuario,
  cola de trabajos, endurecer seguridad. Tiene sentido el día que lo use alguien más.
- **Ampliación futura, no ahora:** De-inmunización real (NetMHCIIpan/FEP).

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
| **VLP-01** | ✅ | **Infra reproducible** (2026-09-17): `requirements.txt` reescrito a versiones que funcionan + RDKit; endpoint `/api/health` real (reporta motores/deps); `debug` respeta config (off por defecto); Dockerfile base py3.12 + motores apt (obabel/vina) + healthcheck urllib; compose sin curl. Verificado en vivo (boot + /api/health 200). **Caveat:** la imagen Docker no se pudo construir aquí (sin daemon); `hole`/`idock` no están en apt → documentado como límite conocido. |
| **VLP-02** | ✅ | **Bug mecánico corregido** (2026-09-17): `5docking.sh` `found_any` ahora se pone a 1 en el loop (antes `exit 1` siempre). Verificado. Los otros 3 "bugs" resultaron ser **decisiones científicas** → reclasificados abajo (CIENCIA-1/2/3), no se tocan ahora por decisión de Lucio. |
| **VLP-03** | ✅ | **`packing_service.py` partido** (2026-09-17, patrón estrangulador): el monolito de 1225 líneas → 6 módulos por responsabilidad — `common.py` (infra+helpers), `library.py`, `pore.py` (526), `deimmuno.py`, `md.py`, `packing.py`. `packing_service.py` quedó como **fachada** (71 líneas) que re-exporta la API; `app.py` y los tests no cambiaron. 17 tests verdes + boot en vivo (una ruta por puerta → 200). Para añadir puerta: nuevo módulo + re-exportar en la fachada. |
| **VLP-04a** | ✅ | **Externalizar `studio.html`** (2026-09-17): CSS y JS inline → `static/css/studio.css` (77) y `static/js/studio.js` (830); el template pasó de 1190 a 281 líneas (solo estructura). Extracción byte-idéntica (script Python). Verificado: node --check del JS, servido con content-type correcto, 17 tests backend verdes, y **en navegador** (render, badge PACKMOL LISTO, biblioteca real, cambio de pestaña a PAC-PORE con gráfica Chart.js, cero errores de consola). |
| **VLP-04b** | ⬜ | **Partir `studio.js`** (830 líneas) en un módulo por pestaña (biblioteca/studio/pore/deimmuno/md) preservando el ámbito global (scripts clásicos en orden). Ya hay red de navegador para verificar. |
| **VLP-04c** | ✅ | **Portada EMBUDO** (2026-09-17): `templates/embudo.html` + `static/css/embudo.css` en la raíz `/`; el Studio pasó a `/studio`. Embudo de 5 barras que se estrechan (Biblioteca→Pac-Pore→Studio3D→De-inmuniz.→MD) con badges real/ilustrativo; cada puerta enlaza a `/studio#<view>` y `studio.js` abre esa pestaña (tras esperar las cargas async — se arregló una carrera que dejaba el perfil en blanco). 18 tests + verificado en navegador (portada, clic en puerta → PAC-PORE con gráfica). |
| **VLP-05** | ⬜ | **Retirar fósiles**: `/classic`, prototipos muertos, código muerto de Poromania, docs que mienten. **+ Renombrar `nanocapsule-mvp/` → `studio/`** (el nombre es fósil; contiene el Studio vivo). OJO al renombrar: actualizar `herramientas/vlpstudio.kdl`, `herramientas/salud.sh`, PENDIENTES/BITACORA y docs que citen la ruta (paths.py se resuelve por `__file__`, no se rompe). |
| **VLP-06** | ✅ | **Tests de humo** (2026-09-17, ADELANTADO antes de VLP-03 para tener red al partir el monolito): `nanocapsule-mvp/tests/test_smoke.py`, 17 tests, ~1.5s. Cubren boot, páginas, biblioteca, Pac-Pore (rutas rápidas), sección RDKit, MD/deimmuno ilustrativos, preview y funciones de servicio. NO ejercen motores lentos (HOLE/PyMOL/Vina/Packmol). Correr: `cd nanocapsule-mvp && python3 -m pytest -q` (o `test` en el pane manual). El tablero `salud.sh` muestra el resultado. |

---

## 7. Cómo arrancar hoy

```bash
cd nanocapsule-mvp
FLASK_DEBUG=0 python3 src/web/app.py
# http://localhost:5000
```

Requiere en el sistema: `packmol`, `pymol`, `hole`, `vina`, `obabel`, `idock` (binarios) y `rdkit`, `flask`, `numpy`, `pyyaml` (Python). Ver §4: `requirements.txt` está incompleto.
