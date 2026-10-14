import sys, unittest
sys.path.insert(0, 'src')
from sugarcode.extra_doc import cart_target_overlap as cto

class Aud(unittest.TestCase):
    def test_audpin_scope_985(self):
        got = cto.overlap((1,2,2,3), (2,4))
        self.assertEqual(got['cart_target_overlap_validated'], False)
        self.assertEqual(got['not_claimed'], ('cart_design','antigen_specificity','clinical_interpretation'))
    def test_audpin_behavior_985(self):
        got = cto.overlap((1,2,2,3), (2,4))
        self.assertEqual(got['shared_count'], 1)
        self.assertEqual(got['missing_count'], 2)
        self.assertEqual(got['extra_count'], 1)
        self.assertEqual(got['all_targets_present'], False)
    def test_audpin_duplicates_once_985(self):
        got = cto.overlap((5,5,5), (5,5))
        self.assertEqual(got['shared_count'], 1)
        self.assertEqual(got['missing_count'], 0)
        self.assertEqual(got['extra_count'], 0)
        self.assertEqual(got['all_targets_present'], True)
    def test_audpin_refusals_985(self):
        with self.assertRaises(ValueError): cto.overlap((), (0,))
        with self.assertRaises(ValueError): cto.overlap((0,)*21, (0,))
        with self.assertRaises(ValueError): cto.overlap((0,), (101,))
        with self.assertRaises(ValueError): cto.overlap((-1,), (0,))
        with self.assertRaises(ValueError): cto.overlap([1], (0,))
    def test_audpin_types_985(self):
        class Items(tuple): pass
        class Number(int): pass
        with self.assertRaises(ValueError): cto.overlap(Items((1,)), (0,))
        with self.assertRaises(ValueError): cto.overlap((Number(1),), (0,))
        with self.assertRaises(ValueError): cto.overlap((True,), (0,))
        with self.assertRaises(ValueError): cto.overlap((1.0,), (0,))

if __name__ == '__main__': unittest.main()
