import sys, unittest
from fractions import Fraction as F
sys.path.insert(0, 'src'); sys.path.insert(0, 'tests')
from sugarcode.extra_doc import emission_changes1663 as m63, atmospheric_transfers1664 as m64

class Aud(unittest.TestCase):
    def test_audpin_behavior_1663(self):
        # ORDER PRESERVED (not sorted), telescoping change
        got = m63.changes([('b',5),('a',9),('c',3)])
        self.assertEqual(got['changes'], (('b',5,None),('a',9,4),('c',3,-6)))
        self.assertEqual(got['increases'], ('a',))
        self.assertEqual(got['total_change'], -2)
        self.assertEqual(got['maximum'], 9)
    def test_audpin_singleton_1663(self):
        self.assertEqual(m63.changes([('x',7)]), {'changes': (('x',7,None),), 'increases': (), 'total_change': 0, 'maximum': 7, 'scope': m63.SCOPE})
        with self.assertRaises(ValueError): m63.changes([('a',1),('a',2)])
    def test_audpin_behavior_1664(self):
        # self-transfer allowed; net and positive labels
        got = m64.transfers([('a','b',3),('b','a',1),('a','a',2)])
        self.assertEqual(got['transfers'], (('a',3,5,-2),('b',3,1,2)))
        self.assertEqual(got['total_transferred'], 6)
        self.assertEqual(got['positive'], ('b',))
    def test_audpin_refusals_1663_1664(self):
        with self.assertRaises(ValueError): m63.changes([])
        with self.assertRaises(ValueError): m64.transfers([('a','b',-1)])
        with self.assertRaises(ValueError): m64.transfers([('a','x'*41,1)])
        with self.assertRaises(ValueError): m64.transfers([('a','b',1.5)])
    def test_audpin_extra_1664(self):
        # zero-quantity transfer counted in total but nets zero
        got = m64.transfers([('a','b',0)])
        self.assertEqual(got['transfers'], (('a',0,0,0),('b',0,0,0)))
        self.assertEqual(got['positive'], ())

if __name__ == '__main__': unittest.main()
