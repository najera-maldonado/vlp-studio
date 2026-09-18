# Pendientes — VLP Studio

> Lista viva. Formato: `- [ ]` pendiente, `- [x]` hecho. Detalle de tareas grandes en
> `ESTADO.md §6`; investigaciones en `INVESTIGACION_*.md`; historial en `BITACORA.md`.
> Actualizado 2026-09-18: repo público; incorporados los apuntes de ciencia/software de Lucio.

## ⏭️ PRÓXIMA SESIÓN (decisión de Lucio, 2026-09-18): REVISAR TODOS LOS MOTORES
Antes de seguir construyendo o extendiendo, hacer una **auditoría científica INDEPENDIENTE
y DESDE CERO** de los 4 motores (Studio/packing, Poromania/poro, PackMan/MD, sustratinaitor).
**Briefing completo en [`REVISION_MOTORES.md`](REVISION_MOTORES.md)** — leerlo primero.
Motivo: Lucio señala que **las corridas de MD PUEDEN ESTAR MAL** → NO dar por buenos los
resultados de dinámica hasta verificarlos. **IMPORTANTE (anti-sesgo):** Lucio quiere una
revisión desde cero, NO que se confirme una revisión previa; cualquier hallazgo anterior es
sospecha sin verificar, para cross-check solo DESPUÉS de la propia pasada — nunca norma.
- Terreno firme vs frágil: el **packing es geométrico y determinista** (semilla fija, golden
  test) → más confiable que la MD. Si la MD flaquea, packing + JOSS siguen en pie.
- Prioridad cercana, enmarcada como VERIFICACIÓN (no extensión): **JOSS en paralelo** (no
  depende de la MD) + **réplicas → condición 6 enzimas → all-atom del sitio activo**, que
  sirven justo para COMPROBAR si la MD se sostiene. Cuello de botella = GPU. ~1 mes JOSS,
  ~3-4 meses la ciencia (ver conversación de estimación).

## 🎯 Meta cumplida: PUBLICABLE COMO SOFTWARE (release v0.1.0)
- [x] **Fase A — instalable:** Docker construye/arranca (.dockerignore, fix libgl1), engines documentados.
- [x] **Fase B — confiable:** LICENSE (AGPLv3, relicenciada desde MIT el 2026-09-18) + THIRD_PARTY · CI verde (VLP-08) · pinning requirements.lock · VLP-09 (entry point) · VLP-05 (/classic oculta+deprecated).
- [x] **Fase C — citable:** README de plataforma (raíz) · CITATION.cff · **release v0.1.0 en GitHub**.

## Para dejarlo "bien bien" ANTES de publicar (pulido recomendado)
- [x] **README de PackMan y sustratinaitor** (2026-09-17): los 4 motores documentados con estado honesto.
- [x] **VLP-11 — `fetch_data.sh`** (2026-09-17): baja P22 5UU5 de RCSB; biblioteca por defecto ya viaja en el repo. Sintaxis validada, RCSB 200.
- [x] **Golden test de regresión científica** (2026-09-17): `tests/test_golden_science.py`, radio de sección RDKit (seed fijo) con tolerancia; corre en CI. 5 tests.
- [x] **VLP-10 — Linter/formatter** (2026-09-17): ruff (pyproject.toml), 39 fixes + format; CI usa ruff check + format --check.
- [x] **CI para los otros motores** (2026-09-18): job `engines` corre compileall sobre Poromania/PackMan/sustratinaitor (verifican que su Python parsea; excluye bundle SIRAH). Verde.
- [x] **VLP-04b — Partir `studio.js`** (2026-09-18): 830 líneas → 6 archivos por puerta (studio-core/library/analisis-md/deinmunizacion/pac-pore/packing). Byte-idéntico, verificado en navegador (PAC-PORE con Chart.js, 0 errores consola).

## Publicar (estado)
- [x] **Repo PÚBLICO** (2026-09-18): https://github.com/najera-maldonado/vlp-studio

## Siguiente objetivo acordado: publicación en JOSS
- [ ] **Repo/docs en INGLÉS** (JOSS exige inglés): README + paper + docs en inglés. (La interfaz del Studio se hará bilingüe ES/EN aparte — ver Software.)
- [ ] `paper.md` (metadata + *statement of need* + resumen + referencias).
- [ ] Docs de instalación/uso completas (JOSS las exige explícitas).
- [ ] Archivar en Zenodo → DOI (añadir a README y CITATION.cff). [repo público ✅ — falta que Lucio active la integración]

## Diferido / cosmético (no bloquea publicar)
- [ ] Renombrar `nanocapsule-mvp/` → `studio/` (nombre fósil). RIESGOSO: toca rutas, build-context de Docker, imports → hacerlo con red y verificación.
- [ ] Borrar `_temp_backup/` local (770 MB, NO está en git). Recupera disco. — Solo Lucio, `rm -rf`.

## Ciencia — "publicable como ciencia" (meses; correr los motores de verdad)
> Muchos vienen de los apuntes de Lucio (2026-09-18). Frontera: los motores de terceros
> se LLAMAN, no se forkean (HOLE/Vina/AMBER/GROMACS/SIRAH).

