# Pendientes — VLP Studio

> Lista viva. Formato: `- [ ]` pendiente, `- [x]` hecho. Detalle de tareas grandes en
> `ESTADO.md §6`; investigaciones en `INVESTIGACION_*.md`; historial en `BITACORA.md`.
> Actualizado 2026-10-05: auditorías de los 4 motores hechas; documentación reconciliada con
> sus hallazgos (ver `CORRECCIONES_DOCUMENTACION.md`). **Lista de trabajo vigente:
> `HOJA_DE_RUTA.md`** (rama `claude/consolidate-audit-roadmap-k82rek`), que consolida los
> 9 informes del 2026-10-04 y los ordena por dependencia. Esta lista queda como índice.

## ⚠️ LO QUE CAMBIÓ CON LAS AUDITORÍAS (2026-10-04) — leer antes que nada
La auditoría pedida el 2026-09-18 se hizo: 9 informes independientes en ramas
(`AUDITORIA_MD.md`, `AUDITORIA_PACKING.md` ×2, `AUDITORIA_PORO.md`, `AUDITORIA_SUSTRATO_Y_CG.md`
×2, `HALLAZGOS_NO_DOCUMENTADOS_2026-10-04.md`, `PLAN_REPARACION_MD.md`, `HOJA_DE_RUTA.md`;
fuentes en `HOJA_DE_RUTA.md §9`). Veredicto, con evidencia reproducible desde el repo:
- **El packing NO es terreno firme.** La frase anterior de esta lista ("geométrico y
  determinista, semilla fija, golden test") era falsa: la ruta de producción no pasa semilla
  (`experiment_runner.py:160` → `random.randint`; `seed_base`/`use_random_seeds` del YAML no
  los lee nadie) y el golden test (`test_golden_science.py`) es de `substrate_section`
  (puerta 1, poro), no del packing, cuya cobertura de tests es cero. Peor: el criterio de
  aceptación busca `Maximum distance violation:` y PACKMOL escribe `Maximum violation of
  target distance:` (0 coincidencias en los dos logs reales del repo); el fallback acepta
  cualquier PDB con ≥ 10 000 líneas, que la cápside sola cumple. Con un doble de PACKMOL que
  coloca 0 enzimas, el motor reporta **100 enzimas, σ = 0**. → PK-1…PK-5.
- **El único resultado de poro (1.92 Å) es inválido:** `mut_129HIS_132GLY/receptor.pdb` es
  byte-idéntico a `WT.pdb`; el script carga otra estructura (CCMV) que la que lo produjo
  (BMV `poro5fold`); `cpoint` a 7.6 Å del eje y `cvect` 19° desviado. Marcado con
  `INVALIDO.md` en la carpeta. → PO-1…PO-7.
- **La MD no solo no corrió: no puede correr con lo commiteado.** `eq1/eq2/prod` tienen
  `nstlim = 500` (10 ps cada uno) bajo títulos "15ns"/"35ns"; 8 de 13 `.in` son all-atom;
  `run_maestro.sh` entrega a `cgconv.pl` un PDB sin H y sin `TER` (180 → 3 → 0). Las cifras
  de MD del Studio son `math.sin`. La receta CG correcta ya existe:
  `sustratinaitor/1_capside/3J7L_cg.pdb`. → MD-1…MD-10.
- **sustratinaitor:** conversión CG de la cápside correcta (byte a byte); pero la salida de
  Packmol pierde los 180 `TER`, el GYE empaquetado es all-atom a 20 fs sin SHAKE (no
  integrable), `GYE_cg_manual.pdb` no sirve de punto de partida, y la etapa 4 busca un
  `prmtop` que tleap no produce. → SU-1…SU-3.
- **JOSS:** `JOSS_CHECKLIST.md` decía "Reproducibility DONE", "gates 1 and 2 real", "licence
  clearly stated"; las tres eran falsas (la última porque el repo versiona 146 ficheros de
  SIRAH mientras `THIRD_PARTY.md` lo listaba como no redistribuido). Corregida.
- **Decisiones de Lucio que ya tienen evidencia para decidirse sin correr nada** (DC-1…DC-8
  en `HOJA_DE_RUTA.md §3`): estrategia JOSS (reparar antes o reetiquetar), CIENCIA-1
  (restar), CIENCIA-2 (sacar el GYE de la MD CG), CIENCIA-3 (5 etapas de `tutorial/5`),
  licencia SIRAH, estadístico del packing, motor de docking (Vina), qué poro se mide
  (`BMV/poro5fold`).

