import sys, unittest
from fractions import Fraction as F
sys.path.insert(0, 'src'); sys.path.insert(0, 'tests')
from sugarcode.extra_doc import water_components1709 as m09, ecological_area1710 as m10

class Aud(unittest.TestCase):
    def test_audpin_behavior_1709(self):
        got = m09.components([('a',1,2,3),('a',1,1,1),('b',0,0,0)])
        self.assertEqual(got['components'], (('a',2,3,4,9),('b',0,0,0,0)))
        self.assertEqual(got['totals'], (2,3,4))
        self.assertEqual(got['total'], 9)
    def test_audpin_aggregation_1709(self):
        got = m09.components([('x',1,0,0),('x',0,2,0),('x',0,0,3)])
        self.assertEqual(got['components'], (('x',1,2,3,6),))
        with self.assertRaises(ValueError): m09.components([])
    def test_audpin_behavior_1710(self):
        got = m10.areas([('a',10,4),('b',0,3)])
        self.assertEqual(got['areas'], (('a',F(5,2)),('b',F(0))))
        self.assertEqual(got['total_area'], F(5,2))
        self.assertEqual(got['zero'], ('b',))
    def test_audpin_refusals_1710(self):
        with self.assertRaises(ValueError): m10.areas([('a',1,0)])
        with self.assertRaises(ValueError): m10.areas([('a',1,1),('a',2,2)])
        with self.assertRaises(ValueError): m10.areas([])
    def test_audpin_extra_1710(self):
        # fractional total
        self.assertEqual(m10.areas([('a',1,2),('b',1,3)])['total_area'], F(5,6))

if __name__ == '__main__': unittest.main()
