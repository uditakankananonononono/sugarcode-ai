import sys, unittest
sys.path.insert(0, 'src')
from sugarcode.extra_doc import defect_opportunities as do

class Aud(unittest.TestCase):
    def test_audpin_scope_458(self):
        got = do.defects(((3, 100), (0, 50)), 50000)
        self.assertEqual(got['defect_opportunities_validated'], False)
        self.assertEqual(got['not_claimed'], ('sigma_level', 'process_capability', 'defect_reduction'))
    def test_audpin_behavior_458(self):
        got = do.defects(((3, 100), (0, 50)), 50000)
        self.assertEqual(got['defects'], 3)
        self.assertEqual(got['opportunities'], 150)
        self.assertEqual(got['ppm'], 20000)
        self.assertEqual(got['within_limit'], True)
    def test_audpin_flooring_458(self):
        got = do.defects(((1, 3),), 333333)
        self.assertEqual(got['ppm'], 333333)
        self.assertEqual(got['within_limit'], False)
        # exact-boundary within_limit: ppm_limit*opp == numerator
        self.assertEqual(do.defects(((2, 3),), 666666)['within_limit'], False)
        self.assertEqual(do.defects(((2, 3),), 666667)['within_limit'], True)
        self.assertEqual(do.defects(((1, 1),), 1000000)['within_limit'], True)
    def test_audpin_zero_defects_458(self):
        got = do.defects(((0, 5),), 0)
        self.assertEqual(got['ppm'], 0)
        self.assertEqual(got['within_limit'], True)
    def test_audpin_refusals_458(self):
        with self.assertRaises(ValueError): do.defects((), 0)
        with self.assertRaises(ValueError): do.defects(((1, 2, 3),), 0)
        with self.assertRaises(ValueError): do.defects(((1, 0),), 0)
        with self.assertRaises(ValueError): do.defects(((2, 1),), 0)
        with self.assertRaises(ValueError): do.defects(((0, 1),), 1000001)

if __name__ == '__main__': unittest.main()
