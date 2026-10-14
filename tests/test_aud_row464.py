import sys, unittest
sys.path.insert(0, 'src')
from sugarcode.extra_doc import fishbone_groups as fg

class Aud(unittest.TestCase):
    def test_audpin_scope_464(self):
        got = fg.groups((0, 2, 2, 1), 3)
        self.assertEqual(got['fishbone_groups_validated'], False)
        self.assertEqual(got['not_claimed'], ('diagram_rendering', 'causality', 'assignment_correctness'))
    def test_audpin_behavior_464(self):
        got = fg.groups((0, 2, 2, 1), 3)
        self.assertEqual(got['positions'], ((0,), (3,), (1, 2)))
        self.assertEqual(got['counts'], (1, 1, 2))
        self.assertEqual(got['empty_categories'], ())
        self.assertEqual(got['covered_count'], 3)
    def test_audpin_empty_464(self):
        got = fg.groups((2, 2), 4)
        self.assertEqual(got['positions'], ((), (), (0, 1), ()))
        self.assertEqual(got['empty_categories'], (0, 1, 3))
        self.assertEqual(got['covered_count'], 1)
    def test_audpin_refusals_464(self):
        with self.assertRaises(ValueError): fg.groups((), 1)
        with self.assertRaises(ValueError): fg.groups((0,)*31, 1)
        with self.assertRaises(ValueError): fg.groups((0,), 0)
        with self.assertRaises(ValueError): fg.groups((0,), 9)
        with self.assertRaises(ValueError): fg.groups((2,), 2)
    def test_audpin_types_464(self):
        class Items(tuple): pass
        class Number(int): pass
        with self.assertRaises(ValueError): fg.groups(Items((0,)), 1)
        with self.assertRaises(ValueError): fg.groups((True,), 1)
        with self.assertRaises(ValueError): fg.groups((0,), Number(2))
        # boundary accepts
        self.assertEqual(fg.groups((7,), 8)['covered_count'], 1)
        self.assertEqual(fg.groups((0,)*30, 1)['counts'], (30,))

if __name__ == '__main__': unittest.main()
