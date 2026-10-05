# Reparación del motor de packing — decisiones y pendientes

> Rama: `claude/fix-packing-engine-pf6f6y` · Fecha: 2026-10-05
>
> Repara los defectos confirmados por dos auditorías independientes
> (`AUDITORIA_PACKING.md` en `claude/audit-packing-engine-wwph45` y
> `claude/audit-packing-engine-vdvq69`) y consolidados en `HOJA_DE_RUTA.md`
> (`claude/consolidate-audit-roadmap-k82rek`) como PK-2, PK-3, PK-4 y PK-5. No es una
> auditoría: el diagnóstico ya estaba hecho. Aquí se anota **qué se cambió, qué decisión
> de software se tomó en cada punto y qué queda pendiente porque exige criterio
> científico del autor**, no de software.
>
> Sin PACKMOL ni PyMOL en el entorno: todo se verificó con un doble de PACKMOL que emite
> las cadenas reales de los dos logs commiteados (`tests/fixtures/packmol_logs/`).

---

## 1. Qué estaba roto (resumen de las auditorías)

| ID | Defecto | Efecto medido |
|---|---|---|
| P-01 / PK-01 | La regex buscaba `Maximum distance violation:`; PACKMOL escribe `Maximum violation of target distance:` | El umbral de violación no se aplicó nunca |
| P-02 / P-04 | Fallback "≥ 10 000 líneas ATOM" que la cápside sola (168 480–216 780 átomos) satisface; `n_packed` = N pedido, no medido | Un empaquetado con **cero** enzimas se aprobaba; con el doble: 100 enzimas, σ 0,00 |
| P-03 | Solo quedaba el código de salida; `<output>_FORCED` y `ENDED WITHOUT PERFECT PACKING` no se miraban | Si PACKMOL devuelve 0 sin converger, la capacidad era el techo del bucle (100) |
| PK-02 | Cápside `fixed` sin `center`; si el centrado fallaba, el runner seguía con el PDB sin centrar | Enzimas empaquetadas a 360 Å de la cápside (BMV) |
| P-05 / P-12 / P-19 | `seed_base`, `use_random_seeds`, `timeout`, `collision_margin` del YAML no se leían; semilla aleatoria, timeout 90 s y margen 2,0 hardcodeados | Irreproducible; capacidad dependiente del hardware |
| G-01 / PK-09 | Cero tests del motor | Todo lo anterior sobrevivió a 22 tests verdes |

---

## 2. Qué se cambió y qué decisión se tomó

### 2.1 Criterio de aceptación (`src/packing/parallel_packer.py`) — P-01, P-02, P-03, P-04

Nuevo criterio, en este orden, para cada corrida de PACKMOL:

1. Existe `<output>_FORCED` → rechazo `forced_output`.
2. El log contiene `ENDED WITHOUT PERFECT PACKING` → rechazo `ended_without_perfect_packing`.
3. Código de salida ≠ 0 → rechazo `exit_code`.
4. No existe `<output>` → `no_output`.
5. El log no contiene `Success!` → `no_success_marker`.
6. No hay ningún valor de `Maximum violation of target distance:` → `no_violation_value`.
7. El **último** valor de esa línea (el del bloque final) > `max_violation_threshold` →
   `violation_above_threshold`.
8. Líneas atómicas del output ≠ `átomos_cápside + N × átomos_enzima` → `atom_count_mismatch`.
   Aquí se mide de verdad cuántas copias hay (`n_enzymes_found`).
9. El centroide de alguna copia de enzima está a más de `packing_radius` del centroide de
   la cápside **en el mismo archivo de salida** → `enzymes_outside_capsid`.

**Decisiones:**

- *Las señales de no convergencia van antes que el código de salida.* Las dos auditorías
  coinciden en que PACKMOL escribe el punto actual en `<output>` durante la optimización y
  que hay versiones que salen con 0 sin converger (P-03 / PK-01 "REQUIERE CORRER"). El
  criterio nuevo no depende de cuál sea la versión instalada: rechaza por `_FORCED` y por
  el marcador de fallo aunque el exit sea 0. Se prueba explícitamente
  (`test_forced_output_with_exit_zero_and_partial_pdb_is_rejected`).
- *Se retira el fallback por conteo de líneas* y la clave `packing.min_lines_threshold`
  del YAML (se deja comentada la razón). No hay criterio de reserva: si el log no permite
  decidir, la corrida se rechaza y la causa queda registrada.
- *Se toma el último valor de violación del log, no el primero.* En los logs reales los
  bloques de iteración llevan valores intermedios (3,97 Å…) y el final 0,000000.
- *La regex acepta números Fortran* (`.12571E-01`, `7.766E-003`, `1.5D+00`).
- *Cada rechazo se registra con su causa* en `replica_N/metadata.json` (`attempts[]`,
  `rejection_reasons`) y agregado en `summary/statistics.json` y `report.txt`. Un
  `timeout` ya no es indistinguible de "no cabe".
- *El techo de búsqueda (100) se mantiene pero se delata:* si una réplica lo alcanza,
  `search_ceiling_reached = true` y el resultado consolidado lleva un aviso de que el
  máximo es una constante del código, no una medición.
