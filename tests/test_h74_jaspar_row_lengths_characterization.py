"""H74: one literal unequal-row-length rejection."""

import pytest

from sugarcode.bio.motif import read_jaspar


def test_longer_c_row_rejects_with_exact_length_diagnostic():
    with pytest.raises(ValueError) as caught:
        read_jaspar(">toy\nA [ 1 ]\nC [ 1 2 ]\nG [ 1 ]\nT [ 1 ]\n")
    assert type(caught.value) is ValueError
    assert str(caught.value) == "toy: rows have different lengths"
