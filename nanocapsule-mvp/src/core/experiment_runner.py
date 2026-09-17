"""
Ejecutor de experimentos con soporte para procesamiento paralelo.
Integra el ExperimentManager con el ParallelPacker para ejecutar réplicas.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import sys
sys.path.append(str(Path(__file__).parent.parent))

from .experiment_manager import ExperimentManager
from .capsid import Capsid
from .cargo import Cargo
from .config import ConfigManager
from packing.parallel_packer import ParallelPacker


class ExperimentRunner:
    """
    Ejecuta experimentos de empaquetamiento con procesamiento paralelo.
    """

    def __init__(self, output_base_dir: str = "Output", config: Optional[ConfigManager] = None):
        """
        Inicializa el ejecutor de experimentos.

        Args:
            output_base_dir: Directorio base para resultados
            config: Configuración del sistema
        """
        self.config = config or ConfigManager()
        self.experiment_manager = ExperimentManager(output_base_dir=output_base_dir, config=self.config)
        self.parallel_packer = ParallelPacker(
            packmol_executable=self.config.get('engines.packmol.executable', 'packmol')
        )

    def run_maximum_packing(
        self,
        capsid_file: str,
        enzyme_file: str,
        capsid_name: Optional[str] = None,
        enzyme_name: Optional[str] = None,
        n_replicas: int = 10
    ) -> Dict[str, Any]:
        """
        Ejecuta empaquetamiento máximo con múltiples réplicas en paralelo.

        Args:
            capsid_file: Archivo PDB de la cápside
            enzyme_file: Archivo PDB de la enzima
            capsid_name: Nombre de la cápside para organización
            enzyme_name: Nombre de la enzima para organización
            n_replicas: Número de réplicas a ejecutar

        Returns:
            Diccionario con resultados consolidados
        """
        # Usar nombres de archivo si no se proporcionan nombres
        if not capsid_name:
            capsid_name = str(Path(capsid_file).stem)
        if not enzyme_name:
            enzyme_name = str(Path(enzyme_file).stem)

        print(f"\n{'='*60}")
        print(f"EXPERIMENTO DE EMPAQUETAMIENTO MÁXIMO")
        print(f"Cápside: {capsid_name}")
        print(f"Enzima: {enzyme_name}")
        print(f"Réplicas: {n_replicas} (ejecutándose en paralelo)")
        print(f"{'='*60}\n")

        # Validar archivos de entrada
        if not Path(capsid_file).exists():
            raise FileNotFoundError(f"Archivo de cápside no encontrado: {capsid_file}")
        if not Path(enzyme_file).exists():
            raise FileNotFoundError(f"Archivo de enzima no encontrado: {enzyme_file}")

        print(f"Archivos validados:")
        print(f"  Cápside: {Path(capsid_file).resolve()}")
        print(f"  Enzima: {Path(enzyme_file).resolve()}\n")

        # Configurar estructura de experimento
        experiment_dir = self.experiment_manager.setup_experiment(capsid_name, enzyme_name)

        if experiment_dir is None:
            raise ValueError("No se pudo configurar el directorio del experimento")

        print(f"Directorio de experimento: {experiment_dir}")

        # Calcular radio interno de la cápside y centrarla
        print("Calculando radio interno de la cápside...")
        print(f"Archivo de cápside: {capsid_file}")

        try:
            capsid = Capsid(capsid_file)
            internal_radius = capsid.calculate_internal_radius()

            if internal_radius is None:
                print("Advertencia: Radio interno retornó None, usando valor por defecto")
                internal_radius = self.config.get('packing.internal_radius_default', 90.0)

            print(f"Radio interno: {internal_radius:.2f} Å\n")

            # IMPORTANTE: Centrar la cápside también
            print("Centrando cápside para alinear con enzimas...")
            centered_capsid = capsid.center_structure()
            if centered_capsid:
                capsid_file = centered_capsid  # Usar la cápside centrada
                print(f"Cápside centrada guardada en: {centered_capsid}")

        except Exception as e:
            print(f"Error calculando radio interno: {e}")
            internal_radius = self.config.get('packing.internal_radius_default', 90.0)
            print(f"Usando radio interno por defecto: {internal_radius:.2f} Å\n")

        # Preparar enzima (centrar)
        print("Preparando enzima...")
        try:
            cargo = Cargo(enzyme_file)
            centered_enzyme = cargo.center_structure()
            if centered_enzyme is None:
                print("Advertencia: No se pudo centrar la enzima, usando archivo original")
                centered_enzyme = enzyme_file
        except Exception as e:
            print(f"Advertencia: Error centrando enzima: {e}")
            print("Usando archivo original de enzima")
            centered_enzyme = enzyme_file

        # Obtener parámetros de configuración
        tolerance = self.config.get('packing.tolerance', 2.0)
        exclusion_radius = self.config.get('packing.exclusion_radius', 10.0)
        max_violation_threshold = self.config.get('packing.max_violation_threshold', 0.05)
        min_lines_threshold = self.config.get('packing.min_lines_threshold', 10000)

        # Ejecutar réplicas en paralelo
        print(f"\nEjecutando {n_replicas} réplicas en paralelo...")
        print("Esto puede tomar varios minutos...\n")

        # Validar todos los parámetros antes de ejecutar
        print(f"Parámetros de ejecución:")
        print(f"  Cápside: {capsid_file}")
        print(f"  Enzima: {centered_enzyme}")
        print(f"  Radio interno: {internal_radius}")
        print(f"  Tolerancia: {tolerance}")
        print(f"  Radio exclusión: {exclusion_radius}")
        print(f"  Umbral violación máx: {max_violation_threshold}")
        print(f"  Directorio salida: {experiment_dir}\n")

        # Verificar que ningún valor sea None
        if any(v is None for v in [capsid_file, centered_enzyme, internal_radius, experiment_dir]):
            raise ValueError(f"Parámetros inválidos para empaquetamiento: "
                           f"capsid={capsid_file}, enzyme={centered_enzyme}, "
                           f"radius={internal_radius}, dir={experiment_dir}")

        results = self.parallel_packer.run_parallel_replicas(
            capsid_file=str(capsid_file),
            enzyme_file=str(centered_enzyme),
            n_replicas=n_replicas,
            internal_radius=float(internal_radius),
            tolerance=float(tolerance),
            exclusion_radius=float(exclusion_radius),
            output_dir=str(experiment_dir),
            max_violation_threshold=float(max_violation_threshold),
            min_lines_threshold=int(min_lines_threshold)
        )

        # Agregar información adicional
        results['capsid_name'] = capsid_name
        results['enzyme_name'] = enzyme_name
        results['internal_radius'] = internal_radius
        results['experiment_dir'] = str(experiment_dir)

        # Mostrar resumen de resultados
        self._print_summary(results)

        return results

    def _print_summary(self, results: Dict[str, Any]):
        """
        Imprime un resumen de los resultados.

        Args:
            results: Resultados del experimento
        """
        print(f"\n{'='*60}")
        print("RESUMEN DE RESULTADOS")
        print(f"{'='*60}")

        if results.get('success'):
            print(f"✓ Experimento completado exitosamente")
            print(f"  - Réplicas exitosas: {results['n_replicas_success']}/{results['n_replicas_total']}")
            print(f"  - Mejor resultado: {results['best']} enzimas")
            print(f"  - Promedio: {results['mean']:.2f} enzimas")
            print(f"  - Desviación estándar: {results['stdev']:.2f}")
            print(f"  - Mejor archivo: {results.get('best_file', 'N/A')}")
        else:
            print(f"✗ Experimento fallido: {results.get('error', 'Error desconocido')}")

        print(f"\nResultados guardados en: {results.get('experiment_dir', 'N/A')}")
        print(f"{'='*60}\n")


def run_parallel_experiment(
    capsid_file: str,
    enzyme_file: str,
    output_dir: str = "Output"
) -> Dict[str, Any]:
    """
    Función auxiliar para ejecutar un experimento con procesamiento paralelo.

    Args:
        capsid_file: Archivo PDB de la cápside
        enzyme_file: Archivo PDB de la enzima
        output_dir: Directorio de salida

    Returns:
        Resultados del experimento
    """
    runner = ExperimentRunner(output_dir)
    return runner.run_maximum_packing(capsid_file, enzyme_file)


if __name__ == "__main__":
    # Ejemplo de uso
    import sys

    if len(sys.argv) != 3:
        print("Uso: python experiment_runner.py <capside.pdb> <enzima.pdb>")
        sys.exit(1)

    capsid_file = sys.argv[1]
    enzyme_file = sys.argv[2]

    results = run_parallel_experiment(capsid_file, enzyme_file)

    print(f"\nExperimento finalizado.")
    print(f"Mejor resultado: {results.get('best', 0)} enzimas empaquetadas")