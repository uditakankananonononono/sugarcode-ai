"""One literal thick-start rejection only."""
import pytest
from sugarcode.bio.bed import parse_bed


def test_literal_thick_start_before_interval():
    with pytest.raises(ValueError) as caught:
        parse_bed('chr1\t0\t9\tg\t0\t+\t-1\t9')
    assert type(caught.value) is ValueError
    assert str(caught.value) == 'line 1: thick block outside the interval'
