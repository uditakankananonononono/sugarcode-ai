"""H71: one literal row-before-header rejection."""

import pytest

from sugarcode.bio.motif import read_jaspar


def test_row_before_header_after_blank_rejects_with_exact_diagnostic():
    with pytest.raises(ValueError) as caught:
        read_jaspar("\nA [ nope ]\n")
    assert type(caught.value) is ValueError
    assert str(caught.value) == "line 2: matrix row before any header"
