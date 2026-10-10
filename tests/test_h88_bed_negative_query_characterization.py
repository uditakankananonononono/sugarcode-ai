"""H88: one literal negative-query rejection only."""

import pytest

from sugarcode.bio.bed import overlaps


def test_negative_query_start_rejects_with_exact_diagnostic():
    with pytest.raises(ValueError) as caught:
        overlaps({"chrom": "chr1", "start": 0, "end": 10}, "chr1", -1, 10)
    assert type(caught.value) is ValueError
    assert str(caught.value) == "invalid query interval -1..10"
