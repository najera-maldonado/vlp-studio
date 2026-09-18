# Investigación externa — proyectos y prácticas similares (2026-09-17)

> **Qué es esto:** resultado de una investigación profunda (deep-research: fan-out de
> búsquedas web → fetch de fuentes → verificación adversarial de cada afirmación →
> síntesis con citas) lanzada tras la pregunta de Lucio: *"tómate el tiempo para ver
> proyectos similares, para saber qué no estamos viendo o se nos está pasando"*.
>
> **Método:** 5 ejes → 24 fuentes → 115 afirmaciones extraídas → 25 verificadas por
> 3 votos adversariales (necesita 2/3 para refutar). Resultado: **24 confirmadas, 0
> refutadas, 1 sin verificar** (fallo de infraestructura, no refutación). Casi todas
> las fuentes son papers revisados por pares; se marca donde no.
>
> **Cómo leerlo:** hallazgos accionables mapeados a las 4 puertas del embudo,
> priorizando lo adoptable por un desarrollador único. Ver también `ESTADO.md` (mapa
> del proyecto) y `PENDIENTES.md`.

---

## 🔴 Puerta 1 «a través» (poro) — HALLAZGO MÁS IMPORTANTE Y CRÍTICO

**El método actual (HOLE2 + cribado geométrico estático de mutantes en PyMOL)
subestima gravemente el transporte.** La literatura de la cápside P22 —el sistema más
parecido al proyecto— lo advierte con evidencia de tres capas acumulativas:

1. **Las cadenas laterales dominan el resultado.** En P22, HOLE da 1.9 nm (PC) y
   1.3 nm (EX) *con* cadenas laterales vs **4.4 nm sin ellas**. El número reportado
   depende brutalmente de ese detalle de tratamiento.
   — *Nat Commun 2021, s41467-021-23200-1 (PMC8131759), revisado por pares.*
2. **Los poros «respiran».** Experimentalmente difundieron moléculas del **doble** del
   tamaño teórico. Una sola estructura estática no basta.
   — *misma fuente.*
3. **La geometría ignora el *gating* hidrofóbico.** Zonas con radio por debajo de
   ~5 Å pueden ser una barrera energética significativa aunque «quepan» iones (el poro
   se seca / de-wetting y no conduce).
   — *Rao, Klesse, Stansfeld, Tucker & Sansom, Channels 2017 (PMC5555266), del propio
   laboratorio de HOLE.*

### Qué adoptar (realista para una persona, de barato a caro)

- **CHAP** (Klesse et al. 2019, extiende HOLE) — **mejora de mayor impacto / menor
  costo.** Usa la distribución de equilibrio del agua dentro del poro (de una MD corta)
  como proxy de si el poro realmente conduce. Es el punto intermedio entre «solo
  geometría» y un PMF completo. — *PMC5555266; CHAP en JMB 2019.*
