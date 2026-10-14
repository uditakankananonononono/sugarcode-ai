import sys, unittest
sys.path.insert(0, 'src'); sys.path.insert(0, 'tests')
from sugarcode.extra_doc import vertical_layers1685 as m85, aqua_balance1686 as m86

class Aud(unittest.TestCase):
    def test_audpin_behavior_1685(self):
        got = m85.layers([('a',10,3,2),('b',0,1,5)])
        self.assertEqual(got['layers'], (('a',30,60),('b',0,0)))
        self.assertEqual(got['total_area'], 30)
        self.assertEqual(got['total_product'], 60)
    def test_audpin_refusals_1685(self):
        with self.assertRaises(ValueError): m85.layers([('a',1,0,1)])
        with self.assertRaises(ValueError): m85.layers([('a',1,65,1)])
        with self.assertRaises(ValueError): m85.layers([('a',1,1,1),('a',2,2,2)])
        with self.assertRaises(ValueError): m85.layers([])
    def test_audpin_behavior_1686(self):
        got = m86.balances([('a',10,3,2),('a',1,1,1),('b',0,5,0)])
        self.assertEqual(got['balances'], (('a',11,4,3,4),('b',0,5,0,-5)))
        self.assertEqual(got['total_residual'], -1)
        self.assertEqual(got['negative'], ('b',))
    def test_audpin_aggregation_1686(self):
        got = m86.balances([('x',5,1,1),('x',5,1,1)])
        self.assertEqual(got['balances'], (('x',10,2,2,6),))
    def test_audpin_extra_1686(self):
        # residual exactly 0 not negative
        self.assertEqual(m86.balances([('a',3,1,2)])['negative'], ())
        with self.assertRaises(ValueError): m86.balances([('a',-1,0,0)])

if __name__ == '__main__': unittest.main()
