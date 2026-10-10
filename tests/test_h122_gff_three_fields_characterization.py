"""H122: incremental identity/full-text pin for the existing short-row case."""
import pytest

from sugarcode.bio import gff


def test_literal_three_fields_exact_error():
    print("LOADED_MODULE=" + gff.__file__)
    with pytest.raises(ValueError) as caught:
        gff.parse_gff('chr1\ta\tgene')
    assert type(caught.value) is ValueError
    assert str(caught.value) == 'line 1: GFF record has 3 fields, need 9'
