import sys, unittest
sys.path.insert(0, 'src')
from sugarcode.extra_doc import jit_arrivals as ja

class Aud(unittest.TestCase):
    def test_audpin_scope_460(self):
        got = ja.arrivals(((0, 5), (5, 5), (9, 4)))
        self.assertEqual(got['jit_arrivals_validated'], False)
        self.assertEqual(got['not_claimed'], ('inventory_optimization', 'real_schedule', 'delivery_reliability'))
    def test_audpin_behavior_460(self):
        got = ja.arrivals(((0, 5), (5, 5), (9, 4)))
        self.assertEqual(got['early_positions'], (0,))
        self.assertEqual(got['late_positions'], (2,))
        self.assertEqual(got['on_time_count'], 1)
        self.assertEqual(got['storage_slots'], 5)
        self.assertEqual(got['delay_slots'], 5)
    def test_audpin_all_ontime_460(self):
        got = ja.arrivals(((3, 3), (0, 0)))
        self.assertEqual(got['on_time_count'], 2)
        self.assertEqual(got['storage_slots'], 0)
        self.assertEqual(got['delay_slots'], 0)
        self.assertEqual(got['early_positions'], ())
        self.assertEqual(got['late_positions'], ())
    def test_audpin_refusals_460(self):
        with self.assertRaises(ValueError): ja.arrivals(())
        with self.assertRaises(ValueError): ja.arrivals(((1, 1),)*21)
        with self.assertRaises(ValueError): ja.arrivals(((1, 2, 3),))
        with self.assertRaises(ValueError): ja.arrivals(((-1, 0),))
        with self.assertRaises(ValueError): ja.arrivals(((0, 1001),))
    def test_audpin_types_460(self):
        class Items(tuple): pass
        class Number(int): pass
        with self.assertRaises(ValueError): ja.arrivals(Items(((1, 1),)))
        with self.assertRaises(ValueError): ja.arrivals(((Number(1), 1),))
        with self.assertRaises(ValueError): ja.arrivals(((True, 1),))

if __name__ == '__main__': unittest.main()
