"""H64: one literal blank-only rejection, not format validation."""

import pytest

from sugarcode.bio.motif import read_jaspar


def test_blank_only_input_rejects_with_no_matrices_diagnostic():
    with pytest.raises(ValueError) as caught:
        read_jaspar("\n \t\n")
    assert type(caught.value) is ValueError
    assert str(caught.value) == "no JASPAR matrices found"