- **CAVER 3.0 / MOLE 2.0** en vez de (o junto a) HOLE2. Detectan túneles ramificados y
  múltiples rutas (HOLE 2.2 no puede: *"cannot be used for calculation of tunnels or
  multiple pathways"*), aceptan trayectorias de MD, y MOLE añade 5 propiedades
  fisicoquímicas del revestimiento (carga, hidropatía, hidrofobicidad, polaridad,
  mutabilidad). — *CAVER 3.0: PLoS Comput Biol 2012, pcbi.1002708. MOLE 2.0: J
  Cheminform 2013, PMC3765717.*
  - *Caveat:* si el poro de la cápside diana es un **canal axial simple** sobre el eje
    de simetría, HOLE sigue siendo el caso de uso nativo y la ventaja de CAVER se
    reduce. El benchmark MOLE-vs-CAVER es de 2013 y de los propios autores de MOLE
    (sesgo); CAVER se ha actualizado desde (existe CAVER Web 2.0, 2025).
- **CaverDock** (Vavra et al., Bioinformatics 2019, PMC6828983) — combina túneles de
  CAVER + Vina restringido para dockear el ligando en cada rebanada del túnel → perfil
  de energía de entrada/salida + estimación de energía de activación. **Puente natural
  entre el HOLE2 y el Vina que ya usa el proyecto.** Empaquetado junto a CAVER 3.02 en
  CAVER Web (Nucleic Acids Res 2019, W414). *Es un proxy de docking, no un PMF: los
  autores advierten que "the actual energy may be higher".*
- **PMF por umbrella sampling + WHAM** (GROMACS + `gmx wham`) — el estándar de energía
  libre para validar la ruta real de transporte. Es la validación energética que el
  cribado geométrico estático omite. Flujo canónico: CAVER predice túneles candidatos
  (T1/T2/T3) → PMF los rankea y valida. **Caro**: reservarlo para los pocos mutantes que
  pasen el filtro geométrico barato. — *PubMed 33576049 (sarcosina oxidasa).*
  - *Caveat de dominio:* este paper es un túnel enzimático intramolecular, no un poro de
    cápside viral. La transferencia a la Puerta 1 es razonable pero es marco del
    sintetizador, no afirmación directa de la fuente.

---

## 🟢 Puerta 2 «dentro» (empaquetamiento) — precedente + una advertencia

- **La cápside VLP del bacteriófago P22 es el precedente experimental más directo.**
  Encapsula enzimas «one-pot» por fusión genética al scaffold y modula volumen/porosidad
  vía estados morfológicos (procápside → expandida → wiffleball) para controlar el
  acceso del sustrato. Buena analogía para justificar el proyecto.
  — *Patterson, Prevelige & Douglas, ACS Nano 2012, nn300545z.*
  - *Matiz:* P22 encapsula **in-vivo** por co-expresión de scaffold; el proyecto hace
    **packing in-silico** (Packmol/PyMOL) de enzima exógena. La comparabilidad es
    arquitectónica, no mecanística.
- **Advertencia accionable (preprint, confianza media):** el protocolo óptimo de carga
  es **dependiente de la enzima/ortólogo** — no transfiere entre enzimas cargo distintas.
  La Puerta 2 debería permitir probar varias condiciones empíricamente, no asumir un
  protocolo de empaquetamiento fijo. — *bioRxiv 2022.02.10.479872v2 (3 ortólogos de
  mevalonato quinasa en P22). No revisado por pares.*

---

## 🟡 Puerta 3 «fuera» (de-inmunización) — hoy ilustrativa; hay motores reales listos

Es la puerta con **mayor salto disponible**: pasar de maqueta a motor real ya.

- **NetMHCIIpan-4.3 — candidato #1.** Predice unión de péptidos a MHC clase II
  (HLA-DR/DQ/DP humanas, + ratón H-2, bovino BoLA-DRB3) por redes neuronales, entrenado
  con 650.000+ mediciones. **Hay paquete standalone descargable para Linux y macOS**
  (Linux, Linux_arm64, Darwin_x86_64, Darwin_arm64), corrible por CLI `netMHCIIpan`
  (requiere `tcsh`), integrable en pipeline. MHC-II = epítopos **CD4+**, los más
  relevantes para de-inmunizar enzimas terapéuticas como la glucocerebrosidasa.
  — *DTU Health Tech, services.healthtech.dtu.dk/services/NetMHCIIpan-4.3/.*
  - *Matiz:* predice **unión a MHC**, proxy necesario pero no suficiente de
    inmunogenicidad real de células T. Requiere aceptar licencia académica.
- **Patrón King et al. (PNAS 2014) — plantilla del «motor real».** SVM de epítopos +
  rediseño estructural en Rosetta para eliminar epítopos conocidos y predichos
  maximizando contenido humano sin romper estructura/función.
  — *King, Garza, Mazor, Linehan, Pastan, Pepper & Baker, PNAS 111(23):8577-8582, 2014
  (PMC4060723).*
  - *Caveat:* método de 2014 (un SVM a medida es menos estándar hoy que NetMHCIIpan
    4.x); Rosetta es libre para académicos pero tiene curva de aprendizaje real, así que
    «construible por una persona» es interpretación blanda. La **validación wet-lab**
    (eliminar epítopos de GFP y exotoxina A de Pseudomonas manteniendo función) quedó
    **SIN VERIFICAR** — 2 de 3 verificadores fallaron por error de infraestructura, no
    fue confirmada ni refutada. El claim del método (SVM+Rosetta) sí está confirmado 3-0.
- **NG-IEDB (complementario, encadenable, sin login).** Permite construir pipelines
  encadenando la salida de una herramienta como entrada de la siguiente.
  — *Nucleic Acids Res 2024, gkae407 (PMC11223806).*
  - *Matiz importante:* la suite NG verificada es **solo MHC clase I** (CD8+/citotóxica),
    **subóptima** para de-inmunizar enzimas (dominada por clase II/CD4+). Usar
    **NetMHCIIpan como motor primario**, no este.

---

## 🟢 Puerta 4 «sobrevive» (MD) — SIRAH confirmado apto; queda un vacío

- **SIRAH es un campo de fuerza CG/multiescala auto-consistente** apto para ensamblajes
  heterogéneos grandes como una cápside VLP cargada con enzima. La elección del proyecto
  está justificada. — *J Struct Biol 2023, S1047847723000485 (autores de SIRAH); JCTC
  2015 (FF de proteínas); Fat SIRAH (lípidos).*
- **VACÍO:** **ningún** claim sobreviviente comparó **SIRAH vs Martini 3** directamente,
  ni verificó un protocolo de validación de la MD con **RMSF / factores B**
  cristalográficos. Ese eje quedó sin respuesta sólida.

---

## ⚠️ Reproducibilidad (eje e) — el MAYOR hueco: la investigación NO lo cerró

**Ningún claim sobre Snakemake/Nextflow/conda/contenedores/FAIR sobrevivió a la
verificación adversarial**, así que el reporte no da recomendación verificada aquí.
Pistas del material bruto (SIN verificar, tomar con cautela):
- Para pipelines cortos de una persona, un shell script bien estructurado o un pequeño
  Makefile puede ser lo correcto antes que un gestor como Nextflow/Snakemake.
  *(blog cytogence.com — fuente débil).*
- El problema real de la MD es el **metadato**: *"sin metadatos apropiados, compartir
  datos es inútil y su reutilización está condenada"*. — *eLife 90061, 2024.*
- Arcadia Science eligió Nextflow sobre Snakemake por integración con AWS Batch (caso de
  uso de nube, no directamente aplicable a un solo desarrollador local).

**Este sigue siendo el punto ciego más grande** — irónicamente es justo lo que el
proyecto está construyendo con VLP-08 (CI) y el sistema ESTADO/PENDIENTES/BITACORA.
Recomendación: una segunda búsqueda enfocada SOLO en este eje.

---

## Lo más urgente que «se nos estaba pasando» (resumen de acción)

1. **Puerta 1 está científicamente frágil.** Reportar un radio de HOLE como veredicto
   binario paso/no-paso es criticable. **Añadir el proxy de agua (CHAP) es la corrección
   de mayor valor y menor esfuerzo.** Considerar CAVER/CaverDock y, para finalistas, PMF.
2. **Puerta 3 puede dejar de ser maqueta YA.** NetMHCIIpan-4.3 es descargable y corrible
   localmente; convierte la puerta de ilustrativa a funcional.
3. **Reproducibilidad quedó sin respuesta verificada.** Merece una segunda búsqueda
   enfocada si importa.

---

## Preguntas abiertas (del propio reporte)

1. ¿Qué prácticas concretas de reproducibilidad (Snakemake vs Nextflow, conda vs
   contenedores, metadatos FAIR) son las más realistas para un pipeline de un solo
   desarrollador que encadena HOLE2/CAVER, Vina/CaverDock, NetMHCIIpan y MD SIRAH?
2. ¿SIRAH o Martini 3 para simular la supervivencia de una cápside VLP+enzima, y cómo se
   valida esa MD CG contra observables experimentales (RMSF, factores B)?
3. Para el poro específico de la cápside diana (¿canal axial simple o realmente
   ramificado?), ¿aporta CAVER ventaja real sobre HOLE2, o el caso axial favorece a
   HOLE + CHAP + PMF?
4. ¿Cómo acoplar el flujo geometría→energía (CAVER/HOLE2 → proxy de agua → PMF) al
   cribado de mutantes sin volverlo inviable: cuántos mutantes pasan del filtro barato
   al PMF caro?

---

## Fuentes verificadas (principales)

| Puerta / eje | Fuente | Calidad |
|---|---|---|
| P22 encapsulación | ACS Nano 2012, nn300545z | primaria |
| P22 poro dinámico | Nat Commun 2021, s41467-021-23200-1 | primaria |
| P22 carga enzima-dependiente | bioRxiv 2022.02.10.479872v2 | preprint |
| Gating hidrofóbico / CHAP | Channels 2017, PMC5555266 | primaria |
| CAVER 3.0 | PLoS Comput Biol 2012, pcbi.1002708 | primaria |
| MOLE 2.0 | J Cheminform 2013, PMC3765717 | primaria |
| CAVER Web | Nucleic Acids Res 2019, W414 | primaria |
| CaverDock | Bioinformatics 2019, PMC6828983 | primaria |
| PMF/umbrella sampling | PubMed 33576049 | primaria |
| NetMHCIIpan-4.3 | DTU Health Tech (NetMHCIIpan-4.3) | primaria |
| De-inmunización SVM+Rosetta | PNAS 2014, 1321126111 | primaria |
| NG-IEDB | Nucleic Acids Res 2024, gkae407 | primaria |
| SIRAH force field | J Struct Biol 2023, S1047847723000485 | primaria |

**Stats:** 5 ejes · 24 fuentes · 115 afirmaciones · 25 verificadas · 24 confirmadas ·
0 refutadas · 1 sin verificar · 106 llamadas a agentes · ~45 min.
