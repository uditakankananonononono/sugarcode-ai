import sys, unittest
from fractions import Fraction as F
sys.path.insert(0, 'src'); sys.path.insert(0, 'tests')
from sugarcode.extra_doc import biodiversity_counts1673 as m73, conservation_change1674 as m74

class Aud(unittest.TestCase):
    def test_audpin_behavior_1673(self):
        got = m73.diversity([('a',2),('b',0),('a',2)])
        self.assertEqual(got['counts'], (('a',4),('b',0)))
        self.assertEqual(got['total'], 4)
        self.assertEqual(got['richness'], 1)
        self.assertEqual(got['diversity'], F(0))
    def test_audpin_zerototal_1673(self):
        self.assertIsNone(m73.diversity([('a',0)])['diversity'])
        got = m73.diversity([('a',1),('b',1)])
        self.assertEqual(got['diversity'], F(1,2))
        self.assertEqual(got['richness'], 2)
    def test_audpin_behavior_1674(self):
        got = m74.changes([('a',10,4),('b',0,3)])
        self.assertEqual(got['changes'], (('a',-6,F(2,5)),('b',3,None)))
        self.assertEqual(got['declining'], ('a',))
        self.assertEqual(got['total_change'], -3)
    def test_audpin_refusals_1674(self):
        with self.assertRaises(ValueError): m74.changes([('a',1,1),('a',2,2)])
        with self.assertRaises(ValueError): m74.changes([])
        with self.assertRaises(ValueError): m73.diversity([('a',-1)])
    def test_audpin_extra_1674(self):
        # final==initial: not declining, ratio 1
        got = m74.changes([('a',5,5)])
        self.assertEqual(got['changes'], (('a',0,F(1)),))
        self.assertEqual(got['declining'], ())

if __name__ == '__main__': unittest.main()
