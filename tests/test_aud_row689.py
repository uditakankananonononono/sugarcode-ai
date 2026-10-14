import sys, unittest
sys.path.insert(0, 'src')
from sugarcode.extra_doc import refactor_trace as rt

class Aud(unittest.TestCase):
    def test_audpin_scope_689(self):
        got = rt.compare((1,2,3), (1,4))
        self.assertEqual(got['refactor_trace_validated'], False)
        self.assertEqual(got['not_claimed'], ('behavior_equivalence','code_transformation','quality_improvement'))
    def test_audpin_behavior_689(self):
        got = rt.compare((1,2,3), (1,4))
        self.assertEqual(got['difference_positions'], (1, 2))
        self.assertEqual(got['first_difference'], 1)
        self.assertEqual(got['same_trace'], False)
        self.assertEqual(got['length_change'], -1)
    def test_audpin_empty_689(self):
        got = rt.compare((), ())
        self.assertEqual(got['difference_positions'], ())
        self.assertEqual(got['first_difference'], None)
        self.assertEqual(got['same_trace'], True)
        self.assertEqual(got['length_change'], 0)
    def test_audpin_length_only_689(self):
        got = rt.compare((1,2), (1,2,3,4))
        self.assertEqual(got['difference_positions'], (2, 3))
        self.assertEqual(got['first_difference'], 2)
        self.assertEqual(got['length_change'], 2)
    def test_audpin_refusals_689(self):
        with self.assertRaises(ValueError): rt.compare((0,)*31, ())
        with self.assertRaises(ValueError): rt.compare((), (0,)*31)
        with self.assertRaises(ValueError): rt.compare((1001,), ())
        with self.assertRaises(ValueError): rt.compare((-1001,), ())
        with self.assertRaises(ValueError): rt.compare([1], ())
    def test_audpin_types_689(self):
        class Items(tuple): pass
        class Number(int): pass
        with self.assertRaises(ValueError): rt.compare(Items((1,)), ())
        with self.assertRaises(ValueError): rt.compare((Number(1),), ())
        with self.assertRaises(ValueError): rt.compare((True,), ())
        with self.assertRaises(ValueError): rt.compare((1.0,), ())

if __name__ == '__main__': unittest.main()
