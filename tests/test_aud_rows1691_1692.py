import sys, unittest
from fractions import Fraction as F
sys.path.insert(0, 'src'); sys.path.insert(0, 'tests')
from sugarcode.extra_doc import diet_factors1691 as m91, food_waste1692 as m92

class Aud(unittest.TestCase):
    def test_audpin_behavior_1691(self):
        got = m91.impacts([('a',10,3),('a',2,5),('b',4,0)])
        self.assertEqual(got['impacts'], (('a',12,40),('b',4,0)))
        self.assertEqual(got['total_impact'], 40)
        self.assertEqual(got['positive'], ('a',))
    def test_audpin_aggregation_1691(self):
        got = m91.impacts([('x',3,2),('x',1,4)])
        self.assertEqual(got['impacts'], (('x',4,10),))
        self.assertEqual(m91.impacts([('a',5,0)])['positive'], ())
    def test_audpin_behavior_1692(self):
        got = m92.waste([('a',10,4),('b',0,0)])
        self.assertEqual(got['waste'], (('a',10,4,6,F(2,5)),('b',0,0,0,None)))
        self.assertEqual(got['total_retained'], 6)
        self.assertEqual(got['discarded_fraction'], F(2,5))
    def test_audpin_refusals_1692(self):
        with self.assertRaises(ValueError): m92.waste([('a',1,2)])
        with self.assertRaises(ValueError): m92.waste([])
        self.assertIsNone(m92.waste([('a',0,0)])['discarded_fraction'])
    def test_audpin_aggregation_1692(self):
        got = m92.waste([('a',4,1),('a',6,3)])
        self.assertEqual(got['waste'], (('a',10,4,6,F(2,5)),))

if __name__ == '__main__': unittest.main()
