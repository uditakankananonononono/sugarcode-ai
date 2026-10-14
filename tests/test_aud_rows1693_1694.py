import sys, unittest
from fractions import Fraction as F
sys.path.insert(0, 'src'); sys.path.insert(0, 'tests')
from sugarcode.extra_doc import environment_bounds1693 as m93, toxicology_ratio1694 as m94

class Aud(unittest.TestCase):
    def test_audpin_behavior_1693(self):
        got = m93.compare([('a',5,3,7),('b',1,2,2),('c',9,3,7)])
        self.assertEqual(got['comparisons'], (('a','within',2,2),('b','below',-1,1),('c','above',6,-2)))
        self.assertEqual(got['outside'], ('b','c'))
        self.assertEqual(got['within_count'], 1)
    def test_audpin_inclusive_1693(self):
        # boundary values are within
        got = m93.compare([('a',3,3,7),('b',7,3,7)])
        self.assertEqual(got['within_count'], 2)
        self.assertEqual(got['outside'], ())
        with self.assertRaises(ValueError): m93.compare([('a',1,2,1)])
        with self.assertRaises(ValueError): m93.compare([('a',1,1,1),('a',2,2,2)])
    def test_audpin_behavior_1694(self):
        got = m94.exceedances([('a',10,4),('b',3,3)])
        self.assertEqual(got['exceedances'], (('a',F(5,2),6),('b',F(1),0)))
        self.assertEqual(got['above'], ('a',))
        self.assertEqual(got['total_excess'], 6)
    def test_audpin_refusals_1694(self):
        with self.assertRaises(ValueError): m94.exceedances([('a',1,0)])
        with self.assertRaises(ValueError): m94.exceedances([])
    def test_audpin_extra_1694(self):
        self.assertEqual(m94.exceedances([('a',5,5)])['above'], ())
        self.assertEqual(m94.exceedances([('a',0,7)])['exceedances'], (('a',F(0),0),))

if __name__ == '__main__': unittest.main()
