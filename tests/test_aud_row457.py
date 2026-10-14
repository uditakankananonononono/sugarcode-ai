import sys, unittest
sys.path.insert(0, 'src')
from sugarcode.extra_doc import tolerance_sample as ts

class Aud(unittest.TestCase):
    def test_audpin_scope_457(self):
        got = ts.inspect((-5, 0, 500, 1000), 0, 500)
        self.assertEqual(got['tolerance_sample_validated'], False)
        self.assertEqual(got['not_claimed'], ('certification', 'sampling_assurance', 'calibration'))
    def test_audpin_behavior_457(self):
        got = ts.inspect((-5, 0, 500, 1000), 0, 500)
        self.assertEqual(got['below_positions'], (0,))
        self.assertEqual(got['above_positions'], (3,))
        self.assertEqual(got['accepted_count'], 2)
        self.assertEqual(got['all_in_bounds'], False)
    def test_audpin_inclusive_bounds_457(self):
        # values exactly on the bounds are accepted
        got = ts.inspect((0, 500), 0, 500)
        self.assertEqual(got['accepted_count'], 2)
        self.assertEqual(got['all_in_bounds'], True)
        # negative window
        got = ts.inspect((-500,), -600, -400)
        self.assertEqual(got['all_in_bounds'], True)
    def test_audpin_refusals_457(self):
        with self.assertRaises(ValueError): ts.inspect((), 0, 1)
        with self.assertRaises(ValueError): ts.inspect((1,)*31, 0, 1)
        with self.assertRaises(ValueError): ts.inspect((1,), 5, 4)
        with self.assertRaises(ValueError): ts.inspect((-1001,), 0, 1)
        with self.assertRaises(ValueError): ts.inspect((1,), 0, 1001)
    def test_audpin_types_457(self):
        class Items(tuple): pass
        class Number(int): pass
        with self.assertRaises(ValueError): ts.inspect(Items((1,)), 0, 1)
        with self.assertRaises(ValueError): ts.inspect((True,), 0, 1)
        with self.assertRaises(ValueError): ts.inspect((1,), Number(0), 1)

if __name__ == '__main__': unittest.main()
