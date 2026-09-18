# Revisión científica de los motores — briefing para una auditoría INDEPENDIENTE

> **Propósito:** encargar a otra instancia (u otra persona) una **auditoría científica de
> los 4 motores DESDE CERO.** Objetivo explícito: un juicio *independiente*, no la
> confirmación de una revisión previa.
>
> **REGLA ANTI-SESGO (importante):** no asumas conclusiones de nadie. Forma tu propio
> criterio a partir del código y —donde se pueda— corriéndolo. Si existe una lista de
> "hallazgos de una pasada previa", trátala como **sospechas sin verificar, para
> cross-check SOLO DESPUÉS de tu propia pasada**, nunca como punto de partida. Lucio pidió
> expresamente que lo visto en una sesión previa **no sea norma**.

## Contexto neutral del proyecto

Plataforma **VLP Studio / PAC-ZYME**: diseño de nanocápsulas VLP cargadas con enzimas
terapéuticas (caso: glucocerebrosidasa para Gaucher). Embudo de 4 filtros, cada uno con un
motor:

- **Packing / Studio** (`nanocapsule-mvp/`): radio interno de la cápside (PyMOL) +
  empaquetamiento de enzimas con PACKMOL + validación estadística por réplicas.
- **Poromania** (`Poromania.v.1.2./`): análisis de poro con HOLE2 + mutagénesis (PyMOL) +
  docking (idock). *Nota:* el Studio tiene una versión más nueva de este análisis
  (`nanocapsule-mvp/src/services/pore.py`); verifica cuál generó cada resultado.
- **PackMan** (`PackMan.v.1.2/`): dinámica molecular coarse-grained SIRAH (AMBER) del
  sistema enzima-en-cápside. Trae la distribución oficial de SIRAH con sus `.in` de
  referencia en `archivos_dm_cg/sirah_x2.3_24-07.amber/tutorial/` — úsalos como patrón.
- **sustratinaitor** (`sustratinaitor/`): construcción del sustrato CG + empaquetado
  alrededor de la cápside para MD.

Frontera permanente: los engines de terceros (HOLE/PACKMOL/PyMOL/Vina/AMBER/SIRAH) se
**llaman, no se forkean** — la auditoría es de *cómo se usan*, no de sus tripas.

## La tarea

Para cada motor, audita de forma independiente:
1. **Setup del sistema** — resolución (CG vs all-atom), force field, moléculas, carga,
   caja, iones. ¿Todo consistente entre etapas?
2. **Método / parámetros** — para MD: timestep, cutoff, termostato, restricciones (SHAKE),
   protocolo de equilibración/calentamiento. ¿Coinciden con lo que el force field exige?
   Para poro: eje/centro del canal, semilla, validación de canal. Para packing: cálculo de
   radio, constraints de PACKMOL, criterio de convergencia/capacidad.
3. **Análisis** — cómo se extraen las métricas; artefactos conocidos del modelo.
4. **Reproducibilidad** — semillas fijas, ¿los inputs commiteados reproducen lo reportado?

Método sugerido: **no te quedes leyendo scripts.** Donde se pueda, corre un caso pequeño y
observa (¿HOLE reproduce el mismo radio dos veces?, ¿el sistema CG mantiene integridad?,
¿una MD corta se mantiene estable?). El comportamiento real vale más que la inspección.

## Preocupación declarada por Lucio (el autor)

Lucio señala que **las corridas de MD pueden estar mal** → trata todo resultado de dinámica
como **provisional** hasta verificarlo independientemente. No lo des por bueno ni por malo:
compruébalo.

## Lo que NO está en el repo y hace falta para una auditoría real

(Sin esto, cualquier auditoría solo revisa los *scripts commiteados*, no lo que realmente
corrió. Pedírselo a Lucio.)

- [ ] Los **inputs de producción reales** (los `.in` commiteados podrían ser stubs de
  prueba — verifica `nstlim`) y los **logs/outputs** de las corridas de la tesis
  (equilibración, calentamiento, producción).
- [ ] Las **trayectorias** y los `.dat` de análisis (gitignoreados / en la workstation con GPU).
- [ ] **Qué versión de código generó cada resultado** (p.ej. ¿los perfiles de poro salieron
  de Poromania standalone o del Studio? ¿la MD usó `run_MD.sh` o una ruta manual?).
- [ ] Las **decisiones científicas** que podrían parecer bugs pero fueron intencionales
  (ver CIENCIA-1/2/3 en `ESTADO.md`): signo del margen del radio, resolución de
  sustratinaitor, protocolo de calentamiento.
- [ ] Un **entorno donde correr** los engines (HOLE/PACKMOL/AMBER/SIRAH instalados; GPU para MD).

## Entregable

Por motor: severidad, qué está bien, qué es dudoso (con evidencia concreta: archivo+línea o
comando+observación), y qué verificar/correr para confirmarlo. Y **explícitamente**: en qué
difiere tu juicio de cualquier revisión previa, si la lees.
