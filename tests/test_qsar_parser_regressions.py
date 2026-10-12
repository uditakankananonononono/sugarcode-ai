"""Regression tests for behavior at base revision 99cb2d32."""
import pytest

from sugarcode.modules.qsar_bench.chemistry import parse_smiles


@pytest.mark.parametrize("smi", ["FC(F)(F)(F)F", "C(C)(C)(C)(C)C", "CC(C)(C)(C)(C)C", "N(C)(C)(C)(C)C",
                                 "C(=O)(=O)(=O)=O", "OO(C)C", "[CH5]", "[CH5+]", "[O+](C)(C)(C)C", "c1ccc(C)(C)(C)cc1"])
def test_valence_impossible_atoms_are_rejected(smi):
    with pytest.raises(ValueError, match="valence error"):
        parse_smiles(smi)


@pytest.mark.parametrize("smi", ["CC(=O)Oc1ccccc1C(=O)O", "CS(=O)(=O)N", "CP(=O)(O)O", "CN(=O)=O", "C[N+](=O)[O-]",
                                 "[NH4+]", "C[N+](C)(C)C", "[13CH4]", "Cn1c(=O)c2c(ncn2C)n(C)c1=O",
                                 "c1ccc2ccccc2c1", "S(=O)(=O)(O)O", "FC(F)(F)c1ccccc1", "C#N", "[Na+].[Cl-]",
                                 "CC(C)(C)c1ccccc1", "C=C=C", "[H][H]", "O=S1(=O)CCCC1"])
def test_valid_molecules_still_parse(smi):
    assert parse_smiles(smi).atoms


def test_stereo_is_flagged_not_silently_dropped():
    assert parse_smiles("CCO").ignored == ()
    assert parse_smiles("c1ccccc1").ignored == ()
    assert any("chirality" in x for x in parse_smiles("N[C@@H](C)C(=O)O").ignored)
    assert any("cis/trans" in x for x in parse_smiles("F/C=C/F").ignored)
    assert any("cis/trans" in x for x in parse_smiles("F/C=C\\F").ignored)
    for smi in ("N[C@@H](C)C(=O)O", "F/C=C/F", "F\\C=C/F"):
        with pytest.raises(ValueError, match="stereochemistry not supported"):
            parse_smiles(smi, strict_stereo=True)
    assert parse_smiles("CCO", strict_stereo=True).atoms


@pytest.mark.parametrize("smi", ["C=", "=C", "C==", "C==C", "C=-C", "C#=", "C-", "C--", "-C", "C(=)C", "C(=O=)C",
                                 "C..", ".C", "C.", "C(.)C", "C(.C)", "C()", "C((C))", "C(()C)", "CC()C", "C11", "C1C1", "C=1C1",
                                 "C//C", "F/C=/C/F", "C(=)", "C(C)=", "C1CC1=", "[Na+].=[Cl-]"])
def test_malformed_strings_are_rejected(smi):
    # old code accepted every one of these (valid_fraction 1.0 for "C=" and "C()")
    with pytest.raises(ValueError):
        parse_smiles(smi)


@pytest.mark.parametrize("smi", ["C=C", "C(=O)O", "C(C)(C)C", "C1CC1", "C=1CCCCC=1", "C%10CCCC%10", "[C-]#[O+]", "C1.C1",
                                 "[Na+].[Cl-]", "F/C=C/F", "F/C=C\\F", "C#CC#N", "CC(=O)[O-]", "c1ccccc1-c1ccccc1",
                                 "C:C", "C(C(C)C)C", "O=C1CCC(=O)N1", "C1CC2CCC1C2"])
def test_well_formed_strings_still_parse(smi):
    assert parse_smiles(smi).atoms
