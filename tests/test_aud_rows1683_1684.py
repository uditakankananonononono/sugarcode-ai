import sys, unittest
from fractions import Fraction as F
sys.path.insert(0, 'src'); sys.path.insert(0, 'tests')
from sugarcode.extra_doc import regenerative_changes1683 as m83, precision_targets1684 as m84

class Aud(unittest.TestCase):
    def test_audpin_behavior_1683(self):
        got = m83.changes([('a',10,14),('b',0,3)])
        self.assertEqual(got['changes'], (('a',4,F(2,5)),('b',3,None)))
        self.assertEqual(got['increased'], ('a','b'))
        self.assertEqual(got['total_change'], 7)
    def test_audpin_refusals_1683(self):
        with self.assertRaises(ValueError): m83.changes([('a',1,1),('a',2,2)])
        with self.assertRaises(ValueError): m83.changes([])
        with self.assertRaises(ValueError): m83.changes([('a',-1,0)])
        self.assertEqual(m83.changes([('a',5,5)])['increased'], ())
    def test_audpin_behavior_1684(self):
        got = m84.adjustments([('a',10,3,5),('b',0,1,1)])
        self.assertEqual(got['adjustments'], (('a',30,50,20),('b',0,0,0)))
        self.assertEqual(got['total_adjustment'], 20)
        self.assertEqual(got['positive'], ('a',))
    def test_audpin_refusals_1684(self):
        with self.assertRaises(ValueError): m84.adjustments([('a',1,1,1),('a',2,2,2)])
        with self.assertRaises(ValueError): m84.adjustments([('a',1,1,1000001)])
        with self.assertRaises(ValueError): m84.adjustments([])
    def test_audpin_extra_1684(self):
        # current==target: zero adjustment, not positive
        self.assertEqual(m84.adjustments([('a',4,3,3)])['positive'], ())
        # negative adjustment allowed
        self.assertEqual(m84.adjustments([('a',2,5,1)])['adjustments'], (('a',10,2,-8),))

if __name__ == '__main__': unittest.main()
