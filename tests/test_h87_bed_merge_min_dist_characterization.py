"""One empty-record invalid-distance rejection only."""
import pytest
from sugarcode.bio.bed import merge_intervals


def test_empty_records_literal_invalid_min_dist():
    with pytest.raises(ValueError) as caught:
        merge_intervals([], min_dist=-2)
    assert type(caught.value) is ValueError
    assert str(caught.value) == 'min_dist must be >= -1'
