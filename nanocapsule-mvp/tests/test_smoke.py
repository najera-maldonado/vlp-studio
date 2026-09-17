"""
Tests de humo de VLP Studio — la RED de seguridad para VLP-03 (partir el monolito).

Filosofía: rápidos y de forma, no de valor científico. Verifican que la app arranca,
que las rutas están cableadas y que las funciones devuelven la ESTRUCTURA esperada.
NO ejercen los motores lentos (HOLE, PyMOL, Vina, Packmol) — esos tienen su propio
camino y tardan; aquí solo lo rápido y determinista.

Si al refactorizar una ruta deja de responder o cambia de forma, estos tests lo cazan.
"""
from src.services import packing_service as svc


# --------------------------------------------------------------------------- #
# La app arranca y las páginas se sirven
# --------------------------------------------------------------------------- #
def test_health_ok(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    d = r.get_json()
    assert d["status"] == "ok"
    assert isinstance(d["engines"], dict) and isinstance(d["deps"], dict)
    # rdkit es dependencia dura del Studio; si falta, algo se rompió en la infra.
    assert d["deps"]["rdkit"] is True


def test_studio_page(client):
    assert client.get("/").status_code == 200


def test_classic_page(client):
    # /classic todavía se sirve (VLP-05 lo retirará). Hoy debe responder.
    assert client.get("/classic").status_code == 200


# --------------------------------------------------------------------------- #
# Biblioteca (lee Input/ real)
# --------------------------------------------------------------------------- #
def test_library_capsides(client):
    r = client.get("/api/library/capsides")
    assert r.status_code == 200
    caps = r.get_json()
    assert isinstance(caps, list) and len(caps) > 0  # el repo trae cápsides reales


def test_library_detail_shape(client):
    r = client.get("/api/library/detail")
    assert r.status_code == 200
    d = r.get_json()
    assert "capsides" in d and "enzymes" in d
    assert len(d["capsides"]) > 0
    c0 = d["capsides"][0]
    for k in ("name", "pdb", "atoms", "chains"):
        assert k in c0


# --------------------------------------------------------------------------- #
# Pac-Pore — solo las rutas rápidas (config/forma), NO run_hole/screen/dock
# --------------------------------------------------------------------------- #
def test_pore_config(client):
    r = client.get("/api/pore/config")
    assert r.status_code == 200
    d = r.get_json()
    assert "axes" in d and "substrates" in d
    assert len(d["substrates"]) > 0


def test_pore_channels_shape(client):
    r = client.get("/api/pore/channels")
    assert r.status_code == 200
    assert isinstance(r.get_json()["channels"], list)


def test_pore_structures_shape(client):
    r = client.get("/api/pore/structures")
    assert r.status_code == 200
    assert isinstance(r.get_json()["structures"], list)


def test_pore_section_valid_smiles(client):
    # Etanol: SMILES válido y trivial → radio de sección positivo (ejercita RDKit).
    r = client.post("/api/pore/section", json={"smiles": "CCO"})
    assert r.status_code == 200
    assert r.get_json()["radius"] > 0


def test_pore_section_invalid_smiles(client):
    r = client.post("/api/pore/section", json={"smiles": "no_es_smiles_valido_%%%"})
    assert r.status_code == 400  # camino de error controlado


def test_pore_profile_illustrative(client):
    caps = client.get("/api/library/capsides").get_json()
    r = client.post("/api/pore/profile", json={"capsid": caps[0], "axis": "3-fold"})
    assert r.status_code == 200
    d = r.get_json()
    assert len(d["positions"]) == len(d["radius"])
    assert d["illustrative"] is True


# --------------------------------------------------------------------------- #
# De-inmunización y Análisis MD (ilustrativos, rápidos)
# --------------------------------------------------------------------------- #
def test_deimmuno_data(client):
    r = client.get("/api/deimmuno/data")
    assert r.status_code == 200
    assert len(r.get_json()["mutants"]) > 0


def test_md_examples(client):
    r = client.get("/api/md/examples")
    assert r.status_code == 200
    ex = r.get_json()["examples"]
    assert len(ex) > 0 and len(ex[0]["points"]) > 0


def test_md_box(client):
    caps = client.get("/api/library/capsides").get_json()
    r = client.get("/api/md/box", query_string={"capsid": caps[0]})
    assert r.status_code == 200
    assert r.get_json()["box_half"] > 0


# --------------------------------------------------------------------------- #
# Preview rápido (colocación aleatoria, sin Packmol)
# --------------------------------------------------------------------------- #
def test_preview_enzymes_returns_pdb(client):
    caps = client.get("/api/library/capsides").get_json()
    enz = client.get("/api/library/enzymes").get_json()
    r = client.post("/api/preview/enzymes",
                    json={"capsid": caps[0], "enzyme": enz[0], "n_enzymes": 2})
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    assert "MODEL" in body and "END" in body  # es un PDB con modelos


# --------------------------------------------------------------------------- #
# Nivel de servicio (funciones puras, sin HTTP)
# --------------------------------------------------------------------------- #
def test_substrate_section_pure():
    assert svc.substrate_section("CCO") > 0


def test_md_prepare_generates_inputs():
    caps = svc.list_library()["capsides"]
    d = svc.md_prepare(caps[0], n_substrate=5)
    assert "packmol_input" in d and "leap_input" in d
    assert "structure" in d["packmol_input"]  # bloque Packmol bien formado
