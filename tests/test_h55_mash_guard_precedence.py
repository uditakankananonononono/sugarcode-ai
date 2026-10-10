"""One invalid-k guard precedence, not model accuracy validation."""
import pytest

from sugarcode.bio.kmer import mash_distance


def test_invalid_k_precedes_low_j_saturation():
    with pytest.raises(ValueError) as caught:
        mash_distance(-1.0, 0)
    assert type(caught.value) is ValueError
    assert str(caught.value) == 'k must be >= 1, got 0'
