import os, pytest
from sugarcode.modules.docking_studio import vina_real

def _have():
    try:
        vina_real._require(); return True
    except vina_real.VinaUnavailable:
        return False

@pytest.mark.skipif(not _have(), reason="vina/openbabel not installed")
def test_real_vina_docks_benzene_in_toy_pocket(tmp_path):
    # minimal receptor: a ring of alanine-like atoms around the origin
    lines = []
    import math
    for i in range(12):
        a = 2 * math.pi * i / 12
        x, y = 4.5 * math.cos(a), 4.5 * math.sin(a)
        for j, z in enumerate((-1.5, 1.5)):
            n = i * 2 + j + 1
            lines.append(f"ATOM  {n:5d}  CB  ALA A{n:4d}    {x:8.3f}{y:8.3f}{z:8.3f}  1.00  0.00           C")
    rec = tmp_path / "r.pdb"; rec.write_text("\n".join(lines) + "\nEND\n")
    r = vina_real.prepare_receptor(str(rec), str(tmp_path / "r.pdbqt"))
    l = vina_real.prepare_ligand_from_smiles("c1ccccc1", str(tmp_path / "l.pdbqt"))
    out = vina_real.dock(r, l, center=(0, 0, 0), box_size=(14, 14, 14), exhaustiveness=2, n_poses=3)
    assert out["best_affinity_kcal_mol"] < 0
    assert "MODEL" in out["poses_pdbqt"]

def test_invalid_smiles_rejected(tmp_path):
    if not _have():
        pytest.skip("vina not installed")
    with pytest.raises(ValueError):
        vina_real.prepare_ligand_from_smiles("not_a_smiles(", str(tmp_path / "x.pdbqt"))
