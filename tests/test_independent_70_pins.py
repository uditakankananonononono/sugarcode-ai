import pytest
from sugarcode.modules.bioplayground.boundary_diversity import diversity_metrics

def test_sequence_cap_guard():
    with pytest.raises(ValueError,match='bounded nonempty probability list'):diversity_metrics([1]+[0]*10000)

def test_nonnegative_guard_stage():
    with pytest.raises(ValueError,match='finite nonnegative probability'):diversity_metrics([-.5,1])
