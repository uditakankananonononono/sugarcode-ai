"""One literal, source-derived missing-value diagnostic characterization."""
import pytest

from sugarcode.bio.gff import parse_gff


def test_second_gtf_item_missing_value_exact_error():
    with pytest.raises(ValueError) as caught:
        parse_gff('chr1\ta\tgene\t1\t9\t.\t+\t.\tgene_id "g"; bad')
    assert type(caught.value) is ValueError
    assert str(caught.value) == "line 1: malformed GTF attribute 'bad'"
