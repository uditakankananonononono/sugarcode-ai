import sys, unittest
sys.path.insert(0, 'src')
from sugarcode.extra_doc import handoff_redesign as hr

class Aud(unittest.TestCase):
    def test_audpin_scope_472(self):
        got = hr.handoffs((1, 1, 2, 2, 3), (1, 2, 3))
        self.assertEqual(got['handoff_redesign_validated'], False)
        self.assertEqual(got['not_claimed'], ('process_redesign', 'organization_outcome', 'execution'))
    def test_audpin_behavior_472(self):
        got = hr.handoffs((1, 1, 2, 2, 3), (1, 2, 3))
        self.assertEqual(got['before_handoffs'], (2, 4))
        self.assertEqual(got['after_handoffs'], (1, 2))
        self.assertEqual(got['handoffs_saved'], 0)
        self.assertEqual(got['steps_saved'], 2)
        self.assertEqual(got['fewer_handoffs'], False)
    def test_audpin_fewer_true_472(self):
        got = hr.handoffs((1, 2, 1, 2), (1, 1))
        self.assertEqual(got['before_handoffs'], (1, 2, 3))
        self.assertEqual(got['after_handoffs'], ())
        self.assertEqual(got['handoffs_saved'], 3)
        self.assertEqual(got['fewer_handoffs'], True)
    def test_audpin_refusals_472(self):
        with self.assertRaises(ValueError): hr.handoffs((), (0,))
        with self.assertRaises(ValueError): hr.handoffs((0,)*31, (0,))
        with self.assertRaises(ValueError): hr.handoffs((0,), (-1,))
        with self.assertRaises(ValueError): hr.handoffs((0,), (101,))
        with self.assertRaises(ValueError): hr.handoffs((True,), (0,))
    def test_audpin_types_472(self):
        class Items(tuple): pass
        class Number(int): pass
        with self.assertRaises(ValueError): hr.handoffs(Items((0,)), (0,))
        with self.assertRaises(ValueError): hr.handoffs((Number(1),), (0,))
        with self.assertRaises(ValueError): hr.handoffs([0], (0,))

if __name__ == '__main__': unittest.main()