Estado del briefing original de la auditoría (2026-09-18): **cumplido**. El texto que había
aquí sobre "terreno firme vs frágil" y "JOSS no depende de la MD" se retira: JOSS depende hoy
de que el packing y el poro digan lo que afirman (DC-1).

## 🎯 Meta cumplida: PUBLICABLE COMO SOFTWARE (release v0.1.0)
- [x] **Fase A — instalable:** Docker construye/arranca (.dockerignore, fix libgl1), engines documentados.
- [x] **Fase B — confiable:** LICENSE (AGPLv3, relicenciada desde MIT el 2026-09-18) + THIRD_PARTY · CI verde (VLP-08) · pinning requirements.lock · VLP-09 (entry point) · VLP-05 (/classic oculta+deprecated).
- [x] **Fase C — citable:** README de plataforma (raíz) · CITATION.cff · **release v0.1.0 en GitHub**.

## Para dejarlo "bien bien" ANTES de publicar (pulido recomendado)
- [x] **README de PackMan y sustratinaitor** (2026-09-17): los 4 motores documentados con estado honesto.
- [x] **VLP-11 — `fetch_data.sh`** (2026-09-17): baja P22 5UU5 de RCSB; biblioteca por defecto ya viaja en el repo. Sintaxis validada, RCSB 200.
- [x] **Golden test de regresión científica** (2026-09-17): `tests/test_golden_science.py`, radio de sección RDKit (seed fijo) con tolerancia; corre en CI. 5 tests. **Alcance real (auditoría 2026-10-04):** cubre solo `substrate_section` (puerta 1); el packing tiene cero tests; el valor congelado es semieje de centros atómicos sin vdW (×1,8–2,2 por debajo de la sección física). → PK-5, PO-10.
- [x] **VLP-10 — Linter/formatter** (2026-09-17): ruff (pyproject.toml), 39 fixes + format; CI usa ruff check + format --check.
- [x] **CI para los otros motores** (2026-09-18): job `engines` corre compileall sobre Poromania/PackMan/sustratinaitor (verifican que su Python parsea; excluye bundle SIRAH). Verde.
- [x] **VLP-04b — Partir `studio.js`** (2026-09-18): 830 líneas → 6 archivos por puerta (studio-core/library/analisis-md/deinmunizacion/pac-pore/packing). Byte-idéntico, verificado en navegador (PAC-PORE con Chart.js, 0 errores consola).

## Publicar (estado)
- [x] **Repo PÚBLICO** (2026-09-18): https://github.com/najera-maldonado/vlp-studio

## Siguiente objetivo acordado: publicación en JOSS
> **Estado completo y accionable en [`JOSS_CHECKLIST.md`](JOSS_CHECKLIST.md)** (en inglés).
> Resumen: el paquete de documentación está hecho y **corregido tras las auditorías**
> (2026-10-05, ver su §0). Antes de enviar hay que decidir **DC-1** (reparar packing y poro
> primero, ~6 días, o enviar con las puertas 1 y 2 etiquetadas "en revisión", como ya dice la
> documentación) y **DC-5** (bundle de SIRAH). Lo demás sigue siendo solo de Lucio.
- [x] **Repo/docs en INGLÉS** (2026-10-04): README de la raíz + los 4 READMEs de motores +
      `docs/installation.md` + `docs/usage.md` + `CONTRIBUTING.md` + `paper.md` + `CITATION.cff`.
      Los documentos internos (ESTADO/PENDIENTES/BITACORA/REVISION/INVESTIGACION) se quedan en
      español a propósito: son bitácora de decisiones, no documentación de usuario.
      (La interfaz del Studio se hará bilingüe ES/EN aparte — ver Software.)
- [x] **`paper.md` + `paper.bib`** (2026-10-04): metadata YAML de JOSS, *statement of need*,
      resumen del software, sección honesta de alcance/limitaciones, 19 referencias.
      **Pendiente: verificar los DOI contra Crossref** (§4.1 de la checklist).
- [x] **Docs de instalación/uso explícitas** (2026-10-04): `docs/installation.md` (Docker +
      local, motores externos, verificación, troubleshooting) y `docs/usage.md` (recorrido
      puerta por puerta sobre el caso Gaucher, con comandos ejecutables).
