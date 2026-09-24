import pytest
from sugarcode.modules.docking_studio import (dock, virtual_screen, validate_smiles,
                                              dock_vina_grid, dock_vina_structure,
                                              vina_pair_terms, complex_pdb)

ASP = "CC(=O)Oc1ccccc1C(=O)O"


@pytest.mark.parametrize("bad", ["", "   ", "xyz!!", "xyz", "CC(C", "C1CC", "CQC", "[Na+"])
def test_dock_rejects_bad_smiles(bad):
    with pytest.raises(ValueError):
        dock("HDESLLFVYW", bad)


@pytest.mark.parametrize("good", [ASP, "CCO", "c1ccccc1", "C[C@H](N)C(=O)O", "[Na+].[Cl-]",
                                  "ClC(Br)F", "C%10CCCC%10", "C1CC1C2CC2"])
def test_valid_smiles_pass(good):
    validate_smiles(good)


def test_screen_skips_garbage():
    r = virtual_screen("HDESLLFVYW", [ASP, "xyz!!", ""])
    assert r["screened"] == 1


def test_dock_labels_one_based_by_default():
    d = dock("HDE", "CCN")
    assert d["key_residues"][0] == "H1"
    assert dock("HDE", "CCN", pocket_start=99)["key_residues"][0] == "H100"


def test_complex_pdb_from_grid():
    pocket = [{"element": "C", "xyz": (float(i), 0.0, 5.0), "resnum": 10 + i,
               "resname": "ALA", "chain": "B"} for i in range(8)]
    r = dock_vina_grid(pocket, ASP, n_steps=2)
    pdb = r["complex_pdb"]
    atoms = [l for l in pdb.splitlines() if l.startswith("ATOM")]
    het = [l for l in pdb.splitlines() if l.startswith("HETATM")]
    assert len(atoms) == 8 and len(het) == len(r["ligand_pose"]) == r["heavy_atoms"]
    assert atoms[0][17:20] == "ALA" and atoms[0][21] == "B" and int(atoms[0][22:26]) == 10
    x, y, z = (float(het[0][30:38]), float(het[0][38:46]), float(het[0][46:54]))
    assert [x, y, z] == pytest.approx(r["ligand_pose"][0]["xyz"], abs=1e-3)
    assert "VINA-FORM SCORE" in pdb and pdb.rstrip().endswith("END")
    assert all(len(l) <= 80 for l in pdb.splitlines())
