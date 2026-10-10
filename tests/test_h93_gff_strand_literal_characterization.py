"""Incremental literal exact identity/text, not new strand behavior."""
import pytest
from sugarcode.bio.gff import parse_gff


def test_parse_gff_literal_invalid_strand():
    with pytest.raises(ValueError) as caught:
        parse_gff('chr1\ta\tgene\t1\t9\t.\tx\t.\tID=g')
    assert type(caught.value) is ValueError
    assert str(caught.value) == "line 1: invalid strand 'x'"
