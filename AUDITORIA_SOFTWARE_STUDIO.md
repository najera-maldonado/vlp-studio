# Auditoría de la capa de software del Studio

**Alcance:** `nanocapsule-mvp/src/web` (Flask, rutas, plantillas, JavaScript de cliente),
`src/services`, `src/core`, `src/io`, `src/packing`, `Dockerfile`, `docker-compose.yml`,
`.github/workflows/ci.yml`, `tests/`, `setup.py`, `requirements*`, `config/default.yaml`.

**Qué NO cubre:** la validez científica de los motores (HOLE, Packmol, PyMOL, Vina,
GROMACS). Eso es objeto de las cuatro auditorías previas y de `REVISION_MOTORES.md`. Aquí
se audita la *aplicación*: lo que un revisor de JOSS o un usuario puede romper, y lo que
puede producir un número equivocado sin que nadie se entere.

**Método:** lectura completa de los 7.020 renglones de código de la capa de aplicación,
más verificación ejecutada de los hallazgos graves con el cliente de pruebas de Flask y
medición real de cobertura (`pytest --cov`, Python 3.11, dependencias de
`requirements.lock`). Los hallazgos marcados **[verificado]** se reprodujeron en esta
sesión; los marcados **[por lectura]** se sostienen sobre el código pero no se ejecutaron
(en general porque requieren PyMOL, HOLE, Packmol o Vina, ausentes en el entorno de
auditoría).

**No se modificó código.**

---

## 1. Resumen ejecutivo

La capa de aplicación está bien organizada: la separación en fachada de servicios
(`packing_service` reexportando cinco módulos de puerta) es limpia, hay un lock de
dependencias generado con `pip-compile`, el CI corre lint y tests, y el `Dockerfile` es
honesto sobre sus límites. **No hay secretos en el código ni en los 47 commits del
historial.** Nada de `shell=True`, ningún SQL, ninguna deserialización insegura.

Dicho eso, hay dos problemas que deben arreglarse antes de que el repositorio siga siendo
público, y un conjunto de problemas de integridad científica que un revisor de JOSS
encontrará.

El primero es ejecución remota de código. `POST /api/pore/mutant` toma la posición de la
mutación del cuerpo JSON sin validarla, la interpola en texto de un programa Python y
ejecuta ese programa con `pymol -cq`. Se verificó la inyección. El segundo es que no hay
autenticación en ninguna de las 32 rutas, y siete de ellas parsean el cuerpo con
`force=True`, lo que las hace alcanzables por petición cruzada desde cualquier página web
sin verificación previa de CORS. Juntos significan: cualquier sitio que el usuario visite
mientras el Studio corre en su máquina puede ejecutar comandos en esa máquina.

En integridad científica el patrón repetido es el mismo: **un fallo del motor se convierte
en un número con pinta de medida.** Si PyMOL no está o falla, el radio interno devuelto es
la constante 90,0 Å y la API responde `"status": "success"` con el mensaje «Radio interno
calculado: 90.0 Å». Las réplicas de empaquetamiento usan semillas aleatorias aunque
`config/default.yaml` documente un `seed_base` para reproducibilidad: esa clave no la lee
nadie. Y la validación de empaquetamiento tiene un camino de reserva que cuenta líneas
atómicas contra un umbral de 10.000, cuando la cápside sola aporta 216.780.

La cobertura real es del **30%**. Cuatro módulos de `src/core` están al 0%, incluido
`capsid.py`, donde vive el cálculo del radio interno. De las 32 rutas, **16 nunca ejecutan
una sola línea de su cuerpo en ninguna prueba**.

### Recuento

| Severidad | Nº | Significado |
|---|---|---|
| Crítica | 2 | Ejecución de código o compromiso del equipo del usuario |
| Alta | 11 | Resultado científico equivocado sin aviso, denegación de servicio, o el repositorio no se instala |
| Media | 17 | Fragilidad, datos cruzados, documentación que contradice al código |
| Baja | 7 | Pulido, deuda de metadatos |

---

## 2. Hallazgos críticos

### C1 · Ejecución remota de código por inyección en el script de PyMOL

**Severidad: crítica. [verificado]**

`src/services/pore.py:228-247` construye un programa Python como texto y lo ejecuta:

```
src/services/pore.py:232   lines = ["from pymol import cmd", f"cmd.load(r'{wt_pdb}','WT')"]
src/services/pore.py:238       lines.append("cmd.wizard('mutagenesis'); w=cmd.get_wizard()")
src/services/pore.py:240       f"w.set_mode('{aa}'); w.do_select('/{tag}//{ch}/{pos}/'); w.apply(); cmd.set_wizard()"
src/services/pore.py:246   script.write_text("\n".join(lines))
src/services/pore.py:247   subprocess.run(["pymol", "-cq", str(script)], ...)
```

El aminoácido `aa` sí se valida contra el conjunto `_AA3` en `pore.py:285-286`. **La
posición `pos` no se valida en absoluto**: `pore.py:287` solo hace
`muts[str(pos).strip()] = aa`. No se comprueba que sea un entero. Esa cadena entra en una
f-string entre comillas simples, y cerrar la comilla basta para escribir sentencias
Python arbitrarias en el archivo que PyMOL va a ejecutar.

Cadena completa, sin autenticación:

```
POST /api/pore/mutant   →  app.py:167-177
  svc.evaluate_mutant(structure, mutations)   →  pore.py:274
    muts[str(pos).strip()] = aa               →  pore.py:287   (pos sin validar)
    _generate_mutants(...)                    →  pore.py:295
      script.write_text(...)                  →  pore.py:246
      subprocess.run(["pymol","-cq",script])  →  pore.py:247   (ejecuta)
```

Reproducción en esta sesión, con la carga
`1'); import os; os.system('echo INYECTADO'); w.do_select('/x//A/1/`
como clave de `mutations`. Línea 5 del `_mutgen.py` generado:

```python
w.set_mode('GLY'); w.do_select('/man_test//A/1'); import os; os.system('echo INYECTADO'); w.do_select('/x//A/1//'); w.apply(); cmd.set_wizard()
```

La inyección es Python sintácticamente válido, así que el intérprete de PyMOL la ejecuta
completa. El `Dockerfile:34` instala `pymol`, de modo que en la imagen publicada el camino
está armado de punta a punta. La única condición extra es que `structure_key` apunte a un
modelo que exista; `../Poromania.v.1.2./modelos/BMV/poro3fold.pdb` y tres más valen, y
`GET /api/pore/structures` los enumera sin autenticación.

**Reparación:** validar la posición como entero antes de usarla
(`if not str(pos).isdigit(): raise ValueError(...)`), y dejar de generar código. El
camino correcto es pasar las mutaciones a PyMOL como datos, no como fuente: escribir un
JSON o un TSV y que un script fijo y versionado lo lea. Mientras se genere texto de
programa a partir de entrada del usuario, la validación es la única barrera y cualquier
descuido futuro reabre el agujero.

### C2 · Ninguna ruta tiene autenticación, y siete son alcanzables por petición cruzada

**Severidad: crítica (como amplificador de C1). [verificado]**

Las 32 rutas de `src/web/app.py` están abiertas. No hay `SECRET_KEY`, ni sesiones, ni
tokens, ni comprobación de origen, ni límite de tasa. Eso sería defendible en una
herramienta que escucha solo en `127.0.0.1`, pero no es el caso: `config/default.yaml:85`
fija `host: "0.0.0.0"` y `docker-compose.yml:11` publica `5000:5000`, así que el servicio
queda expuesto a toda la red local.

Peor: siete rutas POST parsean el cuerpo con `request.get_json(force=True)`, que ignora el
`Content-Type`.

```
src/web/app.py:105   /api/pore/profile
src/web/app.py:144   /api/pore/run_hole
src/web/app.py:157   /api/pore/screen
src/web/app.py:170   /api/pore/mutant        ← el de C1
src/web/app.py:183   /api/pore/dock
src/web/app.py:195   /api/pore/section
src/web/app.py:235   /api/md/prepare
```

Una petición con `Content-Type: text/plain` es una petición CORS «simple»: el navegador la
envía **sin verificación previa**. El atacante no puede leer la respuesta, pero no le hace
falta: el efecto secundario ya ocurrió. Verificado con el cliente de pruebas:

| Petición | Resultado |
|---|---|
| `POST /api/pore/profile` con `text/plain` | 200 |
| `POST /api/pore/mutant` con `text/plain` | 404 *(procesada; 404 solo porque la estructura de prueba no existe)* |
| `POST /api/files/cleanup` con `text/plain` | 500 *(no usa `force`; exige `application/json`)* |

Es decir: **cualquier página web que el usuario visite mientras el Studio corre en su
máquina puede disparar C1 y ejecutar comandos en esa máquina.** El que `/api/files/cleanup`
se salve es accidental, no diseñado: usa `get_json()` sin `force`, lo que obliga a
`application/json` y por tanto a verificación previa.

