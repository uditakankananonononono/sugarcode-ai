import sys, unittest
sys.path.insert(0, 'src'); sys.path.insert(0, 'tests')
from sugarcode.extra_doc import impact_products1705 as m05, strategic_weights1706 as m06

class Aud(unittest.TestCase):
    def test_audpin_behavior_1705(self):
        got = m05.impacts([('a',2,3,4),('b',0,5,5)])
        self.assertEqual(got['impacts'], (('a',24),('b',0)))
        self.assertEqual(got['total'], 24)
        self.assertEqual(got['zero'], ('b',))
    def test_audpin_refusals_1705(self):
        with self.assertRaises(ValueError): m05.impacts([('a',1,1,1),('a',2,2,2)])
        with self.assertRaises(ValueError): m05.impacts([('a',-1,1,1)])
        with self.assertRaises(ValueError): m05.impacts([])
    def test_audpin_behavior_1706(self):
        got = m06.scores([('a','x',2,3),('a','y',1,1),('b','x',4,5)])
        self.assertEqual(got['terms'], (('a','x',6),('a','y',1),('b','x',20)))
        self.assertEqual(got['totals'], (('a',7),('b',20)))
    def test_audpin_refusals_1706(self):
        with self.assertRaises(ValueError): m06.scores([('a','x',1,1),('a','x',2,2)])
        with self.assertRaises(ValueError): m06.scores([('a',True,1,1)])
        with self.assertRaises(ValueError): m06.scores([('a','x'*41,1,1)])
    def test_audpin_extra_1706(self):
        # same criterion under different alternatives OK
        got = m06.scores([('a','x',1,1),('b','x',1,1)])
        self.assertEqual(got['totals'], (('a',1),('b',1)))

if __name__ == '__main__': unittest.main()
