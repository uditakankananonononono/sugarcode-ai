import sys, unittest
sys.path.insert(0, 'src'); sys.path.insert(0, 'tests')
from sugarcode.extra_doc import material_transfers1711 as m11, industrial_balance1712 as m12

class Aud(unittest.TestCase):
    def test_audpin_behavior_1711(self):
        got = m11.transfers([('a','b',3),('b','a',1)])
        self.assertEqual(got['transfers'], (('a',1,3,-2),('b',3,1,2)))
        self.assertEqual(got['total_transferred'], 4)
        self.assertEqual(got['positive'], ('b',))
    def test_audpin_selftransfer_1711(self):
        got = m11.transfers([('a','a',2)])
        self.assertEqual(got['transfers'], (('a',2,2,0),))
        with self.assertRaises(ValueError): m11.transfers([('a','x'*41,1)])
        with self.assertRaises(ValueError): m11.transfers([('a','b',-1)])
    def test_audpin_behavior_1712(self):
        got = m12.balances([('a',10,3,2),('a',1,1,1),('b',0,5,0)])
        self.assertEqual(got['balances'], (('a',11,4,3,4),('b',0,5,0,-5)))
        self.assertEqual(got['total_residual'], -1)
        self.assertEqual(got['negative'], ('b',))
    def test_audpin_aggregation_1712(self):
        got = m12.balances([('x',5,1,1),('x',5,1,1)])
        self.assertEqual(got['balances'], (('x',10,2,2,6),))
    def test_audpin_extra_1712(self):
        self.assertEqual(m12.balances([('a',3,1,2)])['negative'], ())
        with self.assertRaises(ValueError): m12.balances([])

if __name__ == '__main__': unittest.main()
