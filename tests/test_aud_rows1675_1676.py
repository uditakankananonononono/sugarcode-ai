import sys, unittest
from fractions import Fraction as F
sys.path.insert(0, 'src'); sys.path.insert(0, 'tests')
from sugarcode.extra_doc import protected_fraction1675 as m75, wildlife_balance1676 as m76

class Aud(unittest.TestCase):
    def test_audpin_behavior_1675(self):
        got = m75.coverage([('a',10,4),('a',2,2),('b',0,0)])
        self.assertEqual(got['coverage'], (('a',12,6,6,F(1,2)),('b',0,0,0,None)))
        self.assertEqual(got['unprotected'], 6)
        self.assertEqual(got['protected_fraction'], F(1,2))
    def test_audpin_refusals_1675(self):
        with self.assertRaises(ValueError): m75.coverage([('a',1,2)])
        with self.assertRaises(ValueError): m75.coverage([('a',-1,0)])
        self.assertIsNone(m75.coverage([('a',0,0)])['protected_fraction'])
    def test_audpin_behavior_1676(self):
        got = m76.counts([('a',10,4,9),('b',0,0,0)])
        self.assertEqual(got['counts'], (('a',5,-5),('b',0,0)))
        self.assertEqual(got['negative'], ())
        self.assertEqual(got['total_final'], 5)
        self.assertEqual(got['total_change'], -5)
    def test_audpin_negative_1676(self):
        # negative final retained, listed in 'negative'
        got = m76.counts([('a',2,0,5)])
        self.assertEqual(got['counts'], (('a',-3,-5),))
        self.assertEqual(got['negative'], ('a',))
        self.assertEqual(got['total_final'], -3)
    def test_audpin_extra_1676(self):
        with self.assertRaises(ValueError): m76.counts([('a',1,1,1),('a',2,2,2)])
        # final 0 is not negative
        self.assertEqual(m76.counts([('a',3,0,3)])['negative'], ())

if __name__ == '__main__': unittest.main()
