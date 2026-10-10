"""H94: incremental exact identity/text for one noninteger-start literal."""

import pytest

from sugarcode.bio.gff import parse_gff


def test_noninteger_start_rejects_with_exact_diagnostic():
    with pytest.raises(ValueError) as caught:
        parse_gff("chr1\ta\tgene\tx\t9\t.\t+\t.\tID=g")
    assert type(caught.value) is ValueError
    assert str(caught.value) == "line 1: start/end not integers"
