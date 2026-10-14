import sys, unittest
sys.path.insert(0, 'src')
from sugarcode.extra_doc import adoption_checkpoints as ac

class Aud(unittest.TestCase):
    def test_audpin_scope_473(self):
        got = ac.checkpoints((2, 5, 9, 9), 10, 7)
        self.assertEqual(got['adoption_checkpoints_validated'], False)
        self.assertEqual(got['not_claimed'], ('transition_management', 'adoption_prediction', 'readiness'))
    def test_audpin_behavior_473(self):
        got = ac.checkpoints((2, 5, 9, 9), 10, 7)
        self.assertEqual(got['first_reached'], 2)
        self.assertEqual(got['gains'], (3, 4, 0))
        self.assertEqual(got['remaining'], 0)
        self.assertEqual(got['reached'], True)
    def test_audpin_unreached_473(self):
        got = ac.checkpoints((0, 0), 5, 4)
        self.assertEqual(got['first_reached'], None)
        self.assertEqual(got['gains'], (0,))
        self.assertEqual(got['remaining'], 4)
        self.assertEqual(got['reached'], False)
    def test_audpin_refusals_473(self):
        with self.assertRaises(ValueError): ac.checkpoints((), 1, 0)
        with self.assertRaises(ValueError): ac.checkpoints((0,)*21, 1, 0)
        with self.assertRaises(ValueError): ac.checkpoints((3, 2), 5, 0)
        with self.assertRaises(ValueError): ac.checkpoints((0,), 0, 0)
        with self.assertRaises(ValueError): ac.checkpoints((0,), 5, 6)
    def test_audpin_types_473(self):
        class Items(tuple): pass
        class Number(int): pass
        with self.assertRaises(ValueError): ac.checkpoints(Items((0,)), 1, 0)
        with self.assertRaises(ValueError): ac.checkpoints((0,), Number(1), 0)
        with self.assertRaises(ValueError): ac.checkpoints((0,), 1, True)
        with self.assertRaises(ValueError): ac.checkpoints((0,), 10001, 0)

if __name__ == '__main__': unittest.main()
