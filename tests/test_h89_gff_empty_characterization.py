"""One literal empty GFF rejection only."""
import pytest
from sugarcode.bio.gff import parse_gff


def test_parse_gff_empty_literal_rejection():
    with pytest.raises(ValueError) as caught:
        parse_gff('')
    assert type(caught.value) is ValueError
    assert str(caught.value) == 'no GFF records found'
