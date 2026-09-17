# Descripción del Sistema PackMan v.1.2 para Tesis

## Arquitectura del Software de Simulación Molecular

El sistema PackMan v.1.2 constituye una plataforma integral desarrollada para el estudio computacional de sistemas de encapsulación enzimática mediante simulaciones de dinámica molecular coarse-grained. La arquitectura del software se ha diseñado con un enfoque modular que separa claramente las funcionalidades de empaquetamiento molecular, configuración de simulaciones y gestión de réplicas experimentales.

### Módulo de Empaquetamiento Molecular

El núcleo del sistema reside en el módulo de empaquetamiento, implementado a través de tres componentes algorítmicos principales. El script `1calcula_radio_interno.py` determina computacionalmente las dimensiones internas del cápside viral, estableciendo los límites geométricos para el posicionamiento de las enzimas. Posteriormente, dos algoritmos complementarios de empaquetamiento han sido desarrollados: `2Empaquetador_Manual.py`, que permite el control preciso del posicionamiento molecular mediante parámetros definidos por el usuario, y `2Empaquetador_Maximo.py`, que implementa algoritmos de optimización para maximizar la densidad de empaquetamiento enzimático respetando las restricciones estéricas del sistema.

Las estructuras moleculares base del sistema incluyen archivos PDB procesados tanto para el cápside viral como para las enzimas objetivo, con versiones recentradas que optimizan la orientación espacial para las simulaciones subsecuentes. Esta aproximación permite el estudio sistemático de diferentes configuraciones de empaquetamiento y su impacto en la estabilidad y funcionalidad del sistema encapsulado.

### Pipeline de Simulación Molecular

El protocolo de simulación implementa un flujo de trabajo estandarizado que garantiza la estabilización progresiva del sistema molecular. La secuencia comienza con una etapa de minimización energética dual (em1_WT4.in, em2_WT4.in) que elimina contactos atómicos desfavorables y optimiza la geometría inicial. El proceso continúa con un protocolo de calentamiento gradual implementado en seis etapas incrementales (heat1_0to50.in hasta heat6_250to300.in), que eleva la temperatura del sistema de 0 a 300 K de manera controlada, evitando perturbaciones estructurales abruptas.

La fase de equilibración comprende múltiples etapas especializadas: equilibración de densidad (density_eq.in), equilibración de presión (eq1_WT4.in, eq2_WT4.in), y equilibración final (final_eq.in) que estabiliza todas las propiedades termodinámicas del sistema antes de la fase productiva. Finalmente, la simulación de producción (prod_md_WT4.in) genera las trayectorias moleculares que constituyen los datos primarios para el análisis científico.

### Sistema de Gestión y Configuración

La plataforma incluye un conjunto de scripts de configuración que automatizan la preparación y ejecución de simulaciones. El script maestro `run_MD.sh` coordina la ejecución secuencial de todas las etapas de simulación, mientras que `configurar_simulacion.sh` gestiona la parametrización específica de cada sistema de estudio. El conversor `convert_to_cg.sh` facilita la transición entre representaciones all-atom y coarse-grained, optimizando la eficiencia computacional sin comprometer la precisión científica relevante.

El generador de sistemas `gensystem.leap` utiliza el programa LEaP de AMBER para construir la topología molecular completa, integrando las coordenadas del cápside y las enzimas empaquetadas con el entorno de solvente apropiado. Este proceso genera los archivos de topología (.prmtop) y coordenadas (.inpcrd) necesarios para las simulaciones subsecuentes.

### Arquitectura de Réplicas

El sistema implementa una estructura jerárquica para la gestión de réplicas experimentales, permitiendo la evaluación estadística de los resultados y la validación de la reproducibilidad. El directorio ReplicaExtra contiene simulaciones adicionales organizadas numéricamente, cada una manteniendo la misma estructura de directorios que el sistema principal. Esta aproximación facilita el análisis comparativo entre diferentes condiciones experimentales y proporciona la base estadística necesaria para conclusiones científicas robustas.

### Consideraciones Metodológicas

La implementación de simulaciones coarse-grained representa una decisión metodológica estratégica que equilibra la precisión molecular con la eficiencia computacional. Esta aproximación permite el estudio de sistemas de gran escala (cápsides virales con múltiples enzimas encapsuladas) en escalas temporales relevantes para los procesos biológicos de interés, manteniendo la resolución suficiente para caracterizar las interacciones moleculares fundamentales que determinan la funcionalidad del sistema de encapsulación.

El diseño modular del software facilita la extensión y modificación de protocolos específicos sin comprometer la integridad del pipeline general, proporcionando una plataforma versátil para la investigación de sistemas de encapsulación enzimática en diferentes contextos biológicos y aplicaciones biotecnológicas.