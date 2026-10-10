"""Incremental identity/full-text pin of an existing reversed-row rejection."""
import pytest

from sugarcode.bio.gff import parse_gff


def test_literal_reversed_coordinates_exact_valueerror_and_text():
    with pytest.raises(ValueError) as caught:
        parse_gff('chr1\ta\tgene\t9\t5\t.\t+\t.\tID=g')
    assert type(caught.value) is ValueError
    assert str(caught.value) == 'line 1: invalid coordinates 9..5'
