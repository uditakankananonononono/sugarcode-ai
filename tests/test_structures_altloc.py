from sugarcode.bio.structures import parse_pdb_atoms

PDB = (
    "ATOM      1  N   ALA A   1      11.104   6.134  -6.504  1.00  0.00           N\n"
    "ATOM      2  CB AALA A   1      11.639   6.071  -5.147  0.50  0.00           C\n"
    "ATOM      3  CB BALA A   1      12.639   6.071  -5.147  0.50  0.00           C\n"
)


def test_altloc_keeps_first_only():
    a = parse_pdb_atoms(PDB)
    assert len(a) == 2 and a[1]["xyz"][0] == 11.639
