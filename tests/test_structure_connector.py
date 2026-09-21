import json
import pytest

from sugarcode.bio import structures
from sugarcode.bio.structures import parse_pdb, fetch_pdb, fetch_alphafold
from sugarcode.modules.alpha_fold_ui import analyze_real_structure

PDB_TEXT = (
    "ATOM      1  CA  ALA A   1      10.000  10.000  10.000  1.00 75.00           C  \n"
    "ATOM      2  CA  GLY A   2      11.500  10.000  10.000  1.00 80.00           C  \n"
    "ATOM      3  CA  SER A   3      12.000  11.500  10.000  1.00 45.00           C  \n"
    "ATOM      4  CA  VAL B   1      30.000  30.000  30.000  1.00 90.00           C  \n"
    "END\n"
)
ENTRY_JSON = json.dumps({"exptl": [{"method": "X-RAY DIFFRACTION"}],
                         "rcsb_entry_info": {"resolution_combined": [2.2]},
                         "struct": {"title": "Test structure"}}).encode()
AF_LISTING = json.dumps([{"pdbUrl": "https://example/AF-X.pdb", "latestVersion": 4,
                          "paeDocUrl": "https://example/pae"}]).encode()


@pytest.fixture(autouse=True)
def fake_transport(monkeypatch, tmp_path):
    monkeypatch.setattr(structures, "CACHE_DIR", tmp_path / "structures")

    def fake_get(url, offline=False, retries=3):
        if offline:
            raise structures.StructureError("offline mode: no cache")
        if url.endswith(".pdb") and "files.rcsb" in url:
            return PDB_TEXT.encode()
        if "rcsb.org" in url:
            return ENTRY_JSON
        if "alphafold.ebi.ac.uk" in url and url.count("/") <= 5:
            return AF_LISTING
        if url.endswith("AF-X.pdb"):
            return PDB_TEXT.encode()
        raise AssertionError(f"unexpected url {url}")

    monkeypatch.setattr(structures, "_get", fake_get)


def test_parse_pdb_ca_trace():
    p = parse_pdb(PDB_TEXT)
    assert p["n_residues"] == 4
    assert p["chains"] == ["A", "B"]
    assert p["residues"][2]["bfactor"] == 45.0
    assert p["residues"][0]["ca"] == (10.0, 10.0, 10.0)


def test_parse_pdb_rejects_garbage():
    with pytest.raises(structures.StructureError):
        parse_pdb("HEADER nothing here\n")


def test_fetch_pdb_metadata_and_coords():
    s = fetch_pdb("1tup")
    assert s["method"] == "X-RAY DIFFRACTION"
    assert s["resolution_A"] == 2.2
    assert s["n_residues"] == 4


def test_fetch_alphafold_plddt_stats():
    s = fetch_alphafold("P04637")
    assert s["model_version"] == 4
    assert s["mean_plddt"] == 72.5  # mean of 75, 80, 45, 90
    assert s["fraction_low_confidence"] == 0.25  # 45 < 50


def test_analyze_real_structure_routes_by_identifier():
    af = analyze_real_structure("P04637")
    assert af["source"] == "AlphaFold DB (live)"
    assert af["confidence_kind"] == "AlphaFold pLDDT"
    assert af["confidence_stats"]["mean"] == 72.5
    exp = analyze_real_structure("1tup")
    assert exp["source"] == "RCSB PDB (live)"
    assert exp["confidence_kind"] == "crystallographic B-factor"
    assert exp["resolution_A"] == 2.2


def test_offline_raises_without_cache():
    with pytest.raises(structures.StructureError):
        fetch_pdb("1tup", offline=True)
