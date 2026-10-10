"""One rejection diagnostic and precedence, not chemistry validation."""
import pytest

from sugarcode.bio.proteinprops import charge_at_ph


def test_bad_residue_diagnostic_precedes_bad_ph():
    with pytest.raises(ValueError) as caught:
        charge_at_ph(' zx ', 15)
    assert type(caught.value) is ValueError
    assert str(caught.value) == "non-standard residues ['X', 'Z'] - only the 20 standard amino acids are supported"
