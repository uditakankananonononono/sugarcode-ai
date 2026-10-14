import sys, unittest
from fractions import Fraction as F
sys.path.insert(0, 'src'); sys.path.insert(0, 'tests')
from sugarcode.extra_doc import cleaner_intensity1713 as m13, green_mass1714 as m14

class Aud(unittest.TestCase):
    def test_audpin_behavior_1713(self):
        got = m13.intensity([('a',10,4),('a',2,2),('b',0,1)])
        self.assertEqual(got['intensity'], (('a',12,6,F(2)),('b',0,1,F(0))))
        self.assertEqual(got['resource'], 12)
        self.assertEqual(got['output'], 7)
        self.assertEqual(got['aggregate_intensity'], F(12,7))
    def test_audpin_refusals_1713(self):
        with self.assertRaises(ValueError): m13.intensity([('a',1,0)])
        with self.assertRaises(ValueError): m13.intensity([])
    def test_audpin_behavior_1714(self):
        got = m14.masses([('a',10,4),('b',5,5)])
        self.assertEqual(got['masses'], (('a',6,F(3,2)),('b',0,F(0))))
        self.assertEqual(got['total_waste'], 6)
        self.assertEqual(got['aggregate_ratio'], F(2,3))
    def test_audpin_refusals_1714(self):
        with self.assertRaises(ValueError): m14.masses([('a',1,0)])
        with self.assertRaises(ValueError): m14.masses([('a',1,2)])
        with self.assertRaises(ValueError): m14.masses([('a',1,1),('a',2,2)])
    def test_audpin_extra_1714(self):
        # input==product: zero waste
        got = m14.masses([('a',7,7)])
        self.assertEqual(got['masses'], (('a',0,F(0)),))
        self.assertEqual(got['aggregate_ratio'], F(0))

if __name__ == '__main__': unittest.main()
