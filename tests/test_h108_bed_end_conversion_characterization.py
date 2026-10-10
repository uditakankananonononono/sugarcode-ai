"""One literal end-x conversion, exact source-derived diagnostic."""
import pytest

from sugarcode.bio.bed import parse_bed


def test_literal_end_x_exact_error():
    with pytest.raises(ValueError) as caught:
        parse_bed('chr1\t0\tx')
    assert type(caught.value) is ValueError
    assert str(caught.value) == 'line 1: start/end not integers'
