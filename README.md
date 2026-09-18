# VLP Studio

Plataforma computacional para **diseñar nanocápsulas de tipo virus-like particle (VLP)
cargadas con enzimas terapéuticas** (p.ej. glucocerebrosidasa para la enfermedad de
Gaucher). El diseño se organiza como un **embudo de 4 filtros**: cada puerta pregunta si
un candidato sobrevive a un criterio físico antes de pasar al siguiente.

> **Estado:** software de investigación en desarrollo temprano (v0.1.0), mantenido por
> un autor único. Parte de la ciencia está implementada de punta a punta y parte es
> ilustrativa (ver *Estado por puerta* abajo). No es un producto clínico.

## El embudo de 4 puertas

| Puerta | Pregunta | Motor | Estado |
|--------|----------|-------|--------|
| **1 · A través** | ¿El sustrato entra por el poro de la cápside? | HOLE2 + cribado de mutantes (PyMOL) + docking (Vina) — [Poromania](Poromania.v.1.2.) | ✅ real, de punta a punta |
| **2 · Dentro** | ¿La enzima se empaqueta dentro de la cápside? | Packmol + PyMOL — [Studio](nanocapsule-mvp) | ✅ real (empaquetamiento multi-réplica) |
| **3 · Fuera** | ¿Se puede de-inmunizar la enzima? | (motor real pendiente; hoy ilustrativa) | 🟡 ilustrativa |
| **4 · Sobrevive** | ¿El sistema aguanta en dinámica molecular? | MD coarse-grained SIRAH — [PackMan](PackMan.v.1.2) | 🟡 protocolo completo, MD sin correr |

El **Studio** (interfaz web 3D) integra las puertas 1 y 2 de forma interactiva; las
puertas 3 y 4 están representadas en la interfaz de forma ilustrativa mientras se cablean
sus motores.

## Componentes (motores)

Monorepo con cuatro motores versionados de forma independiente:

- **[`nanocapsule-mvp/`](nanocapsule-mvp)** — el **Studio**: app Flask + visor 3D (NGL) que
  orquesta empaquetamiento (Packmol/PyMOL) y Pac-Pore (perfil de poro, docking). `v0.1.0`
- **[`Poromania.v.1.2./`](Poromania.v.1.2.)** — pipeline de análisis de poro: HOLE2 +
  mutagénesis (PyMOL) + docking. `v1.2.0`
- **[`PackMan.v.1.2/`](PackMan.v.1.2)** — preparación y protocolo de MD coarse-grained
  SIRAH del sistema enzima-en-cápside. `v1.2.0`
- **[`sustratinaitor/`](sustratinaitor)** — construcción y empaquetado de sustrato
  alrededor de la cápside para MD. `v0.1.0`

## Inicio rápido (Docker, recomendado)

```bash
git clone https://github.com/najera-maldonado/vlp-studio.git
cd vlp-studio/nanocapsule-mvp
docker compose build
docker compose up -d          # http://localhost:5000
curl http://localhost:5000/api/health   # -> {"status":"ok", ...}
```

La imagen incluye Packmol, PyMOL, Open Babel y Vina. **Pac-Pore** (puerta 1) y la
**MD** (puerta 4) requieren motores adicionales (HOLE, GROMACS) que **debes aportar tú**
bajo su propia licencia — ver [`THIRD_PARTY.md`](THIRD_PARTY.md) y el
[README del Studio](nanocapsule-mvp/README.md) para montarlos por volumen.

Instalación local (pip + binarios del sistema) documentada en el
[README del Studio](nanocapsule-mvp/README.md).

## Reproducibilidad

- **Entorno pinneado:** `nanocapsule-mvp/requirements.lock` (versiones exactas; Docker y
  CI instalan desde ahí).
- **CI:** GitHub Actions corre tests de humo + lint en cada push
  ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)).
- **Documentos de estado del proyecto:** [`ESTADO.md`](ESTADO.md) (mapa auditable),
  [`PENDIENTES.md`](PENDIENTES.md), [`BITACORA.md`](BITACORA.md).

## Licencia

Código propio bajo **GNU AGPLv3 o posterior** (ver [`LICENSE`](LICENSE)) — copyleft
fuerte: cualquier versión modificada debe permanecer abierta, **incluso si se ofrece como
servicio web** (AGPL cubre el caso de red). Copyright (C) 2026 najera-maldonado.

Los motores científicos de terceros que el Studio **invoca** (no redistribuye) conservan
su propia licencia; algunos (HOLE, NetMHCIIpan) no son redistribuibles y los aporta el
usuario — detalle en [`THIRD_PARTY.md`](THIRD_PARTY.md).

## Cómo citar

Ver [`CITATION.cff`](CITATION.cff). (Publicación en JOSS planeada; el DOI se añadirá aquí
cuando esté disponible.)
