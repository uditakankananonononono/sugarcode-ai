"""H84: one literal negative-start rejection only."""

import pytest

from sugarcode.bio.bed import parse_bed


def test_negative_start_rejects_with_exact_diagnostic():
    with pytest.raises(ValueError) as caught:
        parse_bed("chr1\t-1\t10")
    assert type(caught.value) is ValueError
    assert str(caught.value) == "line 1: invalid 0-based interval -1..10"
