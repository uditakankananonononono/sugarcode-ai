"""One bang-strand literal on shared GFF strand guard."""
import pytest
from sugarcode.bio.gff import parse_gff


def test_literal_strand_bang_exact_error():
    with pytest.raises(ValueError) as caught:
        parse_gff('chr1\ta\tgene\t1\t9\t.\t!\t.\tID=g')
    assert type(caught.value) is ValueError
    assert str(caught.value) == "line 1: invalid strand '!'"
