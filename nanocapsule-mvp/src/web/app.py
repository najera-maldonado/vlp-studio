#!/usr/bin/env python3
"""
Servidor web Flask para nanocapsule MVP.

Adaptador de entrada HTTP: traduce peticiones web a llamadas de la capa de
servicios (src.services.packing_service). No contiene lógica de negocio.
"""

import datetime
import sys
from pathlib import Path

from flask import Flask, jsonify, render_template, request

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core import paths
from src.services import packing_service as svc

app = Flask(__name__, template_folder="templates", static_folder="static")


# --------------------------------------------------------------------------- #
# Páginas
# --------------------------------------------------------------------------- #
@app.route("/")
def studio():
    """Interfaz combinada (brutalista + datos reales + NGL)."""
    return render_template("studio.html")


@app.route("/classic")
def classic():
    """Interfaz original NGL. DEPRECATED (VLP-05, 2026-09-17): se conserva funcional
    pero ya NO se enlaza desde el Studio; puede retirarse en el futuro. Ver README."""
    return render_template("index.html")


@app.route("/api/health")
def health():
    """Chequeo de salud: 200 si la app vive, más qué motores/deps están presentes.

    Lo usan el HEALTHCHECK de Docker/compose y el pane 'salud' del tablero. Barato:
    solo `which` de binarios e import diferido de deps, sin lanzar subprocesos.
    """
    import importlib.util
    import shutil

    engines = {
        name: bool(shutil.which(name))
        for name in ("packmol", "pymol", "obabel", "vina", "hole", "idock")
    }
    deps = {
        name: importlib.util.find_spec(name) is not None
        for name in ("rdkit", "numpy", "yaml", "flask")
    }
    return jsonify({"status": "ok", "engines": engines, "deps": deps})


# --------------------------------------------------------------------------- #
# Biblioteca
# --------------------------------------------------------------------------- #
@app.route("/api/library/capsides")
def get_capsides():
    try:
        return jsonify(svc.list_library()["capsides"])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/library/enzymes")
def get_enzymes():
    try:
        return jsonify(svc.list_library()["enzymes"])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/library/combinations")
def get_combinations():
    try:
        return jsonify(svc.list_library())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/library/detail")
def get_library_detail():
    try:
        return jsonify(svc.library_detail())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/pore/config")
def get_pore_config():
    try:
        return jsonify(svc.pore_config())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/pore/profile", methods=["POST"])
def get_pore_profile():
    data = request.get_json(force=True) or {}
    try:
        return jsonify(svc.pore_profile(data.get("capsid"), data.get("axis")))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/pore/channels")
def get_pore_channels():
    try:
        return jsonify(svc.pore_channels())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/pore/channel")
def get_pore_channel():
    try:
        content = svc.pore_channel_content(request.args.get("id"))
        return app.response_class(
            content, mimetype="text/plain", headers={"Access-Control-Allow-Origin": "*"}
        )
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/pore/structures")
def get_pore_structures():
    try:
        return jsonify(svc.hole_structures())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/pore/run_hole", methods=["POST"])
