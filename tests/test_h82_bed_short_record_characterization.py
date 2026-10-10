"""H82: one literal short-record rejection only."""

import pytest

from sugarcode.bio.bed import parse_bed


def test_single_field_record_rejects_with_exact_diagnostic():
    with pytest.raises(ValueError) as caught:
        parse_bed("chr1")
    assert type(caught.value) is ValueError
    assert str(caught.value) == "line 1: BED record has 1 fields, need >= 3"
