from sugarcode.modules.alpha_fold_ui import predict_structure, write_pdb
from sugarcode.modules.docking_studio import dock, virtual_screen, parse_smiles_features
from sugarcode.modules.evofold_4d import anm_modes, transition_trace, perturbation_effect
from sugarcode.modules.mutdock import mutation_effect, resistance_scan
from sugarcode.modules.protein_painter import design_protein

HELIX = "AEAAAKEAAAKA" * 3
POCKET = "GSCSTNDEHK"


def test_structure_pipeline():
    r = predict_structure(HELIX)
    assert r["composition"]["helix"] > 0
    assert r["pdb"].startswith("ATOM")
    assert len(r["pae"]) == len(HELIX)
    assert 0 < r["mean_plddt"] <= 95


def test_smiles_features():
    f = parse_smiles_features("CC(=O)Oc1ccccc1C(=O)O")  # aspirin
    assert f["atom_counts"]["O"] >= 4
    assert f["lipinski_ro5"]["mw_ok"]


def test_dock_and_screen():
    d = dock(POCKET, "CCO")
    assert "binding_dg_kcal_mol" in d and d["key_residues"]
    s = virtual_screen(POCKET, ["CCO", "c1ccccc1", "CC(=O)O", "O"])
    assert s["best"]["smiles"]


def test_anm_modes_and_trace():
    r = predict_structure(HELIX + "GGGG" + HELIX)
    import re
    coords = [[float(l[30:38]), float(l[38:46]), float(l[46:54])]
              for l in r["pdb"].splitlines() if l.startswith("ATOM")]
    modes = anm_modes(coords, n_modes=3)
    assert modes["modes"] and modes["fluctuation_profile"]
    tr = transition_trace(coords, steps=10)
    assert tr["max_rmsd"] > 0 and len(tr["frames"]) == 10
    pe = perturbation_effect(coords, site=len(coords) // 2)
    assert pe["most_affected_residues"]


def test_mutdock_scan():
    r = mutation_effect(POCKET, "CCO", 3, "W", drug_name="testdrug")
    assert r["mutation"] == "S4W"            # POCKET[3] is residue 4 (1-based)
    assert mutation_effect(POCKET, "CCO", 3, "S")["ddg_kcal_mol"] == 0.0  # no-change
    assert r["resistance_risk"] in ("low", "moderate", "high")
    scan = resistance_scan("GSCSTN", {"d1": "CCO", "d2": "c1ccccc1"})
    assert len(scan["per_drug"]) == 2


def test_protein_painter_enzyme():
    r = design_protein("catalyze a redox reaction", length=60, seed=3)
    assert r["fold_class"] == "enzyme"
    assert len(r["best"]["sequence"]) == 60
    assert r["best"]["active_site_residues"]
    assert r["verification"]["method"]
