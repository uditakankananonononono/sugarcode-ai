import sys, unittest
from fractions import Fraction as F
sys.path.insert(0, 'src'); sys.path.insert(0, 'tests')
from sugarcode.extra_doc import hydro_solution1687 as m87, urban_yield1688 as m88

class Aud(unittest.TestCase):
    def test_audpin_behavior_1687(self):
        got = m87.fractions([('a',10,4),('b',0,0)])
        self.assertEqual(got['fractions'], (('a',10,4,6,F(2,5)),('b',0,0,0,None)))
        self.assertEqual(got['total_carrier'], 6)
        self.assertEqual(got['solute_fraction'], F(2,5))
    def test_audpin_refusals_1687(self):
        with self.assertRaises(ValueError): m87.fractions([('a',1,2)])
        self.assertIsNone(m87.fractions([('a',0,0)])['solute_fraction'])
    def test_audpin_behavior_1688(self):
        got = m88.area([('a',10,4),('a',2,2),('b',0,1)])
        self.assertEqual(got['area'], (('a',12,6,F(2)),('b',0,1,F(0))))
        self.assertEqual(got['total_harvest'], 12)
        self.assertEqual(got['total_area'], 7)
        self.assertEqual(got['overall_ratio'], F(12,7))
    def test_audpin_refusals_1688(self):
        with self.assertRaises(ValueError): m88.area([('a',1,0)])
        with self.assertRaises(ValueError): m88.area([('a',-1,1)])
        with self.assertRaises(ValueError): m88.area([])
    def test_audpin_aggregation_1688(self):
        got = m88.area([('x',3,2),('x',1,2)])
        self.assertEqual(got['area'], (('x',4,4,F(1)),))

if __name__ == '__main__': unittest.main()
