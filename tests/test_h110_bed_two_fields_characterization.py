"""H110: one literal two-field record rejection only."""

import pytest

from sugarcode.bio.bed import parse_bed


def test_two_field_record_rejects_with_exact_diagnostic():
    with pytest.raises(ValueError) as caught:
        parse_bed("chr1\t0")
    assert type(caught.value) is ValueError
    assert str(caught.value) == "line 1: BED record has 2 fields, need >= 3"
