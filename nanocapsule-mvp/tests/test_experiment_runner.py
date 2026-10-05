"""
Tests del orquestador (``ExperimentRunner``) y del centrado sin PyMOL.

Cazan: config no leída (P-05/P-12/P-19: semilla, margen, timeout), el fallback
silencioso del radio y el centrado que fallaba y seguía (PK-02), y la pérdida de
``TER`` al centrar (P-22, primera mitad).
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from packmol_double import install_double
from pdb_fixtures import centroid, count_ter, make_capsid, make_enzyme

from src.core import capsid as capsid_module
from src.core.capsid import Capsid
from src.core.config import ConfigManager
from src.core.experiment_manager import ExperimentManager
from src.core.experiment_runner import ExperimentRunner
from src.core.pdb_geometry import center_pdb
from src.packing.parallel_packer import ParallelPacker


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #
@pytest.fixture
def inputs(tmp_path):
    """Cápside SIN centrar (como BMV_IJS9 en Input/) y enzima descentrada."""
    capsid = make_capsid(
        tmp_path / "Input" / "capside.pdb", n_atoms=12000, radius=95.0, center=(207.9, 207.9, 207.9)
    )
    enzyme = make_enzyme(
        tmp_path / "Input" / "enzima.pdb", n_atoms=50, radius=8.0, center=(210.2, 192.4, 206.3)
    )
    return capsid, enzyme


def write_config(tmp_path, executable="packmol", **overrides):
    cfg = {
        "packing": {
            "internal_radius_default": 90.0,
            "collision_margin": 3.5,
            "exclusion_radius": 4.0,
            "tolerance": 2.0,
            "max_violation_threshold": 0.2,
        },
        "engines": {
            "packmol": {
                "executable": executable,
                "timeout": 7,
                "seed_base": 42,
                "use_random_seeds": False,
                "max_workers": 1,
            }
        },
        "experiments": {"n_replicas": 2},
    }
    for dotted, value in overrides.items():
        node = cfg
        keys = dotted.split(".")
        for k in keys[:-1]:
            node = node.setdefault(k, {})
        node[keys[-1]] = value
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(cfg))
    return ConfigManager(config_path=str(path))


def fake_radius(value=91.0):
    def _calc(self, save_to_file=True):
        self.internal_radius = value
        self.radius_source = "calculated"
        return value

    return _calc


# --------------------------------------------------------------------------- #
# Centrado en Python puro
# --------------------------------------------------------------------------- #
def test_center_pdb_moves_centroid_to_origin_and_keeps_ter(tmp_path, inputs):
    capsid, _ = inputs
    assert count_ter(capsid) == 4
    out, original = center_pdb(capsid, tmp_path / "centered.pdb")
    assert original == pytest.approx((207.9, 207.9, 207.9), abs=1e-3)
    assert centroid(out) == pytest.approx((0.0, 0.0, 0.0), abs=1e-3)
    assert count_ter(out) == 4  # PyMOL fundía las cadenas; esto las conserva


def test_capsid_center_structure_does_not_need_pymol(tmp_path, inputs, monkeypatch):
    monkeypatch.setattr(capsid_module, "PYMOL_AVAILABLE", False)
    capsid, _ = inputs
    config = write_config(tmp_path)
    out = Capsid(capsid, config=config).center_structure(str(tmp_path / "c.pdb"))
    assert centroid(out) == pytest.approx((0.0, 0.0, 0.0), abs=1e-3)


# --------------------------------------------------------------------------- #
# El runner lee la config y la pasa al motor (P-05 / P-12 / P-19)
# --------------------------------------------------------------------------- #
def test_runner_passes_config_values_to_packer(tmp_path, inputs, monkeypatch):
    capsid, enzyme = inputs
    config = write_config(tmp_path, executable="/opt/bin/packmol-x")
    monkeypatch.setattr(Capsid, "calculate_internal_radius", fake_radius(91.0))

    captured = {}

    def fake_run(self, **kwargs):
        captured.update(kwargs)
        return {
            "success": True,
            "best": 1,
            "n_replicas_total": 2,
            "n_replicas_success": 2,
            "mean": 1.0,
            "stdev": 0.0,
            "all_results": [],
        }

    monkeypatch.setattr(ParallelPacker, "run_parallel_replicas", fake_run)

    runner = ExperimentRunner(output_base_dir=str(tmp_path / "Output"), config=config)
    assert runner.parallel_packer.packmol_executable == "/opt/bin/packmol-x"
    assert runner.parallel_packer.max_workers == 1

    results = runner.run_maximum_packing(capsid, enzyme, "CAP", "ENZ")

    assert captured["seed_base"] == 42
    assert captured["use_random_seeds"] is False
    assert captured["timeout"] == 7.0
    assert captured["collision_margin"] == 3.5
    assert captured["exclusion_radius"] == 4.0
    assert captured["max_violation_threshold"] == 0.2
    assert captured["tolerance"] == 2.0
    assert captured["internal_radius"] == 91.0
    assert captured["n_replicas"] == 2  # experiments.n_replicas de la config
    assert results["radius_source"] == "calculated"

    # Los archivos que llegan al motor están centrados y viven en el experimento, no en Input/.
    exp_dir = Path(results["experiment_dir"])
    assert Path(captured["capsid_file"]).parent == exp_dir
    assert Path(captured["enzyme_file"]).parent == exp_dir
    assert centroid(captured["capsid_file"]) == pytest.approx((0, 0, 0), abs=1e-3)
    assert centroid(captured["enzyme_file"]) == pytest.approx((0, 0, 0), abs=1e-3)
    assert not list((tmp_path / "Input").glob("*_centered.pdb"))


def test_runner_honours_random_seeds_from_config(tmp_path, inputs, monkeypatch):
    capsid, enzyme = inputs
    config = write_config(tmp_path, **{"engines.packmol.use_random_seeds": True})
    monkeypatch.setattr(Capsid, "calculate_internal_radius", fake_radius())
    captured = {}
    monkeypatch.setattr(
        ParallelPacker,
        "run_parallel_replicas",
        lambda self, **kw: captured.update(kw) or {"success": False, "error": "x"},
    )
    ExperimentRunner(str(tmp_path / "Output"), config=config).run_maximum_packing(
        capsid, enzyme, n_replicas=3
    )
    assert captured["use_random_seeds"] is True
    assert captured["n_replicas"] == 3


# --------------------------------------------------------------------------- #
# Política "que falle, no que avise" (PK-02 / P-11)
# --------------------------------------------------------------------------- #
def test_runner_refuses_to_run_on_default_radius_without_pymol(tmp_path, inputs, monkeypatch):
    monkeypatch.setattr(capsid_module, "PYMOL_AVAILABLE", False)
    capsid, enzyme = inputs
    config = write_config(tmp_path)
    runner = ExperimentRunner(str(tmp_path / "Output"), config=config)
    called = []
    monkeypatch.setattr(
        ParallelPacker, "run_parallel_replicas", lambda self, **kw: called.append(kw)
    )
    with pytest.raises(RuntimeError, match="radio interno"):
        runner.run_maximum_packing(capsid, enzyme)
    assert called == []  # antes seguía con 90 Å y la cápside sin centrar


def test_runner_aborts_when_centering_fails(tmp_path, inputs, monkeypatch):
    capsid, enzyme = inputs
    config = write_config(tmp_path)
    monkeypatch.setattr(Capsid, "calculate_internal_radius", fake_radius())

    def boom(self, output_path=None):
        raise RuntimeError("centrado imposible")

    monkeypatch.setattr(Capsid, "center_structure", boom)
    called = []
    monkeypatch.setattr(
        ParallelPacker, "run_parallel_replicas", lambda self, **kw: called.append(kw)
    )
    with pytest.raises(RuntimeError, match="centrado imposible"):
        ExperimentRunner(str(tmp_path / "Output"), config=config).run_maximum_packing(
            capsid, enzyme
        )
    assert called == []


def test_runner_with_explicit_radius_runs_without_pymol_end_to_end(tmp_path, inputs, monkeypatch):
    """Sin PyMOL, con radio explícito, cápside sin centrar y el doble de PACKMOL: el
    experimento completo produce 3 enzimas contadas dentro de la cápside."""
    monkeypatch.setattr(capsid_module, "PYMOL_AVAILABLE", False)
    capsid, enzyme = inputs
    exe = install_double(tmp_path / "bin", capacity=3)
    config = write_config(tmp_path, executable=exe, **{"engines.packmol.timeout": 30})

    runner = ExperimentRunner(str(tmp_path / "Output"), config=config)
    results = runner.run_maximum_packing(capsid, enzyme, "CAP", "ENZ", internal_radius=90.0)

    assert results["success"] is True
    assert results["best"] == 3
    assert results["radius_source"] == "user"
    assert results["run_config"]["seeds"] == [43, 44]
    assert results["run_config"]["packing_radius"] == 86.5  # 90 − 3.5 de la config
    assert results["run_config"]["timeout"] == 30.0

    exp_dir = Path(results["experiment_dir"])
    centered = exp_dir / "capside_centered.pdb"
    assert centered.exists() and count_ter(centered) == 4
    assert (exp_dir / "summary" / "best_packing.pdb").exists()
    assert (exp_dir / "summary" / "report.txt").exists()


def test_experiment_manager_creates_requested_replica_dirs(tmp_path):
    config = write_config(tmp_path)
    manager = ExperimentManager(config=config, output_base_dir=str(tmp_path / "Output"))
    assert manager.n_replicas == 2  # de la config, no 7 hardcodeado
    exp_dir = manager.setup_experiment("CAP", "ENZ", n_replicas=3)
    assert sorted(p.name for p in exp_dir.glob("replica_*")) == [
        "replica_1",
        "replica_2",
        "replica_3",
    ]
