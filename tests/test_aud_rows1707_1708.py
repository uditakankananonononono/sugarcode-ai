import sys, unittest
from fractions import Fraction as F
sys.path.insert(0, 'src'); sys.path.insert(0, 'tests')
from sugarcode.extra_doc import lifecycle_terms1707 as m07, carbon_factors1708 as m08

class Aud(unittest.TestCase):
    def test_audpin_behavior_1707(self):
        got = m07.terms([('a',10,3),('a',2,-5),('b',4,0)])
        self.assertEqual(got['terms'], (('a',12,20),('b',4,0)))
        self.assertEqual(got['total'], 20)
        self.assertEqual(got['negative'], ())
    def test_audpin_signed_1707(self):
        # negative factors allowed; negative totals listed
        got = m07.terms([('a',3,-4)])
        self.assertEqual(got['terms'], (('a',3,-12),))
        self.assertEqual(got['negative'], ('a',))
        self.assertEqual(got['total'], -12)
        with self.assertRaises(ValueError): m07.terms([('a',1,-1000001)])
    def test_audpin_behavior_1708(self):
        got = m08.footprint([('a',10,3,2),('b',0,5,1)])
        self.assertEqual(got['footprint'], (('a',F(15)),('b',F(0))))
        self.assertEqual(got['total'], F(15))
        self.assertEqual(got['positive'], ('a',))
    def test_audpin_refusals_1708(self):
        with self.assertRaises(ValueError): m08.footprint([('a',1,1,0)])
        with self.assertRaises(ValueError): m08.footprint([('a',1,1,1),('a',1,1,1)])
        with self.assertRaises(ValueError): m08.footprint([])
    def test_audpin_extra_1708(self):
        # numerator 0 -> zero footprint, not positive
        self.assertEqual(m08.footprint([('a',5,0,3)])['footprint'], (('a',F(0)),))

if __name__ == '__main__': unittest.main()
