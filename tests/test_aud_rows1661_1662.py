import sys, unittest
from fractions import Fraction as F
sys.path.insert(0, 'src'); sys.path.insert(0, 'tests')
from sugarcode.extra_doc import air_weighted1661 as m61, pollution_stages1662 as m62

class Aud(unittest.TestCase):
    def test_audpin_behavior_1661(self):
        # aggregating labels; sorted; overall totals
        got = m61.means([('b',0,3),('a',10,2),('a',4,1)])
        self.assertEqual(got['means'], (('a',3,F(8)),('b',3,F(0))))
        self.assertEqual(got['duration'], 6)
        self.assertEqual(got['overall_mean'], F(4))
    def test_audpin_empty_1661(self):
        with self.assertRaises(ValueError): m61.means([])
        with self.assertRaises(ValueError): m61.means([('a',1,0)])  # duration 0
    def test_audpin_behavior_1662(self):
        got = m62.stages([('a',1,2),('b',1,4)], 16)
        self.assertEqual(got['stages'], (('a',F(8),F(8)),('b',F(6),F(2))))
        self.assertEqual(got['final'], F(6))
        self.assertEqual(got['total_removed'], 10)
    def test_audpin_empty_1662(self):
        got = m62.stages([], 7)
        self.assertEqual(got, {'stages': (), 'final': F(7), 'total_removed': 0, 'scope': m62.SCOPE})
        with self.assertRaises(ValueError): m62.stages([('a',2,1)], 4)  # num>den
        with self.assertRaises(ValueError): m62.stages([('a',1,2),('a',1,2)], 4)  # dup label
    def test_audpin_extra_1661_1662(self):
        # 1661 full-volume aggregation: value0 duration allowed
        self.assertEqual(m61.means([('a',0,5)])['overall_mean'], F(0))
        # 1662 zero removal: fraction 0 leaves residual
        self.assertEqual(m62.stages([('a',0,3)], 9)['final'], F(9))

if __name__ == '__main__': unittest.main()