def post_run_hole():
    data = request.get_json(force=True) or {}
    try:
        return jsonify(svc.run_hole(data.get("structure")))
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/pore/screen", methods=["POST"])
def post_pore_screen():
    data = request.get_json(force=True) or {}
    try:
        return jsonify(svc.screen_mutants(data.get("structure"), data.get("substrate_radius")))
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/pore/mutant", methods=["POST"])
def post_pore_mutant():
    data = request.get_json(force=True) or {}
    try:
        return jsonify(svc.evaluate_mutant(data.get("structure"), data.get("mutations")))
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/pore/dock", methods=["POST"])
def post_pore_dock():
    data = request.get_json(force=True) or {}
    try:
        return jsonify(svc.dock_correlate(data.get("structure"), data.get("smiles")))
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/pore/section", methods=["POST"])
def get_pore_section():
    data = request.get_json(force=True) or {}
    try:
        return jsonify(
            {"smiles": data.get("smiles"), "radius": svc.substrate_section(data.get("smiles"))}
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/deimmuno/data")
def get_deimmuno_data():
    try:
        return jsonify(svc.deimmuno_data())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/md/examples")
def get_md_examples():
    try:
        return jsonify(svc.md_examples())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/md/box")
def get_md_box():
    try:
        return jsonify(svc.md_box(request.args.get("capsid")))
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/md/prepare", methods=["POST"])
def post_md_prepare():
    data = request.get_json(force=True) or {}
    try:
        return jsonify(
            svc.md_prepare(
                data.get("capsid"),
                int(data.get("n_substrate", 40)),
                data.get("smiles"),
            )
        )
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --------------------------------------------------------------------------- #
# Radio interno
# --------------------------------------------------------------------------- #
@app.route("/api/capsid/radius", methods=["POST"])
def calculate_radius():
    try:
        data = request.get_json() or {}
        capsid = data.get("capsid")
        if not capsid:
            return jsonify({"error": "Nombre de cápside requerido"}), 400

        radius = svc.calculate_radius(capsid, save=True)
        return jsonify(
            {
                "status": "success",
                "capsid": capsid,
                "internal_radius": radius,
                "message": f"Radio interno calculado: {radius:.1f} Å",
            }
        )
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --------------------------------------------------------------------------- #
# Experimento real
# --------------------------------------------------------------------------- #
@app.route("/api/experiment/run", methods=["POST"])
def run_experiment():
    try:
        data = request.get_json() or {}
        capsid = data.get("capsid")
        enzyme = data.get("enzyme")
        n_replicas = data.get("n_replicas")
        run_packing = data.get("run_packing", False)

        if not capsid or not enzyme:
            return jsonify({"error": "Cápside y enzima requeridas"}), 400

        if not run_packing:
            # Modo configuración: no ejecuta Packmol, solo confirma parámetros.
            return jsonify(
                {
                    "status": "configured",
                    "capsid": capsid,
                    "enzyme": enzyme,
                    "n_replicas": n_replicas or svc._config.get("experiments.n_replicas", 10),
                    "message": "Experimento configurado. Envía run_packing=true para ejecutar.",
                }
            )

        results = svc.run_experiment(capsid, enzyme, n_replicas=n_replicas)
        return jsonify(
            {
                "status": "completed",
                "success": results.get("success", False),
                "best_result": results.get("best", 0),
                "mean": results.get("mean", 0.0),
                "stdev": results.get("stdev", 0.0),
                "median": results.get("median", 0.0),
                "worst": results.get("worst", 0),
                "n_replicas_success": results.get("n_replicas_success", 0),
                "n_replicas_total": results.get("n_replicas_total", n_replicas),
                "internal_radius": results.get("internal_radius", 0.0),
                "experiment_dir": results.get("experiment_dir", ""),
                "best_file": results.get("best_file", ""),
                "all_results": results.get("all_results", []),
                "message": f"Mejor resultado: {results.get('best', 0)} enzimas",
            }
        )
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


# --------------------------------------------------------------------------- #
# Info y archivos de estructuras
# --------------------------------------------------------------------------- #
@app.route("/api/structure/<structure_type>/<structure_name>")
def get_structure_info(structure_type, structure_name):
    try:
        info = svc.structure_info(structure_type, structure_name)
        info["path"] = f"/api/file/{structure_type}/{structure_name}"
        return jsonify(info)
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/file/<structure_type>/<structure_name>")
def serve_structure_file(structure_type, structure_name):
    try:
        content = svc.read_structure_pdb(structure_type, structure_name)
        return app.response_class(
            content,
            mimetype="text/plain",
            headers={
                "Content-Disposition": f'inline; filename="{structure_name}.pdb"',
                "Access-Control-Allow-Origin": "*",
            },
        )
    except FileNotFoundError:
        return "Estructura no encontrada", 404
    except Exception as e:
        return f"Error: {str(e)}", 500


@app.route("/api/result/pdb")
def serve_result_pdb():
    """
    Sirve un PDB resultante (preview guardado o mejor réplica de un experimento).

    Valida que la ruta esté dentro de Output/ para no exponer el sistema de archivos.
    """
    raw = request.args.get("path", "")
    if not raw:
        return "Falta 'path'", 400
    try:
        target = Path(raw).resolve()
        if not str(target).startswith(str(paths.OUTPUT_DIR.resolve())):
            return "Ruta no permitida", 403
        if not target.exists():
            return "Archivo no encontrado", 404
        return app.response_class(
            target.read_text(),
            mimetype="text/plain",
            headers={
                "Content-Disposition": f'inline; filename="{target.name}"',
                "Access-Control-Allow-Origin": "*",
            },
        )
    except Exception as e:
        return f"Error: {str(e)}", 500


# --------------------------------------------------------------------------- #
# Preview rápido
# --------------------------------------------------------------------------- #
@app.route("/api/preview/enzymes", methods=["POST"])
def preview_enzymes():
    try:
        data = request.get_json() or {}
        result = svc.preview(
            capsid_name=data.get("capsid"),
            enzyme_name=data.get("enzyme"),
            n_enzymes=data.get("n_enzymes", 10),
            radius=data.get("radius", 50.0),
            save_file=data.get("save_file", False),
        )
        return app.response_class(
            result["content"],
            mimetype="text/plain",
            headers={
                "Content-Disposition": f'inline; filename="{result["filename"]}"',
                "Access-Control-Allow-Origin": "*",
                "X-Saved-Path": result["saved_path"] or "not-saved",
            },
        )
    except (TypeError, ValueError) as e:
        return jsonify({"error": f"Parámetros inválidos: {e}"}), 400
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/preview/substrate", methods=["POST"])
def preview_substrate():
    try:
        data = request.get_json() or {}
        result = svc.preview_substrate(
            capsid_name=data.get("capsid"),
            n=int(data.get("n", 60)),
            smiles=data.get("smiles"),
            save_file=data.get("save_file", False),
        )
        return app.response_class(
            result["content"],
            mimetype="text/plain",
            headers={"Access-Control-Allow-Origin": "*"},
        )
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --------------------------------------------------------------------------- #
# Gestión de archivos generados
# --------------------------------------------------------------------------- #
@app.route("/api/files/generated")
def list_generated_files():
    try:
        output_dir = paths.GENERATED_DIR
        if not output_dir.exists():
            return jsonify({"files": [], "count": 0, "total_size_mb": 0})

        files = []
        for file_path in output_dir.glob("*.pdb"):
            stat = file_path.stat()
            files.append(
                {
                    "name": file_path.name,
                    "size": stat.st_size,
                    "size_mb": round(stat.st_size / 1024 / 1024, 2),
                    "modified": datetime.datetime.fromtimestamp(stat.st_mtime).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    "path": str(file_path),
                }
            )
        files.sort(key=lambda x: x["modified"], reverse=True)
        return jsonify(
            {
                "files": files,
                "count": len(files),
                "total_size_mb": round(sum(f["size"] for f in files) / 1024 / 1024, 2),
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/files/cleanup", methods=["POST"])
def cleanup_generated_files():
    try:
        data = request.get_json() or {}
        days_old = data.get("days_old", 7)
        output_dir = paths.GENERATED_DIR
        if not output_dir.exists():
            return jsonify({"message": "No hay archivos para limpiar", "removed": 0})

        cutoff = datetime.datetime.now() - datetime.timedelta(days=days_old)
        removed = []
        for file_path in output_dir.glob("*.pdb"):
            if datetime.datetime.fromtimestamp(file_path.stat().st_mtime) < cutoff:
                removed.append(file_path.name)
                file_path.unlink()
        return jsonify(
            {"message": "Limpieza completada", "removed": len(removed), "removed_files": removed}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/download/single/<filename>")
def download_single_file(filename):
    try:
        file_path = paths.GENERATED_DIR / filename
        if not file_path.exists():
            return jsonify({"error": "Archivo no encontrado"}), 404
        return app.response_class(
            file_path.read_bytes(),
            mimetype="application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Access-Control-Allow-Origin": "*",
            },
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/download/experiment-zip", methods=["POST"])
def download_experiment_zip():
    """Empaqueta en ZIP los PDBs generados de una combinación + estructuras de entrada."""
    import io
    import zipfile

    try:
        data = request.get_json() or {}
        capsid = data.get("capsid")
        enzyme = data.get("enzyme")
        if not capsid or not enzyme:
            return jsonify({"error": "Cápside y enzima requeridas"}), 400

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            if paths.GENERATED_DIR.exists():
                for fp in paths.GENERATED_DIR.glob(f"{capsid}_*enzimas_{enzyme}_*.pdb"):
                    zf.write(fp, f"generated_pdbs/{fp.name}")
            for stype, sname, label in (
                ("capside", capsid, "capside"),
                ("enzima", enzyme, "enzima"),
            ):
                try:
                    p = svc.structure_path(stype, sname)
                    if p.exists():
                        zf.write(p, f"inputs/{sname}_{label}.pdb")
                except Exception:
                    pass
            zf.writestr(
                "README.txt",
                f"Nanocapsule MVP\nCapsid: {capsid}\nEnzyme: {enzyme}\n"
                f"Fecha: {datetime.datetime.now():%Y-%m-%d %H:%M:%S}\n",
            )

        buffer.seek(0)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        return app.response_class(
            buffer.getvalue(),
            mimetype="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{capsid}_{enzyme}_{ts}.zip"',
                "Access-Control-Allow-Origin": "*",
            },
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    import os

    port = svc._config.get("web.port", 5000)
    host = svc._config.get("web.host", "0.0.0.0")
    # debug: respeta config (web.debug, por defecto false) y el override FLASK_DEBUG.
    env_debug = os.environ.get("FLASK_DEBUG")
    debug = (env_debug == "1") if env_debug is not None else svc._config.get("web.debug", False)
    print("Iniciando servidor web VLP Studio...")
    print(f"Studio (nuevo):  http://localhost:{port}/")
    print(f"Clásico (NGL):   http://localhost:{port}/classic  (deprecated)")
    print(f"Salud:           http://localhost:{port}/api/health")
    app.run(debug=debug, host=host, port=port)
