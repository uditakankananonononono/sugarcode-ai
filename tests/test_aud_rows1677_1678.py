import sys, unittest
from fractions import Fraction as F
sys.path.insert(0, 'src'); sys.path.insert(0, 'tests')
from sugarcode.extra_doc import fisheries_effort1677 as m77, forest_area1678 as m78

class Aud(unittest.TestCase):
    def test_audpin_behavior_1677(self):
        got = m77.effort([('a',10,4),('a',2,2),('b',0,1)])
        self.assertEqual(got['effort'], (('a',12,6,F(2)),('b',0,1,F(0))))
        self.assertEqual(got['total_catch'], 12)
        self.assertEqual(got['total_effort'], 7)
        self.assertEqual(got['overall_ratio'], F(12,7))
    def test_audpin_refusals_1677(self):
        with self.assertRaises(ValueError): m77.effort([('a',1,0)])
        with self.assertRaises(ValueError): m77.effort([('a',-1,1)])
        with self.assertRaises(ValueError): m77.effort([])
    def test_audpin_behavior_1678(self):
        got = m78.areas([('a',10,4,9),('b',0,0,0)])
        self.assertEqual(got['areas'], (('a',5,-5),('b',0,0)))
        self.assertEqual(got['negative'], ())
        self.assertEqual(got['total_final'], 5)
        self.assertEqual(got['total_change'], -5)
    def test_audpin_negative_1678(self):
        got = m78.areas([('a',2,0,5)])
        self.assertEqual(got['areas'], (('a',-3,-5),))
        self.assertEqual(got['negative'], ('a',))
        self.assertEqual(got['total_final'], -3)
    def test_audpin_extra_1678(self):
        with self.assertRaises(ValueError): m78.areas([('a',1,1,1),('a',2,2,2)])
        self.assertEqual(m78.areas([('a',3,0,3)])['negative'], ())

if __name__ == '__main__': unittest.main()
