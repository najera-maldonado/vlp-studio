"""
Motor de empaquetamiento paralelo con multiprocessing.
Ejecuta múltiples réplicas de Packmol simultáneamente.
"""

import json
import multiprocessing
import random
import re
import shutil
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional


class ParallelPacker:
    """
    Motor de empaquetamiento paralelo que ejecuta múltiples réplicas simultáneamente.
    """

    def __init__(self, packmol_executable: str = "packmol", max_workers: Optional[int] = None):
        """
        Inicializa el motor de empaquetamiento paralelo.

        Args:
            packmol_executable: Ruta al ejecutable de Packmol
            max_workers: Número máximo de workers paralelos (None = núcleos disponibles)
        """
        self.packmol_executable = packmol_executable
        self.max_workers = max_workers or min(multiprocessing.cpu_count(), 7)

        # Regex para extraer violación máxima del log de Packmol
        self._violation_regex = re.compile(
            r"Maximum\s+distance\s+violation:\s*([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)"
        )

    def _read_max_violation(self, log_file: str) -> Optional[float]:
        """
        Extrae la violación máxima de distancia del log de Packmol.

        Args:
            log_file: Archivo de log de Packmol

        Returns:
            Violación máxima en Angstroms, o None si no se encuentra
        """
        try:
            with open(log_file, "r") as f:
                log_content = f.read()
            match = self._violation_regex.search(log_content)
            if match:
                return float(match.group(1))
        except Exception:
            pass
        return None

    def _count_atomic_lines(self, pdb_file: str) -> int:
        """
        Cuenta líneas ATOM/HETATM en archivo PDB.

        Args:
            pdb_file: Archivo PDB

        Returns:
            Número de líneas atómicas
        """
        try:
            with open(pdb_file, "r") as f:
                return sum(1 for line in f if line.startswith(("ATOM", "HETATM")))
        except Exception:
            return 0

    def run_parallel_replicas(
        self,
        capsid_file: str,
        enzyme_file: str,
        n_replicas: int = 7,
        internal_radius: float = 90.0,
        tolerance: float = 2.0,
        exclusion_radius: float = 10.0,
        output_dir: str = "./output",
        seed_base: int = None,
        max_violation_threshold: float = 0.05,
        min_lines_threshold: int = 10000,
    ) -> Dict[str, Any]:
        """
        Ejecuta múltiples réplicas de empaquetamiento en paralelo.

        Args:
            capsid_file: Archivo PDB de la cápside
            enzyme_file: Archivo PDB de la enzima
            n_replicas: Número de réplicas a ejecutar
            internal_radius: Radio interno de la cápside
            tolerance: Tolerancia para Packmol
            exclusion_radius: Radio de exclusión entre enzimas
            output_dir: Directorio de salida
            seed_base: Semilla base para random (None = aleatorio)
            max_violation_threshold: Umbral máximo de violación de distancia (Å)
            min_lines_threshold: Mínimo de líneas atómicas para validar (fallback)

        Returns:
            Diccionario con resultados consolidados
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Preparar argumentos para cada réplica
        replica_args = []
        for i in range(1, n_replicas + 1):
            replica_dir = output_path / f"replica_{i}"
            replica_dir.mkdir(parents=True, exist_ok=True)

            # Semilla única para cada réplica
            if seed_base is not None:
                seed = seed_base + i
            else:
                seed = random.randint(1, 1000000)

            args = {
                "replica_id": i,
                "capsid_file": capsid_file,
                "enzyme_file": enzyme_file,
                "output_dir": str(replica_dir),
                "internal_radius": internal_radius,
                "tolerance": tolerance,
                "exclusion_radius": exclusion_radius,
                "seed": seed,
                "packmol_executable": self.packmol_executable,
                "max_violation_threshold": max_violation_threshold,
                "min_lines_threshold": min_lines_threshold,
            }
            replica_args.append(args)

        # Ejecutar réplicas en paralelo
        print(f"Iniciando {n_replicas} réplicas en paralelo con {self.max_workers} workers...")

        results = []
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # Enviar todas las tareas
            future_to_replica = {
                executor.submit(self._run_single_replica, args): args["replica_id"]
                for args in replica_args
            }

            # Recolectar resultados conforme se completan
            for future in as_completed(future_to_replica):
                replica_id = future_to_replica[future]
                try:
                    result = future.result()
                    results.append(result)
                    print(
                        f"Réplica {replica_id} completada: {result['n_packed']} enzimas empaquetadas"
                    )
                except Exception as e:
                    print(f"Error en réplica {replica_id}: {e}")
                    results.append(
                        {"replica": replica_id, "success": False, "error": str(e), "n_packed": 0}
                    )

        # Consolidar resultados
        consolidated = self._consolidate_results(results, output_path)

        return consolidated

    @staticmethod
    def _run_single_replica(args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta una réplica única de empaquetamiento.
        Worker function para multiprocessing.

        Args:
            args: Argumentos para la réplica

        Returns:
            Diccionario con resultados de la réplica
        """
        replica_id = args["replica_id"]
        capsid_file = args["capsid_file"]
        enzyme_file = args["enzyme_file"]
        output_dir = Path(args["output_dir"])
        internal_radius = args["internal_radius"]
        tolerance = args["tolerance"]
        exclusion_radius = args["exclusion_radius"]
        seed = args["seed"]
        packmol_executable = args["packmol_executable"]
        max_violation_threshold = args["max_violation_threshold"]
        min_lines_threshold = args["min_lines_threshold"]

        # Regex para violación máxima (necesaria en static method)
        violation_regex = re.compile(
            r"Maximum\s+distance\s+violation:\s*([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)"
        )

        def read_max_violation(log_file: str) -> Optional[float]:
            """Extrae violación máxima del log"""
            try:
                with open(log_file, "r") as f:
                    log_content = f.read()
                match = violation_regex.search(log_content)
                if match:
                    return float(match.group(1))
            except Exception:
                pass
            return None

        def count_atomic_lines(pdb_file: str) -> int:
            """Cuenta líneas atómicas"""
            try:
                with open(pdb_file, "r") as f:
                    return sum(1 for line in f if line.startswith(("ATOM", "HETATM")))
            except Exception:
                return 0

        # Validar que los archivos existen
        if not Path(capsid_file).exists():
            return {
                "replica": replica_id,
                "success": False,
                "error": f"Archivo de cápside no encontrado: {capsid_file}",
                "n_packed": 0,
            }

        if not Path(enzyme_file).exists():
            return {
                "replica": replica_id,
                "success": False,
                "error": f"Archivo de enzima no encontrado: {enzyme_file}",
                "n_packed": 0,
            }

        # ALGORITMO INCREMENTAL como en el código original para encontrar máximo empaquetamiento
        best_n = 0
        best_file = None

        def test_packing(n_enzymes: int, max_attempts: int = 2) -> bool:
            """Prueba si N enzimas caben, con múltiples semillas si es necesario"""
            nonlocal best_n, best_file

            for attempt in range(max_attempts):
                # Usar semilla diferente en cada intento
                test_seed = seed + attempt * 1000

                input_file = output_dir / f"packmol_input_{n_enzymes}_attempt{attempt}.inp"
                output_pdb = output_dir / f"packed_{n_enzymes}_attempt{attempt}.pdb"
                log_file = output_dir / f"packmol_log_{n_enzymes}_attempt{attempt}.txt"

                # Generar configuración Packmol
                with open(input_file, "w") as f:
                    f.write(
                        f"# Réplica {replica_id} - {n_enzymes} enzimas (intento {attempt + 1})\n"
                    )
                    f.write(f"tolerance {tolerance}\n")
                    f.write(f"output {output_pdb}\n")
                    # Usar seed para reproducibilidad
                    f.write(f"seed {test_seed}\n")
                    f.write("filetype pdb\n\n")

                    # Cápside fija
                    f.write(f"structure {capsid_file}\n")
                    f.write("  number 1\n")
                    f.write("  fixed 0. 0. 0. 0. 0. 0.\n")
                    f.write("end structure\n\n")

                    # Enzimas dentro de la esfera
                    # CORRECCIÓN CRÍTICA: Aplicar margen de colisión como en código original
                    # radio_usado = radio_interno - margen_colision (90 - 2 = 88)
                    collision_margin = 2.0  # margen por defecto como en original
                    packing_radius = internal_radius - collision_margin
                    f.write(f"structure {enzyme_file}\n")
                    f.write(f"  number {n_enzymes}\n")
                    f.write(f"  inside sphere 0. 0. 0. {packing_radius}\n")
                    f.write(f"  radius {exclusion_radius}\n")
                    f.write("end structure\n")

                # Ejecutar Packmol
                try:
                    result = subprocess.run(
                        [packmol_executable],
                        stdin=open(input_file),
                        stdout=open(log_file, "w"),
                        stderr=subprocess.STDOUT,
                        timeout=90,
                        check=False,
                    )

                    if result.returncode == 0 and output_pdb.exists():
                        # Verificar criterios de éxito
                        violation = read_max_violation(log_file)
                        if violation is not None:
                            if violation <= max_violation_threshold:
                                # Guardar mejor resultado
                                if n_enzymes > best_n:
                                    best_n = n_enzymes
                                    best_file = str(output_pdb)
                                print(
                                    f"    Réplica {replica_id}: ✓ {n_enzymes} enzimas OK (violación: {violation:.4f})"
                                )
                                return True
                        else:
                            # Fallback por conteo de líneas
                            total_lines = count_atomic_lines(output_pdb)
                            if total_lines >= min_lines_threshold:
                                if n_enzymes > best_n:
                                    best_n = n_enzymes
                                    best_file = str(output_pdb)
                                print(
                                    f"    Réplica {replica_id}: ✓ {n_enzymes} enzimas OK (fallback: {total_lines} líneas)"
                                )
                                return True

                except (subprocess.TimeoutExpired, Exception):
                    print(
                        f"    Réplica {replica_id}: Intento {attempt + 1}/{max_attempts} falló con {n_enzymes} enzimas"
                    )

            print(
                f"    Réplica {replica_id}: ✗ {n_enzymes} enzimas NO cabe (después de {max_attempts} intentos)"
            )
            return False

        # BÚSQUEDA INCREMENTAL como en el código original (1, 2, 3, 4, 5...)
        print(f"    Réplica {replica_id}: Búsqueda incremental iniciando...")
        n = 1
        consecutive_failures = 0
        max_consecutive_failures = 3  # Parar después de 3 fallos consecutivos

        while n <= 100:  # Límite de seguridad (tu código llegó a 14)
            print(f"    Réplica {replica_id}: Probando {n} enzimas...")

            if test_packing(n):
                consecutive_failures = 0  # Resetear contador de fallos
                n += 1  # Incrementar de 1 en 1
            else:
                consecutive_failures += 1
                print(
                    f"    Réplica {replica_id}: Fallo con {n} enzimas (fallo {consecutive_failures}/{max_consecutive_failures})"
                )

                if consecutive_failures >= max_consecutive_failures:
                    print(
                        f"    Réplica {replica_id}: {max_consecutive_failures} fallos consecutivos. Deteniendo."
                    )
                    break

                n += 1  # Seguir probando el siguiente número

        print(
            f"    Réplica {replica_id}: Búsqueda incremental completada. Máximo: {best_n} enzimas"
        )

        # Guardar metadata
        metadata = {
            "replica": replica_id,
            "success": best_n > 0,
            "n_packed": best_n,
            "seed": seed,
            "output_file": best_file,
            "internal_radius": internal_radius,
            "tolerance": tolerance,
            "exclusion_radius": exclusion_radius,
        }

        metadata_file = output_dir / "metadata.json"
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)

        return metadata

    def _consolidate_results(self, results: List[Dict], output_path: Path) -> Dict[str, Any]:
        """
        Consolida resultados de todas las réplicas.

        Args:
            results: Lista de resultados de cada réplica
            output_path: Directorio de salida

        Returns:
            Diccionario con estadísticas consolidadas
        """
        # Filtrar solo réplicas exitosas
        successful = [r for r in results if r.get("success", False)]

        if not successful:
            return {
                "success": False,
                "error": "Ninguna réplica fue exitosa",
                "n_replicas_total": len(results),
                "n_replicas_success": 0,
            }

        # Extraer números de enzimas
        n_packed_list = [r["n_packed"] for r in successful]

        # Encontrar mejor resultado
        best_result = max(successful, key=lambda x: x["n_packed"])

        # Copiar mejor resultado a summary
        summary_dir = output_path / "summary"
        summary_dir.mkdir(exist_ok=True)

        if best_result.get("output_file") and Path(best_result["output_file"]).exists():
            best_dest = summary_dir / "best_packing.pdb"
            shutil.copy2(best_result["output_file"], best_dest)

        # Calcular estadísticas
        import statistics

        stats = {
            "success": True,
            "n_replicas_total": len(results),
            "n_replicas_success": len(successful),
            "best": max(n_packed_list),
            "worst": min(n_packed_list),
            "mean": statistics.mean(n_packed_list),
            "median": statistics.median(n_packed_list),
            "stdev": statistics.stdev(n_packed_list) if len(n_packed_list) > 1 else 0,
            "best_replica": best_result["replica"],
            "best_file": str(summary_dir / "best_packing.pdb"),
            "all_results": results,
        }

        # Guardar estadísticas
        stats_file = summary_dir / "statistics.json"
        with open(stats_file, "w") as f:
            json.dump(stats, f, indent=2)

        # Generar reporte
        report_file = summary_dir / "report.txt"
        with open(report_file, "w") as f:
            f.write("=" * 60 + "\n")
            f.write("REPORTE DE EMPAQUETAMIENTO PARALELO\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Réplicas totales: {stats['n_replicas_total']}\n")
            f.write(f"Réplicas exitosas: {stats['n_replicas_success']}\n")
            f.write(f"Mejor resultado: {stats['best']} enzimas (Réplica {stats['best_replica']})\n")
            f.write(f"Promedio: {stats['mean']:.2f} enzimas\n")
            f.write(f"Desviación estándar: {stats['stdev']:.2f}\n\n")

            f.write("Resultados por réplica:\n")
            for r in results:
                status = "OK" if r.get("success") else "FALLO"
                f.write(f"  Réplica {r['replica']}: {r.get('n_packed', 0)} enzimas [{status}]\n")

        print("\nEmpaquetamiento paralelo completado:")
        print(f"  - Mejor resultado: {stats['best']} enzimas")
        print(f"  - Archivo guardado en: {stats['best_file']}")

        return stats


if __name__ == "__main__":
    # Ejemplo de uso
    packer = ParallelPacker()

    results = packer.run_parallel_replicas(
        capsid_file="capside.pdb",
        enzyme_file="enzima.pdb",
        n_replicas=7,
        internal_radius=90.0,
        output_dir="./parallel_output",
    )

    print("\nResultados finales:")
    print(f"  Mejor: {results['best']} enzimas")
    print(f"  Promedio: {results['mean']:.2f}")
    print(f"  Desviación: {results['stdev']:.2f}")
