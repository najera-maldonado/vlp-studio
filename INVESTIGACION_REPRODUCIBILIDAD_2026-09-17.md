# Investigación — Reproducibilidad para un pipeline científico de UNA persona (2026-09-17)

> **Qué es esto:** segunda investigación profunda (deep-research verificada), enfocada
> SOLO en el eje que quedó sin respuesta en `INVESTIGACION_2026-09-17.md`:
> reproducibilidad realista para VLP Studio, mantenido por un solo desarrollador.
>
> **Método:** 6 ejes → 23 fuentes → 111 afirmaciones → 25 verificadas por 3 votos
> adversariales. Resultado: **23 confirmadas, 2 refutadas, 0 sin verificar.**
> ⚠️ **El paso de síntesis automática falló por límite de sesión**; esta síntesis está
> hecha a mano sobre los 23 claims confirmados (cada recomendación cita su fuente).

---

## TL;DR — el orden de prioridad para una sola persona

Regla de oro encontrada (PLoS Comput Biol 2023, pcbi.1011920): **subir el código un nivel
de madurez cuesta 5-10× más esfuerzo.** Por eso, para un dev único, la estrategia correcta
es elegir el mínimo nivel necesario y NO sobre-ingeniarlo. Prioridad de mayor a menor
retorno por esfuerzo:

1. **Pinning exacto del entorno** (conda-lock) + **un entorno por motor**.
2. **Provenance mínimo**: un archivo de log/config por corrida (parámetros + versiones).
3. **CI de humo/stub + lint** en GitHub Actions (ya tienes la base con pytest).
4. **Golden files con tolerancia numérica** para detectar regresiones científicas.
5. **Orquestación**: quedarte en Makefile/scripts hasta que duela; WMS solo después.

---

## (a) Orquestación: Snakemake vs Nextflow vs Makefile

**Veredicto: para tu escala (una persona, pocos pasos, una máquina), un Makefile/shell
bien estructurado es la elección correcta, NO sobre-ingeniería.** Un WMS deja de ser
sobre-ingeniería cuando necesitas: paralelismo real, reanudar corridas caras a mitad,
o barrer muchas combinaciones de parámetros.

- La investigación anterior ya lo apuntaba (blog, sin verificar): para pipelines cortos
  de una persona, "un shell script bien estructurado o un Makefile no es la opción
  perezosa; es la correcta".
- **Si algún día migras a WMS, Snakemake te da provenance gratis:** registra
  automáticamente metadatos de qué produjo cada output en `.snakemake/metadata`, sin
  herramienta extra. *(snakemake.readthedocs.io, provenance) [3-0]*. Ese solo hecho lo
  hace preferible a Nextflow para un dev único que quiere trazabilidad sin montar nada.
- **No sobre-ingeniar:** un claim que decía "el testing automatizado es la práctica más
  valiosa para mantener código científico" fue **REFUTADO (0-3)** — no lo tomes como
  dogma; prioriza por retorno, no por regla universal.

## (b) Entornos y dependencias — el de MAYOR impacto para ti

Aquí está el mayor retorno por esfuerzo, dado que tus binarios (HOLE, Vina, GROMACS) son
justo los difíciles de instalar.

- **Un entorno/contenedor POR motor**, no uno monolítico. *"Isolate environments and
  containers for individual steps... Use Conda environments or Singularity containers per
  tool to minimize dependency conflicts."* (PMC9754251) [3-0]. Encaja exactamente con tu
  arquitectura de motores separados (Studio/Poromania/PackMan/sustratinaitor).
- **conda-lock para pinning EXACTO.** Un `environment.yml` define el entorno de forma
  *laxa* y NO garantiza reproducirlo; **conda-lock genera lock files totalmente
  reproducibles** (mismas versiones exactas descargadas/instaladas). *(github.com/conda/
  conda-lock)* [3-0 ×2]. **Acción concreta: añade un lock file por motor.**
