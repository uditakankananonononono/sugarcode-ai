"""H75: one empty-literal equality in sequence, not mass or type validation."""

from sugarcode.bio.sequence import molecular_weight


def test_empty_input_weight_equals_zero():
    assert molecular_weight('') == 0.0
