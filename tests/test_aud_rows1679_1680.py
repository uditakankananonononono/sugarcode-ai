import sys, unittest
from fractions import Fraction as F
sys.path.insert(0, 'src'); sys.path.insert(0, 'tests')
from sugarcode.extra_doc import agro_categories1679 as m79, agriculture_inputs1680 as m80

class Aud(unittest.TestCase):
    def test_audpin_behavior_1679(self):
        got = m79.diversity([('a',2),('b',0),('a',2)])
        self.assertEqual(got['counts'], (('a',4),('b',0)))
        self.assertEqual(got['total'], 4)
        self.assertEqual(got['richness'], 1)
        self.assertEqual(got['diversity'], F(0))
    def test_audpin_zerototal_1679(self):
        self.assertIsNone(m79.diversity([('a',0)])['diversity'])
        got = m79.diversity([('a',1),('b',1)])
        self.assertEqual(got['diversity'], F(1,2))
        self.assertEqual(got['richness'], 2)
    def test_audpin_behavior_1680(self):
        got = m80.remaining([('a',10,4),('b',0,0)])
        self.assertEqual(got['remaining'], (('a',10,4,6,F(2,5)),('b',0,0,0,None)))
        self.assertEqual(got['total_residual'], 6)
        self.assertEqual(got['removal_fraction'], F(2,5))
    def test_audpin_refusals_1680(self):
        with self.assertRaises(ValueError): m80.remaining([('a',1,2)])
        with self.assertRaises(ValueError): m80.remaining([])
        with self.assertRaises(ValueError): m79.diversity([('a',-1)])
    def test_audpin_aggregation_1680(self):
        got = m80.remaining([('a',4,1),('a',6,3)])
        self.assertEqual(got['remaining'], (('a',10,4,6,F(2,5)),))
        self.assertIsNone(m80.remaining([('a',0,0)])['removal_fraction'])

if __name__ == '__main__': unittest.main()