**Reparación, en este orden:**

1. Que el servidor escuche en `127.0.0.1` por defecto. `0.0.0.0` debe ser una opción
   explícita y documentada, no el valor de fábrica.
2. Quitar `force=True` de las siete rutas. Si el cliente propio manda
   `application/json`, y lo manda (todos los `fetch` de `static/js/` fijan la cabecera),
   `force` no aporta nada y sí quita la protección gratuita que da CORS.
3. Comprobar la cabecera `Origin` en los POST y rechazar lo que no venga del propio
   servidor.
4. Si el Studio alguna vez se despliega para más de una persona, hace falta autenticación
   real. Ahora mismo no hay ningún concepto de usuario.

---

## 3. Hallazgos altos

### A1 · El radio interno devuelve una constante como si fuera una medida

**Severidad: alta (integridad científica). [por lectura]**

`src/core/capsid.py` tiene dos caminos que sustituyen el cálculo por el valor por defecto
de 90,0 Å sin dejar rastro en el valor devuelto:

```
src/core/capsid.py:72-77    si PyMOL no está disponible → devuelve 90.0
src/core/capsid.py:163-168  except Exception → devuelve 90.0
```

El segundo captura cualquier fallo: PDB corrupto, PyMOL sin bibliotecas gráficas, memoria
insuficiente, cualquier cosa. El `print` del error va a la consola del servidor, que el
usuario del navegador no ve. Y el valor devuelto es indistinguible de una medida real.

Lo que el usuario recibe, de `src/web/app.py:260-268`:

```json
{"status": "success", "internal_radius": 90.0,
 "message": "Radio interno calculado: 90.0 Å"}
```

«calculado» es falso en ese camino. Y el daño no se queda en la pantalla: el radio
alimenta el empaquetamiento real. `src/core/experiment_runner.py:114-117` repite el mismo
patrón, cayendo al mismo 90,0 Å, y ese número entra en el input de Packmol como radio de
la esfera (`src/packing/parallel_packer.py:269`). Un experimento completo puede correr,
publicar «Mejor resultado: N enzimas» y estar construido sobre una constante que nadie
midió.

**Reparación:** devolver la procedencia junto al valor. Que `calculate_internal_radius`
devuelva algo como `{"value": 90.0, "source": "default", "reason": "PyMOL no disponible"}`
y que la API lo propague, con `status` distinto de `success`. El frontend debe mostrarlo:
`static/js/packing.js:45` pone el número en el campo de radio sin ninguna marca. Un
usuario no puede distinguir hoy una medida de un relleno.

### A2 · Los experimentos no son reproducibles, y la configuración dice que sí lo son

**Severidad: alta (integridad científica). [verificado por lectura exhaustiva]**

`config/default.yaml:36-40` documenta:

```yaml
    # Semilla base para reproducibilidad
    # Cada réplica usará seed_base + replica_number
    seed_base: 1234567
    # Si use_random_seeds es true, ignora seed_base y usa semillas aleatorias
    use_random_seeds: false
```

**Ninguna de esas dos claves se lee en ninguna parte del repositorio.** Un `grep` de
`seed_base` y `use_random_seeds` sobre todo `src/` solo encuentra el parámetro homónimo de
`parallel_packer.py:83`, que nadie rellena:
`src/core/experiment_runner.py:160-170` llama a `run_parallel_replicas` con ocho argumentos
y `seed_base` no está entre ellos. Así que se queda en `None` y se toma la otra rama:

```
src/packing/parallel_packer.py:115-118
    if seed_base is not None:
        seed = seed_base + i
    else:
        seed = random.randint(1, 1000000)
```

Resultado: **toda ejecución usa semillas aleatorias.** La configuración afirma lo
contrario. Dos ejecuciones del mismo experimento con los mismos archivos no dan el mismo
número, y el `config/default.yaml` que un revisor leerá para entender el protocolo
describe un comportamiento que el código no tiene.

Atenuante: la semilla efectiva sí se guarda en `metadata.json`
(`parallel_packer.py:357`), así que una ejecución pasada es rastreable a posteriori. Lo que
no se puede es pedirle al sistema que repita.

**Reparación:** cablear `engines.packmol.seed_base` y `use_random_seeds` desde
`ConfigManager` hasta `run_parallel_replicas`, y exponer la semilla en la respuesta de
`/api/experiment/run`. Para JOSS esto no es opcional: la reproducibilidad es criterio de
revisión, y hay un archivo de configuración que promete algo que no se cumple.

### A3 · La validación de empaquetamiento tiene un camino que acepta cualquier resultado

**Severidad: alta (integridad científica). [por lectura, con aritmética verificada]**

`src/packing/parallel_packer.py:287-310` valida una réplica así: si el log de Packmol
contiene «Maximum distance violation», compara contra el umbral. Si **no** lo contiene, cae
a un criterio de reserva:

```
src/packing/parallel_packer.py:300-310
    else:
        # Fallback por conteo de líneas
        total_lines = count_atomic_lines(output_pdb)
        if total_lines >= min_lines_threshold:
            ...
            return True
```

`min_lines_threshold` es 10.000 (`config/default.yaml:24`). El PDB de salida contiene la
cápside, que está fija en el input (`parallel_packer.py:260-263`). Los conteos reales de la
biblioteca del repositorio:

| Cápside | Líneas ATOM |
|---|---|
| BMV_IJS9 | 216.780 |
| CCMV_1CWP | 214.440 |
| MS2_2MS2 | 173.700 |
| QB_1QBE | 168.480 |

El umbral es 10.000. **La cápside sola lo supera veinte veces.** Es decir, en el camino de
reserva el criterio se cumple siempre, con independencia de cuántas enzimas se empaquetaron
— incluso con cero. Y la búsqueda incremental de `parallel_packer.py:328-346` no se
detiene mientras `test_packing` devuelva `True`, así que el resultado sería «100 enzimas»,
el tope de seguridad, para cualquier combinación.

El camino se activa cuando la expresión regular de `parallel_packer.py:191-193` no
encuentra su patrón: otra versión de Packmol, otro formato de log, o una localización
distinta. Es exactamente el tipo de cosa que cambia cuando un revisor instala el software
en su propia máquina.

**Reparación:** el criterio de reserva debe contar enzimas, no líneas. Lo correcto es
contar átomos *añadidos* respecto a la cápside de entrada y dividir por los átomos de la
enzima, o bien contar cadenas o modelos nuevos. Y si la violación no se puede leer, lo
honesto es fallar la réplica y decirlo, no aprobarla.

### A4 · Entradas numéricas sin cota: memoria y CPU a discreción del cliente

**Severidad: alta. [verificado]**

Ninguna ruta acota sus parámetros numéricos. La interfaz sí los acota
(`templates/studio.html:68` pone `max="50"` a `nEnz`, la línea 76 pone `max="300"` a
`nSub`, la 91 pone `max="12"` a `nRep`), pero esos límites viven en HTML y la API no los
repite. Medido en esta sesión contra `/api/preview/enzymes` con BMV y GCase:

| `n_enzymes` | Respuesta | RSS pico | Tiempo |
|---|---|---|---|
| 10 | 20,8 MB | 0,08 GB | 0,23 s |
| 100 | 50,1 MB | 0,19 GB | 1,08 s |
| 500 | 181,4 MB | 0,59 GB | 5,85 s |

El crecimiento es lineal, unos 0,36 MB de respuesta y 1,2 MB de memoria residente por
enzima. `n_enzymes: 50000` pide unos 18 GB. El servidor de desarrollo de Flask atiende con
hilos (verificado: `Flask.run` fija `threaded=True`), así que varias peticiones de este
tipo en paralelo multiplican el consumo sin tope hasta que el proceso muere por falta de
memoria. El contenedor no tiene límites: `docker-compose.yml` no declara ni `mem_limit` ni
`cpus`.

Los puntos exactos donde el valor entra sin validar:

```
src/web/app.py:398    n_enzymes=data.get("n_enzymes", 10)     → packing.py:98  _random_positions(n, ...)
src/web/app.py:426    n=int(data.get("n", 60))                → packing.py:284 _around_positions(n, ...)
src/web/app.py:284    n_replicas = data.get("n_replicas")     → parallel_packer.py:110 range(1, n+1)
src/web/app.py:399    radius=data.get("radius", 50.0)         → sin cota
src/web/app.py:239    int(data.get("n_substrate", 40))        → sin cota
```

Dos casos concretos verificados: `/api/preview/substrate` con `n: -5` responde 200;
`/api/experiment/run` en modo configuración con `n_replicas: 10**9` responde 200 y devuelve
ese número tal cual. En modo de ejecución, `parallel_packer.py:110-112` crearía mil millones
de directorios **antes** de empezar a calcular, agotando los inodos del sistema de archivos.