- **Bioconda como canal de distribución = alto retorno, bajo esfuerzo.** *"Providing
  bioconda packages almost completely eliminates bug reports related to installation."*
  (pcbi.1011920) [3-0]. Si algún día empaquetas un motor, hazlo por Bioconda.
- Contenedores (Docker/Apptainer) son la capa siguiente si conda no basta para un binario
  terco; para una sola persona, conda-lock + entorno-por-motor suele ser suficiente.

## (c) Provenance y datos FAIR — mínimo viable

- **El mínimo viable es un archivo log/config por corrida** en el directorio de trabajo,
  con todas las rutas de archivos, parámetros y **versiones de software**, versionado.
  *(PMC9754251)* [3-0]. Esto es literalmente lo que te falta hoy para tus outputs
  (`hole_profile.tsv`, trayectorias, `.dat`).
- **Rastrear versiones NO es opcional:** *"differences in software versions lead to
  discrepancies in experiment results"* → registra versión por experimento, sobre todo
  para software que evoluciona rápido. *(Nature s41597-025-05126-1)* [3-0]. Tu
  VERSION/CHANGELOG por motor ya es media batalla; falta estamparlo en cada output.
- **Estrategia de captura barata (push-based, dos pasos):** durante la corrida, cada paso
  vuelca sus metadatos en crudo (sin infraestructura de monitoreo); en un paso posterior
  separado los estructuras/filtras. *"can readily be applied to existing simulations."*
  (Nature s41597-025-05126-1) [3-0]. **Ideal para añadir a tu pipeline sin refactor.**
- **Sobre-recolectar y filtrar después** es lo seguro: los metadatos NO se pueden
  reconstruir cuando la simulación termina. *(misma fuente)* [2-1, más débil].
- **Herramienta lista si quieres automatizarlo: Sumatra** — "cuaderno de laboratorio
  electrónico" que registra por corrida el script+versión, parámetros, duración, salida de
  consola y enlaces a todos los outputs. *(github.com/open-research/sumatra)* [3-0].
  Opcional; el log manual ya cubre el mínimo.
- **Qué NO vale la pena para una persona:** metadatos FAIR completos con ontologías,
  repositorios indexados, DOIs por dataset — sobre-ingeniería salvo que vayas a publicar
  los datos. El objetivo aquí es *"que tú mismo dentro de 6 meses puedas reproducir un
  output"*, no cumplir FAIR institucional.

## (d) CI para ciencia (GitHub Actions) — cuando los motores pesados no corren en CI

Esto conecta directo con tu **VLP-08 pendiente**.

- **Tests de "stub-run": el estándar es que un test de CI reemplace la corrida pesada por
  la generación de outputs (vacíos).** *"a stub test that replicates the generation of
  (empty) output files."* (nf-core) [3-0]. Es decir: en CI no corres HOLE/GROMACS; corres
  un stub que verifica que el *cableado* del paso funciona.
- **CI valida ejecución, no validez científica.** *"CI tests are not required to produce
  meaningful output... OK for a test to produce nonsense... as long as the tool does not
  crash."* (nf-core) [3-0]. Bájale las expectativas a CI: que no truene, que los esquemas
  encajen, que el lint pase. La corrección científica se valida aparte (ver (e)).
- **Datos de prueba: "tan pequeños como sea posible, tan grandes como sea necesario".**
  *(nf-core/test-datasets)* [3-0]. Mini-fixtures que ejerciten el pipeline sin motor real.
  - ⚠️ **Matiz (refutado):** la idea de poner esos fixtures en un **repositorio separado**
    fue **REFUTADA (0-3)** — para un dev único, mantenlos DENTRO del repo, no montes un
    segundo repo de test-data (eso es patrón de proyecto grande tipo nf-core).
- Tu base ya existe (17 tests de humo + pytest); el siguiente paso realista es
  automatizarlos en GitHub Actions + lint, que es exactamente VLP-08 / VLP-10.

## (e) Detección de REGRESIONES CIENTÍFICAS (no solo bugs de código)

El punto más sutil: un test verde no garantiza corrección científica.

