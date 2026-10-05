"""
Ejecutor de experimentos con soporte para procesamiento paralelo.
Integra el ExperimentManager con el ParallelPacker para ejecutar réplicas.

Política "que falle, no que avise" (AUDITORIA_PACKING PK-02/P-11, HOJA_DE_RUTA T3):
un experimento NO se ejecuta con un radio de reserva ni con una cápside sin centrar.
Si el radio no se pudo calcular o el centrado falla, se lanza una excepción con la
causa; nunca se sigue adelante en silencio.
"""

import sys
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from ..packing.parallel_packer import DEFAULT_SEED_BASE, ParallelPacker
except ImportError:  # ejecución como script suelto (python experiment_runner.py ...)
    sys.path.append(str(Path(__file__).parent.parent))
    from packing.parallel_packer import DEFAULT_SEED_BASE, ParallelPacker

from .capsid import Capsid
from .cargo import Cargo
from .config import ConfigManager
from .experiment_manager import ExperimentManager


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
        self.experiment_manager = ExperimentManager(
            output_base_dir=output_base_dir, config=self.config
        )
        packmol_cfg = self.config.get_engine_config("packmol") or {}
        max_workers = packmol_cfg.get("max_workers")
        self.parallel_packer = ParallelPacker(
            packmol_executable=packmol_cfg.get("executable", "packmol"),
            max_workers=int(max_workers) if max_workers else None,
        )

    def packing_parameters(self) -> Dict[str, Any]:
        """
        Único punto de lectura de los parámetros de empaquetamiento desde la config.

        Los valores de reserva coinciden con ``config/default.yaml``; si una clave falta
        en el YAML se usa el mismo número que está documentado ahí.
        """
        packmol_cfg = self.config.get_engine_config("packmol") or {}
        return {
            "tolerance": float(self.config.get("packing.tolerance", 2.0)),
            "exclusion_radius": float(self.config.get("packing.exclusion_radius", 5.0)),
            "collision_margin": float(self.config.get("packing.collision_margin", 2.0)),
            "max_violation_threshold": float(
                self.config.get("packing.max_violation_threshold", 0.10)
            ),
            "timeout": float(packmol_cfg.get("timeout", 300)),
            "seed_base": int(packmol_cfg.get("seed_base", DEFAULT_SEED_BASE)),
            "use_random_seeds": bool(packmol_cfg.get("use_random_seeds", False)),
        }

    def run_maximum_packing(
        self,
        capsid_file: str,
        enzyme_file: str,
        capsid_name: Optional[str] = None,
        enzyme_name: Optional[str] = None,
        n_replicas: Optional[int] = None,
        internal_radius: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Ejecuta empaquetamiento máximo con múltiples réplicas en paralelo.

        Args:
            capsid_file: Archivo PDB de la cápside
            enzyme_file: Archivo PDB de la enzima
            capsid_name: Nombre de la cápside para organización
            enzyme_name: Nombre de la enzima para organización
            n_replicas: Número de réplicas (None → ``experiments.n_replicas`` de la config)
            internal_radius: Radio interno en Å dado por el usuario. Si es None se
                calcula con PyMOL y se exige que el cálculo haya ocurrido de verdad.

        Returns:
            Diccionario con resultados consolidados

        Raises:
            FileNotFoundError: si falta algún PDB de entrada
            RuntimeError: si el radio no se pudo calcular o el centrado falló
        """
        # Usar nombres de archivo si no se proporcionan nombres
        if not capsid_name:
            capsid_name = str(Path(capsid_file).stem)
        if not enzyme_name:
            enzyme_name = str(Path(enzyme_file).stem)
        if n_replicas is None:
            n_replicas = int(self.config.get("experiments.n_replicas", 10))

        print(f"\n{'=' * 60}")
        print("EXPERIMENTO DE EMPAQUETAMIENTO MÁXIMO")
        print(f"Cápside: {capsid_name}")
        print(f"Enzima: {enzyme_name}")
        print(f"Réplicas: {n_replicas} (ejecutándose en paralelo)")
        print(f"{'=' * 60}\n")

        # Validar archivos de entrada
        if not Path(capsid_file).exists():
            raise FileNotFoundError(f"Archivo de cápside no encontrado: {capsid_file}")
        if not Path(enzyme_file).exists():
            raise FileNotFoundError(f"Archivo de enzima no encontrado: {enzyme_file}")

        print("Archivos validados:")
        print(f"  Cápside: {Path(capsid_file).resolve()}")
        print(f"  Enzima: {Path(enzyme_file).resolve()}\n")

        # Configurar estructura de experimento
        experiment_dir = self.experiment_manager.setup_experiment(
            capsid_name, enzyme_name, n_replicas=n_replicas
        )
        if experiment_dir is None:
            raise ValueError("No se pudo configurar el directorio del experimento")
        experiment_dir = Path(experiment_dir)
        print(f"Directorio de experimento: {experiment_dir}")

        # 1) Radio interno: calculado de verdad o dado por el usuario; nunca el de reserva.
        capsid = Capsid(capsid_file, config=self.config)
        if internal_radius is not None:
            internal_radius = float(internal_radius)
            radius_source = "user"
            print(f"Radio interno dado por el usuario: {internal_radius:.2f} Å\n")
        else:
            print("Calculando radio interno de la cápside...")
            internal_radius = capsid.calculate_internal_radius()
            radius_source = capsid.radius_source
            if radius_source != "calculated" or internal_radius is None:
                default = self.config.get("packing.internal_radius_default", 90.0)
                raise RuntimeError(
                    "No se pudo calcular el radio interno de la cápside (PyMOL no "
                    "disponible en este intérprete o cálculo fallido). No se ejecuta el "
                    f"experimento con el valor de reserva ({default} Å): instala el módulo "
                    "Python `pymol` o pasa `internal_radius` explícitamente."
                )
            print(f"Radio interno calculado: {internal_radius:.2f} Å\n")

        # 2) Centrado de cápside y enzima (Python puro). Si falla, se aborta: una cápside
        #    sin centrar con la esfera en el origen empaqueta enzimas en el vacío.
        #    Los archivos centrados van al directorio del experimento, no a Input/.
        print("Centrando cápside y enzima...")
        centered_capsid = capsid.center_structure(
            output_path=str(experiment_dir / "capside_centered.pdb")
        )
        cargo = Cargo(enzyme_file, config=self.config)
        centered_enzyme = cargo.center_structure(
            output_path=str(experiment_dir / "enzima_centered.pdb")
        )

        # 3) Parámetros: un solo sitio de lectura.
        params = self.packing_parameters()

        print(f"\nEjecutando {n_replicas} réplicas en paralelo...")
        print("Parámetros de ejecución:")
        print(f"  Cápside: {centered_capsid}")
        print(f"  Enzima: {centered_enzyme}")
        print(f"  Radio interno: {internal_radius} ({radius_source})")
        for k, v in params.items():
            print(f"  {k}: {v}")
        print(f"  Directorio salida: {experiment_dir}\n")

        results = self.parallel_packer.run_parallel_replicas(
            capsid_file=str(centered_capsid),
            enzyme_file=str(centered_enzyme),
            n_replicas=n_replicas,
            internal_radius=float(internal_radius),
            output_dir=str(experiment_dir),
            **params,
        )

        # Agregar información adicional
        results["capsid_name"] = capsid_name
        results["enzyme_name"] = enzyme_name
        results["internal_radius"] = internal_radius
        results["radius_source"] = radius_source
        results["experiment_dir"] = str(experiment_dir)

        # Mostrar resumen de resultados
        self._print_summary(results)

        return results

    def _print_summary(self, results: Dict[str, Any]):
        """
        Imprime un resumen de los resultados.

        Args:
            results: Resultados del experimento
        """
        print(f"\n{'=' * 60}")
        print("RESUMEN DE RESULTADOS")
        print(f"{'=' * 60}")

        if results.get("success"):
            print("✓ Experimento completado exitosamente")
            print(
                f"  - Réplicas exitosas: {results['n_replicas_success']}/{results['n_replicas_total']}"
            )
            print(f"  - Mejor resultado: {results['best']} enzimas")
            print(f"  - Promedio: {results['mean']:.2f} enzimas")
            stdev = results.get("stdev")
            print(
                "  - Desviación estándar: "
                + (f"{stdev:.2f}" if stdev is not None else "no definida (< 2 réplicas)")
            )
            print(f"  - Mejor archivo: {results.get('best_file', 'N/A')}")
        else:
            print(f"✗ Experimento fallido: {results.get('error', 'Error desconocido')}")
            if results.get("rejection_reasons"):
                print(f"  - Causas de rechazo: {results['rejection_reasons']}")

        for w in results.get("warnings", []):
            print(f"  - AVISO: {w}")

        print(f"\nResultados guardados en: {results.get('experiment_dir', 'N/A')}")
        print(f"{'=' * 60}\n")


def run_parallel_experiment(
    capsid_file: str, enzyme_file: str, output_dir: str = "Output"
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

    print("\nExperimento finalizado.")
    print(f"Mejor resultado: {results.get('best', 0)} enzimas empaquetadas")
