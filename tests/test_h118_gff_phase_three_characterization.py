"""One literal numeric phase-three exact diagnostic pin."""
import pytest

from sugarcode.bio.gff import parse_gff


def test_literal_phase_three_exact_error():
    with pytest.raises(ValueError) as caught:
        parse_gff('chr1\ta\tgene\t1\t9\t.\t+\t3\tID=g')
    assert type(caught.value) is ValueError
    assert str(caught.value) == "line 1: invalid phase '3'"
