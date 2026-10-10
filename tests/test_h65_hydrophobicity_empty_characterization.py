"""H65: one literal empty-input return, not scale or window validation."""

from sugarcode.bio.sequence import hydrophobicity_profile


def test_empty_input_returns_empty_profile():
    assert hydrophobicity_profile('') == []
