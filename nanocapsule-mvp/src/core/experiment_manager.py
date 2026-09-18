"""
Gestor de experimentos con múltiples réplicas.
Maneja la ejecución de 7 réplicas para cada combinación cápside-enzima
y organiza los resultados en estructura de carpetas apropiada.
"""

import json
import os
import shutil
import statistics
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.append(str(Path(__file__).parent.parent))

from .config import ConfigManager

try:
    from packing.parallel_packer import ParallelPacker
except ImportError:
    ParallelPacker = None


class ExperimentManager:
    """
    Gestiona experimentos de empaquetamiento con múltiples réplicas.

    Para cada combinación cápside-enzima:
    - Ejecuta 7 réplicas con diferentes semillas
    - Organiza resultados en carpetas estructuradas
    - Genera estadísticas consolidadas
    - Selecciona el mejor resultado
    """

    def __init__(self, config: Optional[ConfigManager] = None, output_base_dir: str = "../Output"):
        """
        Inicializa el gestor de experimentos.

        Args:
            config: Configuración del sistema
            output_base_dir: Directorio base para resultados
        """
        self.config = config or ConfigManager()
        self.output_base_dir = Path(output_base_dir)
        self.n_replicas = 7  # Número de réplicas por experimento
        self.current_experiment = None
        self.use_parallel = (
            ParallelPacker is not None
        )  # Usar procesamiento paralelo si está disponible

    def setup_experiment(self, capsid_name: str, enzyme_name: str) -> Path:
        """
        Configura la estructura de carpetas para un experimento.

        Args:
            capsid_name: Nombre de la cápside (sin extensión)
            enzyme_name: Nombre de la enzima (sin extensión)

        Returns:
            Path al directorio del experimento
        """
        # Limpiar nombres para uso en carpetas
        capsid_clean = Path(capsid_name).stem.replace(" ", "_")
        enzyme_clean = Path(enzyme_name).stem.replace(" ", "_")

        # Crear estructura de carpetas
        experiment_dir = self.output_base_dir / capsid_clean / enzyme_clean

        # Crear carpetas para cada réplica
        for i in range(1, self.n_replicas + 1):
            replica_dir = experiment_dir / f"replica_{i}"
            replica_dir.mkdir(parents=True, exist_ok=True)

        # Crear carpeta para resumen
        summary_dir = experiment_dir / "summary"
        summary_dir.mkdir(parents=True, exist_ok=True)

        # Guardar información del experimento
        self.current_experiment = {
            "capsid": capsid_name,
            "enzyme": enzyme_name,
            "experiment_dir": experiment_dir,
            "timestamp": datetime.now().isoformat(),
            "n_replicas": self.n_replicas,
        }

        # Guardar metadata del experimento
        metadata_path = experiment_dir / "experiment_metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(self.current_experiment, f, indent=2, default=str)

        print(f"Experimento configurado en: {experiment_dir}")
        return experiment_dir

    def get_replica_dir(self, replica_number: int) -> Path:
        """
        Obtiene el directorio para una réplica específica.

        Args:
            replica_number: Número de réplica (1-7)

        Returns:
            Path al directorio de la réplica
        """
        if not self.current_experiment:
            raise RuntimeError("No hay experimento activo. Ejecutar setup_experiment primero.")

        if not 1 <= replica_number <= self.n_replicas:
            raise ValueError(f"Réplica debe estar entre 1 y {self.n_replicas}")

        return self.current_experiment["experiment_dir"] / f"replica_{replica_number}"

    def save_replica_result(self, replica_number: int, result_data: Dict[str, Any]):
        """
        Guarda los resultados de una réplica.

        Args:
            replica_number: Número de réplica
            result_data: Diccionario con resultados
                - n_packed: Número de enzimas empaquetadas
                - output_file: Archivo PDB resultante
                - log_file: Log de Packmol
                - seed: Semilla usada
                - success: Si fue exitoso
                - time_elapsed: Tiempo de ejecución
        """
        replica_dir = self.get_replica_dir(replica_number)

        # Guardar metadata de la réplica
        metadata = {
            "replica": replica_number,
            "timestamp": datetime.now().isoformat(),
            **result_data,
        }

        metadata_path = replica_dir / "metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2, default=str)

        # Copiar archivos de resultado si existen
        if result_data.get("output_file") and os.path.exists(result_data["output_file"]):
            output_dest = replica_dir / Path(result_data["output_file"]).name
            shutil.copy2(result_data["output_file"], output_dest)

        if result_data.get("log_file") and os.path.exists(result_data["log_file"]):
            log_dest = replica_dir / Path(result_data["log_file"]).name
            shutil.copy2(result_data["log_file"], log_dest)

    def consolidate_results(self) -> Dict[str, Any]:
        """
        Consolida los resultados de todas las réplicas.

        Returns:
            Diccionario con estadísticas consolidadas
        """
        if not self.current_experiment:
            raise RuntimeError("No hay experimento activo")

        experiment_dir = self.current_experiment["experiment_dir"]

        # Recolectar resultados de todas las réplicas
        results = []
        for i in range(1, self.n_replicas + 1):
            metadata_path = experiment_dir / f"replica_{i}" / "metadata.json"
            if metadata_path.exists():
                with open(metadata_path, "r") as f:
                    results.append(json.load(f))

        if not results:
            return {"error": "No se encontraron resultados"}

        # Extraer números de enzimas empaquetadas
        n_packed_list = [r["n_packed"] for r in results if r.get("success", False)]

        if not n_packed_list:
            return {"error": "Ninguna réplica fue exitosa"}

        # Calcular estadísticas
        stats = {
            "n_replicas_success": len(n_packed_list),
            "n_replicas_total": self.n_replicas,
            "best": max(n_packed_list),
            "worst": min(n_packed_list),
            "mean": statistics.mean(n_packed_list),
            "median": statistics.median(n_packed_list),
            "stdev": statistics.stdev(n_packed_list) if len(n_packed_list) > 1 else 0,
            "all_values": n_packed_list,
        }

        # Identificar mejor réplica
        best_replica = None
        for r in results:
            if r.get("n_packed") == stats["best"]:
                best_replica = r
                break

        # Copiar mejor resultado a summary
        if best_replica and best_replica.get("output_file"):
            source_file = (
                experiment_dir
                / f"replica_{best_replica['replica']}"
                / Path(best_replica["output_file"]).name
            )
            if source_file.exists():
                best_dest = experiment_dir / "summary" / "best_packing.pdb"
                shutil.copy2(source_file, best_dest)
                stats["best_replica"] = best_replica["replica"]
                stats["best_file"] = str(best_dest)

        # Guardar estadísticas
        stats_path = experiment_dir / "summary" / "statistics.json"
        with open(stats_path, "w") as f:
            json.dump(stats, f, indent=2)

        # Generar reporte texto
        self._generate_report(stats)

        return stats

    def _generate_report(self, stats: Dict[str, Any]):
        """
        Genera un reporte en texto de los resultados.

        Args:
            stats: Estadísticas consolidadas
        """
        experiment_dir = self.current_experiment["experiment_dir"]
        report_path = experiment_dir / "summary" / "report.txt"

        with open(report_path, "w") as f:
            f.write("=" * 60 + "\n")
            f.write("REPORTE DE EXPERIMENTO DE EMPAQUETAMIENTO\n")
            f.write("=" * 60 + "\n\n")

            f.write(f"Cápside: {self.current_experiment['capsid']}\n")
            f.write(f"Enzima: {self.current_experiment['enzyme']}\n")
            f.write(f"Fecha: {self.current_experiment['timestamp']}\n")
            f.write(f"Réplicas: {self.n_replicas}\n\n")

            f.write("RESULTADOS:\n")
            f.write("-" * 40 + "\n")
            f.write(
                f"Réplicas exitosas: {stats.get('n_replicas_success', 0)}/{stats.get('n_replicas_total', 0)}\n"
            )
            f.write(f"Mejor resultado: {stats.get('best', 'N/A')} enzimas\n")
            f.write(f"Peor resultado: {stats.get('worst', 'N/A')} enzimas\n")
            f.write(f"Promedio: {stats.get('mean', 0):.2f} enzimas\n")
            f.write(f"Mediana: {stats.get('median', 0):.2f} enzimas\n")
            f.write(f"Desviación estándar: {stats.get('stdev', 0):.2f}\n\n")

            if stats.get("all_values"):
                f.write("Valores por réplica:\n")
                for i, val in enumerate(stats["all_values"], 1):
                    f.write(f"  Réplica {i}: {val} enzimas\n")

            if stats.get("best_file"):
                f.write(f"\nMejor archivo: {Path(stats['best_file']).name}\n")
                f.write(f"De réplica: {stats.get('best_replica', 'N/A')}\n")

            f.write("\n" + "=" * 60 + "\n")

    def get_experiment_summary(self, capsid_name: str, enzyme_name: str) -> Optional[Dict]:
        """
        Obtiene el resumen de un experimento previo.

        Args:
            capsid_name: Nombre de la cápside
            enzyme_name: Nombre de la enzima

        Returns:
            Diccionario con estadísticas o None si no existe
        """
        capsid_clean = Path(capsid_name).stem.replace(" ", "_")
        enzyme_clean = Path(enzyme_name).stem.replace(" ", "_")

        stats_path = (
            self.output_base_dir / capsid_clean / enzyme_clean / "summary" / "statistics.json"
        )

        if stats_path.exists():
            with open(stats_path, "r") as f:
                return json.load(f)

        return None

    def list_experiments(self) -> List[Dict[str, str]]:
        """
        Lista todos los experimentos realizados.

        Returns:
            Lista de diccionarios con información de experimentos
        """
        experiments = []

        if not self.output_base_dir.exists():
            return experiments

        # Iterar sobre carpetas de cápsides
        for capsid_dir in self.output_base_dir.iterdir():
            if capsid_dir.is_dir():
                # Iterar sobre carpetas de enzimas
                for enzyme_dir in capsid_dir.iterdir():
                    if enzyme_dir.is_dir():
                        # Verificar si hay metadata
                        metadata_path = enzyme_dir / "experiment_metadata.json"
                        if metadata_path.exists():
                            with open(metadata_path, "r") as f:
                                exp_data = json.load(f)

                            # Verificar si hay estadísticas
                            stats_path = enzyme_dir / "summary" / "statistics.json"
                            if stats_path.exists():
                                with open(stats_path, "r") as f:
                                    stats = json.load(f)
                                exp_data["best_result"] = stats.get("best")

                            experiments.append(exp_data)

        return experiments
