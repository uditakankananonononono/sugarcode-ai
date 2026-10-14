import sys; sys.path.insert(0,'src')
from sugarcode.extra_doc.social_choice1769 import compare

class TestAud:
    def test_audpin_pairwise_winner_1769(self):
        got = compare(['a','b'],[['a','b'],['a','b'],['b','a']])
        assert got['pairwise'] == [('a','b',2),('b','a',1)]
        assert got['winners'] == ['a']
        assert got['welfare_validated'] is False
    def test_audpin_cycle_no_winner_1769(self):
        ballots = [['a','b','c'],['b','c','a'],['c','a','b']]
        got = compare(['a','b','c'],ballots)
        assert got['winners'] == []
        assert sorted(got['pairwise']) == sorted([('a','b',2),('b','a',1),('b','c',2),('c','b',1),('a','c',1),('c','a',2)])
