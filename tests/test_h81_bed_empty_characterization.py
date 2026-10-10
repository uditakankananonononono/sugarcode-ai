"""One literal BED rejection, not format validation."""
import pytest
from sugarcode.bio.bed import parse_bed


def test_parse_bed_empty_literal_rejection():
    with pytest.raises(ValueError) as caught:
        parse_bed('')
    assert type(caught.value) is ValueError
    assert str(caught.value) == 'no BED records found'
