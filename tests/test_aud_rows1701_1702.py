import sys, unittest
sys.path.insert(0, 'src'); sys.path.insert(0, 'tests')
from sugarcode.extra_doc import stakeholder_grid1701 as m01, policy_net1702 as m02

class Aud(unittest.TestCase):
    def test_audpin_behavior_1701(self):
        got = m01.grid([('a',5,1),('b',3,7),('c',9,9)], 5)
        self.assertEqual(got['grid'], (('a',True,False),('b',False,True),('c',True,True)))
        self.assertEqual(got['counts'], ((False,False,0),(False,True,1),(True,False,1),(True,True,1)))
        self.assertEqual(got['both_high'], ('c',))
    def test_audpin_refusals_1701(self):
        with self.assertRaises(ValueError): m01.grid([('a',1,1),('a',2,2)], 1)
        with self.assertRaises(ValueError): m01.grid([('a',1,1)], -1)
        with self.assertRaises(ValueError): m01.grid([], 1)
        # equal to threshold counts as high
        self.assertEqual(m01.grid([('a',5,5)], 5)['both_high'], ('a',))
    def test_audpin_behavior_1702(self):
        got = m02.net([('a',10,4),('a',1,9),('b',5,5)])
        self.assertEqual(got['net'], (('a',11,13,2),('b',5,5,0)))
        self.assertEqual(got['total_net'], 2)
        self.assertEqual(got['positive'], ('a',))
    def test_audpin_aggregation_1702(self):
        got = m02.net([('x',3,2),('x',1,4)])
        self.assertEqual(got['net'], (('x',4,6,2),))
    def test_audpin_extra_1702(self):
        # negative net not positive
        self.assertEqual(m02.net([('a',5,2)])['positive'], ())
        with self.assertRaises(ValueError): m02.net([('a',-1,1)])

if __name__ == '__main__': unittest.main()
