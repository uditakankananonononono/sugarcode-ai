"""H60: one literal row-prefix rejection, not format validation."""

import pytest

from sugarcode.bio.motif import read_jaspar


def test_invalid_prefix_rejects_before_numeric_conversion():
    with pytest.raises(ValueError) as caught:
        read_jaspar(">toy\nX [ nope ]\n")
    assert type(caught.value) is ValueError
    assert str(caught.value) == "line 2: row must start with A/C/G/T"
