"""H111: one literal ten-field GFF record rejection only."""

import pytest

from sugarcode.bio.gff import parse_gff


def test_ten_field_record_rejects_with_exact_diagnostic():
    with pytest.raises(ValueError) as caught:
        parse_gff('chr1\ta\tgene\t1\t9\t.\t+\t.\tID=g\textra')
    assert type(caught.value) is ValueError
    assert str(caught.value) == "line 1: GFF record has 10 fields, need 9"
