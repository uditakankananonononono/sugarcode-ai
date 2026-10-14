import sys, unittest
sys.path.insert(0, 'src')
from sugarcode.extra_doc import chain_capacity as cc

class Aud(unittest.TestCase):
    def test_audpin_scope_452(self):
        got = cc.capacity((5, 3, 9, 3), 4)
        self.assertEqual(got['chain_capacity_validated'], False)
        self.assertEqual(got['not_claimed'], ('network_design', 'transport_plan', 'real_throughput'))
    def test_audpin_behavior_452(self):
        got = cc.capacity((5, 3, 9, 3), 4)
        self.assertEqual(got['bottleneck'], 3)
        self.assertEqual(got['limiting_positions'], (1, 3))
        self.assertEqual(got['shortfall_positions'], (1, 3))
        self.assertEqual(got['all_sufficient'], False)
        self.assertEqual(got['margin'], -1)
    def test_audpin_sufficient_452(self):
        got = cc.capacity((5, 3, 9), 2)
        self.assertEqual(got['shortfall_positions'], ())
        self.assertEqual(got['all_sufficient'], True)
        self.assertEqual(got['margin'], 1)
        # exact equality is sufficient, not a shortfall
        self.assertEqual(cc.capacity((4, 4), 4)['shortfall_positions'], ())
    def test_audpin_refusals_452(self):
        with self.assertRaises(ValueError): cc.capacity((1,), 1)
        with self.assertRaises(ValueError): cc.capacity((1,)*13, 1)
        with self.assertRaises(ValueError): cc.capacity((0, 2), 1)
        with self.assertRaises(ValueError): cc.capacity((True, 2), 1)
        with self.assertRaises(ValueError): cc.capacity((1, 2), 0)
    def test_audpin_subclass_refused_452(self):
        class Items(tuple): pass
        class Number(int): pass
        with self.assertRaises(ValueError): cc.capacity(Items((1, 2)), 1)
        with self.assertRaises(ValueError): cc.capacity((Number(3), 2), 1)

if __name__ == '__main__': unittest.main()