**Puerta 1 — transporte por el poro:**
- [ ] **Steered MD / "push"**: forzar al sustrato a cruzar el poro y medir la ENERGÍA de cruce (= PMF por umbrella sampling / SMD). Realización concreta de "robustecer Puerta 1". Ver INVESTIGACION_2026-09-17.md (CHAP/PMF).
- [ ] **Barrido de pH** y medir el cambio de tamaño del poro (conecta con los estados morfológicos de P22).
- [ ] **Estabilidad de mutantes del poro** (mapeados a la cápside) vs la cápside sola.
- [ ] Complemento barato: CHAP (proxy de agua) antes del PMF caro.
- [ ] Métodos de energía libre del cruce/unión (apuntes Lucio): umbrella sampling (= el push de arriba) · **metadinámica** (alternativa para el PMF) · **MM-PBSA/MM-GBSA** (energía de unión desde trayectoria MD; complementa/sustituye a Vina en `dock_correlate`).

**Puerta 4 — MD (hoy NUNCA corrida; bloque "correr la MD bien"):**
- [ ] Correr la MD (PackMan tiene el protocolo; faltan trayectorias/`.dat`).
- [ ] **Réplicas a distintas temperaturas** (liga con CIENCIA-3, heat).
- [ ] **Solvatar con dodecaedro rómbico** los sistemas icosaédricos (eficiente para ~esféricos).
- [ ] **Añadir GROMACS** al pipeline empaquetador→MD (hoy PackMan es estilo AMBER).
- [ ] **Decidir CG: SIRAH vs Martini 3** (apunte Lucio; ya era pregunta abierta en INVESTIGACION_2026-09-17.md).
- [ ] **Replica-exchange (T-REMD/HREMD)** como sampling avanzado (confirmado por Lucio 2026-09-18; probablemente T-REMD, que unifica con "réplicas a distintas temperaturas").

**Puerta 3 — de-inmunización:**
- [ ] Motor real (NetMHCIIpan-4.3, ya identificado).

**Validación con datos experimentales:**
- [ ] **Buscar publicaciones del nº de enzimas encapsuladas experimentalmente** en VLPs y **comparar** con nuestro packing (investigación dirigida, como las 2 ya hechas).

**Decisiones (Lucio, al correr la MD):**
- [ ] **CIENCIA-1** — `capsid.py` radio ±1 Å (IA recomienda restar). Ver ESTADO §4b.
- [ ] **CIENCIA-2** — resolución de `sustratinaitor` (CG vs all-atom).
- [ ] **CIENCIA-3** — protocolo de heat de `PackMan`.

## Software — features nuevas (la IA puede hacerlas; no bloquean publicar)
> De los apuntes de Lucio (2026-09-18).
- [ ] **Cápside sola (0 enzimas)** como control apo, para comparar contra el cargo. ← candidato fácil para empezar.
- [ ] **Cargar la VLP a 20/40/50/60/80/100%** de su capacidad máxima.
- [ ] **Interfaz bilingüe ES/EN** (i18n del Studio). [la doc de JOSS va en inglés, aparte].
- [ ] **Sistema de log** (estaba "fuera de alcance"; ahora encaja con provenance).
- [ ] **Base de datos** (SQLite) para historial de experimentos.
- [ ] Conectar la **MD de PackMan al visor 3D** (extensión de motor↔visualizador).
- [ ] **Quitar emojis del código + comentarios/strings a INGLÉS** (pulido pro/JOSS; también los READMEs públicos). Se solapa con "repo/docs en inglés".
- [ ] **Demo hosteado de solo lectura** (a): sitio que muestra el Studio + resultados precomputados usando los endpoints ligeros (sin motores pesados). Deployable (Vercel); la app completa con HOLE/GROMACS no. Para visibilidad/JOSS.

## Frontera nueva — QM/MM (confirmado: modelar la reacción; PERO es lo más limitante)
- [ ] **QM/MM** — modelar la CATÁLISIS / reacción de la enzima en el sitio activo (QM en el sitio + MM en el resto). Confirmado por Lucio (2026-09-18) que es modelar la reacción. **ES LA PIEZA MÁS PESADA Y LIMITANTE DEL PLAN:** muy caro (coordenada de reacción, TS), necesita motor QM (ORCA/CP2K gratis-académico, o Gaussian) acoplado a MM, y criterio experto (región QM, nivel de teoría, frontera). Subproyecto de MESES. Es ORTOGONAL al embudo (pregunta por la FUNCIÓN, no por transporte/estabilidad). **Recomendación: DESPUÉS de que corra la MD de Puerta 4; que NO bloquee lo cercano.** Frontera OK (se llama el motor QM, no se forkea).

## Grande / a scopear (visión del embudo — no bloquea publicar)
- [ ] **Combinar los motores**: que el Studio orqueste el embudo COMPLETO end-to-end (packing → poro → de-inmunización → MD) desde una interfaz. Hoy solo Pac-Pore está cableado (vía Poromania). Software + ciencia; es la dirección natural del proyecto.
- [ ] **Base de datos comunitaria** (b): que otros conecten SUS resultados a la BD. Multiusuario (login/moderación/seguridad/hosting). Grande, a futuro. AGPL cubre el caso de servicio web.

## Ya existía — apuntes de Lucio ya cubiertos (confirmado 2026-09-18)
- [x] Interfaz del Studio (app Flask + visor 3D). — nota "interfaz (antes no había)".
- [x] Colorear arcoíris cada enzima como figura individual (modelindex + rainbow; bug de centrado ya arreglado).
- [x] Conectar motor con visualizador (Studio 3D y Pac-Pore; la MD aún no → ver Software).
- [x] Especificar enzimas (selección desde la biblioteca).

## Descartado / no descifrable
- [x] ~~VLP-04c — Portada EMBUDO~~ (Lucio: "no le veo utilidad"). No reconstruir.
- [x] ~~"uMD PyMOL"~~ — apunte suelto (2026-09-18); ni Lucio recuerda qué era y no cree que lo sepa. Archivado, no se retoma salvo que reaparezca el contexto.
