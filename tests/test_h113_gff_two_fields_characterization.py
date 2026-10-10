"""One two-field GFF literal, shared count guard diagnostic only."""
import pytest
from sugarcode.bio.gff import parse_gff


def test_literal_two_fields_exact_error():
    with pytest.raises(ValueError) as caught:
        parse_gff('chr1\ta')
    assert type(caught.value) is ValueError
    assert str(caught.value) == 'line 1: GFF record has 2 fields, need 9'
