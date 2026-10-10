"""One literal start-conversion rejection only."""
import pytest
from sugarcode.bio.bed import parse_bed


def test_parse_bed_literal_noninteger_start_rejection():
    with pytest.raises(ValueError) as caught:
        parse_bed('chr1\tx\t10')
    assert type(caught.value) is ValueError
    assert str(caught.value) == 'line 1: start/end not integers'
