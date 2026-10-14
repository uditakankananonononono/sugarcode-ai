import sys; sys.path.insert(0,'src')
from sugarcode.extra_doc.abstract_cloak_mask import evaluate
import pytest

class TestAud:
    def test_audpin_visible_hidden_955(self):
        got = evaluate(((5,1),(7,0),(0,1)))
        assert got['visible_values'] == (5,0,0)
        assert got['hidden_positions'] == (1,)
        assert got['visible_total'] == 5
        assert got['abstract_cloak_mask_validated'] is False
    def test_audpin_all_hidden_955(self):
        got = evaluate(((9,0),))
        assert got['visible_values'] == (0,) and got['hidden_positions'] == (0,)
        assert got['visible_total'] == 0
    def test_audpin_refusals_955(self):
        with pytest.raises(ValueError): evaluate(((5,2),))
        with pytest.raises(ValueError): evaluate(((101,1),))
