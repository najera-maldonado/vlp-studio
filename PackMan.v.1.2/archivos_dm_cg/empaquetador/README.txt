README — Empaquetamiento máximo de enzimas dentro de una cápside (PyMOL + Packmol)
================================================================================

Este README describe un pipeline listo para correr para empaquetar el MAYOR número posible de copias
de una enzima dentro de una cápside, usando PyMOL para preprocesado y Packmol para el acomodo.
El modo automático itera n=1→… y se detiene cuando el log de Packmol reporta colisiones por encima
del umbral permitido. El modo manual permite fijar N.

------------------------------------------------------------------------------
TL;DR (pasos express)
------------------------------------------------------------------------------
1) Nombra tus archivos EXACTAMENTE así (en el mismo directorio):
   capside.pdb
   enzima.pdb

2) Calcula el radio interno de la cápside (se guarda en radio_interno.txt):
   pymol -cq 1calcula_radio_interno.py

3) Empaquetamiento máximo (loop automático n=1→… hasta colisión inaceptable):
   pymol -cq Empaquetador_Maximo.py

   Alternativa manual (elige N fijo):
   pymol -cq Empaquetador_Manual.py

------------------------------------------------------------------------------
Requisitos
------------------------------------------------------------------------------
- PyMOL con interfaz Python (para ejecutar con 'pymol -cq').
- Packmol instalado y accesible en PATH (comando 'packmol').
- NumPy disponible para el Python que usa PyMOL.

------------------------------------------------------------------------------
Archivos del repositorio
------------------------------------------------------------------------------
- 1calcula_radio_interno.py
  Centra la cápside, estima el RADIO INTERNO por colisión de un pseudoátomo
  y guarda el resultado en 'radio_interno.txt'.

- Empaquetador_Manual.py
  Empaca N enzimas: centra PDBs, construye el input de Packmol, ejecuta Packmol
  y separa las enzimas individuales del PDB final si todo salió bien.

- Empaquetador_Maximo.py
  Auto-maximiza N: itera corriendo Packmol, PARSEA el log para
  'Maximum distance violation' y se queda con el último N aceptado.
  También separa enzimas individuales al final.

------------------------------------------------------------------------------
Flujo detallado
------------------------------------------------------------------------------
1) Calcular radio interno (obligatorio la primera vez)
   Comando:
     pymol -cq 1calcula_radio_interno.py

   Qué hace:
   - Carga 'capside.pdb', la centra/orienta.
   - Calcula centro geométrico y crea un pseudoátomo en el centro.
   - Aumenta su radio VDW hasta el primer contacto con la malla de la cápside.
   - Registra el valor de radio interno y añade ~1 Å de holgura.
   - Escribe 'radio_interno.txt' con el valor en Å.

   Nota: Si 'radio_interno.txt' no existe, los empacadores usan 90 Å por defecto.

2A) Modo AUTOMÁTICO (recomendado): Empaquetamiento máximo
   Comando:
     pymol -cq Empaquetador_Maximo.py

   Resumen operativo:
   - Re-centra 'capside.pdb' y 'enzima.pdb' al origen y guarda
     'capside_recentrada.pdb' y 'enzima_recentrada.pdb'.
   - Lee 'radio_interno.txt' (o usa 90 Å por defecto) y aplica
     MARGEN_DE_COLISIÓN = 2 Å → radio_usado = radio_interno − 2.
   - Itera n = 1, 2, 3, …:
       * Genera input Packmol con:
           tolerance = 2.0
           inside sphere 0.0 0.0 0.0 <radio_usado>
           radius = 5.0  (exclusión entre copias de la enzima)
           (opcional) seed 1234567
       * Ejecuta Packmol y parsea el log buscando 'Maximum distance violation'.
       * ACEPTA si violación ≤ 0.10 Å (umbral por defecto).
       * Si la violación supera el umbral, se detiene y conserva el último n válido.
       * Fallback: si el log no trae la métrica, valida por conteo mínimo de líneas
         ATOM/HETATM (> 10 000, ajustable).
   - Al final:
       * Reporta N máximo aceptado.
       * Deja PDB ensamblado: 'capside_{N}enzimas_YYYYmmdd_HHMMSS.pdb'.
       * Separa cada enzima en 'enzimas_individuales/enzima_#.pdb'
         (asumiendo cápside primero y conteo de líneas uniforme).

   Parámetros clave (editables dentro del script):
     umbral_violacion_maxima = 0.10       # Å
     packmol_tolerance       = 2.0
     margen_colision         = 2.0        # Å → radio_usado = radio_interno − margen
     radio_exclusion         = 5.0        # Å (entre enzimas)
     umbral_minimo_lineas    = 10000      # fallback de validez

