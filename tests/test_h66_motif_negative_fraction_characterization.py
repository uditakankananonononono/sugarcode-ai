"""H66: literal negative-fraction rejection only."""

import pytest

from sugarcode.bio.motif import threshold_score


def test_negative_fraction_rejects_with_exact_range_diagnostic():
    with pytest.raises(ValueError) as caught:
        threshold_score({"min_score": 0, "max_score": 1}, -0.1)
    assert type(caught.value) is ValueError
    assert str(caught.value) == "fraction must be in [0, 1]"
