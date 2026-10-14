import sys; sys.path.insert(0,'src')
from sugarcode.extra_doc.rational1764 import evaluate

class TestAud:
    def test_audpin_utilities_maximizers_regret_1764(self):
        got = evaluate([('a',5,2),('b',9,4),('c',3,0)])
        assert got['utilities'] == [('a',3),('b',5),('c',3)]
        assert got['maximizers'] == ['b']
        assert got['regret'] == [('a',2),('b',0),('c',2)]
        assert got['behavior_validated'] is False
    def test_audpin_tied_maximizers_1764(self):
        got = evaluate([('a',2,0),('b',4,2)])
        assert got['maximizers'] == ['a','b'] and got['regret'] == [('a',0),('b',0)]