- *`stdev` con menos de dos réplicas exitosas es `None`* ("no definida"), nunca 0. La UI
  muestra "—". Antes un 0 fabricaba apariencia de convergencia (P-07).
- Se añade `n_replicas_at_best` (cuántas réplicas alcanzan el máximo) al JSON y al
  reporte. **No** se cambia el estadístico titular (ver §3, DC-6).
- Los descriptores de `stdin`/`stdout` del subproceso se cierran (`with`); antes se
  filtraban en cada corrida.

### 2.2 Centrado y `center` (PK-02, T2 de la hoja de ruta)

- El `.inp` lleva `center` encima de `fixed 0. 0. 0. 0. 0. 0.`: PACKMOL recentra la
  cápside en el origen aunque el PDB de entrada no lo esté (como ya hacía el `.inp` de
  sustratinaitor). Verificado con el doble, que honra o ignora `center` según se le pida.
- El centrado de cápside y enzima deja de depender de PyMOL: es una traslación de
  coordenadas en Python puro (`src/core/pdb_geometry.py`) que **conserva los registros
  `TER`** y el resto del archivo. Esto elimina el modo de fallo "sin PyMOL → cápside sin
  centrar" y, de paso, la primera pérdida de `TER` (180 → 3) que señalaba P-22. La
  segunda pérdida (la que causa PACKMOL) queda pendiente (PK-8 / T1).
- Los archivos centrados se escriben en el directorio del experimento
  (`Output/<cápside>/<enzima>/capside_centered.pdb`), no en `Input/` (P-17).
- `ExperimentRunner` **ya no sigue adelante** si el centrado falla: propaga la excepción.
- Verificación geométrica a posteriori (criterio 9 de §2.1): aunque alguien quite el
  `center` o PACKMOL cambie de semántica, un output con las enzimas fuera de la cápside se
  rechaza con causa `enzymes_outside_capsid`.

### 2.3 El radio de reserva (P-11 / PK-07, parte de PK-3)

- `Capsid.calculate_internal_radius` ahora deja constancia de la procedencia del valor en
  `Capsid.radius_source`: `"calculated"` o `"default"`. El endpoint `/api/capsid/radius` no
  cambia de comportamiento (sigue devolviendo el valor; distinguirlo en la respuesta es
  PK-3 completo, fuera de este encargo).
- `ExperimentRunner` **se niega a ejecutar un experimento con el radio de reserva**:
  lanza `RuntimeError` con la causa (PyMOL no importable en el intérprete o cálculo
  fallido) y la salida (instalar el módulo `pymol` o pasar `internal_radius` explícito).
  Antes corría con 90 Å para cualquier cápside y sin centrar.
- Se añade `internal_radius` opcional a `run_maximum_packing`, `services.run_experiment` y
  al JSON de `/api/experiment/run`. **La UI no lo envía a propósito:** el campo "Radio
  interno" del Studio vale 90 por defecto para la vista previa, y mandarlo a ciegas
  reproduciría el fallback silencioso. Si el autor quiere ese atajo en la UI, debe ser una
  acción explícita del usuario (p. ej. una casilla "usar este radio").

### 2.4 Configuración leída de verdad (P-05, P-12, P-19, P-20)

`ExperimentRunner.packing_parameters()` es el único punto de lectura y pasa al motor:

| Clave YAML | Antes | Ahora |
|---|---|---|
| `engines.packmol.seed_base` (1234567) | no se leía; `random.randint` por réplica | semilla de la réplica i = `seed_base + i`; reintento k = `+ 1000·k` |
| `engines.packmol.use_random_seeds` (false) | no se leía | si `true`, semillas de `SystemRandom`, registradas en metadata y `report.txt` |
| `engines.packmol.timeout` (300) | `timeout=90` hardcodeado | se usa; un timeout es causa `timeout` registrada |
| `packing.collision_margin` (2.0) | `2.0` hardcodeado en el motor | se usa: esfera = radio − margen; queda en `run_config.packing_radius` |
| `engines.packmol.max_workers` (nuevo, `null`) | `min(cpu, 7)` | configurable; documentado que afecta a los timeouts |
| `experiments.n_replicas` (10) | `ExperimentManager.n_replicas = 7` | el manager lee la config y acepta el N pedido |

**Decisiones:**

- Con `seed_base` ausente y `use_random_seeds: false`, se usa 1234567 (la semilla por
  defecto de PACKMOL). La llamada sin argumentos es reproducible; aleatorio solo si se pide.
- Los valores de reserva del código se alinean con el YAML (`exclusion_radius` 5.0,
  `max_violation_threshold` 0.10): antes el código decía 10.0 y 0.05 (P-20). Son solo
  fallbacks; en producción gana el YAML.
- `run_config` (todos los parámetros efectivos, semillas, nº de átomos, centroide de
  entrada) se guarda en `summary/statistics.json` y se imprime en `report.txt`.

### 2.5 Respuesta de la API y UI

