"""H86: one literal nonnumeric score rejection only."""

import pytest

from sugarcode.bio.bed import parse_bed


def test_nonnumeric_score_rejects_with_exact_diagnostic():
    with pytest.raises(ValueError) as caught:
        parse_bed("chr1\t0\t10\tx\tbad")
    assert type(caught.value) is ValueError
    assert str(caught.value) == "line 1: score not numeric: 'bad'"
