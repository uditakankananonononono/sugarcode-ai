"""H52: one literal JASPAR rejection diagnostic, not format validation."""

import pytest

from sugarcode.bio.motif import read_jaspar


def test_nonnumeric_count_uses_physical_line_number():
    with pytest.raises(ValueError) as caught:
        read_jaspar("\n>toy\n\nA [ nope ]\n")
    assert type(caught.value) is ValueError
    assert str(caught.value) == "line 4: non-numeric count"
