"""H73: one literal empty return, not mapping or reverse-order validation."""

from sugarcode.bio.sequence import reverse_complement


def test_empty_input_returns_empty_string():
    assert reverse_complement('') == ''
