import sys, unittest
sys.path.insert(0, 'src')
from sugarcode.extra_doc import vendor_shortlist as vs

class Aud(unittest.TestCase):
    def test_audpin_scope_451(self):
        got = vs.shortlist((10, 20), 15)
        self.assertEqual(got['vendor_shortlist_validated'], False)
        self.assertEqual(got['not_claimed'], ('score_validity', 'supplier_quality', 'selection_advice'))
    def test_audpin_behavior_451(self):
        got = vs.shortlist((5, 90, 90, 10), 50)
        self.assertEqual(got['qualified_positions'], (1, 2))
        self.assertEqual(got['qualified_count'], 2)
        self.assertEqual(got['any_qualified'], True)
        self.assertEqual(got['best_score'], 90)
        self.assertEqual(got['best_positions'], (1, 2))
    def test_audpin_ties_and_none_451(self):
        got = vs.shortlist((7, 7, 7), 8)
        self.assertEqual(got['qualified_positions'], ())
        self.assertEqual(got['any_qualified'], False)
        self.assertEqual(got['best_positions'], (0, 1, 2))
        self.assertEqual(got['best_score'], 7)
    def test_audpin_threshold_edge_451(self):
        # score == minimum qualifies
        self.assertEqual(vs.shortlist((50, 49), 50)['qualified_positions'], (0,))
        self.assertEqual(vs.shortlist((0, 100), 100)['best_positions'], (1,))
    def test_audpin_refusals_451(self):
        class Number(int): pass
        with self.assertRaises(ValueError): vs.shortlist((1,), 0)
        with self.assertRaises(ValueError): vs.shortlist((1,)*16, 0)
        with self.assertRaises(ValueError): vs.shortlist((True, 1), 0)
        with self.assertRaises(ValueError): vs.shortlist((1, 2), Number(5))
        with self.assertRaises(ValueError): vs.shortlist((1, 2), 101)

if __name__ == '__main__': unittest.main()
