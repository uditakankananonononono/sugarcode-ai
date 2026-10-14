import sys, unittest
sys.path.insert(0, 'src')
from sugarcode.extra_doc import repetition_runs as rr

class Aud(unittest.TestCase):
    def test_audpin_scope_471(self):
        got = rr.runs((2, 2, 2, 5, 5, 1))
        self.assertEqual(got['repetition_runs_validated'], False)
        self.assertEqual(got['not_claimed'], ('robotic_execution', 'automation_suitability', 'external_effects'))
    def test_audpin_behavior_471(self):
        got = rr.runs((2, 2, 2, 5, 5, 1))
        self.assertEqual(got['starts'], (0, 3, 5))
        self.assertEqual(got['lengths'], (3, 2, 1))
        self.assertEqual(got['repeated_starts'], (0, 3))
        self.assertEqual(got['saved_if_collapsed'], 3)
    def test_audpin_singleton_471(self):
        got = rr.runs((7,))
        self.assertEqual(got['starts'], (0,))
        self.assertEqual(got['lengths'], (1,))
        self.assertEqual(got['repeated_starts'], ())
        self.assertEqual(got['saved_if_collapsed'], 0)
    def test_audpin_all_same_471(self):
        got = rr.runs((100,)*30)
        self.assertEqual(got['starts'], (0,))
        self.assertEqual(got['lengths'], (30,))
        self.assertEqual(got['repeated_starts'], (0,))
        self.assertEqual(got['saved_if_collapsed'], 29)
    def test_audpin_refusals_471(self):
        with self.assertRaises(ValueError): rr.runs(())
        with self.assertRaises(ValueError): rr.runs((0,)*31)
        with self.assertRaises(ValueError): rr.runs((-1,))
        with self.assertRaises(ValueError): rr.runs((101,))
        with self.assertRaises(ValueError): rr.runs((True,))

if __name__ == '__main__': unittest.main()
