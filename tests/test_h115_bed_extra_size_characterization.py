"""One extra-size literal on the shared BED block-count guard."""
import pytest
from sugarcode.bio.bed import parse_bed


def test_literal_extra_size_exact_error():
    with pytest.raises(ValueError) as caught:
        parse_bed('chr1\t0\t9\tg\t0\t+\t0\t9\t0\t1\t4,5\t0')
    assert type(caught.value) is ValueError
    assert str(caught.value) == 'line 1: blockCount 1 != 2 sizes / 1 starts'
