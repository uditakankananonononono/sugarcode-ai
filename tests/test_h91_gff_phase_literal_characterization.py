"""One literal phase rejection only."""
import pytest
from sugarcode.bio.gff import parse_gff


def test_parse_gff_literal_invalid_phase():
    with pytest.raises(ValueError) as caught:
        parse_gff('chr1\ta\tgene\t1\t9\t.\t+\tx\tID=g')
    assert type(caught.value) is ValueError
    assert str(caught.value) == "line 1: invalid phase 'x'"
