"""
Motor de empaquetamiento paralelo con multiprocessing.
Ejecuta múltiples réplicas de Packmol simultáneamente.

Criterio de aceptación de una corrida de PACKMOL (reparación tras AUDITORIA_PACKING,
hallazgos P-01/P-02/P-04 y PK-01/PK-02):

1. El log debe contener el marcador de éxito de PACKMOL (``Success!``) y NO el de
   fallo (``ENDED WITHOUT PERFECT PACKING``); tampoco debe existir ``<output>_FORCED``,
   que es la señal explícita de PACKMOL de que no convergió. El código de salida del
   proceso se registra pero no basta por sí solo.
2. La violación máxima se lee de la línea real que escribe PACKMOL,
   ``Maximum violation of target distance:``, tomando el ÚLTIMO valor del log (el del
   bloque final), y debe ser ≤ ``max_violation_threshold``.
3. El PDB de salida debe contener exactamente ``átomos_cápside + n × átomos_enzima``
   líneas atómicas: se cuentan las copias de enzima realmente colocadas. Ya no existe el
   fallback por "≥ 10 000 líneas", que la cápside sola satisfacía.
4. El centroide de cada copia de enzima debe caer dentro de la esfera de empaque medida
   desde el centroide de la cápside en el MISMO archivo de salida. Esto detecta el caso
   de una cápside sin centrar con enzimas empaquetadas en el vacío.

La cápside entra en el ``.inp`` como ``center`` + ``fixed 0 0 0 0 0 0``: PACKMOL la
recentra en el origen aunque el PDB de entrada no lo esté.
"""

import json
import multiprocessing
import random
import re
import shutil
import statistics
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

# --------------------------------------------------------------------------- #
# Especificación del log de PACKMOL (cadenas reales, ver tests/fixtures/packmol_logs)
# --------------------------------------------------------------------------- #

#: Marcador que PACKMOL escribe en el bloque final cuando el empaquetado convergió.
PACKMOL_SUCCESS_MARKER = "Success!"

#: Marcador del bloque final cuando PACKMOL NO convergió (deja ``<output>_FORCED``).
PACKMOL_FAILURE_REGEX = re.compile(r"ENDED\s+WITHOUT\s+PERFECT\s+PACKING")

# Número en formato Fortran: "3.970194", ".12571E-01", "7.7660690978852759E-003", "0.0".
_FORTRAN_NUMBER = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eEdD][-+]?\d+)?"

#: Línea real de violación máxima. Aparece en cada bloque de iteración y en el final;
#: el valor que importa es el ÚLTIMO.
PACKMOL_VIOLATION_REGEX = re.compile(
    r"Maximum\s+violation\s+of\s+target\s+distance:\s*(" + _FORTRAN_NUMBER + r")"
)

#: Semilla base por defecto (coincide con la semilla interna por defecto de PACKMOL).
DEFAULT_SEED_BASE = 1234567

#: Techo del bucle de búsqueda incremental. Si una réplica lo alcanza, el resultado se
#: marca ``search_ceiling_reached``: es una constante del código, no una medición.
SEARCH_CEILING = 100


@dataclass
class PackmolLogSummary:
    """Lo que el log de PACKMOL dice sobre la corrida."""

    success_marker: bool
    failure_marker: bool
    max_violation: Optional[float]
    n_violation_values: int


def parse_packmol_log(log_text: str) -> PackmolLogSummary:
    """Extrae del log de PACKMOL los marcadores de éxito/fallo y la violación final."""
    values = PACKMOL_VIOLATION_REGEX.findall(log_text)
    max_violation = None
    if values:
        max_violation = float(values[-1].replace("D", "E").replace("d", "e"))
    return PackmolLogSummary(
        success_marker=PACKMOL_SUCCESS_MARKER in log_text,
        failure_marker=PACKMOL_FAILURE_REGEX.search(log_text) is not None,
        max_violation=max_violation,
        n_violation_values=len(values),
    )


