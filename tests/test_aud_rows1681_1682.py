import sys, unittest
sys.path.insert(0, 'src'); sys.path.insert(0, 'tests')
from sugarcode.extra_doc import organic_input1681 as m81, perma_transfers1682 as m82

class Aud(unittest.TestCase):
    def test_audpin_behavior_1681(self):
        got = m81.inputs([('a',10,3),('a',2,5),('b',4,0)])
        self.assertEqual(got['inputs'], (('a',12,40),('b',4,0)))
        self.assertEqual(got['total_input'], 40)
        self.assertEqual(got['positive'], ('a',))
    def test_audpin_aggregation_1681(self):
        got = m81.inputs([('x',3,2),('x',1,4)])
        self.assertEqual(got['inputs'], (('x',4,10),))
        self.assertEqual(m81.inputs([('a',5,0)])['positive'], ())
    def test_audpin_behavior_1682(self):
        got = m82.transfers([('a','b',3),('b','a',1),('a','a',2)])
        self.assertEqual(got['transfers'], (('a',3,5,-2),('b',3,1,2)))
        self.assertEqual(got['total_transferred'], 6)
        self.assertEqual(got['positive'], ('b',))
    def test_audpin_refusals_1682(self):
        with self.assertRaises(ValueError): m82.transfers([('a','b',-1)])
        with self.assertRaises(ValueError): m82.transfers([('a','x'*41,1)])
        with self.assertRaises(ValueError): m82.transfers([('a','b',1.5)])
        with self.assertRaises(ValueError): m82.transfers([])
    def test_audpin_extra_1682(self):
        got = m82.transfers([('a','b',0)])
        self.assertEqual(got['transfers'], (('a',0,0,0),('b',0,0,0)))
        self.assertEqual(got['positive'], ())

if __name__ == '__main__': unittest.main()