**Reparación:** validar y acotar en la frontera HTTP, con los mismos topes que la interfaz
ya usa. Conviene un helper único, del estilo
`def entero(data, clave, defecto, minimo, maximo)`, que devuelva 400 con un mensaje claro
fuera de rango, aplicado a las cinco entradas de arriba. Y poner `mem_limit` y `cpus` en
`docker-compose.yml`.

### A5 · Endpoints que encadenan subprocesos sin presupuesto total

**Severidad: alta. [por lectura]**

Cada llamada a subproceso tiene su propio `timeout`, lo cual está bien. Lo que no hay es un
presupuesto para la petición completa:

```
src/services/pore.py:139   hole      timeout=180
src/services/pore.py:247   pymol     timeout=400
src/services/pore.py:394   obabel    timeout=180
src/services/pore.py:409   obabel    timeout=180
src/services/pore.py:473   vina      timeout=400
```

`screen_mutants` (`pore.py:318-381`) genera una biblioteca de hasta siete mutantes
(`pore.py:337-345`), los crea con una llamada a PyMOL de hasta 400 s, y después corre HOLE
sobre cada uno en un bucle (`pore.py:354-372`), a 180 s cada uno. Cota superior: unos 28
minutos para una sola petición HTTP.

`dock_correlate` (`pore.py:493-560`) llama a `screen_mutants` y encima prepara receptor y
ligando con `obabel` y dockea cinco entradas con Vina (`pore.py:531-551`). Sumando los
topes: por encima de **una hora** de subprocesos para una única petición, síncrona, sin
autenticación y sin límite de concurrencia. La interfaz le dice al usuario «~30 s»
(`static/js/pac-pore.js:158`).

Esto es denegación de servicio con una petición, y recursos del equipo del usuario a
disposición de cualquiera que alcance el puerto. El código reconoce el problema a medias:
`src/services/packing.py:336-342` documenta que `run_experiment` «bloquea hasta terminar» y
que «en una versión escalable esto se movería a una cola de trabajos en background».

**Reparación:** a corto plazo, un presupuesto de tiempo por petición y un semáforo que
limite a una ejecución de motor concurrente, devolviendo 429 cuando esté ocupado. A medio
plazo es lo que dice el comentario: una cola de trabajos, con la ruta devolviendo un
identificador y el cliente consultando el estado. También conviene alinear los mensajes de
la interfaz con los tiempos reales.

### A6 · `pip install .` falla: el repositorio no se instala

**Severidad: alta (bloquea la revisión de JOSS). [verificado]**

`setup.py:16-22` arma `install_requires` leyendo `requirements.txt` y descartando solo las
líneas que empiezan por `#`. No quita los comentarios **al final** de la línea. Y hay uno:

```
requirements.txt:16   rdkit==2025.9.1          # geometría 3D de sustratos por SMILES (STUDIO 3D + PAC-PORE)
```

Verificado en esta sesión, la entrada que llega a `install_requires` es la línea completa, y
el analizador de requisitos la rechaza:

```
InvalidRequirement: Expected comma (within version specifier), semicolon (after version
specifier) or end
    rdkit==2025.9.1          # geometría 3D de sustratos por SMILES (STUDIO 3D + PAC-PORE)
         ~~~~~~~~~~~~~~~~~~~~^
```

Un revisor que haga `pip install .` o `pip install -e .`, el primer gesto de cualquiera que
se encuentre un `setup.py`, se estrella. El CI no lo detecta porque nunca instala el
paquete: `.github/workflows/ci.yml:38-41` solo hace `pip install -r requirements.lock`.

**Reparación:** cortar en `#` al leer (`line.split("#")[0].strip()`), o mejor, mover las
dependencias a `pyproject.toml`, que ya existe pero hoy solo configura ruff
(`pyproject.toml:1-3` lo dice explícitamente). Y añadir un paso de CI que haga
`pip install .` y después `python -c "import ..."`.

### A7 · El paquete instalado tapa el módulo `io` de la biblioteca estándar

**Severidad: alta. [por lectura]**

```
setup.py:41   packages=find_packages(where='src'),
setup.py:42   package_dir={'': 'src'},
```

Esa combinación publica el *contenido* de `src/` como paquetes de primer nivel:
`core`, `services`, `web`, `packing`, `engines` y **`io`**. Instalar este paquete pone un
`io` en `site-packages` que compite con el `io` de la biblioteca estándar. Es uno de los
nombres que nunca hay que ocupar.

Y hay una segunda consecuencia: todo el código importa con el prefijo `src.`
(`from src.core import paths` en `common.py:15`, `from src.services import packing_service`
en `app.py:18`, y así en todos los módulos). Tras instalar, esos módulos se llaman
`core` y `services`, no `src.core` ni `src.services`, así que los imports fallan. El
paquete instalado no funciona. Hoy solo funciona ejecutándolo desde el árbol de fuentes,
con los parches de `sys.path` de `app.py:15` y `experiment_runner.py:10` y con
`pythonpath = .` en `pytest.ini`.

**Reparación:** hacer de `src` un paquete de verdad
(`packages=find_packages(include=["src", "src.*"])`, sin `package_dir`), o renombrar el
árbol a un nombre propio, por ejemplo `vlp_studio/`, y ajustar los imports. Lo segundo es
más trabajo y mejor resultado: elimina también los parches de `sys.path`. En cualquier
caso, `io` tiene que dejar de ser un paquete de primer nivel.

### A8 · `radio_interno.txt`: se escribe en un sitio, se lee en otro, y se atribuye a BMV

**Severidad: alta (datos científicos cruzados). [por lectura]**

Tres defectos en el mismo archivo. Primero, la escritura usa una ruta relativa, así que el
destino depende del directorio desde el que se lanzó el servidor:

```
src/core/capsid.py:153   output_file = "radio_interno.txt"
src/core/capsid.py:154   with open(output_file, "w") as f:
```

Segundo, la lectura usa una ruta absoluta distinta:

```
src/services/library.py:63   radius_file = paths.PROJECT_ROOT / "radio_interno.txt"
```

`CLAUDE.md` indica arrancar con `cd src/web && python app.py`. Con esa instrucción, el
archivo se escribe en `src/web/radio_interno.txt` y se lee en
`nanocapsule-mvp/radio_interno.txt`. **La caché nunca acierta.**

Tercero, y es el peor: hay un único archivo global para todas las cápsides, y el valor que
contenga se atribuye por nombre a BMV.

```
src/services/library.py:85
    "radius": cached_radius if name.startswith("BMV") else None,
```

Si el usuario calcula el radio de MS2, el archivo se sobreescribe, y si el servidor se
lanzó desde el directorio correcto, la tabla de la biblioteca mostrará **el radio de MS2
en la fila de BMV**. Es contaminación silenciosa de un dato científico en la interfaz.

**Reparación:** una caché por estructura, junto a su PDB o en `Output/`, con el nombre de
la cápside en la ruta, resuelta con `paths.PROJECT_ROOT` y nunca con una ruta relativa.
Guardar junto al valor la procedencia (A1) y la fecha.

### A9 · Docker: servidor de desarrollo, como root, sin límites, en todas las interfaces

**Severidad: alta. [por lectura]**

```
Dockerfile:59        CMD ["python", "src/web/app.py"]
docker-compose.yml:11    - "5000:5000"
```

El comando de la imagen arranca `app.run()` (`app.py:578`), el servidor de desarrollo de
Werkzeug. Su propia documentación advierte de no usarlo en producción: no está endurecido
contra peticiones malformadas, no limita cuerpos ni cabeceras, no tiene cola ni tiempos de
espera. No hay instrucción `USER` en el `Dockerfile`, así que el proceso corre **como
root**, lo que convierte C1 en ejecución de código como root dentro del contenedor.
`docker-compose.yml` no declara `read_only`, `cap_drop`, `mem_limit` ni `cpus`, y publica
el puerto en todas las interfaces del anfitrión.

Detalle menor en el mismo archivo: `docker-compose.yml:18` fija `FLASK_ENV=production`, que
Flask 3 ignora (se eliminó en la versión 2.3). No hace daño, pero da una falsa sensación de
endurecimiento. El archivo también declara `version: '3.8'`, obsoleto en Compose v2.

**Reparación:** servir con gunicorn o waitress, no con el servidor de desarrollo. Añadir
`USER` con un usuario sin privilegios. Publicar `127.0.0.1:5000:5000` por defecto. Poner
`mem_limit`, `cpus`, `read_only: true` con `tmpfs` para lo escribible, y `cap_drop: [ALL]`.

### A10 · Cobertura real del 30%, con el núcleo científico en 0%

**Severidad: alta. [verificado]**

Medición ejecutada en esta sesión: `pytest -q --cov=src`, 22 pruebas, todas pasan, 2,46 s.

