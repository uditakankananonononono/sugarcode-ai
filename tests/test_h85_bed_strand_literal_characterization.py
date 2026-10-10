"""One literal strand rejection only."""
import pytest
from sugarcode.bio.bed import parse_bed


def test_parse_bed_literal_invalid_strand():
    with pytest.raises(ValueError) as caught:
        parse_bed('chr1\t0\t10\tx\t0\tx')
    assert type(caught.value) is ValueError
    assert str(caught.value) == "line 1: invalid strand 'x'"
