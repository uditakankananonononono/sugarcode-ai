"""H92: one literal zero-start rejection only."""

import pytest

from sugarcode.bio.gff import parse_gff


def test_zero_start_rejects_with_exact_diagnostic():
    with pytest.raises(ValueError) as caught:
        parse_gff("chr1\ta\tgene\t0\t9\t.\t+\t.\tID=g")
    assert type(caught.value) is ValueError
    assert str(caught.value) == "line 1: invalid coordinates 0..9"