| Módulo | Sentencias | Cubiertas | % |
|---|---|---|---|
| `src/core/capsid.py` | 121 | 0 | **0** |
| `src/core/cargo.py` | 96 | 0 | **0** |
| `src/core/experiment_manager.py` | 141 | 0 | **0** |
| `src/core/experiment_runner.py` | 115 | 0 | **0** |
| `src/services/pore.py` | 328 | 86 | 26 |
| `src/io/structure_fetcher.py` | 132 | 42 | 32 |
| `src/web/app.py` | 328 | 110 | 34 |
| `src/services/packing.py` | 190 | 73 | 38 |
| `src/core/config.py` | 46 | 31 | 67 |
| `src/services/common.py` | 68 | 49 | 72 |
| `src/services/library.py` | 55 | 43 | 78 |
| `src/core/paths.py` | 12 | 10 | 83 |
| `src/services/md.py` | 52 | 51 | 98 |
| `src/services/deimmuno.py` | 5 | 5 | 100 |
| `src/services/packing_service.py` | 8 | 8 | 100 |
| **TOTAL** | **1.697** | **508** | **30** |

Lo que está al 100% son los módulos que devuelven diccionarios literales. Lo que está al 0%
es donde vive la ciencia.

**Partes críticas sin ninguna prueba:**

- `capsid.py` — el cálculo del radio interno, el número que alimenta el input de Packmol.
  Nadie prueba ni el camino bueno ni los dos caminos de degradación de A1.
- `cargo.py` — el centrado de la enzima, prerrequisito de que Packmol funcione.
- `experiment_runner.py` y `experiment_manager.py` — la orquestación completa del
  experimento multirréplica.
- `parallel_packer.py` — no aparece en el informe porque `--cov=src` no lo alcanzó al no
  importarse nunca. Es el motor de empaquetamiento, 467 renglones, y contiene A3.
- `substrate_section` sí tiene un golden test (`tests/test_golden_science.py`), y es lo
  mejor del conjunto de pruebas: congela tres valores numéricos con tolerancia justificada.
  Es el patrón que debería replicarse.

**Rutas cuyo cuerpo no ejecuta ni una línea en ninguna prueba: 16 de 32.** Medido contando
líneas ejecutables tras el `def`, excluyendo decorador y firma:

```
GET   /api/library/combinations      GET   /api/structure/<type>/<name>
GET   /api/pore/channel              GET   /api/file/<type>/<name>
POST  /api/pore/run_hole             GET   /api/result/pdb
POST  /api/pore/screen               POST  /api/preview/substrate
POST  /api/pore/mutant               GET   /api/files/generated
POST  /api/pore/dock                 POST  /api/files/cleanup
POST  /api/md/prepare                GET   /api/download/single/<filename>
POST  /api/capsid/radius
POST  /api/experiment/run
```

Dos observaciones. La ruta que contiene C1, `/api/pore/mutant`, está entre ellas. Y
`/api/download/experiment-zip` tiene 37 líneas de cuerpo con **una** ejecutada (3%), que es
el `try`.

De las 16 rutas restantes, ninguna llega al 80%: lo que se ejerce es el camino feliz, y los
`except` quedan sin tocar. Eso explica por qué los defectos de tipo de respuesta del
hallazgo A11 nunca se notaron.

**Reparación:** priorizar por riesgo, no por facilidad.

1. `capsid.calculate_internal_radius` con PyMOL simulado, incluidos los dos caminos de
   degradación, aseverando que la procedencia viaja en el resultado (cierra A1).
2. `parallel_packer._run_single_replica` con Packmol simulado: un log con violación
   aceptable, uno con violación excesiva, y uno **sin** la línea de violación, aseverando
   que ese último no aprueba la réplica (cierra A3).
3. Una prueba por ruta no cubierta, con entrada válida e inválida, aseverando el código de
   estado. Son 16 rutas y cuesta una tarde.
4. Pruebas de validación de límites para las cinco entradas numéricas de A4.
5. Una prueba de regresión para C1: que una posición no numérica dé 400 y que no se escriba
   ningún `_mutgen.py`.
6. Activar el umbral en CI: `pytest --cov=src --cov-fail-under=N`, con N en el valor actual
   y subiéndolo a medida que se añaden pruebas. `pytest-cov` ya está en
   `requirements.txt:29` y nunca se usa.

### A11 · Cincuenta bloques `except Exception` convierten errores de cliente en 500

**Severidad: alta (fragilidad y diagnóstico). [verificado]**

`src/web/app.py` tiene 50 cláusulas `except`, casi todas con la misma forma:

```python
except Exception as e:
    return jsonify({"error": str(e)}), 500
```

El patrón se repite en las líneas 67, 75, 83, 91, 99, 108, 116, 129, 137, 150, 163, 176,
189, 202, 210, 218, 228, 245, 271, 323, 338, 356, 384, 415, 438, 474, 496, 514 y 562. El
efecto es que cualquier fallo, sea del cliente o del servidor, sale como 500 con el texto
crudo de la excepción. Verificado:

| Petición | Responde | Debería |
|---|---|---|
| `GET /api/structure/invalido/x` | **500** `structure_type debe ser 'capside' o 'enzima'` | 400 |
| `POST /api/md/prepare` con `n_substrate: "x"` | **500** `invalid literal for int() with base 10: 'x'` | 400 |
| `POST /api/preview/substrate` con `n: "x"` | 400 `invalid literal for int()...` | 400, con mensaje propio |

El primer caso es claro: `structure_fetcher.py:267` lanza `ValueError`, que es un error de
entrada, y la ruta solo captura `FileNotFoundError` antes del genérico
(`app.py:336-339`). El segundo es el mismo defecto en `/api/md/prepare`
(`app.py:243-246`): el `int()` de la línea 239 puede lanzar `ValueError` y nada lo recoge
como 400.

Además se filtra detalle interno. `invalid literal for int() with base 10: 'x'` es un
mensaje del intérprete, no del dominio: le dice al cliente cómo está implementado el
servidor y no le dice qué arreglar. Y como contrapartida, los fallos genuinos del servidor
quedan sin registrar: no hay `logging` en todo el proyecto, solo `print`, y la
configuración de `logging` de `config/default.yaml:69-77` no la lee nadie. Cuando algo se
rompe de verdad, el rastro de la pila no se guarda en ninguna parte.

**Reparación:** un manejador de errores de aplicación (`@app.errorhandler`) en lugar de 50
bloques repetidos. Que `ValueError` se traduzca a 400, `FileNotFoundError` a 404, y todo lo
demás a 500 con un mensaje genérico y el rastro de la pila en el log del servidor, no en la
respuesta. Y poner en marcha `logging` con la configuración que ya está escrita.

---

## 4. Hallazgos medios

### M1 · Una ruta absoluta esquiva el filtro de `..`

**[verificado]** Tres funciones de `pore.py` filtran la travesía de directorios buscando
`..` en la cadena:

```
src/services/pore.py:160   if not structure_key or ".." in structure_key:
src/services/pore.py:277   (idéntico, en evaluate_mutant)
src/services/pore.py:320   (idéntico, en screen_mutants)
```

Pero la ruta se compone con el operador `/` de `pathlib`, que al recibir una ruta absoluta
a la derecha **descarta la base**. Verificado:

```
structure_key = "/etc/passwd"
".." in structure_key                                      → False   (pasa el filtro)
(POROMANIA_DIR / "modelos" / structure_key).with_suffix(".pdb")  → /etc/passwd.pdb
```

El filtro se esquiva sin usar `..`. La explotación requiere que exista un `.pdb` en el
destino, así que no es lectura arbitraria inmediata, pero el confinamiento al directorio de
modelos no existe. Hay un segundo detalle en la misma línea: `with_suffix(".pdb")`
**reemplaza** la extensión existente, así que una clave como `a/b.c` apunta a `a/b.pdb`,
que no es lo que el nombre sugiere.

**Reparación:** resolver y comprobar la contención de verdad:
`p = (base / key).resolve()` seguido de `if not p.is_relative_to(base.resolve()): raise`.
Mejor aún, validar la clave contra la lista que `hole_structures()` ya produce, en vez de
construir rutas con entrada del usuario.

### M2 · `/api/result/pdb` compara prefijos de cadena en lugar de contención real

**[verificado]**

```
src/web/app.py:372
    if not str(target).startswith(str(paths.OUTPUT_DIR.resolve())):
        return "Ruta no permitida", 403
```

Comparar prefijos de texto no es comprobar contención de rutas. Un hermano cuyo nombre
empiece igual pasa el filtro:

```
OUTPUT_DIR.resolve()   = /home/user/vlp-studio/nanocapsule-mvp/Output
ruta candidata         = /home/user/vlp-studio/nanocapsule-mvp/Output_secreto/x.pdb
startswith             → True   (el filtro la acepta)
```

Hoy no es explotable: no existe tal directorio y ninguna ruta del Studio escribe fuera de
`Output/`, así que el atacante no puede crearlo. Es una debilidad latente, del tipo que se
convierte en vulnerabilidad el día que alguien añada un directorio `Output_backup` o
`Output_v2`. El comentario de la propia función (`app.py:366`) dice «Valida que la ruta
esté dentro de Output/ para no exponer el sistema de archivos», que es la intención
correcta mal implementada.

