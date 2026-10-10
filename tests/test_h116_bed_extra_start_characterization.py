"""H116: one extra-start literal, authored only under PREP-NORUN fallback."""
import pytest

from sugarcode.bio.bed import parse_bed


def test_literal_bed_extra_start_exact_error():
    with pytest.raises(ValueError) as caught:
        parse_bed('chr1\t0\t9\tg\t0\t+\t0\t9\t0\t1\t9\t0,1')
    assert type(caught.value) is ValueError
    assert str(caught.value) == 'line 1: blockCount 1 != 1 sizes / 2 starts'
