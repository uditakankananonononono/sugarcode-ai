import sys; sys.path.insert(0,'src')
from sugarcode.extra_doc.voting1768 import tally

class TestAud:
    def test_audpin_borda_tie_all_1768(self):
        got = tally(['a','b','c'],[['a','b','c'],['c','b','a']])
        assert got['scores'] == [('a',2),('b',2),('c',2)]
        assert got['leaders'] == ['a','b','c']
        assert got['election_validated'] is False
    def test_audpin_clear_winner_1768(self):
        got = tally(['a','b'],[['a','b'],['a','b'],['b','a']])
        assert got['scores'] == [('a',2),('b',1)] and got['leaders'] == ['a']
