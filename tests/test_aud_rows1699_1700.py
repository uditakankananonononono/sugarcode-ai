import sys, unittest
from fractions import Fraction as F
sys.path.insert(0, 'src'); sys.path.insert(0, 'tests')
from sugarcode.extra_doc import rights_records1699 as m99, community_counts1700 as m00

class Aud(unittest.TestCase):
    def test_audpin_behavior_1699(self):
        got = m99.records([('a','open',2),('b','disputed',1),('c','recorded',3)])
        self.assertEqual(got['records'], (('a','open',2),('b','disputed',1),('c','recorded',3)))
        self.assertEqual(got['statuses'], (('open',1,2),('recorded',1,3),('disputed',1,1)))
        self.assertEqual(got['disputed'], ('b',))
    def test_audpin_refusals_1699(self):
        with self.assertRaises(ValueError): m99.records([('a','pending',1)])
        with self.assertRaises(ValueError): m99.records([('a','open',1),('a','open',2)])
        with self.assertRaises(ValueError): m99.records([])
        # empty statuses still reported with zeros
        got = m99.records([('a','open',1)])
        self.assertEqual(got['statuses'], (('open',1,1),('recorded',0,0),('disputed',0,0)))
    def test_audpin_behavior_1700(self):
        got = m00.participation([('a',10,4),('b',0,0)])
        self.assertEqual(got['participation'], (('a',10,4,F(2,5)),('b',0,0,None)))
        self.assertEqual(got['invited'], 10)
        self.assertEqual(got['participated'], 4)
        self.assertEqual(got['fraction'], F(2,5))
    def test_audpin_refusals_1700(self):
        with self.assertRaises(ValueError): m00.participation([('a',1,2)])
        self.assertIsNone(m00.participation([('a',0,0)])['fraction'])
    def test_audpin_aggregation_1700(self):
        got = m00.participation([('a',4,1),('a',6,3)])
        self.assertEqual(got['participation'], (('a',10,4,F(2,5)),))

if __name__ == '__main__': unittest.main()
