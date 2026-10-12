"""Bracket atoms with unrecognised trailing content must be rejected.

Base revision accepted "[CH4garbage]" silently: the element and H count were
parsed and the leftover characters were ignored, so the module docstring's
rejection claims did not hold for bracket content.
"""
import pytest

from sugarcode.modules.qsar_bench.chemistry import parse_smiles


@pytest.mark.parametrize("smi", ["[CH4garbage]", "[Cfoo]", "[NH4+z]", "[C@junk]",
                                 "[13CH4x]", "[O-2q]", "[Na+.]"])
def test_bracket_trailing_content_is_rejected(smi):
    with pytest.raises(ValueError, match="unsupported bracket atom content|unsupported atom token"):
        parse_smiles(smi)


@pytest.mark.parametrize("smi,charges", [
    ("[13CH4]", [0]), ("[2H]", [0]), ("[C@@H]", [0]), ("[NH4+]", [1]),
    ("[O-]", [-1]), ("[Na+]", [1]), ("[C-]#[O+]", [-1, 1]), ("[nH]", [0]),
])
def test_legitimate_bracket_atoms_still_parse(smi, charges):
    mol = parse_smiles(smi)
    assert [a.charge for a in mol.atoms] == charges
