import sys, unittest
sys.path.insert(0, 'src')
from sugarcode.extra_doc import valuation_multiple as vm

class Aud(unittest.TestCase):
    def test_audpin_scope_501(self):
        got = vm.values(1000, (3,1,8,8))
        self.assertEqual(got['valuation_multiple_validated'], False)
        self.assertEqual(got['not_claimed'], ('fair_value','market_evidence','investment_advice'))
    def test_audpin_behavior_501(self):
        got = vm.values(1000, (3,1,8,8))
        self.assertEqual(got['scenarios'], (3000, 1000, 8000, 8000))
        self.assertEqual(got['low'], 1000)
        self.assertEqual(got['high'], 8000)
        self.assertEqual(got['spread'], 7000)
    def test_audpin_zero_metric_501(self):
        got = vm.values(0, (1, 100))
        self.assertEqual(got['scenarios'], (0, 0))
        self.assertEqual(got['low'], 0)
        self.assertEqual(got['high'], 0)
        self.assertEqual(got['spread'], 0)
    def test_audpin_refusals_501(self):
        with self.assertRaises(ValueError): vm.values(0, ())
        with self.assertRaises(ValueError): vm.values(0, (1,)*13)
        with self.assertRaises(ValueError): vm.values(0, (0,))
        with self.assertRaises(ValueError): vm.values(0, (101,))
        with self.assertRaises(ValueError): vm.values(-1, (1,))
        with self.assertRaises(ValueError): vm.values(1000001, (1,))
    def test_audpin_types_501(self):
        class Items(tuple): pass
        class Number(int): pass
        with self.assertRaises(ValueError): vm.values(0, Items((1,)))
        with self.assertRaises(ValueError): vm.values(Number(1), (1,))
        with self.assertRaises(ValueError): vm.values(0, (Number(1),))
        with self.assertRaises(ValueError): vm.values(True, (1,))
        with self.assertRaises(ValueError): vm.values(0, (True,))

if __name__ == '__main__': unittest.main()
