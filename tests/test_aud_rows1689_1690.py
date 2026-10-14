import sys, unittest
sys.path.insert(0, 'src'); sys.path.insert(0, 'tests')
from sugarcode.extra_doc import food_supply1689 as m89, food_transfers1690 as m90

class Aud(unittest.TestCase):
    def test_audpin_behavior_1689(self):
        got = m89.allocations([('a',10,4),('b',3,7)])
        self.assertEqual(got['allocations'], (('a',4,0,6),('b',3,4,0)))
        self.assertEqual(got['total_unmet'], 4)
        self.assertEqual(got['total_unused'], 6)
        self.assertEqual(got['unmet'], ('b',))
    def test_audpin_refusals_1689(self):
        with self.assertRaises(ValueError): m89.allocations([('a',1,1),('a',2,2)])
        with self.assertRaises(ValueError): m89.allocations([])
        # supply==demand: no unmet, no unused
        self.assertEqual(m89.allocations([('a',5,5)])['allocations'], (('a',5,0,0),))
    def test_audpin_behavior_1690(self):
        got = m90.transfers([('a','b',3),('b','a',1)])
        self.assertEqual(got['transfers'], (('a',1,3,-2),('b',3,1,2)))
        self.assertEqual(got['total_transferred'], 4)
        self.assertEqual(got['positive'], ('b',))
    def test_audpin_selftransfer_1690(self):
        got = m90.transfers([('a','a',2)])
        self.assertEqual(got['transfers'], (('a',2,2,0),))
        self.assertEqual(got['positive'], ())
    def test_audpin_refusals_1690(self):
        with self.assertRaises(ValueError): m90.transfers([('a','b',-1)])
        with self.assertRaises(ValueError): m90.transfers([('a','x'*41,1)])
        with self.assertRaises(ValueError): m90.transfers([])

if __name__ == '__main__': unittest.main()
