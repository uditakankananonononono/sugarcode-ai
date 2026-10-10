"""One literal rejection, not FASTA validation."""
import pytest
from sugarcode.bio.fasta import parse_fasta


def test_parse_fasta_empty_literal_rejection():
    with pytest.raises(ValueError) as exc:
        parse_fasta('')
    assert str(exc.value) == 'no FASTA records found'
