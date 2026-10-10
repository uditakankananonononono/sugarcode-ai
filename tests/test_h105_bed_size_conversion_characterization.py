"""One literal size conversion diagnostic, incremental on shared handler."""
import pytest
from sugarcode.bio.bed import parse_bed


def test_literal_size_x_exact_error():
    with pytest.raises(ValueError) as caught:
        parse_bed('chr1\t0\t9\tg\t0\t+\t0\t9\t0\t1\tx\t0')
    assert type(caught.value) is ValueError
    assert str(caught.value) == 'line 1: malformed block fields'
