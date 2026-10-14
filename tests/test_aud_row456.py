import sys, unittest
sys.path.insert(0, 'src')
from sugarcode.extra_doc import production_batches as pb

class Aud(unittest.TestCase):
    def test_audpin_scope_456(self):
        got = pb.batches(25, 10, 3)
        self.assertEqual(got['production_batches_validated'], False)
        self.assertEqual(got['not_claimed'], ('machine_assignment', 'real_schedule', 'feasibility'))
    def test_audpin_behavior_456(self):
        got = pb.batches(25, 10, 3)
        self.assertEqual(got['sizes'], (10, 10, 5))
        self.assertEqual(got['finish_slots'], (3, 6, 9))
        self.assertEqual(got['batch_count'], 3)
        self.assertEqual(got['total_duration'], 9)
    def test_audpin_exact_split_456(self):
        got = pb.batches(30, 10, 5)
        self.assertEqual(got['sizes'], (10, 10, 10))
        self.assertEqual(got['finish_slots'], (5, 10, 15))
        # single partial batch
        got = pb.batches(7, 10, 2)
        self.assertEqual(got['sizes'], (7,))
        self.assertEqual(got['finish_slots'], (2,))
    def test_audpin_refusals_456(self):
        with self.assertRaises(ValueError): pb.batches(0, 1, 1)
        with self.assertRaises(ValueError): pb.batches(10001, 1, 1)
        with self.assertRaises(ValueError): pb.batches(1, 0, 1)
        with self.assertRaises(ValueError): pb.batches(1, 1001, 1)
        with self.assertRaises(ValueError): pb.batches(1, 1, 101)
        with self.assertRaises(ValueError): pb.batches(True, 1, 1)
    def test_audpin_bounds_ok_456(self):
        got = pb.batches(10000, 1000, 100)
        self.assertEqual(got['batch_count'], 10)
        self.assertEqual(got['total_duration'], 1000)

if __name__ == '__main__': unittest.main()
