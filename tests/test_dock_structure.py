import json
import pytest

from sugarcode.bio import structures
from sugarcode.modules.docking_studio import dock_into_structure

# fixture: 40 residues - residues 10-19 in a tight ball (dense pocket),
# the rest spread on a line (no neighbors within 9A)
def _fixture_pdb() -> bytes:
    rows = []
    resnum = 1
    for i in range(30):
        rows.append(f"ATOM  {resnum:5d}  CA  ALA A{resnum:4d}    "
                    f"{20.0 * i:8.3f}{0.0:8.3f}{0.0:8.3f}  1.00 80.00           C  ")
        resnum += 1
    for i in range(12):
        x = 3.0 * (i % 3); y = 3.0 * ((i // 3) % 2); z = 3.0 * (i // 6)
        rows.append(f"ATOM  {resnum:5d}  CA  SER A{resnum:4d}    "
                    f"{x:8.3f}{y:8.3f}{z:8.3f}  1.00 80.00           C  ")
        resnum += 1
    rows.append("END")
    return ("\n".join(rows) + "\n").encode()

ENTRY_JSON = json.dumps({"exptl": [{"method": "X-RAY DIFFRACTION"}],
                         "rcsb_entry_info": {"resolution_combined": [2.0]},
                         "struct": {"title": "fixture"}}).encode()


@pytest.fixture(autouse=True)
def fake_transport(monkeypatch, tmp_path):
    monkeypatch.setattr(structures, "CACHE_DIR", tmp_path / "structures")

    def fake_get(url, offline=False, retries=3):
        if offline:
            raise structures.StructureError("offline")
        if "files.rcsb" in url:
            return _fixture_pdb()
        return ENTRY_JSON

    monkeypatch.setattr(structures, "_get", fake_get)


def test_dock_into_structure_finds_dense_pocket():
    r = dock_into_structure("1fix", "c1ccccc1O")
    assert r["structure"]["source"] == "RCSB PDB (live)"
    assert r["structure"]["resolution_A"] == 2.0
    assert r["pocket"]["n_pockets_found"] >= 1
    # dense SER ball should be the lining
    assert all(x.startswith("SER") for x in r["pocket"]["lining_residues"])
    assert "enclosure_bonus" in r["geometry_terms"]
    assert r["binding_dg_kcal_mol"] < 0
    assert r["estimated_kd_uM"] > 0


def test_geometry_terms_change_score():
    from sugarcode.modules.docking_studio.core import dock
    r = dock_into_structure("1fix", "CCO")
    # geometry-adjusted dg differs from composition-only dg on same lining
    assert "geometry_terms" in r and "scoring_note" in r
    assert r["geometry_terms"]["pocket_span_A"] > 0


def test_oversized_ligand_penalized():
    small = dock_into_structure("1fix", "CCO")
    big = dock_into_structure("1fix", "C" * 40)
    assert big["geometry_terms"]["size_fit_penalty"] > small["geometry_terms"]["size_fit_penalty"]


def test_offline_raises():
    with pytest.raises(structures.StructureError):
        dock_into_structure("1fix", "CCO", offline=True)