- `/api/experiment/run` devuelve `status: "failed"` y `error` cuando ninguna réplica fue
  aceptada; antes devolvía `completed` con `success: false` y la UI pintaba en verde
  "Packing real OK: 0 enzimas". `packing.js` trata `failed` como error y muestra "—" para
  σ no definida. La respuesta incluye `seeds`, `warnings`, `rejection_reasons`,
  `n_replicas_at_best` y `radius_source`.

### 2.6 Tests (`tests/test_packing_engine.py`, `tests/test_experiment_runner.py`)

- `tests/packmol_double.py`: doble de PACKMOL que lee el `.inp` por stdin y emite las
  cadenas reales. Modos: capacidad máxima (más copias → `ENDED WITHOUT PERFECT PACKING`,
  `_FORCED`, exit configurable 173 o 0, y `<output>` parcial), `capsid_only` (Success! con
  cero enzimas), `ignore_center`, `sleep` (timeout), `crash`, `final_violation`.
- `tests/fixtures/packmol_logs/`: los dos logs reales del repo (PACKMOL 20.14.3 y 21.0.1)
  como especificación del parser.
- `tests/pdb_fixtures.py`: cápside sintética de 12 000 átomos (> 10 000 a propósito: el
  fallback viejo la aceptaba) y enzima de 50.
- 30 tests del motor + 9 del runner/centrado. **Contra el código de `main`: 28 de 30
  fallan** (los 2 restantes solo documentan fixtures) y la suite del runner no importa.
  Suite completa: 60 pasan, 1 se salta (`@pytest.mark.engine`, PACKMOL real; corre en la
  máquina del autor y comprueba que el vocabulario del log de la versión instalada
  coincide con el parser).
- CI (`ruff check`, `ruff format --check`, `pytest -q`) verde sin PACKMOL ni PyMOL.

---

## 3. Decisiones pendientes para el autor (criterio científico, no de software)

No se ha tocado nada de esto. Cada punto está anotado en el código donde corresponde.

| # | Decisión | Dónde | Referencia |
|---|---|---|---|
| **DC-A** | **CIENCIA-1, signo del ±1 Å del radio interno.** El código suma 1 Å (como el script original); docstring, README y CLAUDE.md dicen restar. Las dos auditorías argumentan "restar" (o mejor: redefinir el radio con `d_min − r_vdW` y radios de van der Waals, sin PyMOL ni rejilla de 1 Å). Se deja el `+1` tal cual, con un comentario `DECISIÓN CIENTÍFICA PENDIENTE`. | `capsid.py` (bucle del pseudoátomo) | P-08/P-09/P-10, PK-06, HOJA PK-6 / DC-2 |
| **DC-B** | **`exclusion_radius = 5.0`** es radio *por átomo* en PACKMOL (10 Å enzima–enzima, 6 Å enzima–cápside efectivos) y es la perilla que fija la capacidad. Hace falta justificarlo y publicar un barrido `N_max(radius)`. Se deja 5.0 (valor del YAML). | `default.yaml` | P-13/P-14, PK-05, HOJA PK-7 |
| **DC-C** | **Qué estadístico se publica.** El titular sigue siendo `best` (máximo sobre réplicas, que crece con el nº de réplicas). Se añade `n_replicas_at_best` como dato, pero elegir titular (máximo etiquetado + fracción que lo alcanza + mediana/IQR) es decisión del autor. | `parallel_packer._consolidate_results`, UI | P-06/P-07, PK-08, HOJA DC-6 |
| **DC-D** | **`max_violation_threshold = 0.10 Å`.** Ahora sí se aplica. El valor es el del YAML; el código decía 0.05. ¿Es 0.10 el umbral científico correcto? Los dos logs reales terminan en 0.000000, así que hoy no discrimina nada, pero debe quedar justificado. | `default.yaml` | P-20, PK-01 |
| **DC-E** | **PK-1: medir PACKMOL real.** Versión instalada, código de salida al no converger (173 o 0), si deja `<output>` además de `_FORCED`. El criterio nuevo no depende de la respuesta, pero el dato debe quedar registrado. `pytest -m engine` corre el test de vocabulario del log con la versión instalada. | máquina del autor | P-03, PK-1 |
| **DC-F** | **Esfera inscrita como región de empaque.** La fija la punta de una Arg (0,14 % de los átomos); la pared real empieza ~7 Å más afuera. Conservador para "no salir", subestima el volumen. Documentarlo o cambiar de criterio. | `capsid.py`, paper | P-09, PK-12 |
| **DC-G** | **Radio en la UI.** La API acepta `internal_radius`; la UI no lo envía (ver §2.3). Decidir si debe existir el atajo y con qué salvaguarda. | `packing.js` | HOJA PK-4 |

Pendientes de **software** fuera de este encargo y no tocados: `TER` perdidos por PACKMOL
y seriales hexadecimales en el PDB entregado (P-22 / T1), carpetas de experimento con
timestamp y limpieza de `packed_*.pdb` (P-16 / P-21 / PK-8), caché del radio por cápside
en lugar de `radio_interno.txt` global (P-18 / PK-10), `/api/health` que compruebe
`import pymol` (PK-14), y el preview del Studio (PK-9).
