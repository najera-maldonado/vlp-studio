"""
Tests del motor de packing (``src/packing/parallel_packer.py``) con un doble de PACKMOL.

Cada test de esta suite caza uno de los defectos confirmados por las dos auditorías
independientes (AUDITORIA_PACKING, ramas wwph45 y vdvq69) y falla con el código
anterior:

- P-01/PK-01: la regex buscaba una frase que PACKMOL no escribe → se parsea la real.
- P-02/P-04: el fallback "≥ 10 000 líneas" aprobaba una cápside sin enzimas → se cuentan
  las copias colocadas.
- P-03: una corrida sin convergencia (``_FORCED``, exit 0) se aceptaba → se rechaza.
- PK-02: cápside sin centrar → enzimas en el vacío → ``center`` + verificación geométrica.
- P-05/P-12/P-19: semilla, margen y timeout → parámetros explícitos y reproducibles.

No se necesita PACKMOL: ``tests/packmol_double.py`` emite las cadenas reales que están
en ``tests/fixtures/packmol_logs`` (logs reales de PACKMOL 20.14.3 y 21.0.1).
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest
from packmol_double import install_double
from pdb_fixtures import count_atoms, make_capsid, make_enzyme

from src.packing import parallel_packer as pp
from src.packing.parallel_packer import ParallelPacker

FIXTURES = Path(__file__).parent / "fixtures" / "packmol_logs"
REAL_LOGS = sorted(FIXTURES.glob("*.log"))

N_CAPSID = 12000
N_ENZYME = 50


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #
@pytest.fixture
def structures(tmp_path):
    capsid = make_capsid(tmp_path / "in" / "capside.pdb", n_atoms=N_CAPSID, radius=95.0)
    enzyme = make_enzyme(tmp_path / "in" / "enzima.pdb", n_atoms=N_ENZYME, radius=8.0)
    return capsid, enzyme


def run_engine(tmp_path, structures, exe, **kwargs):
    capsid, enzyme = structures
    params = dict(
        n_replicas=2,
        internal_radius=90.0,
        output_dir=str(tmp_path / "out"),
        timeout=30.0,
    )
    params.update(kwargs)
    packer = ParallelPacker(packmol_executable=exe, max_workers=2)
    return packer.run_parallel_replicas(capsid, enzyme, **params)


def all_reasons(result):
    return result.get("rejection_reasons", {})


# --------------------------------------------------------------------------- #
# 1. Parseo del log: las cadenas reales de PACKMOL (P-01 / PK-01)
# --------------------------------------------------------------------------- #
def test_real_logs_exist_as_fixtures():
    assert len(REAL_LOGS) == 2, "faltan los dos logs reales de PACKMOL en tests/fixtures"


@pytest.mark.parametrize("log", REAL_LOGS, ids=lambda p: p.name)
def test_real_packmol_log_parses_as_success_with_zero_violation(log):
    summary = pp.parse_packmol_log(log.read_text())
    assert summary.success_marker is True
    assert summary.failure_marker is False
    assert summary.n_violation_values >= 1
    # Las dos corridas reales terminaron con violación 0.0; la regex vieja devolvía None.
    assert summary.max_violation == 0.0


def test_violation_value_is_the_last_one_in_the_log():
    text = next(p for p in REAL_LOGS if "sustratinaitor" in p.name).read_text()
    assert "3.970194" in text  # valores intermedios de iteración
    assert pp.parse_packmol_log(text).max_violation == 0.0  # el del bloque final


def test_legacy_phrase_never_appears_in_real_logs():
    # Documenta el defecto: la frase que buscaba el código no la escribe PACKMOL.
    for log in REAL_LOGS:
        assert "Maximum distance violation" not in log.read_text()


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("3.970194", 3.970194),
        (".12571E-01", 0.012571),
        ("7.7660690978852759E-003", 0.0077660690978852759),
        ("0.0000000000000000", 0.0),
        ("1.5D+00", 1.5),
    ],
)
def test_fortran_number_formats_are_parsed(raw, expected):
    summary = pp.parse_packmol_log(f"  Maximum violation of target distance:    {raw}\n")
    assert summary.max_violation == pytest.approx(expected)


def test_log_without_success_marker_is_rejected(tmp_path):
    out = tmp_path / "packed.pdb"
    out.write_text("END\n")
    log = tmp_path / "log.txt"
    log.write_text("  Maximum violation of target distance:     0.000000\n")
    verdict = pp.evaluate_packmol_run(0, out, log, 10, 5, 1, 50.0, 0.1)
    assert verdict.accepted is False
    assert verdict.reason == "no_success_marker"


def test_ended_without_perfect_packing_is_rejected_even_with_exit_zero(tmp_path):
    out = tmp_path / "packed.pdb"
    out.write_text("END\n")
    log = tmp_path / "log.txt"
    log.write_text(
        "  Maximum violation of target distance:     7.430001\n"
        "                         ENDED WITHOUT PERFECT PACKING: \n"
    )
    verdict = pp.evaluate_packmol_run(0, out, log, 10, 5, 1, 50.0, 0.1)
    assert verdict.accepted is False
    assert verdict.reason == "ended_without_perfect_packing"


def test_forced_file_is_rejected_even_if_log_says_success(tmp_path):
    out = tmp_path / "packed.pdb"
    out.write_text("END\n")
    Path(str(out) + "_FORCED").write_text("END\n")
    log = tmp_path / "log.txt"
    log.write_text("Success!\n  Maximum violation of target distance:   0.000000\n")
    verdict = pp.evaluate_packmol_run(0, out, log, 10, 5, 1, 50.0, 0.1)
    assert verdict.reason == "forced_output"


# --------------------------------------------------------------------------- #
# 2. Conteo de enzimas y geometría (P-02 / P-04 / PK-02)
# --------------------------------------------------------------------------- #
def test_verify_counts_enzyme_copies(tmp_path):
    capsid = make_capsid(tmp_path / "c.pdb", n_atoms=300, radius=50.0)
    enzyme = make_enzyme(tmp_path / "e.pdb", n_atoms=10, radius=3.0)
    out = tmp_path / "packed.pdb"
    with open(out, "w") as f:
        f.writelines(ln for ln in open(capsid) if ln.startswith("ATOM"))
        for _ in range(2):
            f.writelines(ln for ln in open(enzyme) if ln.startswith("ATOM"))

    bad = pp.verify_packed_output(out, 300, 10, n_requested=3, packing_radius=48.0)
    assert bad.accepted is False
    assert bad.reason == "atom_count_mismatch"
    assert bad.details["n_enzymes_found"] == 2

    good = pp.verify_packed_output(out, 300, 10, n_requested=2, packing_radius=48.0)
    assert good.accepted is True
    # Las dos copias están donde la enzima original (centroide ≈ origen, no exacto).
    assert good.details["max_enzyme_centroid_distance"] < 0.1


def test_verify_rejects_enzymes_outside_the_capsid(tmp_path):
    # Cápside sin centrar (200, 200, 200) y enzimas alrededor del origen: el caso PK-02.
    capsid = make_capsid(tmp_path / "c.pdb", n_atoms=300, radius=50.0, center=(200, 200, 200))
    enzyme = make_enzyme(tmp_path / "e.pdb", n_atoms=10, radius=3.0)
    out = tmp_path / "packed.pdb"
    with open(out, "w") as f:
        f.writelines(ln for ln in open(capsid) if ln.startswith("ATOM"))
        f.writelines(ln for ln in open(enzyme) if ln.startswith("ATOM"))
    verdict = pp.verify_packed_output(out, 300, 10, n_requested=1, packing_radius=48.0)
    assert verdict.accepted is False
    assert verdict.reason == "enzymes_outside_capsid"
    assert verdict.details["max_enzyme_centroid_distance"] > 300


def test_engine_rejects_output_with_capsid_but_zero_enzymes(tmp_path, structures):
    """El peor caso de la auditoría: PACKMOL dice Success!, el PDB tiene > 10 000 líneas
    (la cápside) y cero enzimas. El código viejo reportaba 100 enzimas y σ = 0."""
    exe = install_double(tmp_path / "bin", mode="capsid_only")
    result = run_engine(tmp_path, structures, exe)

    assert result["success"] is False
    assert result["best"] == 0
    assert result["n_replicas_success"] == 0
    assert set(all_reasons(result)) == {"atom_count_mismatch"}
    assert not (tmp_path / "out" / "summary" / "best_packing.pdb").exists()

    meta = json.loads((tmp_path / "out" / "replica_1" / "metadata.json").read_text())
    assert meta["success"] is False
    assert all(a["n_enzymes_found"] == 0 for a in meta["attempts"])


def test_engine_counts_placed_enzymes_and_stops_at_capacity(tmp_path, structures):
    exe = install_double(tmp_path / "bin", capacity=4)
    result = run_engine(tmp_path, structures, exe)

    assert result["success"] is True
    assert result["best"] == 4  # no 100: el techo del bucle ya no es el resultado
    assert [r["n_packed"] for r in result["all_results"]] == [4, 4]
    assert result["n_replicas_at_best"] == 2
    assert result["warnings"] == []

    best = Path(result["best_file"])
    assert best.exists()
    assert count_atoms(best) == N_CAPSID + 4 * N_ENZYME

    meta = json.loads((tmp_path / "out" / "replica_1" / "metadata.json").read_text())
    tried = sorted({a["n"] for a in meta["attempts"]})
    assert tried == [1, 2, 3, 4, 5, 6, 7]  # 4 aceptados + 3 fallos consecutivos
    assert meta["search_ceiling_reached"] is False
    rejected = {a["reason"] for a in meta["attempts"] if not a["accepted"]}
    assert rejected == {"forced_output"}


def test_forced_output_with_exit_zero_and_partial_pdb_is_rejected(tmp_path, structures):
    """Versiones de PACKMOL que devuelven 0 sin converger y dejan escrito <output>:
    el código viejo las aceptaba (P-03)."""
    exe = install_double(tmp_path / "bin", capacity=2, fail_exit_code=0, write_partial_output=True)
    result = run_engine(tmp_path, structures, exe, n_replicas=1)
    assert result["success"] is True
    assert result["best"] == 2
    assert "forced_output" in all_reasons(result)


def test_violation_above_threshold_is_rejected(tmp_path, structures):
    exe = install_double(tmp_path / "bin", final_violation=0.5)
    result = run_engine(tmp_path, structures, exe, n_replicas=1, max_violation_threshold=0.10)
    assert result["success"] is False
    assert set(all_reasons(result)) == {"violation_above_threshold"}


def test_violation_below_threshold_is_accepted(tmp_path, structures):
    exe = install_double(tmp_path / "bin", final_violation=0.05, capacity=1)
    result = run_engine(tmp_path, structures, exe, n_replicas=1, max_violation_threshold=0.10)
    assert result["success"] is True
    assert result["all_results"][0]["max_violation"] == pytest.approx(0.05)


# --------------------------------------------------------------------------- #
# 3. El .inp: `center`, margen de colisión y semillas (PK-02 / P-12 / P-05)
# --------------------------------------------------------------------------- #
def test_generated_inp_is_frozen(tmp_path, structures):
    capsid, enzyme = structures
    exe = install_double(tmp_path / "bin", capacity=1)
    run_engine(
        tmp_path,
        structures,
        exe,
        n_replicas=1,
        internal_radius=90.0,
        collision_margin=3.5,
        exclusion_radius=5.0,
        tolerance=2.0,
    )
    inp = (tmp_path / "out" / "replica_1" / "packmol_input_1_attempt0.inp").read_text()
    output_pdb = tmp_path / "out" / "replica_1" / "packed_1_attempt0.pdb"
    expected = [
        "# Réplica 1 - 1 enzimas (intento 1)",
        "tolerance 2.0",
        f"output {output_pdb}",
        "seed 1234568",
        "filetype pdb",
        "",
        f"structure {capsid}",
        "  number 1",
        "  center",
        "  fixed 0. 0. 0. 0. 0. 0.",
        "end structure",
        "",
        f"structure {enzyme}",
        "  number 1",
        "  inside sphere 0. 0. 0. 86.5",  # 90 − 3.5: el margen viene del parámetro
        "  radius 5.0",
        "end structure",
        "",
    ]
    assert inp.split("\n") == expected

    retry = (tmp_path / "out" / "replica_1" / "packmol_input_2_attempt1.inp").read_text()
    assert "seed 1235568" in retry  # semilla + 1000 × intento


def test_uncentered_capsid_is_recentered_by_center_keyword(tmp_path):
    capsid = make_capsid(
        tmp_path / "in" / "capside.pdb", n_atoms=N_CAPSID, radius=95.0, center=(200, 200, 200)
    )
    enzyme = make_enzyme(tmp_path / "in" / "enzima.pdb", n_atoms=N_ENZYME, radius=8.0)
    exe = install_double(tmp_path / "bin", capacity=3)
    result = run_engine(tmp_path, (capsid, enzyme), exe, n_replicas=1)
    assert result["success"] is True
    assert result["best"] == 3
    assert result["run_config"]["capsid_input_centroid"] == pytest.approx([200, 200, 200], abs=0.01)


def test_enzymes_packed_in_the_void_are_rejected(tmp_path):
    """Si PACKMOL (o quien sea) no recentra la cápside, las enzimas quedan a 350 Å de
    ella. El código viejo lo aprobaba; ahora se rechaza por geometría."""
    capsid = make_capsid(
        tmp_path / "in" / "capside.pdb", n_atoms=N_CAPSID, radius=95.0, center=(200, 200, 200)
    )
    enzyme = make_enzyme(tmp_path / "in" / "enzima.pdb", n_atoms=N_ENZYME, radius=8.0)
    exe = install_double(tmp_path / "bin", capacity=3, ignore_center=True)
    result = run_engine(tmp_path, (capsid, enzyme), exe, n_replicas=1)
    assert result["success"] is False
    assert set(all_reasons(result)) == {"enzymes_outside_capsid"}


def test_seeds_are_fixed_and_reproducible_by_default(tmp_path, structures):
    exe = install_double(tmp_path / "bin", capacity=1)
    first = run_engine(tmp_path, structures, exe, output_dir=str(tmp_path / "run1"))
    second = run_engine(tmp_path, structures, exe, output_dir=str(tmp_path / "run2"))

    assert first["run_config"]["seed_mode"] == "fixed"
    assert first["run_config"]["seeds"] == [1234568, 1234569]
    assert first["run_config"]["seeds"] == second["run_config"]["seeds"]
    assert [r["seed"] for r in first["all_results"]] == [1234568, 1234569]

    inp = (tmp_path / "run1" / "replica_2" / "packmol_input_1_attempt0.inp").read_text()
    assert "seed 1234569" in inp


def test_seed_base_parameter_is_honoured(tmp_path, structures):
    exe = install_double(tmp_path / "bin", capacity=1)
    result = run_engine(tmp_path, structures, exe, seed_base=42)
    assert result["run_config"]["seeds"] == [43, 44]
    assert result["run_config"]["seed_base"] == 42


def test_random_seeds_are_recorded(tmp_path, structures):
    exe = install_double(tmp_path / "bin", capacity=1)
    result = run_engine(tmp_path, structures, exe, use_random_seeds=True)
    assert result["run_config"]["seed_mode"] == "random"
    seeds = result["run_config"]["seeds"]
    assert len(seeds) == 2 and all(isinstance(s, int) for s in seeds)
    report = (tmp_path / "out" / "summary" / "report.txt").read_text()
    for s in seeds:
        assert f"semilla={s}" in report


# --------------------------------------------------------------------------- #
# 4. Timeout como causa registrada, no como "no cabe" (P-19 / PK-04)
# --------------------------------------------------------------------------- #
def test_timeout_is_recorded_as_rejection_reason(tmp_path, structures):
    exe = install_double(tmp_path / "bin", sleep=1.5)
    result = run_engine(
        tmp_path,
        structures,
        exe,
        n_replicas=1,
        timeout=0.4,
        max_attempts_per_n=1,
        max_consecutive_failures=1,
    )
    assert result["success"] is False
    assert all_reasons(result) == {"timeout": 1}
    meta = json.loads((tmp_path / "out" / "replica_1" / "metadata.json").read_text())
    assert meta["timeout"] == 0.4
    assert meta["attempts"][0]["reason"] == "timeout"


def test_crash_is_recorded_as_exit_code(tmp_path, structures):
    exe = install_double(tmp_path / "bin", crash=True)
    result = run_engine(
        tmp_path, structures, exe, n_replicas=1, max_attempts_per_n=1, max_consecutive_failures=1
    )
    assert result["success"] is False
    assert all_reasons(result) == {"exit_code": 1}


# --------------------------------------------------------------------------- #
# 5. Consolidación y techo de búsqueda (P-06 / P-07)
# --------------------------------------------------------------------------- #
def test_consolidation_with_one_success_has_undefined_stdev(tmp_path):
    packer = ParallelPacker(max_workers=1)
    results = [
        {"replica": 1, "success": True, "n_packed": 3, "seed": 1, "output_file": None},
        {"replica": 2, "success": False, "n_packed": 0, "seed": 2, "error": "boom"},
    ]
    stats = packer._consolidate_results(results, tmp_path)
    assert stats["success"] is True
    assert stats["n_replicas_total"] == 2
    assert stats["n_replicas_success"] == 1
    assert stats["best"] == 3
    assert stats["stdev"] is None  # no definida, no 0
    assert "no definida" in (tmp_path / "summary" / "report.txt").read_text()


def test_search_ceiling_is_flagged_not_reported_as_capacity(tmp_path, structures, monkeypatch):
    capsid, enzyme = structures
    exe = install_double(tmp_path / "bin")  # cabe todo: la búsqueda llegaría al techo
    monkeypatch.setattr(pp, "SEARCH_CEILING", 3)
    out = tmp_path / "replica_1"
    out.mkdir()
    meta = ParallelPacker._run_single_replica(
        {
            "replica_id": 1,
            "capsid_file": capsid,
            "enzyme_file": enzyme,
            "output_dir": str(out),
            "internal_radius": 90.0,
            "packing_radius": 88.0,
            "collision_margin": 2.0,
            "tolerance": 2.0,
            "exclusion_radius": 5.0,
            "seed": 7,
            "seed_mode": "fixed",
            "packmol_executable": exe,
            "max_violation_threshold": 0.1,
            "timeout": 30.0,
            "n_capsid_atoms": N_CAPSID,
            "n_enzyme_atoms": N_ENZYME,
        }
    )
    assert meta["n_packed"] == 3
    assert meta["search_ceiling_reached"] is True
    stats = ParallelPacker(max_workers=1)._consolidate_results([meta], tmp_path)
    assert any("techo" in w for w in stats["warnings"])


# --------------------------------------------------------------------------- #
# 6. PACKMOL real (solo en la máquina del autor; se salta si no está instalado)
# --------------------------------------------------------------------------- #
@pytest.mark.engine
@pytest.mark.skipif(shutil.which("packmol") is None, reason="PACKMOL no instalado")
def test_real_packmol_log_vocabulary_matches_parser(tmp_path):
    """Confirma contra la versión instalada que el parser ve `Success!` y la línea de
    violación. Caso trivial: 2 copias de una molécula pequeña en una esfera."""
    enzyme = make_enzyme(tmp_path / "e.pdb", n_atoms=20, radius=3.0)
    inp = tmp_path / "run.inp"
    out = tmp_path / "out.pdb"
    inp.write_text(
        f"tolerance 2.0\noutput {out}\nseed 1234567\nfiletype pdb\n\n"
        f"structure {enzyme}\n  number 2\n  inside sphere 0. 0. 0. 30.\nend structure\n"
    )
    with open(inp) as stdin:
        completed = subprocess.run(
            ["packmol"], stdin=stdin, capture_output=True, text=True, timeout=120
        )
    summary = pp.parse_packmol_log(completed.stdout)
    assert summary.success_marker is True
    assert summary.max_violation is not None
    assert completed.returncode == 0
