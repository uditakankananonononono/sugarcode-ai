import sys; sys.path.insert(0,'src')
from sugarcode.extra_doc.abstract_change_budget import changes
import pytest

class TestAud:
    def test_audpin_costs_within_1194(self):
        got = changes(((0,5),(10,4)),8)
        assert got['change_costs'] == (5,6) and got['total_cost'] == 11
        assert got['within_budget'] is False and got['remaining_budget'] == -3
        assert got['abstract_change_budget_validated'] is False
    def test_audpin_exact_budget_boundary_1194(self):
        got = changes(((7,7),),6)
        assert got['change_costs'] == (0,) and got['total_cost'] == 0
        assert got['within_budget'] is True and got['remaining_budget'] == 6
    def test_audpin_equal_boundary_1194(self):
        got = changes(((0,5),),5)
        assert got['within_budget'] is True and got['remaining_budget'] == 0
    def test_audpin_refusals_1194(self):
        with pytest.raises(ValueError): changes(((0,5),),20001)
        with pytest.raises(ValueError): changes(((0,1001),),5)
        with pytest.raises(ValueError): changes((),5)
