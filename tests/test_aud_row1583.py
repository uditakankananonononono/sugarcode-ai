import sys, unittest
sys.path.insert(0, 'src')
from sugarcode.extra_doc import finite_convolution as fc

class Aud(unittest.TestCase):
    def test_audpin_scope_1583(self):
        got = fc.convolve((1,2,3), (1,1))
        self.assertEqual(got['finite_convolution_validated'], False)
        self.assertEqual(got['not_claimed'], ('sampling_assumptions','spectral_interpretation','filter_design'))
    def test_audpin_behavior_1583(self):
        got = fc.convolve((1,2,3), (1,1))
        self.assertEqual(got['samples'], (1, 3, 5, 3))
        self.assertEqual(got['output_length'], 4)
    def test_audpin_negatives_1583(self):
        got = fc.convolve((-2, 4), (3, -1, 2))
        self.assertEqual(got['samples'], (-6, 14, -8, 8))
        self.assertEqual(got['output_length'], 4)
    def test_audpin_singleton_1583(self):
        got = fc.convolve((-1000,), (1000,))
        self.assertEqual(got['samples'], (-1000000,))
        self.assertEqual(got['output_length'], 1)
    def test_audpin_refusals_1583(self):
        with self.assertRaises(ValueError): fc.convolve((), (1,))
        with self.assertRaises(ValueError): fc.convolve((0,)*31, (1,))
        with self.assertRaises(ValueError): fc.convolve((1,), (0,)*9)
        with self.assertRaises(ValueError): fc.convolve((1001,), (1,))
        with self.assertRaises(ValueError): fc.convolve((-1001,), (1,))
    def test_audpin_types_1583(self):
        class Items(tuple): pass
        class Number(int): pass
        with self.assertRaises(ValueError): fc.convolve(Items((1,)), (1,))
        with self.assertRaises(ValueError): fc.convolve((Number(1),), (1,))
        with self.assertRaises(ValueError): fc.convolve((True,), (1,))
        with self.assertRaises(ValueError): fc.convolve([1], (1,))

if __name__ == '__main__': unittest.main()
