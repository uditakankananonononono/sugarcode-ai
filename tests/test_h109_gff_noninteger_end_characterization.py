"""One end-x literal on the shared GFF conversion handler."""
import pytest
from sugarcode.bio.gff import parse_gff


def test_literal_end_x_exact_error():
    with pytest.raises(ValueError) as caught:
        parse_gff('chr1\ta\tgene\t1\tx\t.\t+\t.\tID=g')
    assert type(caught.value) is ValueError
    assert str(caught.value) == 'line 1: start/end not integers'