def read_packmol_log(log_file) -> Optional[PackmolLogSummary]:
    """Lee y parsea un log de PACKMOL; ``None`` si el archivo no se puede leer."""
    try:
        with open(log_file, "r", errors="replace") as f:
            return parse_packmol_log(f.read())
    except OSError:
        return None


# --------------------------------------------------------------------------- #
# Utilidades PDB (Python puro, sin PyMOL)
# --------------------------------------------------------------------------- #
def iter_atomic_coords(pdb_file) -> Iterator[Tuple[float, float, float]]:
    """Itera las coordenadas de las líneas ATOM/HETATM de un PDB (columnas fijas)."""
    with open(pdb_file, "r", errors="replace") as f:
        for line in f:
            if line.startswith(("ATOM", "HETATM")) and len(line) >= 54:
                try:
                    yield (float(line[30:38]), float(line[38:46]), float(line[46:54]))
                except ValueError:
                    continue


def count_atomic_lines(pdb_file) -> int:
    """Cuenta líneas ATOM/HETATM de un PDB (0 si no se puede leer)."""
    try:
        with open(pdb_file, "r", errors="replace") as f:
            return sum(1 for line in f if line.startswith(("ATOM", "HETATM")))
    except OSError:
        return 0


def pdb_centroid(pdb_file) -> Optional[Tuple[float, float, float]]:
    """Centroide (media de coordenadas) de los átomos de un PDB, o None si no hay átomos."""
    sx = sy = sz = 0.0
    n = 0
    for x, y, z in iter_atomic_coords(pdb_file):
        sx += x
        sy += y
        sz += z
        n += 1
    if n == 0:
        return None
    return (sx / n, sy / n, sz / n)


def _dist(a, b) -> float:
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2) ** 0.5


@dataclass
class RunVerdict:
    """Resultado de evaluar una corrida de PACKMOL."""

    accepted: bool
    reason: str
    details: Dict[str, Any] = field(default_factory=dict)


def verify_packed_output(
    output_pdb,
    n_capsid_atoms: int,
    n_enzyme_atoms: int,
    n_requested: int,
    packing_radius: float,
) -> RunVerdict:
    """
    Verifica que el PDB de salida contenga exactamente las enzimas pedidas y que estén
    dentro de la esfera de empaque medida desde el centroide de la cápside.

    PACKMOL escribe las estructuras en el orden del ``.inp``: primero la cápside (fija),
    después las ``n`` copias de la enzima, cada una con ``n_enzyme_atoms`` líneas.
    """
    coords = list(iter_atomic_coords(output_pdb))
    n_atoms = len(coords)
    expected = n_capsid_atoms + n_requested * n_enzyme_atoms
    details: Dict[str, Any] = {"n_atoms": n_atoms, "n_atoms_expected": expected}

    extra = n_atoms - n_capsid_atoms
    if n_enzyme_atoms > 0 and extra >= 0 and extra % n_enzyme_atoms == 0:
        details["n_enzymes_found"] = extra // n_enzyme_atoms
    else:
        details["n_enzymes_found"] = None

    if n_atoms != expected:
        return RunVerdict(False, "atom_count_mismatch", details)

    capsid_block = coords[:n_capsid_atoms]
    if not capsid_block:
        return RunVerdict(False, "atom_count_mismatch", details)
    cc = tuple(sum(c[i] for c in capsid_block) / len(capsid_block) for i in range(3))
    details["capsid_centroid"] = [round(v, 3) for v in cc]

    max_copy_distance = 0.0
    for k in range(n_requested):
        block = coords[
            n_capsid_atoms + k * n_enzyme_atoms : n_capsid_atoms + (k + 1) * n_enzyme_atoms
        ]
        ec = tuple(sum(c[i] for c in block) / len(block) for i in range(3))
        max_copy_distance = max(max_copy_distance, _dist(ec, cc))
    details["max_enzyme_centroid_distance"] = round(max_copy_distance, 3)

    if n_requested > 0 and max_copy_distance > packing_radius:
        return RunVerdict(False, "enzymes_outside_capsid", details)

    return RunVerdict(True, "ok", details)


