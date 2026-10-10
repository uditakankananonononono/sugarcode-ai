"""One literal second GFF3 attribute item rejection only."""
import pytest
from sugarcode.bio.gff import parse_gff


def test_literal_second_gff3_item_missing_equals():
    with pytest.raises(ValueError) as caught:
        parse_gff('chr1\ta\tgene\t1\t9\t.\t+\t.\tID=g;bad')
    assert type(caught.value) is ValueError
    assert str(caught.value) == "line 1: malformed GFF3 attribute 'bad'"
