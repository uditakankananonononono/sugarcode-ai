import sys; sys.path.insert(0,'src')
from sugarcode.extra_doc.coalition1767 import enumerate_coalitions

class TestAud:
    def test_audpin_winning_minimal_1767(self):
        got = enumerate_coalitions([('a',2),('b',3),('c',1)],4)
        assert got['winning'] == [(['a','b'],5),(['b','c'],4),(['a','b','c'],6)]
        assert got['minimal'] == [(['a','b'],5),(['b','c'],4)]
        assert got['coalitions_validated'] is False
    def test_audpin_grand_only_1767(self):
        got = enumerate_coalitions([('a',1),('b',1)],3)
        assert got['winning'] == [] and got['minimal'] == []
