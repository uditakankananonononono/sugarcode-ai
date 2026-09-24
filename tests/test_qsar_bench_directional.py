from sugarcode.modules.qsar_bench.chemistry import parse_smiles
from sugarcode.modules.molecule_eval.core import _canonical_graph_key


def test_directional_bond_between_aromatic_atoms_stays_aromatic():
    m = parse_smiles("CC(=O)/N=c1/sc(S(N)(=O)=O)nn1C")  # acetazolamide as written by ChEMBL
    assert (4, 5, 1.5) in m.bonds
    assert _canonical_graph_key("CC(=O)/N=c1/sc(S(N)(=O)=O)nn1C") == _canonical_graph_key("CC(N=c1n(nc(s1)S(=O)(=O)N)C)=O")


def test_directional_bond_between_aliphatic_atoms_is_single():
    m = parse_smiles("F/C=C/F")
    assert (0, 1, 1.0) in m.bonds and (2, 3, 1.0) in m.bonds