**Reparación:** `target.is_relative_to(paths.OUTPUT_DIR.resolve())`, disponible desde
Python 3.9. Y conviene acotar el tamaño: `target.read_text()` en `app.py:377` carga el
archivo completo en memoria sin mirar cuánto pesa.

### M3 · Borrado de archivos sin autenticación, y `days_old: 0` borra todo

**[por lectura]**

```
src/web/app.py:478   @app.route("/api/files/cleanup", methods=["POST"])
src/web/app.py:482       days_old = data.get("days_old", 7)
src/web/app.py:487       cutoff = datetime.datetime.now() - datetime.timedelta(days=days_old)
src/web/app.py:489       for file_path in output_dir.glob("*.pdb"):
src/web/app.py:490-492       if ...mtime < cutoff: removed.append(...); file_path.unlink()
```

`days_old` no se valida. Con `0` el corte es «ahora», y todos los PDB generados se borran.
Con un valor negativo, también. Es la única ruta destructiva del Studio y no tiene
autenticación ni confirmación. Un tipo no numérico produce `TypeError` en `timedelta`, que
el `except Exception` de la línea 496 convierte en 500.

Atenuante: al usar `get_json()` sin `force`, exige `application/json` y por tanto
verificación previa de CORS, así que no es alcanzable por petición cruzada. Esa protección
es accidental (ver C2).

**Reparación:** validar `days_old` como entero no negativo con un mínimo sensato, exigir un
parámetro de confirmación explícito, y registrar en el log qué se borró. Mover los archivos
a una papelera antes de borrarlos sería mejor aún, dado que son resultados de experimentos.

### M4 · XSS en el DOM: `innerHTML` con datos que vienen del usuario

**[por lectura, cadena completa trazada]**

El frontend compone HTML por concatenación en varios sitios:

```
static/js/studio-core.js:7       el.innerHTML = (...) + msg;
static/js/pac-pore.js:93-99      $('tb-cribado').innerHTML = d.mutants.map(m => `...${m.name}...${m.mutations}...`)
static/js/pac-pore.js:118-120    tr.innerHTML = `...${m.name}...${m.mutations}...`
static/js/library.js:38-47       $('tb-caps').innerHTML = caps.map(...)
static/js/library.js:53-64       $('tb-enz').innerHTML = enz.map(...)
static/js/analisis-md.js:14-15   $('md-examples').innerHTML = mdExamples.map(...)
```

Hay dos caminos por los que entrada del usuario llega a esos `innerHTML`.

El primero es `m.mutations`, que `pore.py:311` construye como
`", ".join(f"{p}{aa}" for p, aa in muts.items())`, donde `p` es la posición **sin validar**
de C1. Lo que el usuario escriba acaba renderizado como HTML en la tabla de cribado.

El segundo es más directo y está completamente trazado:

```
el usuario pega un SMILES con «<img src=x onerror=...>»
  → packing.py:229   raise ValueError(f"SMILES inválido: {smiles}")    (eco literal)
  → app.py:436-437   return jsonify({"error": str(e)}), 400
  → packing.js:28    throw new Error((await r.json()).error)
  → packing.js:33    setStatus('Error sustrato: ' + e, 'err')
  → studio-core.js:7 el.innerHTML = ... + msg                          (ejecuta)
```

Verificado que el servidor hace el eco: `POST /api/pore/section` con
`{"smiles": "<img src=x onerror=alert(1)>"}` responde
`{"error": "SMILES inválido: <img src=x onerror=alert(1)>"}`.

Es sobre todo auto-XSS, porque el Studio es monousuario y el SMILES lo escribe el propio
usuario. Pero en combinación con C2 y sin autenticación el impacto crece, y «el usuario se
lo hizo a sí mismo» deja de aplicar cuando alguien publica un SMILES en un tutorial o un
suplemento de un artículo y pide copiarlo.

**Reparación:** `textContent` en `setStatus` (el único `innerHTML` que necesita es el
`<span class="spinner">`, que se puede insertar como nodo). Para las tablas, construir las
filas con `createElement` y `textContent`, como `fillSelect` ya hace bien en
`library.js:17-20`. Y en el servidor, no devolver la entrada del usuario tal cual en los
mensajes de error.

### M5 · Dos CDN sin verificación de integridad, sin CSP, y la aplicación no funciona sin red

**[por lectura]**

```
templates/studio.html:7   <script src="https://cdn.jsdelivr.net/npm/ngl@2.0.0-dev.37/dist/ngl.js"></script>
templates/studio.html:8   <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
templates/index.html:7    (el mismo NGL)
```

No hay atributo `integrity`, ni `crossorigin`, ni cabecera `Content-Security-Policy` en
ninguna respuesta. Si una de esas dos CDN sirve algo distinto, se ejecuta en el navegador
del usuario con acceso completo a la API local sin autenticación.

Hay un segundo problema, y para JOSS puede importar más: **el Studio no funciona sin
conexión.** Un revisor en un clúster sin salida a internet, o en un avión, carga la página
y obtiene un visor en blanco. Y la versión de NGL es una preliberación,
`2.0.0-dev.37`: las preliberaciones se despublican con más frecuencia que las estables.

**Reparación:** descargar las dos bibliotecas a `static/vendor/` y servirlas localmente,
anotando versión y licencia en `THIRD_PARTY.md`, que ya existe. Eso resuelve integridad,
funcionamiento sin red y reproducibilidad a la vez. Si se prefiere mantener la CDN, como
mínimo añadir `integrity` con el hash y una CSP restrictiva.

### M6 · El número de triangulación se deduce del número de identificadores de cadena

**[verificado]**

```
src/services/library.py:83
    "t_number": _T_NUMBER.get(chains, f"T={chains}" if chains else "—"),
```

donde `chains` viene de `_count_atoms_chains` (`common.py:29-38`), que cuenta caracteres
distintos en la columna 22 del PDB. El número de triangulación de una cápside icosaédrica
no es el número de identificadores de cadena del archivo.

Hoy la respuesta sale bien por una coincidencia estructural: las cuatro cápsides de la
biblioteca tienen tres identificadores distintos (A, B, C, repetidos sesenta veces) y las
cuatro son T=3. Verificado: BMV, CCMV, MS2 y QB dan `chains = 3` cada una.

Pero el camino de reserva delata el problema: si el archivo trae identificadores únicos por
subunidad, la interfaz mostrará «T=60» o «T=180». Y eso es justo lo que produce el propio
`StructureFetcher.fetch_capsid` del repositorio, que descarga el ensamblaje biológico con
`type="pdb1"` y `all_states on` (`structure_fetcher.py:73-78`).

**Reparación:** o se declara el T en los metadatos de cada estructura, que es lo honesto, o
se documenta en el código y en la interfaz que es una heurística sobre la unidad asimétrica
con la condición en que vale. Un revisor que vea «T=3» asumirá que se calculó.

### M7 · Estado global compartido entre peticiones

**[por lectura]**

```
src/services/common.py:20    _config = ConfigManager()
src/services/common.py:21    _fetcher = StructureFetcher(str(paths.INPUT_DIR))
src/services/packing.py:211  _smiles_cache: Dict[str, List] = {}
src/services/packing.py:54   random.uniform(...)   (estado global del módulo random)
```

`_config` y `_fetcher` son de solo lectura en la práctica, así que compartirlos es
razonable y está documentado. Los otros dos no.

`_smiles_cache` crece sin tope, con claves que son SMILES del usuario de hasta 400
caracteres (`packing.py:219`), y nunca desaloja nada. Con el servidor en hilos (A4), es
también un diccionario mutado desde varios hilos sin cerrojo. No corrompe datos en CPython
por el bloqueo global del intérprete, pero es memoria que solo sube.

El módulo `random` sin semilla hace que `preview` y `preview_substrate` den un resultado
distinto en cada llamada. Para una vista previa es defendible, y el código lo llama «preview»
con claridad. Lo que falta es poder fijarla: no hay parámetro de semilla en
`/api/preview/enzymes` ni en `/api/preview/substrate`, así que una figura generada con el
Studio no se puede reproducir. Para un artículo eso es un problema.

**Reparación:** acotar `_smiles_cache` (un `functools.lru_cache` con `maxsize` resuelve
las tres cosas de golpe). Aceptar un parámetro `seed` opcional en las dos rutas de
vista previa y devolver en la respuesta la semilla usada.

### M8 · Un experimento sobreescribe el anterior

**[por lectura]**

```
src/core/experiment_manager.py:66
    experiment_dir = self.output_base_dir / capsid_clean / enzyme_clean
```

La ruta no lleva marca de tiempo. Volver a correr la misma combinación cápside-enzima
escribe encima de los resultados anteriores: las réplicas, el `summary/`, el
`statistics.json` y el `report.txt`. No hay aviso ni copia.

