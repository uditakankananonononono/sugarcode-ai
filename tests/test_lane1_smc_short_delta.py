import pytest
from sugarcode.extra_doc.smc1037 import update


def test_shorter_likelihood_list_rejected():
    with pytest.raises(ValueError) as exc:update([1,2],[1])
    assert str(exc.value)=='likelihood must be an exact list matching prior count'
