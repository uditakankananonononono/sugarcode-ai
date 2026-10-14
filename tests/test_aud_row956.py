import sys; sys.path.insert(0,'src')
from sugarcode.extra_doc.abstract_signal_cancel import evaluate
import pytest

class TestAud:
    def test_audpin_residuals_cancelled_956(self):
        got = evaluate(((3,-3),(5,2),(-1,1)))
        assert got['residuals'] == (0,7,0)
        assert got['cancelled_positions'] == (0,2)
        assert got['magnitude_total'] == 7
        assert got['abstract_signal_cancel_validated'] is False
    def test_audpin_zero_pair_cancelled_956(self):
        got = evaluate(((0,0),))
        assert got['residuals'] == (0,) and got['cancelled_positions'] == (0,)
        assert got['magnitude_total'] == 0
    def test_audpin_refusals_956(self):
        with pytest.raises(ValueError): evaluate(((101,0),))
        with pytest.raises(ValueError): evaluate(((0,-101),))
