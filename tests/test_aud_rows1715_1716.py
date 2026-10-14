import sys, unittest
from fractions import Fraction as F
sys.path.insert(0, 'src'); sys.path.insert(0, 'tests')
from sugarcode.extra_doc import green_engineering1715 as m15, design_targets1716 as m16

class Aud(unittest.TestCase):
    def test_audpin_behavior_1715(self):
        got = m15.changes([('a',10,14),('b',0,3)])
        self.assertEqual(got['changes'], (('a',4,F(2,5)),('b',3,None)))
        self.assertEqual(got['increased'], ('a','b'))
        self.assertEqual(got['total_change'], 7)
    def test_audpin_refusals_1715(self):
        with self.assertRaises(ValueError): m15.changes([('a',1,1),('a',2,2)])
        with self.assertRaises(ValueError): m15.changes([])
        self.assertEqual(m15.changes([('a',5,5)])['increased'], ())
    def test_audpin_behavior_1716(self):
        got = m16.adjustments([('a',10,3,5),('b',0,1,1)])
        self.assertEqual(got['adjustments'], (('a',30,50,20),('b',0,0,0)))
        self.assertEqual(got['total_adjustment'], 20)
        self.assertEqual(got['positive'], ('a',))
    def test_audpin_refusals_1716(self):
        with self.assertRaises(ValueError): m16.adjustments([('a',1,1,1),('a',2,2,2)])
        with self.assertRaises(ValueError): m16.adjustments([])
    def test_audpin_extra_1716(self):
        self.assertEqual(m16.adjustments([('a',4,3,3)])['positive'], ())
        self.assertEqual(m16.adjustments([('a',2,5,1)])['adjustments'], (('a',10,2,-8),))

if __name__ == '__main__': unittest.main()