`CLAUDE.md` describe otra cosa: «Each replica in `Output/Experiments/[timestamp]/replica_[N]/`».
El código no hace eso. Un usuario que lea la documentación creerá que su historial se
conserva.

Hay además una discrepancia de conteo: `experiment_manager.py:47` fija
`self.n_replicas = 7` y crea siete directorios en `setup_experiment`, mientras
`parallel_packer.py:110` crea tantos como diga el parámetro (10 por configuración, o lo que
mande el cliente). Es inofensivo pero deja directorios vacíos y confunde.

**Reparación:** incluir la marca de tiempo en la ruta, como dice la documentación, y añadir
un enlace o un archivo `latest` que apunte a la última ejecución. Unificar el conteo de
réplicas en una sola fuente.

### M9 · Fuga de descriptores de archivo en el bucle de Packmol

**[por lectura]**

```
src/packing/parallel_packer.py:278-285
    result = subprocess.run(
        [packmol_executable],
        stdin=open(input_file),
        stdout=open(log_file, "w"),
        ...
    )
```

Los dos `open()` crean objetos de archivo que nadie cierra ni envuelve en `with`. Se cierran
cuando el recolector de basura los recoja, que en CPython suele ser pronto, pero no está
garantizado y bajo presión de memoria se retrasa. El bucle de búsqueda incremental
(`parallel_packer.py:328-346`) puede llamar a `test_packing` hasta cien veces, y cada
llamada hace hasta dos intentos: unos doscientos pares de descriptores por réplica, por
siete réplicas en paralelo. Es un camino creíble al agotamiento de descriptores en un
sistema con el límite por defecto.

**Reparación:** `with open(input_file) as fin, open(log_file, "w") as fout:` alrededor de
la llamada.

### M10 · Configuración muerta: el archivo documenta comportamiento que no existe

**[verificado]**

Claves de `config/default.yaml` que ningún código lee:

| Clave | Línea | Qué pasa en realidad |
|---|---|---|
| `engines.packmol.timeout: 300` | 33 | `parallel_packer.py:283` fija `timeout=90` |
| `engines.packmol.seed_base` | 37 | nunca se lee (ver A2) |
| `engines.packmol.use_random_seeds` | 40 | nunca se lee (ver A2) |
| `engines.pymol.headless` / `quiet` | 44, 47 | nunca se leen |
| `packing.collision_margin: 2.0` | 10 | `parallel_packer.py:268` lo fija a mano a 2.0 |
| `io.temp_dir`, `cleanup_temp`, `output_formats` | 52, 55, 58 | nunca se leen |
| `logging.*` (nivel, formato, archivo) | 69-77 | nunca se leen; el proyecto usa `print` |
| `web.cors_enabled` | 91 | nunca se lee; CORS está fijo en `*` en las respuestas |
| `experiments.output_base_dir`, `keep_temp_files`, `auto_generate_reports` | 99-105 | nunca se leen |
| `library.capsides_dir`, `enzymes_dir`, `output_dir` | 110-116 | nunca se leen; `paths.py` manda |

Y `.env.example` es casi entero decorativo: de sus más de veinte variables, la única que el
código consulta es `FLASK_DEBUG` (`app.py:572`). Dos son activamente engañosas:
`MAX_ENZYMES=50` y `API_RATE_LIMIT=100` sugieren que existen el límite de enzimas y el
límite de tasa de A4. No existen. `SECRET_KEY=your-secret-key-here-change-in-production`
sugiere que hay sesiones. No hay.

Un auditor o un revisor que lea estos archivos para entender el sistema se formará una
imagen equivocada, y es razonable que lo haga: son los archivos que existen para eso.

**Reparación:** borrar lo que no se usa, o cablearlo. `timeout`, `seed_base` y
`collision_margin` merecen cablearse, porque son parámetros científicos. El resto se borra.
`.env.example` debería quedarse en las dos o tres variables reales.

### M11 · El mismo parámetro científico tiene tres valores distintos según dónde se mire

**[verificado]**

| Parámetro | `config/default.yaml` | Respaldo en `config.py` | Valor por defecto en el código |
|---|---|---|---|
| `exclusion_radius` | 5.0 (línea 13) | 5.0 (`config.py:85`) | **10.0** (`experiment_runner.py:134`, `packing.py:97`) |
| `max_violation_threshold` | 0.10 (línea 20) | 0.10 (`config.py:87`) | **0.05** (`experiment_runner.py:135`) |
| `web.port` | 5000 (línea 82) | **5001** (`config.py:104`) | 5000 (`app.py:569`) |

Los valores por defecto del código solo se usan si falta la clave en el YAML, así que hoy
gana el archivo. El problema es que un lector del código verá `10.0` y `0.05` y creerá que
esos son los valores del experimento, cuando son 5.0 y 0.10. Para dos parámetros que
determinan si un empaquetamiento se acepta, esa ambigüedad no es aceptable en un artículo.

El caso del puerto es más visible: si `config/default.yaml` falta, el servidor arranca en
5001 mientras el `Dockerfile:59` expone 5000 (`EXPOSE` en la línea 53) y el healthcheck consulta 5000. El
contenedor quedaría permanentemente insano.

**Reparación:** una sola fuente de verdad. Lo más limpio es que
`ConfigManager._get_default_config` sea el único sitio con valores por defecto y que las
llamadas a `.get()` no lleven segundo argumento. Y que la respuesta de
`/api/experiment/run` incluya los parámetros efectivos usados, para que queden registrados
con el resultado.

### M12 · El centrado solo toca el primer estado, pero divide por los átomos de todos

**[por lectura; hoy no se activa con la biblioteca del repositorio]**

```
src/core/capsid.py:88-90   cmd.iterate_state(1, "capside", "stored.xyz[0] += x; ...")
src/core/capsid.py:91      n_atoms = cmd.count_atoms("capside")
src/core/capsid.py:96      center_original = [coord / n_atoms for coord in stored.xyz]
src/core/capsid.py:102-104 cmd.alter_state(1, "capside", f"x = x - {center_original[0]}")
```

`iterate_state(1, ...)` suma coordenadas **del estado 1**. `count_atoms` cuenta los átomos
de la selección. Si el objeto tiene varios estados, se divide una suma parcial por un
conteo total, y el centroide sale mal por un factor igual al número de estados. Además
`alter_state(1, ...)` solo recentra el estado 1, dejando el resto desplazado. `cargo.py:95-97`
tiene la misma forma.

Verificado que **hoy no se activa**: los cuatro `capside.pdb` de la biblioteca no tienen
registros `MODEL`, así que son de un solo estado. Pero el flujo documentado del propio
repositorio produce archivos multiestado: `structure_fetcher.py:73-78` descarga con
`type="pdb1"` y activa `all_states`, precisamente porque para una cápside hace falta el
ensamblaje biológico completo. Un usuario que siga ese camino obtiene un radio interno
equivocado sin ningún aviso, y por A1 no distinguirá ese número de uno bueno.

**Reparación:** usar `cmd.get_coords("capside")`, que ya se emplea en `capsid.py:202` para
el otro método, y calcular el centroide con numpy sobre todos los estados. O iterar los
estados explícitamente. Y añadir una prueba con un PDB de dos modelos, que es
exactamente el caso que hoy nadie cubre (A10).

### M13 · La documentación dice «menos 1 Å» y el código suma 1 Å

**[verificado]**

```
src/core/capsid.py:57-58 (docstring)
    Migrado desde 1calcula_radio_interno.py con el cambio importante:
    - Original: radio_colision + 1 Å
    - Nuevo: radio_colision - 1 Å (margen interno de seguridad)
```

```
src/core/capsid.py:144-147 (código)
    # CORRECCIÓN: Expandir 1 Å más allá de la colisión como en original
    # Esto da margen de maniobra para el empaquetamiento
    radio_colision = radio_colision + 1.0
```

`CLAUDE.md` respalda la versión del docstring: «**Subtract 1Å safety margin** from collision
radius (not add)». El código suma. Dos renglones de comentario contradictorios en la misma
función, y una diferencia de 2 Å en el radio efectivo.

Para un revisor esto es una señal de alarma desproporcionada a su impacto numérico: no
sabrá qué versión es la intencionada ni qué resultados publicados corresponden a cuál. El
comentario de la línea 144 dice «como en original», que contradice el docstring que dice
que lo nuevo es lo contrario del original.

Nota aparte sobre la misma función: la búsqueda de colisión es `for r in range(5, 200)`
(`capsid.py:125`), con pasos de 1 Å, así que el radio está cuantizado al angstrom. Y el
predicado usa `within {r + 0.5}` (línea 130), de modo que la primera iteración ya busca
colisiones a 5,5 Å. No es un defecto, pero la precisión declarada en la respuesta de la API
(`f"{radius:.1f} Å"`, `app.py:266`) sugiere una décima de angstrom que el método no tiene.

