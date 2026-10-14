import sys; sys.path.insert(0,'src')
from sugarcode.extra_doc.bargaining1766 import select_offers

class TestAud:
    def test_audpin_products_maximizers_1766(self):
        got = select_offers((2,2),[('x',5,3),('y',1,9),('z',4,4)])
        assert got['products'] == [('x',3),('z',4)]
        assert got['maximizers'] == ['z'] and got['infeasible'] == ['y']
        assert got['bargaining_validated'] is False
    def test_audpin_zero_product_feasible_1766(self):
        got = select_offers((2,2),[('x',2,9)])
        assert got['products'] == [('x',0)] and got['maximizers'] == ['x']
        assert got['infeasible'] == []
