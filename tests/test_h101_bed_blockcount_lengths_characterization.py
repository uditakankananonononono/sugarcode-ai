"""Incremental exact identity/text for one literal count mismatch."""
import pytest
from sugarcode.bio.bed import parse_bed


def test_literal_blockcount_lengths_mismatch():
    with pytest.raises(ValueError) as caught:
        parse_bed('chr1\t0\t9\tg\t0\t+\t0\t9\t0\t2\t9\t0')
    assert type(caught.value) is ValueError
    assert str(caught.value) == 'line 1: blockCount 2 != 1 sizes / 1 starts'