- **Por qué la ciencia es distinta:** *"Faults can be masked by round-off errors,
  truncation errors and model simplifications."* (arXiv 1804.01954) [3-0]. Un fallo
  científico puede esconderse tras el error numérico.
- **Técnica concreta — golden files:** usa la salida de una versión previa como oráculo de
  la actual. *"the output from a previous version of the software can serve as an oracle."*
  (PMC8128694) [3-0]. Guardas un output de referencia "bueno" y comparas contra él.
- **Compara con TOLERANCIA, nunca igualdad exacta** (por punto flotante): tolerancia
  absoluta + relativa, p.ej. `numpy.allclose` o `assertAlmostEqual(..., places=N)`.
  *(PMC8128694; arXiv 2312.12604)* [3-0 ×2]. Taxonomía reutilizable de oráculos:
  tolerancia relativa, absoluta, de redondeo, y error-bounding. *(arXiv 2312.12604)* [2-0].
- **Elegir la tolerancia es lo difícil** y tiene un trade-off documentado: tolerancia más
  ajustada = detecta más fallos, pero más falsos positivos. **Truco:** descomponer el
  cálculo en pasos pequeños testeados por separado reduce el error acumulado y facilita
  fijar tolerancias. *(arXiv 1804.01954)* [3-0].
- **Aplicación a ti:** un golden file para el perfil HOLE de un poro nativo conocido
  (p.ej. el BMV 3-fold ≈2.47 Å que ya es reproducible con `rseed 1`) + `numpy.allclose`
  con tolerancia elegida detectaría si un cambio futuro rompe la ciencia, no solo el código.
  Los checks de sanidad (radio > 0, nº de puntos del canal > 30, etc.) ya los tienes
  parcialmente en Poromania — formalízalos como asserts.

---

## Plan de acción priorizado (lo mínimo viable, en orden)

1. **conda-lock por motor** — pinning exacto de HOLE/Vina/GROMACS/RDKit. Mayor retorno.
2. **Log de provenance por corrida** — un archivo con params + versiones junto a cada
   output; empezar push-based (volcado crudo) sin refactor.
3. **VLP-08 (CI) como stub + lint** — pytest de humo + linting en GitHub Actions; NO
   intentar correr motores pesados en CI.
4. **Golden file + `numpy.allclose`** para un perfil de poro de referencia — red contra
   regresiones científicas.
5. **Quedarte en Makefile/scripts**; migrar a Snakemake solo si necesitas
   paralelismo/reanudar/barridos (y entonces ganas provenance gratis).

**Sobre-ingeniería a EVITAR (para una persona):** metadatos FAIR con ontologías/DOIs;
repo separado de test-data; adoptar un WMS "porque sí"; tratar el testing automatizado
como dogma universal (claim refutado).

---

## Fuentes verificadas

| Eje | Fuente | Uso |
|---|---|---|
| Entornos/provenance | PMC9754251 | entorno por paso + log por corrida |
| Pinning | github.com/conda/conda-lock | lock files exactos |
| Distribución | PLoS Comp Biol 2023, pcbi.1011920 | Bioconda; regla 5-10× madurez |
| Provenance WMS | snakemake.readthedocs.io | metadata automática |
| Metadatos MD | Nature s41597-025-05126-1 | push-based, versiones, sobre-recolectar |
| Provenance tool | github.com/open-research/sumatra | ELN automático (opcional) |
| CI científico | nf-core (specs + test-datasets) | stub-run; datos mínimos |
| Regresiones | PMC8128694 | golden files como oráculo, tolerancias |
| Tolerancias | arXiv 1804.01954 | trade-off de tolerancia, pasos pequeños |
| Tolerancias | arXiv 2312.12604 | taxonomía de oráculos aproximados |

**Refutados (NO adoptar):** repo separado de test-data (0-3); "testing automatizado = la
práctica más valiosa" como regla universal (0-3).

**Stats:** 6 ejes · 23 fuentes · 111 afirmaciones · 25 verificadas · 23 confirmadas ·
2 refutadas · síntesis automática fallida (límite de sesión) → sintetizado a mano.
