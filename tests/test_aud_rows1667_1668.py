import sys, unittest
from fractions import Fraction as F
sys.path.insert(0, 'src'); sys.path.insert(0, 'tests')
from sugarcode.extra_doc import soil_removed1667 as m67, land_exceedance1668 as m68

class Aud(unittest.TestCase):
    def test_audpin_behavior_1667(self):
        got = m67.remaining([('a',10,4),('b',5,5)])
        self.assertEqual(got['remaining'], (('a',10,4,6,F(2,5)),('b',5,5,0,F(1))))
        self.assertEqual(got['total_residual'], 6)
        self.assertEqual(got['removal_fraction'], F(3,5))
    def test_audpin_zeroinit_1667(self):
        got = m67.remaining([('a',0,0)])
        self.assertEqual(got['remaining'], (('a',0,0,0,None),))
        self.assertIsNone(got['removal_fraction'])
        with self.assertRaises(ValueError): m67.remaining([('a',1,2)])
    def test_audpin_behavior_1668(self):
        got = m68.exceedances([('a',10,4),('b',3,3)])
        self.assertEqual(got['exceedances'], (('a',F(5,2),6),('b',F(1),0)))
        self.assertEqual(got['above'], ('a',))
        self.assertEqual(got['total_excess'], 6)
    def test_audpin_refusals_1668(self):
        with self.assertRaises(ValueError): m68.exceedances([('a',1,0)])
        with self.assertRaises(ValueError): m68.exceedances([('a',1,1),('a',2,2)])
        with self.assertRaises(ValueError): m68.exceedances([])
    def test_audpin_extra_1668(self):
        # value==limit: ratio 1 not above, excess 0
        self.assertEqual(m68.exceedances([('a',5,5)])['above'], ())
        # value0: excess 0
        self.assertEqual(m68.exceedances([('a',0,7)])['exceedances'], (('a',F(0),0),))

if __name__ == '__main__': unittest.main()
