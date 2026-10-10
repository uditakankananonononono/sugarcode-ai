"""One literal incremental exact positive-overshoot diagnostic pin."""
import pytest

from sugarcode.bio.bed import parse_bed


def test_literal_positive_overshoot_exact_error():
    with pytest.raises(ValueError) as caught:
        parse_bed('chr1\t0\t9\tg\t0\t+\t0\t9\t0\t1\t10\t0')
    assert type(caught.value) is ValueError
    assert str(caught.value) == 'line 1: block at +0 size 10 escapes the interval'