**Reparación:** decidir el signo, corregir el docstring, el comentario y `CLAUDE.md` para
que coincidan con el código, y anotar en el `CHANGELOG.md` desde qué versión aplica. La
precisión del formato debería reflejar la del método.

### M14 · La versión difiere según el archivo

**[verificado]**

| Archivo | Versión |
|---|---|
| `nanocapsule-mvp/VERSION` | 0.1.0 |
| `CITATION.cff:14` | 0.1.0 |
| `nanocapsule-mvp/setup.py:33` | **1.0.0** |

JOSS revisa el `CITATION.cff` y la correspondencia entre la versión citada y la etiqueta
publicada. Un `setup.py` que dice 1.0.0 mientras el resto dice 0.1.0 produce un paquete
instalado con una versión que no se puede citar.

**Reparación:** que `setup.py` lea el archivo `VERSION`, como ya lee `README.md` en la línea
13. Una sola fuente.

### M15 · La descarga de estructuras no verifica integridad

**[por lectura]**

`scripts/fetch_data.sh:46-52` descarga la cápside P22 desde `files.rcsb.org` sobre HTTPS y
la usa sin comprobar ningún hash. Si la entrada del PDB se revisa, y el RCSB revisa
entradas, el archivo que baja hoy no es el que bajó quien publicó los resultados, y nada lo
señala. El script tiene además un camino de reserva que, si el ensamblaje biológico no está
disponible, **baja la unidad asimétrica en su lugar** (líneas 50-51), que para una cápside
es un objeto científicamente distinto. Lo avisa por consola, con una línea que se pierde
entre el resto de la salida, y el archivo resultante se llama igual: `capside.pdb`.

**Reparación:** publicar el SHA-256 esperado junto a cada estructura y verificarlo tras
descargar, abortando si no coincide. Y que el camino de reserva no produzca un archivo con
el mismo nombre que el bueno: si solo hay unidad asimétrica, debe fallar o guardar con un
nombre que lo diga.

### M16 · El CI no prueba lo que más se rompe

**[por lectura]**

`.github/workflows/ci.yml` hace lint con ruff, comprueba formato y corre pytest. Eso está
bien y es más de lo que tienen muchos repositorios. Lo que no hace:

- **No instala el paquete.** Por eso A6 y A7 llevan ahí sin que nadie los note. Un
  `pip install .` en el CI los habría cazado el primer día.
- **No mide cobertura.** `pytest-cov` está en `requirements.txt:29` y en el lock, y no se
  usa. Sin `--cov-fail-under` nada impide que la cobertura siga bajando.
- **No construye la imagen Docker.** Un `Dockerfile` que no se construye en CI es un
  `Dockerfile` roto en algún momento futuro que nadie sabrá cuándo.
- **No audita dependencias.** Ni `pip-audit` ni nada equivalente. Las versiones están
  fijadas, que es lo correcto, pero fijado significa también que no se actualiza cuando
  sale un aviso de seguridad, así que hace falta algo que mire.
- **Una sola versión de Python.** Solo 3.12, mientras `setup.py:48` declara `>=3.7` y los
  clasificadores prometen de 3.7 a 3.11. Lo que se promete no se prueba (ver B1).

El segundo trabajo, `engines`, hace `compileall` sobre los otros tres motores. El comentario
del archivo es honesto sobre lo poco que eso valida, y la honestidad se agradece, pero
conviene no confundirlo con pruebas.

**Reparación, por orden de rentabilidad:** añadir un paso de `pip install .` con un import
de verificación; activar `--cov=src --cov-fail-under` con el valor actual; construir la
imagen; añadir `pip-audit`. Los cuatro son unas pocas líneas de YAML.

### M17 · Datos ilustrativos servidos por endpoints con la misma forma que los reales

**[por lectura]**

Cuatro fuentes devuelven datos sintéticos o de literatura, no calculados:

```
src/services/pore.py:615-649    pore_profile      → gaussiana sintética, "illustrative": True
src/services/pore.py:22-27      _SUBSTRATES       → radios «ILUSTRATIVOS hasta portar el cálculo real»
src/services/md.py:65-122       md_examples       → cinco curvas generadas con seno, "illustrative": True
src/services/deimmuno.py:14-37  deimmuno_data     → doce mutantes con valores fijos, "illustrative": True
```

El código es ejemplar en su honestidad: cada uno lleva su bandera `illustrative` y un
comentario que dice qué habría que portar. La interfaz también la respeta en los sitios que
revisé: `pac-pore.js:75-76` muestra «perfil ilustrativo» y `static/js/pac-pore.js:226`
distingue «HOLE real».

El riesgo que queda es de forma, no de intención: `pore_profile` y `run_hole` devuelven el
mismo contrato (`positions`, `radius`, `pore_min`, `min_index`), de modo que un consumidor
de la API que no lea la bandera no puede distinguirlos, y la gaussiana de `pore_profile`
tiene el aspecto de un perfil de poro medido. `_SUBSTRATES` es el caso más expuesto: los
radios se sirven por `/api/pore/config` sin ninguna bandera y se muestran en el selector
(`pac-pore.js:41`) junto al valor calculado de verdad por `substrate_section`, con el mismo
formato y sin distinción visible.

**Reparación:** que la bandera viaje en todos los casos, `_SUBSTRATES` incluido, y que la
interfaz la muestre siempre, no solo en el texto de estado. Para un repositorio camino de
JOSS vale la pena ir más lejos: separar las rutas ilustrativas bajo un prefijo
`/api/demo/...`, de modo que sea imposible confundirlas al leer el código o los registros
del servidor.

---

## 5. Hallazgos bajos

**B1 · Compatibilidad de Python prometida y no probada.** `setup.py:48` declara
`python_requires='>=3.7'` y las líneas 63-67 clasifican de 3.7 a 3.11. Pero `common.py:29`
usa `tuple[int, int]` como anotación, `packing.py:58` usa `math.dist` (3.8+),
`app.py:372` depende de comparaciones de rutas resueltas y `pyproject.toml:7` fija
`target-version = "py312"`. El CI prueba solo 3.12. Declarar 3.7 es falso. Subir el mínimo
a 3.9 (por `is_relative_to`, que hace falta para M2) y probar 3.9 y 3.12 en el CI.

**B2 · Parches de `sys.path` en lugar de empaquetado.** `app.py:15` y
`experiment_runner.py:10` insertan rutas a mano, y `experiment_runner.py:12` importa
`from packing.parallel_packer import ParallelPacker` apoyándose en ese parche. Es frágil
ante cualquier cambio de directorio de trabajo, y desaparece solo si se arregla A7.

**B3 · Sin cabeceras de seguridad.** Ninguna respuesta lleva `X-Content-Type-Options:
nosniff`, `X-Frame-Options` ni `Referrer-Policy`. Los PDB se sirven como `text/plain` en
`app.py:125`, `app.py:347` y `app.py:378`, y sin `nosniff` un navegador viejo podría
interpretarlos como otra cosa.

**B4 · `Access-Control-Allow-Origin: *` en siete respuestas.** `app.py:125`, `351`, `381`,
`407`, `432`, `511` y `559` lo fijan a mano. El visor NGL carga desde el mismo origen, así
que probablemente no hace falta en ninguna. Si hace falta, debe ser una lista blanca.

**B5 · Metadatos de Compose obsoletos.** `docker-compose.yml:1` declara `version: '3.8'`,
ignorado por Compose v2, y la línea 18 fija `FLASK_ENV=production`, eliminado en Flask 2.3.
Ninguno hace daño; los dos engañan al lector.

**B6 · `CLAUDE.md` describe una aplicación distinta de la que existe.** Documenta cuatro
endpoints que no están: `/api/structures`, `/api/radius/{capsid}`, `/api/generate_pdb` y
`/api/download/{exp_id}`. Dice que las pruebas son «placeholder scripts in `_temp_backup/`»
cuando existe `tests/` con 22 pruebas que pasan. Dice que el radio resta 1 Å cuando suma
(M13) y que los experimentos se guardan con marca de tiempo cuando no (M8). Un asistente o
un colaborador nuevo que lo lea trabajará sobre premisas falsas.

**B7 · `print` en lugar de `logging`.** Hay decenas de `print` por todo `src/core` y
`src/packing`, incluidos los que informan de fallos degradados de A1. En un servidor web
van a la salida estándar sin nivel, sin marca de tiempo y sin estructura, y el usuario del
navegador no los ve. La configuración de `logging` está escrita en
`config/default.yaml:69-77` y no se usa (M10).

---

## 6. Lo que se buscó y no se encontró

Vale la pena dejarlo escrito, porque son las preguntas que un revisor hará:

- **Secretos en el código:** ninguno. Barrido de `api_key`, `secret`, `token`, `password`,
  `credential`, `private_key`, `BEGIN RSA`, `AKIA`, `ghp_`, `sk-` sobre todos los `.py`,
  `.js`, `.yaml`, `.yml`, `.html`, `.sh`, `.toml`, `.ini` y `.cff`. Cero resultados reales.
