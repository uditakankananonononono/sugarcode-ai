import sys; sys.path.insert(0,'src')
from sugarcode.extra_doc.collective1770 import audit_contributions

class TestAud:
    def test_audpin_pivotal_met_1770(self):
        got = audit_contributions([('a',5),('b',3),('c',4)],10)
        assert got['total'] == 12 and got['met'] is True and got['shortfall'] == 0
        assert got['pivotal'] == ['a','b','c']
        assert got['action_validated'] is False
    def test_audpin_unmet_no_pivotal_1770(self):
        got = audit_contributions([('a',2),('b',3)],10)
        assert got['met'] is False and got['shortfall'] == 5 and got['pivotal'] == []
