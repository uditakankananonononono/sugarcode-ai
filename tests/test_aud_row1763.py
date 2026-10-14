import sys; sys.path.insert(0,'src')
from sugarcode.extra_doc.public1763 import tally

class TestAud:
    def test_audpin_counts_leaders_1763(self):
        got = tally(['p1','p2'],[('b1',['p1']),('b2',['p1','p2'])])
        assert got['counts'] == [('p1',2),('p2',1)]
        assert got['leaders'] == ['p1']
        assert got['election_validated'] is False
    def test_audpin_tie_all_1763(self):
        got = tally(['p2','p1'],[('b1',[])])
        assert got['counts'] == [('p2',0),('p1',0)] and got['leaders'] == ['p2','p1']
