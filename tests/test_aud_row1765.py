import sys; sys.path.insert(0,'src')
from sugarcode.extra_doc.game1765 import pure_equilibria

class TestAud:
    def test_audpin_two_equilibria_1765(self):
        got = pure_equilibria([[(1,1),(0,0)],[(0,0),(1,1)]])
        assert got['equilibria'] == [(0,0),(1,1)]
        assert got['row_best'] == [(0,[0]),(1,[1])]
        assert got['col_best'] == [(0,[0]),(1,[1])]
        assert got['behavior_validated'] is False
    def test_audpin_prisoner_single_1765(self):
        got = pure_equilibria([[(2,2),(0,3)],[(3,0),(1,1)]])
        assert got['equilibria'] == [(1,1)]
        assert got['row_best'] == [(0,[1]),(1,[1])]
        assert got['col_best'] == [(0,[1]),(1,[1])]
