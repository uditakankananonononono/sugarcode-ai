import sys; sys.path.insert(0,'src')
from sugarcode.extra_doc.political1762 import audit_sectors

class TestAud:
    def test_audpin_balances_shares_1762(self):
        got = audit_sectors([('a',10,4),('b',0,6)])
        assert got['balances'] == [('a',6),('b',-6)]
        assert got['totals'] == (10,10,0)
        assert got['revenue_shares'] == [('a',(1,1)),('b',(0,1))]
        assert got['economy_validated'] is False
    def test_audpin_zero_revenue_none_1762(self):
        got = audit_sectors([('a',0,4)])
        assert got['revenue_shares'] == [('a',None)] and got['totals'] == (0,4,-4)
