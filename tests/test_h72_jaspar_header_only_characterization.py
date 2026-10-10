"""H72: one literal header-only row-set rejection."""

import pytest

from sugarcode.bio.motif import read_jaspar


def test_header_only_rejects_with_exact_empty_rows_diagnostic():
    with pytest.raises(ValueError) as caught:
        read_jaspar(">toy\n")
    assert type(caught.value) is ValueError
    assert str(caught.value) == "toy: need exactly 4 rows A/C/G/T, got []"
