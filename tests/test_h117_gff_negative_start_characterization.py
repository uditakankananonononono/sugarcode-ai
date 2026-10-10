"""H117: negative-start literal only, shared coordinate guard, not novelty."""
import pytest

from sugarcode.bio.gff import parse_gff


def test_literal_negative_start_exact_error():
    with pytest.raises(ValueError) as caught:
        parse_gff('chr1\ta\tgene\t-1\t9\t.\t+\t.\tID=g')
    assert type(caught.value) is ValueError
    assert str(caught.value) == 'line 1: invalid coordinates -1..9'