- [x] **Guías de comunidad** (2026-10-04): `CONTRIBUTING.md` — requisito de JOSS que no
      estaba en esta lista (cómo reportar bugs, cómo contribuir, fronteras de alcance).
- [ ] **Identidad de autor** — nombre legal exacto + ORCID + afiliación. Marcado con `TODO`
      en `paper.md` y `CITATION.cff`. **Solo Lucio.**
- [ ] **Tag de release** — los tags **sí existen** en el remoto (`v0.1.0` y los cuatro por
      motor; `git ls-remote --tags origin`); la checklist decía que no porque ese clon no los
      había traído. Falta decidir si `v0.1.0` (anterior a las correcciones) es el que se
      archiva o se corta uno nuevo tras DC-1. **Solo Lucio.**
- [ ] **DC-1 — estrategia JOSS** (reparar antes / reetiquetar y enviar) y **DC-5 — licencia
      SIRAH** (quitar el bundle o declararlo). Ver `HOJA_DE_RUTA.md §3`. **Solo Lucio.**
- [ ] Archivar en Zenodo → DOI (añadir a README y CITATION.cff). [repo público ✅ — falta que Lucio active la integración]
- [ ] **Enviar** en <https://joss.theoj.org/papers/new>, declarando la cronología real de
      desarrollo (el git log son 2 días; la ciencia es muy anterior). **Solo Lucio.**

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
- [ ] **Antes de correr nada: reparar la preparación del sistema y los `.in`** (MD-1…MD-6 de
      `HOJA_DE_RUTA.md`; los 5 `.in` correctos están literales en `PLAN_REPARACION_MD.md`,
      rama `claude/packman-repair-plan-9c287t`). PackMan **no** tiene el protocolo: los `.in`
      commiteados son stubs de 10 ps (≈ 240 ps en total) y la topología que genera
      `run_maestro.sh` es inválida (sin H, sin `TER`).
- [ ] Humo en GPU (MD-7) y solo después producción 5 + 25 + ≥ 100 ns con `ig` fijo y
      manifiesto (MD-8). Faltan trayectorias/`.dat`.
- [ ] **Réplicas a distintas temperaturas** (liga con CIENCIA-3, heat).
- [ ] **Solvatar con dodecaedro rómbico** los sistemas icosaédricos (eficiente para ~esféricos).
- [ ] **Añadir GROMACS** al pipeline empaquetador→MD (hoy PackMan es estilo AMBER).
- [ ] **Decidir CG: SIRAH vs Martini 3** (apunte Lucio; ya era pregunta abierta en INVESTIGACION_2026-09-17.md).
- [ ] **Replica-exchange (T-REMD/HREMD)** como sampling avanzado (confirmado por Lucio 2026-09-18; probablemente T-REMD, que unifica con "réplicas a distintas temperaturas").

**Puerta 3 — de-inmunización:**
- [ ] Motor real (NetMHCIIpan-4.3, ya identificado).

**Validación con datos experimentales:**
- [ ] **Buscar publicaciones del nº de enzimas encapsuladas experimentalmente** en VLPs y **comparar** con nuestro packing (investigación dirigida, como las 2 ya hechas).

**Decisiones (Lucio; las auditorías concluyen que se pueden tomar YA, sin correr la MD):**
- [ ] **CIENCIA-1** — `capsid.py` radio ±1 Å. Recomendación con número: **restar** (con `+1`
      la holgura mínima garantizada es 0,5 Å, por debajo de cualquier radio de vdW). Y mejor:
      `d_min` exacto con NumPy y publicar dos números con nombre (radio físico y radio de
      empaque). Ver ESTADO §4b, DC-2.
- [ ] **CIENCIA-2** — resolución de `sustratinaitor`. Recomendación: **opción B, sacar el GYE
      de la MD CG** (el híbrido está descartado por física; `GYE_cg_manual.pdb` no sirve de
      partida). DC-3.
- [ ] **CIENCIA-3** — protocolo de `PackMan`. Recomendación: **eliminar `heat1..6`,
      `density_eq`, `final_eq`** y usar las 5 etapas de SIRAH `tutorial/5`;
      `configurar_simulacion.sh` NO es "los `.in` correctos" (restringe el solvente,
      `gamma_ln = 5`, no borra los all-atom). DC-4.

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