def evaluate_packmol_run(
    returncode: Optional[int],
    output_pdb,
    log_file,
    n_capsid_atoms: int,
    n_enzyme_atoms: int,
    n_requested: int,
    packing_radius: float,
    max_violation_threshold: float,
) -> RunVerdict:
    """
    Aplica el criterio de aceptación completo a una corrida de PACKMOL ya terminada.

    El orden importa: las señales explícitas de no convergencia (``_FORCED``, marcador
    de fallo) se comprueban ANTES del código de salida, porque hay versiones de PACKMOL
    que devuelven 0 aunque no converjan y dejan escrito el punto actual en ``<output>``.
    """
    output_pdb = Path(output_pdb)
    forced = Path(str(output_pdb) + "_FORCED")
    summary = read_packmol_log(log_file)
    details: Dict[str, Any] = {
        "returncode": returncode,
        "max_violation": summary.max_violation if summary else None,
        "forced_file_exists": forced.exists(),
    }

    if forced.exists():
        return RunVerdict(False, "forced_output", details)
    if summary is None:
        return RunVerdict(False, "log_unreadable", details)
    if summary.failure_marker:
        return RunVerdict(False, "ended_without_perfect_packing", details)
    if returncode != 0:
        return RunVerdict(False, "exit_code", details)
    if not output_pdb.exists():
        return RunVerdict(False, "no_output", details)
    if not summary.success_marker:
        return RunVerdict(False, "no_success_marker", details)
    if summary.max_violation is None:
        return RunVerdict(False, "no_violation_value", details)
    if summary.max_violation > max_violation_threshold:
        return RunVerdict(False, "violation_above_threshold", details)

    geometry = verify_packed_output(
        output_pdb, n_capsid_atoms, n_enzyme_atoms, n_requested, packing_radius
    )
    details.update(geometry.details)
    return RunVerdict(geometry.accepted, geometry.reason, details)


def write_packmol_input(
    path,
    *,
    capsid_file: str,
    enzyme_file: str,
    output_pdb,
    n_enzymes: int,
    seed: int,
    tolerance: float,
    packing_radius: float,
    exclusion_radius: float,
    comment: str = "",
) -> str:
    """Escribe el ``.inp`` de PACKMOL y devuelve su contenido."""
    lines = []
    if comment:
        lines.append(f"# {comment}")
    lines += [
        f"tolerance {tolerance}",
        f"output {output_pdb}",
        f"seed {seed}",
        "filetype pdb",
        "",
        # Cápside fija. `center` hace que PACKMOL la recentre en el origen aunque el
        # PDB de entrada no lo esté: la esfera de empaque y la cápside quedan siempre
        # alineadas (hallazgo PK-02).
        f"structure {capsid_file}",
        "  number 1",
        "  center",
        "  fixed 0. 0. 0. 0. 0. 0.",
        "end structure",
        "",
        # Enzimas dentro de la esfera de empaque = radio interno − margen de colisión.
        f"structure {enzyme_file}",
        f"  number {n_enzymes}",
        f"  inside sphere 0. 0. 0. {packing_radius}",
        f"  radius {exclusion_radius}",
        "end structure",
        "",
    ]
    content = "\n".join(lines)
    with open(path, "w") as f:
        f.write(content)
    return content


