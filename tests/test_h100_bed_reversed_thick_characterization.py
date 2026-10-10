"""One literal reversed thick endpoints, source-derived diagnostic only."""
import pytest

from sugarcode.bio.bed import parse_bed


def test_literal_reversed_thick_exact_error():
    with pytest.raises(ValueError) as caught:
        parse_bed('chr1\t0\t9\tg\t0\t+\t5\t4')
    assert type(caught.value) is ValueError
    assert str(caught.value) == 'line 1: thick block outside the interval'