2B) Modo MANUAL: N fijo
   Comando:
     pymol -cq Empaquetador_Manual.py

   Comportamiento:
   - Pide por consola la cantidad de enzimas N.
   - Re-centra cápside y enzima, arma el input de Packmol con 'tolerance=2.0',
     'inside sphere' usando 'radio_interno − 2 Å' y 'radius=5.0'.
   - Ejecuta Packmol y separa enzimas individuales si el ensamblado es válido.

------------------------------------------------------------------------------
Nombres de salida (convenciones)
------------------------------------------------------------------------------
- radio_interno.txt                           → radio interno estimado (Å)
- capside_recentrada.pdb / enzima_recentrada.pdb
- capside_{n}enzimas_YYYYmmdd_HHMMSS.pdb      → ensamblado final
- log_packmol_{n}enzimas_YYYYmmdd_HHMMSS.txt  → logs de Packmol
- enzimas_individuales/enzima_#.pdb           → copias separadas

------------------------------------------------------------------------------
Ajustes finos (cuándo mover perillas)
------------------------------------------------------------------------------
- ¿N máximo muy bajo (choca pronto)?
  * Baja 'radio_exclusion' a 4.0–4.5 Å si tu enzima lo tolera.
  * Reduce 'margen_colision' a 1.0 Å si el radio interno está bien medido.
  * Sube 'packmol_tolerance' a 2.5–3.0 para darle más holgura a Packmol.

- ¿Acepta geometrías raras?
  * Endurece 'umbral_violacion_maxima' (p. ej. 0.05 Å).

- Reproducibilidad
  * Define 'seed 1234567' en el input de Packmol si deseas resultados repetibles.

------------------------------------------------------------------------------
Solución de problemas
------------------------------------------------------------------------------
- 'packmol: command not found'
  * Instala Packmol y confirma que 'which packmol' lo encuentra.

- El log no muestra 'Maximum distance violation'
  * Usa el fallback de 'umbral_minimo_lineas' o ajusta ese umbral para sistemas pequeños.

- 'enzimas_individuales' incompleto
  * Asegúrate de que la PRIMERA estructura del PDB final es la cápside y que cada enzima
    tiene el mismo número de líneas ATOM/HETATM que 'enzima_recentrada.pdb'.
  * Limpia 'enzima.pdb' (sin MODEL/ENDMDL ni solvente/ligandos innecesarios).

- Radio interno absurdo
  * Verifica que 'capside.pdb' SOLO contenga la malla de la cápside (sin agua/ligandos).
  * Repite: pymol -cq 1calcula_radio_interno.py

------------------------------------------------------------------------------
Notas prácticas
------------------------------------------------------------------------------
- El radio efectivo para colocar enzimas es: radio_interno − margen_colision.
- 'radius' en Packmol (default 5 Å) controla la separación entre copias de la enzima;
  bajarlo aumenta N pero arriesga solapamientos poco realistas.
- No requieres GPU para estos pasos; el cuello de botella suele ser Packmol cuando N crece.

------------------------------------------------------------------------------
Ejemplos de ejecución
------------------------------------------------------------------------------
# Máximo automático
pymol -cq 1calcula_radio_interno.py
pymol -cq Empaquetador_Maximo.py

# Manual con N=6
pymol -cq 1calcula_radio_interno.py
pymol -cq Empaquetador_Manual.py   # al solicitarlo, ingresa: 6

------------------------------------------------------------------------------
Estructura mínima del directorio
------------------------------------------------------------------------------
./capside.pdb
./enzima.pdb
./1calcula_radio_interno.py
./Empaquetador_Maximo.py
./Empaquetador_Manual.py

------------------------------------------------------------------------------
Fin
------------------------------------------------------------------------------
