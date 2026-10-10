"""H56: one literal mixed-sign guard diagnostic, not normalization validation."""

import pytest

from sugarcode.bio.rnaseq import size_factors


def test_mixed_sign_row_rejects_negative_before_positive_row_selection():
    with pytest.raises(ValueError) as caught:
        size_factors([[1, -1]])
    assert type(caught.value) is ValueError
    assert str(caught.value) == "negative count"
