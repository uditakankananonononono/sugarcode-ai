import sys, unittest
from fractions import Fraction as F
sys.path.insert(0, 'src'); sys.path.insert(0, 'tests')
from sugarcode.extra_doc import risk_products1695 as m95, exposure_integral1696 as m96

class Aud(unittest.TestCase):
    def test_audpin_behavior_1695(self):
        got = m95.scores([('a',1,2,10),('b',1,1,3)], 4)
        self.assertEqual(got['scores'], (('a',F(5)),('b',F(3))))
        self.assertEqual(got['above'], ('a',))
        self.assertEqual(got['total_score'], F(8))
    def test_audpin_refusals_1695(self):
        with self.assertRaises(ValueError): m95.scores([('a',2,1,1)], 1)
        with self.assertRaises(ValueError): m95.scores([('a',1,0,1)], 1)
        with self.assertRaises(ValueError): m95.scores([('a',1,1,1)], -1)
        with self.assertRaises(ValueError): m95.scores([('a',1,1,1),('a',1,1,1)], 1)
        self.assertEqual(m95.scores([('a',1,2,8)], 4)['above'], ())  # equal not above
    def test_audpin_behavior_1696(self):
        got = m96.integrals([('a',10,2),('a',4,1),('b',0,3)])
        self.assertEqual(got['integrals'], (('a',3,24,F(8)),('b',3,0,F(0))))
        self.assertEqual(got['total_integral'], 24)
        self.assertEqual(got['total_duration'], 6)
    def test_audpin_refusals_1696(self):
        with self.assertRaises(ValueError): m96.integrals([('a',1,0)])
        with self.assertRaises(ValueError): m96.integrals([])
    def test_audpin_aggregation_1696(self):
        got = m96.integrals([('x',6,2),('x',3,2)])
        self.assertEqual(got['integrals'], (('x',4,18,F(9,2)),))

if __name__ == '__main__': unittest.main()