class ParallelPacker:
    """
    Motor de empaquetamiento paralelo que ejecuta múltiples réplicas simultáneamente.
    """

    def __init__(self, packmol_executable: str = "packmol", max_workers: Optional[int] = None):
        """
        Inicializa el motor de empaquetamiento paralelo.

        Args:
            packmol_executable: Ruta al ejecutable de Packmol
            max_workers: Número máximo de workers paralelos (None = min(núcleos, 7)).
                Nota: más procesos compitiendo por CPU alargan cada corrida y, con un
                timeout fijo, pueden convertir un "cabe" en "no cabe".
        """
        self.packmol_executable = packmol_executable
        self.max_workers = max_workers or min(multiprocessing.cpu_count(), 7)

    # Compatibilidad: API anterior de lectura de violación (ahora con la regex real).
    def _read_max_violation(self, log_file: str) -> Optional[float]:
        summary = read_packmol_log(log_file)
        return summary.max_violation if summary else None

    def _count_atomic_lines(self, pdb_file: str) -> int:
        return count_atomic_lines(pdb_file)

    @staticmethod
    def make_seeds(
        n_replicas: int, seed_base: Optional[int], use_random_seeds: bool
    ) -> Tuple[List[int], str]:
        """
        Semillas por réplica.

        - Modo fijo (por defecto): ``seed_base + i`` para i = 1..n. Si ``seed_base`` es
          None se usa ``DEFAULT_SEED_BASE``. Dos corridas idénticas dan las mismas semillas.
        - Modo aleatorio (``use_random_seeds=True``): semillas del generador del sistema,
          registradas en metadata para poder reproducir a posteriori.
        """
        if use_random_seeds:
            rng = random.SystemRandom()
            return [rng.randint(1, 1_000_000) for _ in range(n_replicas)], "random"
        base = DEFAULT_SEED_BASE if seed_base is None else int(seed_base)
        return [base + i for i in range(1, n_replicas + 1)], "fixed"

    def run_parallel_replicas(
        self,
        capsid_file: str,
        enzyme_file: str,
        n_replicas: int = 7,
        internal_radius: float = 90.0,
        tolerance: float = 2.0,
        exclusion_radius: float = 5.0,
        output_dir: str = "./output",
        seed_base: Optional[int] = None,
        use_random_seeds: bool = False,
        max_violation_threshold: float = 0.10,
        collision_margin: float = 2.0,
        timeout: float = 300.0,
        max_attempts_per_n: int = 2,
        max_consecutive_failures: int = 3,
    ) -> Dict[str, Any]:
        """
        Ejecuta múltiples réplicas de empaquetamiento en paralelo.

        Args:
            capsid_file: Archivo PDB de la cápside
            enzyme_file: Archivo PDB de la enzima
            n_replicas: Número de réplicas a ejecutar
            internal_radius: Radio interno de la cápside (Å)
            tolerance: Tolerancia para Packmol (Å)
            exclusion_radius: ``radius`` por átomo de la enzima en Packmol (Å)
            output_dir: Directorio de salida
            seed_base: Semilla base; cada réplica usa seed_base + i (None → 1234567)
            use_random_seeds: Si True ignora seed_base y usa semillas aleatorias
            max_violation_threshold: Umbral máximo de violación de distancia (Å)
            collision_margin: Se resta del radio interno para la esfera de empaque (Å)
            timeout: Tiempo máximo por corrida de Packmol (s); un timeout se registra
                como causa de rechazo, no como "no cabe" silencioso
            max_attempts_per_n: Intentos (semillas) por cada N antes de darlo por fallido
            max_consecutive_failures: Fallos consecutivos de N que detienen la búsqueda

        Returns:
            Diccionario con resultados consolidados
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        capsid_path = Path(capsid_file)
        enzyme_path = Path(enzyme_file)
        if not capsid_path.exists():
            raise FileNotFoundError(f"Archivo de cápside no encontrado: {capsid_file}")
        if not enzyme_path.exists():
            raise FileNotFoundError(f"Archivo de enzima no encontrado: {enzyme_file}")

        # Datos de referencia para contar enzimas colocadas (se calculan una sola vez).
        n_capsid_atoms = count_atomic_lines(capsid_path)
        n_enzyme_atoms = count_atomic_lines(enzyme_path)
        if n_capsid_atoms == 0:
            raise ValueError(f"La cápside no contiene átomos: {capsid_file}")
        if n_enzyme_atoms == 0:
            raise ValueError(f"La enzima no contiene átomos: {enzyme_file}")

        capsid_centroid = pdb_centroid(capsid_path)
        capsid_offset = _dist(capsid_centroid, (0.0, 0.0, 0.0))
        if capsid_offset > 1.0:
            print(
                f"Aviso: la cápside de entrada no está centrada (centroide a "
                f"{capsid_offset:.1f} Å del origen). PACKMOL la recentrará (`center`)."
            )

        packing_radius = float(internal_radius) - float(collision_margin)
        if packing_radius <= 0:
            raise ValueError(
                f"Radio de empaque no positivo: {internal_radius} - {collision_margin}"
            )

        seeds, seed_mode = self.make_seeds(n_replicas, seed_base, use_random_seeds)

        # Preparar argumentos para cada réplica
        replica_args = []
        for i in range(1, n_replicas + 1):
            replica_dir = output_path / f"replica_{i}"
            replica_dir.mkdir(parents=True, exist_ok=True)
            replica_args.append(
                {
                    "replica_id": i,
                    "capsid_file": str(capsid_path),
                    "enzyme_file": str(enzyme_path),
                    "output_dir": str(replica_dir),
                    "internal_radius": float(internal_radius),
                    "packing_radius": packing_radius,
                    "collision_margin": float(collision_margin),
                    "tolerance": float(tolerance),
                    "exclusion_radius": float(exclusion_radius),
                    "seed": seeds[i - 1],
                    "seed_mode": seed_mode,
                    "packmol_executable": self.packmol_executable,
                    "max_violation_threshold": float(max_violation_threshold),
                    "timeout": float(timeout),
                    "n_capsid_atoms": n_capsid_atoms,
                    "n_enzyme_atoms": n_enzyme_atoms,
                    "max_attempts_per_n": int(max_attempts_per_n),
                    "max_consecutive_failures": int(max_consecutive_failures),
                }
            )

        print(f"Iniciando {n_replicas} réplicas en paralelo con {self.max_workers} workers...")
        print(f"Semillas ({seed_mode}): {seeds}")

        results = []
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_replica = {
                executor.submit(self._run_single_replica, args): args["replica_id"]
                for args in replica_args
            }
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
                        {
                            "replica": replica_id,
                            "success": False,
                            "error": str(e),
                            "n_packed": 0,
                            "seed": seeds[replica_id - 1],
                        }
                    )

        results.sort(key=lambda r: r["replica"])

        run_config = {
            "capsid_file": str(capsid_path),
            "enzyme_file": str(enzyme_path),
            "n_capsid_atoms": n_capsid_atoms,
            "n_enzyme_atoms": n_enzyme_atoms,
            "capsid_input_centroid": [round(v, 3) for v in capsid_centroid],
            "internal_radius": float(internal_radius),
            "collision_margin": float(collision_margin),
            "packing_radius": packing_radius,
            "tolerance": float(tolerance),
            "exclusion_radius": float(exclusion_radius),
            "max_violation_threshold": float(max_violation_threshold),
            "timeout": float(timeout),
            "seed_mode": seed_mode,
            "seed_base": None if seed_mode == "random" else seeds[0] - 1,
            "seeds": seeds,
            "max_workers": self.max_workers,
            "packmol_executable": self.packmol_executable,
        }

        return self._consolidate_results(results, output_path, run_config)

    @staticmethod
    def _run_single_replica(args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta una réplica única de empaquetamiento (worker de multiprocessing).

        Búsqueda incremental N = 1, 2, 3, … con ``max_attempts_per_n`` semillas por N;
        se detiene tras ``max_consecutive_failures`` valores de N consecutivos rechazados
        o al alcanzar ``SEARCH_CEILING``.
        """
        replica_id = args["replica_id"]
        capsid_file = args["capsid_file"]
        enzyme_file = args["enzyme_file"]
        output_dir = Path(args["output_dir"])
        packing_radius = args["packing_radius"]
        tolerance = args["tolerance"]
        exclusion_radius = args["exclusion_radius"]
        seed = args["seed"]
        packmol_executable = args["packmol_executable"]
        max_violation_threshold = args["max_violation_threshold"]
        timeout = args["timeout"]
        n_capsid_atoms = args["n_capsid_atoms"]
        n_enzyme_atoms = args["n_enzyme_atoms"]
        max_attempts = args.get("max_attempts_per_n", 2)
        max_consecutive_failures = args.get("max_consecutive_failures", 3)

        best_n = 0
        best_file = None
        best_log = None
        best_violation = None
        attempts_log: List[Dict[str, Any]] = []

        def run_one(n_enzymes: int, attempt: int) -> RunVerdict:
            test_seed = seed + attempt * 1000
            input_file = output_dir / f"packmol_input_{n_enzymes}_attempt{attempt}.inp"
            output_pdb = output_dir / f"packed_{n_enzymes}_attempt{attempt}.pdb"
            log_file = output_dir / f"packmol_log_{n_enzymes}_attempt{attempt}.txt"

            # Nunca evaluar restos de una corrida anterior.
            for stale in (output_pdb, Path(str(output_pdb) + "_FORCED")):
                if stale.exists():
                    stale.unlink()

            write_packmol_input(
                input_file,
                capsid_file=capsid_file,
                enzyme_file=enzyme_file,
                output_pdb=output_pdb,
                n_enzymes=n_enzymes,
                seed=test_seed,
                tolerance=tolerance,
                packing_radius=packing_radius,
                exclusion_radius=exclusion_radius,
                comment=f"Réplica {replica_id} - {n_enzymes} enzimas (intento {attempt + 1})",
            )

            t0 = time.monotonic()
            try:
                with open(input_file, "r") as stdin, open(log_file, "w") as stdout:
                    completed = subprocess.run(
                        [packmol_executable],
                        stdin=stdin,
                        stdout=stdout,
                        stderr=subprocess.STDOUT,
                        timeout=timeout,
                        check=False,
                    )
                verdict = evaluate_packmol_run(
                    completed.returncode,
                    output_pdb,
                    log_file,
                    n_capsid_atoms,
                    n_enzyme_atoms,
                    n_enzymes,
                    packing_radius,
                    max_violation_threshold,
                )
            except subprocess.TimeoutExpired:
                verdict = RunVerdict(False, "timeout", {"timeout": timeout})
            except OSError as e:
                verdict = RunVerdict(False, "exception", {"error": str(e)})

            verdict.details["elapsed_s"] = round(time.monotonic() - t0, 3)
            attempts_log.append(
                {
                    "n": n_enzymes,
                    "attempt": attempt,
                    "seed": test_seed,
                    "accepted": verdict.accepted,
                    "reason": verdict.reason,
                    "input_file": str(input_file),
                    "output_file": str(output_pdb),
                    "log_file": str(log_file),
                    **verdict.details,
                }
            )
            return verdict

        def test_packing(n_enzymes: int) -> bool:
            nonlocal best_n, best_file, best_log, best_violation
            for attempt in range(max_attempts):
                verdict = run_one(n_enzymes, attempt)
                if verdict.accepted:
                    if n_enzymes > best_n:
                        best_n = n_enzymes
                        best_file = attempts_log[-1]["output_file"]
                        best_log = attempts_log[-1]["log_file"]
                        best_violation = verdict.details.get("max_violation")
                    print(
                        f"    Réplica {replica_id}: ✓ {n_enzymes} enzimas OK "
                        f"(violación: {verdict.details.get('max_violation')})"
                    )
                    return True
                print(
                    f"    Réplica {replica_id}: intento {attempt + 1}/{max_attempts} con "
                    f"{n_enzymes} enzimas rechazado ({verdict.reason})"
                )
            print(f"    Réplica {replica_id}: ✗ {n_enzymes} enzimas NO cabe")
            return False

        print(f"    Réplica {replica_id}: Búsqueda incremental iniciando...")
        n = 1
        consecutive_failures = 0
        ceiling_reached = False
        while True:
            if n > SEARCH_CEILING:
                ceiling_reached = True
                print(f"    Réplica {replica_id}: techo de búsqueda ({SEARCH_CEILING}) alcanzado.")
                break
            if test_packing(n):
                consecutive_failures = 0
            else:
                consecutive_failures += 1
                if consecutive_failures >= max_consecutive_failures:
                    print(
                        f"    Réplica {replica_id}: {max_consecutive_failures} fallos consecutivos."
                    )
                    break
            n += 1

        print(f"    Réplica {replica_id}: Búsqueda completada. Máximo: {best_n} enzimas")

        reasons: Dict[str, int] = {}
        for a in attempts_log:
            if not a["accepted"]:
                reasons[a["reason"]] = reasons.get(a["reason"], 0) + 1

        metadata = {
            "replica": replica_id,
            "success": best_n > 0,
            "n_packed": best_n,
            "seed": seed,
            "seed_mode": args.get("seed_mode"),
            "output_file": best_file,
            "log_file": best_log,
            "max_violation": best_violation,
            "internal_radius": args["internal_radius"],
            "collision_margin": args["collision_margin"],
            "packing_radius": packing_radius,
            "tolerance": tolerance,
            "exclusion_radius": exclusion_radius,
            "timeout": timeout,
            "n_capsid_atoms": n_capsid_atoms,
            "n_enzyme_atoms": n_enzyme_atoms,
            "search_ceiling_reached": ceiling_reached,
            "n_attempts": len(attempts_log),
            "rejection_reasons": reasons,
            "attempts": attempts_log,
        }

        with open(output_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

        return metadata

    def _consolidate_results(
        self,
        results: List[Dict],
        output_path: Path,
        run_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Consolida resultados de todas las réplicas.

        ``stdev`` es ``None`` (no definida) con menos de dos réplicas exitosas; nunca se
        reporta un 0 que no se midió.
        """
        run_config = run_config or {}
        summary_dir = output_path / "summary"
        summary_dir.mkdir(parents=True, exist_ok=True)

        successful = [r for r in results if r.get("success", False)]
        warnings: List[str] = []
        if any(r.get("search_ceiling_reached") for r in results):
            warnings.append(
                f"Alguna réplica alcanzó el techo de búsqueda ({SEARCH_CEILING}): el máximo "
                "reportado es una constante del código, no una medición."
            )

        rejection_reasons: Dict[str, int] = {}
        for r in results:
            for reason, count in (r.get("rejection_reasons") or {}).items():
                rejection_reasons[reason] = rejection_reasons.get(reason, 0) + count

        if not successful:
            stats: Dict[str, Any] = {
                "success": False,
                "error": "Ninguna réplica fue exitosa: PACKMOL no colocó ninguna enzima "
                "que superara el criterio de aceptación",
                "n_replicas_total": len(results),
                "n_replicas_success": 0,
                "best": 0,
                "rejection_reasons": rejection_reasons,
                "warnings": warnings,
                "run_config": run_config,
                "all_results": results,
            }
            with open(summary_dir / "statistics.json", "w") as f:
                json.dump(stats, f, indent=2)
            self._write_report(summary_dir / "report.txt", stats, results)
            print("\nEmpaquetamiento paralelo: ninguna réplica aceptada.")
            return stats

        n_packed_list = [r["n_packed"] for r in successful]
        best_result = max(successful, key=lambda x: x["n_packed"])

        best_file = None
        if best_result.get("output_file") and Path(best_result["output_file"]).exists():
            best_file = summary_dir / "best_packing.pdb"
            shutil.copy2(best_result["output_file"], best_file)
        if best_result.get("log_file") and Path(best_result["log_file"]).exists():
            shutil.copy2(best_result["log_file"], summary_dir / "best_packing_packmol.log")

        best = max(n_packed_list)
        stats = {
            "success": True,
            "n_replicas_total": len(results),
            "n_replicas_success": len(successful),
            "best": best,
            "worst": min(n_packed_list),
            "mean": statistics.mean(n_packed_list),
            "median": statistics.median(n_packed_list),
            "stdev": statistics.stdev(n_packed_list) if len(n_packed_list) > 1 else None,
            "n_replicas_at_best": sum(1 for v in n_packed_list if v == best),
            "best_replica": best_result["replica"],
            "best_seed": best_result.get("seed"),
            "best_file": str(best_file) if best_file else None,
            "rejection_reasons": rejection_reasons,
            "warnings": warnings,
            "run_config": run_config,
            "all_results": results,
        }

        with open(summary_dir / "statistics.json", "w") as f:
            json.dump(stats, f, indent=2)
        self._write_report(summary_dir / "report.txt", stats, results)

        print("\nEmpaquetamiento paralelo completado:")
        print(f"  - Mejor resultado: {stats['best']} enzimas")
        print(f"  - Archivo guardado en: {stats['best_file']}")
        for w in warnings:
            print(f"  - AVISO: {w}")

        return stats

    @staticmethod
    def _write_report(report_file: Path, stats: Dict[str, Any], results: List[Dict]) -> None:
        cfg = stats.get("run_config", {})
        with open(report_file, "w") as f:
            f.write("=" * 60 + "\n")
            f.write("REPORTE DE EMPAQUETAMIENTO PARALELO\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Réplicas totales: {stats['n_replicas_total']}\n")
            f.write(f"Réplicas exitosas: {stats['n_replicas_success']}\n")
            if stats.get("success"):
                f.write(
                    f"Mejor resultado: {stats['best']} enzimas "
                    f"(Réplica {stats['best_replica']}, semilla {stats.get('best_seed')})\n"
                )
                f.write(
                    f"Réplicas que alcanzan el máximo: {stats['n_replicas_at_best']}"
                    f"/{stats['n_replicas_success']}\n"
                )
                f.write(f"Promedio: {stats['mean']:.2f} enzimas\n")
                f.write(f"Mediana: {stats['median']:.2f} enzimas\n")
                stdev = stats.get("stdev")
                f.write(
                    "Desviación estándar: "
                    + (f"{stdev:.2f}" if stdev is not None else "no definida (< 2 réplicas)")
                    + "\n"
                )
            else:
                f.write(f"RESULTADO: FALLO — {stats.get('error')}\n")
            f.write("\n")

            f.write("Parámetros efectivos:\n")
            for key in (
                "internal_radius",
                "collision_margin",
                "packing_radius",
                "tolerance",
                "exclusion_radius",
                "max_violation_threshold",
                "timeout",
                "seed_mode",
                "seed_base",
                "max_workers",
                "n_capsid_atoms",
                "n_enzyme_atoms",
            ):
                if key in cfg:
                    f.write(f"  {key}: {cfg[key]}\n")
            f.write("\n")

            for w in stats.get("warnings", []):
                f.write(f"AVISO: {w}\n")
            if stats.get("rejection_reasons"):
                f.write("Causas de rechazo (todas las corridas):\n")
                for reason, count in sorted(stats["rejection_reasons"].items()):
                    f.write(f"  {reason}: {count}\n")
            f.write("\n")

            f.write("Resultados por réplica:\n")
            for r in results:
                status = "OK" if r.get("success") else "FALLO"
                f.write(
                    f"  Réplica {r['replica']}: {r.get('n_packed', 0)} enzimas [{status}] "
                    f"semilla={r.get('seed')}"
                )
                if r.get("error"):
                    f.write(f" error={r['error']}")
                f.write("\n")


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
    print(f"  Mejor: {results.get('best')} enzimas")
    if results.get("success"):
        print(f"  Promedio: {results['mean']:.2f}")
        print(f"  Desviación: {results['stdev']}")
