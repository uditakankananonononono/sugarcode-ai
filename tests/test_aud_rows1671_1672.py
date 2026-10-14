import sys, unittest
from fractions import Fraction as F
sys.path.insert(0, 'src'); sys.path.insert(0, 'tests')
from sugarcode.extra_doc import bio_fraction1671 as m71, ecosystem_value1672 as m72

class Aud(unittest.TestCase):
    def test_audpin_behavior_1671(self):
        got = m71.remaining([('a',1,2),('b',1,4)], 16)
        self.assertEqual(got['remaining'], (('a',F(8),F(-8)),('b',F(2),F(-6))))
        self.assertEqual(got['final'], F(2))
        self.assertEqual(got['total_change'], F(-14))
    def test_audpin_empty_1671(self):
        got = m71.remaining([], 7)
        self.assertEqual(got, {'remaining': (), 'final': F(7), 'total_change': F(0), 'scope': m71.SCOPE})
        with self.assertRaises(ValueError): m71.remaining([('a',2,1)], 4)
        with self.assertRaises(ValueError): m71.remaining([('a',1,2),('a',1,2)], 4)
        with self.assertRaises(ValueError): m71.remaining([], -1)
    def test_audpin_behavior_1672(self):
        got = m72.values([('a',10,3),('a',2,5),('b',4,0)])
        self.assertEqual(got['values'], (('a',12,40),('b',4,0)))
        self.assertEqual(got['total_value'], 40)
        self.assertEqual(got['zero_value'], ('b',))
    def test_audpin_aggregation_1672(self):
        got = m72.values([('x',3,2),('x',1,4)])
        self.assertEqual(got['values'], (('x',4,10),))
    def test_audpin_extra_1671_1672(self):
        # 1671 fraction 1: no change
        self.assertEqual(m71.remaining([('a',1,1)], 9)['final'], F(9))
        # 1672 area 0 -> zero value
        self.assertEqual(m72.values([('a',0,5)])['zero_value'], ('a',))

if __name__ == '__main__': unittest.main()
