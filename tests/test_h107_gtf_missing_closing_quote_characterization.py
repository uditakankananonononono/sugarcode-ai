"""One literal missing closing quote, source-derived GTF diagnostic only."""
import pytest
from sugarcode.bio.gff import parse_gff


def test_literal_missing_closing_quote_exact_error():
    with pytest.raises(ValueError) as caught:
        parse_gff('chr1\ta\tgene\t1\t9\t.\t+\t.\tgene_id "g')
    assert type(caught.value) is ValueError
    assert str(caught.value) == """line 1: malformed GTF attribute 'gene_id "g'"""