- **Secretos en el historial:** ninguno. Los 47 commits revisados con los mismos patrones.
- **Travesía de directorios en las rutas con parámetro de ruta:** bloqueada. `/api/file/...`
  y `/api/download/single/<filename>` resisten `..`, `../../etc/passwd`,
  `..%2f..%2fetc%2fpasswd` y `....//etc/passwd`, todas con 404 **[verificado]**. La defensa
  la pone el conversor de rutas de Werkzeug, que no acepta barras, no el código de la
  aplicación: el filtro es gratuito y correcto, pero no es intencionado. Donde el código sí
  valida por su cuenta, falla (M1, M2).
- **Inyección de shell:** ninguna. Todas las llamadas a subproceso usan listas de
  argumentos, nunca `shell=True`. El SMILES llega a `obabel` como `f"-:{smiles}"`
  (`pore.py:420`), que es un argumento, no una orden.
- **`eval` / `exec` / deserialización insegura:** ninguno sobre datos del usuario. El YAML
  se carga con `yaml.safe_load` (`config.py:63`), que es lo correcto. El único camino de
  ejecución de código generado es el de C1, vía PyMOL.
- **SQL:** no hay base de datos.
- **Seguridad de sesiones:** no aplica. No hay `SECRET_KEY`, ni cookies, ni sesiones. Eso es
  una virtud: no hay nada que robar. El `SECRET_KEY` de `.env.example` es decorativo (M10).
- **Dependencias sin fijar:** ninguna. `requirements.txt` fija las cinco directas con `==`,
  y `requirements.lock` fija las transitivas con `pip-compile`. El CI y el `Dockerfile`
  instalan del lock. Esta parte está bien hecha y conviene decirlo. Lo que falta no es
  fijación, es vigilancia (M16) y que `setup.py` sepa leer su propio archivo (A6).

---

## 7. Plan de reparación priorizado

El orden es por riesgo y por lo que desbloquea, no por esfuerzo.

### Tanda 0 — Antes de nada (horas)

Son tres cambios pequeños que cierran la ejecución remota de código. Mientras el
repositorio sea público y alguien pueda estar corriendo el Studio, esto va primero.

| # | Acción | Archivo |
|---|---|---|
| 1 | Validar la posición de mutación como entero antes de interpolarla | `pore.py:287` |
| 2 | Quitar `force=True` de las siete rutas POST | `app.py:105,144,157,170,183,195,235` |
| 3 | Que el host por defecto sea `127.0.0.1` | `config/default.yaml:84` |

Con 1 y 2, C1 deja de ser alcanzable por petición cruzada y deja de ser inyectable. Con 3,
deja de estar expuesto a la red local. La reparación de fondo de C1, dejar de generar
código Python, va en la tanda 2.

### Tanda 1 — Integridad científica (días)

Lo que hace que un número publicado por el Studio sea defendible. Para JOSS esto es el
núcleo.

| # | Acción | Hallazgo |
|---|---|---|
| 4 | Que el radio interno devuelva su procedencia, y que la API y la interfaz la muestren | A1 |
| 5 | Cablear `seed_base` y `use_random_seeds`; devolver la semilla en la respuesta | A2 |
| 6 | Que el criterio de reserva cuente enzimas, no líneas; fallar si no se puede leer la violación | A3 |
| 7 | Prueba de `capsid.calculate_internal_radius` con PyMOL simulado, incluidos los caminos degradados | A10 |
| 8 | Prueba de `_run_single_replica` con log sin línea de violación, aseverando que **no** aprueba | A10 |
| 9 | Unificar los valores de `exclusion_radius` y `max_violation_threshold` en una sola fuente | M11 |
| 10 | Decidir el signo del margen de 1 Å y alinear código, docstring y `CLAUDE.md` | M13 |
| 11 | Arreglar `radio_interno.txt`: por estructura, ruta absoluta, con procedencia | A8 |
| 12 | Marca de tiempo en la ruta del experimento | M8 |
| 13 | Centroide sobre todos los estados, con prueba de un PDB multimodelo | M12 |

Los puntos 4, 5 y 6 son los tres que pueden producir un resultado publicado equivocado. Si
hubiera que elegir tres cosas de todo este informe, serían esas.

### Tanda 2 — Robustez de la aplicación (semana)

| # | Acción | Hallazgo |
|---|---|---|
| 14 | Validar y acotar las cinco entradas numéricas en la frontera HTTP, con un helper único | A4 |
| 15 | Presupuesto de tiempo por petición y semáforo de un motor concurrente, con 429 | A5 |
| 16 | Manejador de errores único: `ValueError`→400, `FileNotFoundError`→404, resto→500 genérico con traza en log | A11 |
| 17 | Poner en marcha `logging` con la configuración que ya está escrita | A11, B7 |
| 18 | Pasar las mutaciones a PyMOL como datos, con un script fijo y versionado | C1 (fondo) |
| 19 | `is_relative_to` en lugar de `startswith`, y resolución con contención en `pore.py` | M1, M2 |
| 20 | Validar `days_old` y exigir confirmación explícita en el borrado | M3 |
| 21 | `textContent` en `setStatus`; filas de tabla con `createElement` | M4 |
| 22 | Cerrar los descriptores del bucle de Packmol con `with` | M9 |
| 23 | Acotar `_smiles_cache` con `lru_cache`; parámetro `seed` en las vistas previas | M7 |

### Tanda 3 — Empaquetado y despliegue (días)

| # | Acción | Hallazgo |
|---|---|---|
| 24 | Cortar comentarios en línea al leer `requirements.txt`, o mover deps a `pyproject.toml` | A6 |
| 25 | Que `io` deje de ser paquete de primer nivel; renombrar el árbol a `vlp_studio/` | A7, B2 |
| 26 | Servir con gunicorn; añadir `USER`; límites de memoria y CPU; publicar en `127.0.0.1` | A9 |
| 27 | Que `setup.py` lea el archivo `VERSION` | M14 |
| 28 | Pasos de CI: `pip install .`, `--cov-fail-under`, construir la imagen, `pip-audit` | M16 |
| 29 | Vendorizar NGL y Chart.js en `static/vendor/`; anotar en `THIRD_PARTY.md` | M5 |
| 30 | Subir `python_requires` a 3.9, corregir clasificadores, probar 3.9 y 3.12 | B1 |

### Tanda 4 — Cobertura y documentación (continuo)

| # | Acción | Hallazgo |
|---|---|---|
| 31 | Una prueba por cada una de las 16 rutas sin cubrir, con entrada válida e inválida | A10 |
| 32 | Prueba de regresión de C1: posición no numérica da 400 y no escribe `_mutgen.py` | C1 |
| 33 | Pruebas de límites para las cinco entradas numéricas | A4 |
| 34 | Limpiar la configuración muerta de `default.yaml` y `.env.example` | M10 |
| 35 | Reescribir `CLAUDE.md` para que describa la aplicación que existe | B6 |
| 36 | Checksums en `fetch_data.sh`; que el camino de reserva no produzca `capside.pdb` | M15 |
| 37 | Bandera `illustrative` en todos los casos, `_SUBSTRATES` incluido; prefijo `/api/demo/` | M17 |
| 38 | Declarar el T de cada cápside en metadatos, o documentar la heurística | M6 |
| 39 | Cabeceras de seguridad y revisión de los `Access-Control-Allow-Origin: *` | B3, B4 |

---

## 8. Nota para la revisión de JOSS

Tres cosas que un revisor va a hacer en los primeros quince minutos, y lo que encontrará
hoy:

1. **`pip install .`** → falla con `InvalidRequirement` (A6). Es el primer gesto y es el
   primer tropiezo.
2. **Leer `config/default.yaml` para entender el protocolo** → encontrará un `seed_base`
   documentado para reproducibilidad que no se usa (A2), un `timeout` de 300 s que en
   realidad es 90 (M10) y valores de `exclusion_radius` que el código contradice (M11).
3. **Abrir la interfaz y pulsar «Calcular radio interno»** → si su PyMOL no está perfecto,
   recibirá 90,0 Å con el mensaje «Radio interno calculado» (A1), sin forma de saber que no
   se calculó nada.

Lo que está bien y conviene no perder en la reparación: la separación de la fachada de
servicios, el lock de dependencias, el golden test de `substrate_section`, las banderas
`illustrative` en los datos sintéticos, la honestidad de los comentarios del `Dockerfile`
sobre lo que la imagen no trae, y la ausencia total de secretos en el código y el historial.

---

*Auditoría de la capa de software, 2026-10-05. Cobertura medida con Python 3.11 y las
dependencias de `requirements.lock`; 22 pruebas, todas pasan, 30% de 1.697 sentencias. Los
hallazgos marcados **[verificado]** se reprodujeron en esta sesión. No se modificó código.*
