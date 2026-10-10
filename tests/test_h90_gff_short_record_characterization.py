"""H90: one literal single-field rejection only."""

import pytest

from sugarcode.bio.gff import parse_gff


def test_single_field_record_rejects_with_exact_diagnostic():
    with pytest.raises(ValueError) as caught:
        parse_gff("chr1")
    assert type(caught.value) is ValueError
    assert str(caught.value) == "line 1: GFF record has 1 fields, need 9"
