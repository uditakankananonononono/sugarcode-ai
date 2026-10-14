import sys, unittest
sys.path.insert(0, 'src')
from sugarcode.extra_doc import demand_recent_mean as dm

class Aud(unittest.TestCase):
    def test_audpin_scope_454(self):
        got = dm.recent_mean((3, 5, 7, 9), 2)
        self.assertEqual(got['demand_recent_mean_validated'], False)
        self.assertEqual(got['not_claimed'], ('predictive_accuracy', 'statistical_model', 'seasonality'))
    def test_audpin_behavior_454(self):
        got = dm.recent_mean((3, 5, 7, 9), 2)
        self.assertEqual(got['mean'], 8)
        self.assertEqual(got['remainder'], 0)
        self.assertEqual(got['window_total'], 16)
        self.assertEqual(got['previous_mean'], 4)
        self.assertEqual(got['change'], 4)
    def test_audpin_remainder_454(self):
        got = dm.recent_mean((1, 2, 2), 2)
        self.assertEqual(got['mean'], 2)
        self.assertEqual(got['remainder'], 0)
        got = dm.recent_mean((0, 1, 2), 2)
        self.assertEqual((got['mean'], got['remainder']), (1, 1))
    def test_audpin_no_previous_454(self):
        got = dm.recent_mean((3, 5, 7), 3)
        self.assertIsNone(got['previous_mean'])
        self.assertIsNone(got['change'])
        # exactly 2*window -> previous available
        self.assertEqual(dm.recent_mean((1, 1, 3, 3), 2)['previous_mean'], 1)
    def test_audpin_refusals_454(self):
        with self.assertRaises(ValueError): dm.recent_mean((1,), 1)
        with self.assertRaises(ValueError): dm.recent_mean((1,)*25, 1)
        with self.assertRaises(ValueError): dm.recent_mean((1, 2), 0)
        with self.assertRaises(ValueError): dm.recent_mean((1, 2, 3), 4)
        with self.assertRaises(ValueError): dm.recent_mean((-1, 2), 1)

if __name__ == '__main__': unittest.main()
