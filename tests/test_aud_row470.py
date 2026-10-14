import sys, unittest
sys.path.insert(0, 'src')
from sugarcode.extra_doc import workflow_savings as ws

class Aud(unittest.TestCase):
    def test_audpin_scope_470(self):
        got = ws.savings(((10, 4), (3, 9), (5, 5)))
        self.assertEqual(got['workflow_savings_validated'], False)
        self.assertEqual(got['not_claimed'], ('actual_automation', 'workflow_integration', 'feasibility'))
    def test_audpin_behavior_470(self):
        got = ws.savings(((10, 4), (3, 9), (5, 5)))
        self.assertEqual(got['before_total'], 18)
        self.assertEqual(got['after_total'], 18)
        self.assertEqual(got['saved'], 0)
        self.assertEqual(got['improved_positions'], (0,))
        self.assertEqual(got['regressed_positions'], (1,))
    def test_audpin_negative_saved_470(self):
        got = ws.savings(((1, 10),))
        self.assertEqual(got['saved'], -9)
        self.assertEqual(got['regressed_positions'], (0,))
        self.assertEqual(got['improved_positions'], ())
    def test_audpin_refusals_470(self):
        with self.assertRaises(ValueError): ws.savings(())
        with self.assertRaises(ValueError): ws.savings(((1, 1),)*21)
        with self.assertRaises(ValueError): ws.savings(((1, 2, 3),))
        with self.assertRaises(ValueError): ws.savings(((-1, 0),))
        with self.assertRaises(ValueError): ws.savings(((0, 1001),))
    def test_audpin_types_470(self):
        class Items(tuple): pass
        class Number(int): pass
        with self.assertRaises(ValueError): ws.savings(Items(((1, 1),)))
        with self.assertRaises(ValueError): ws.savings(((Number(1), 1),))
        with self.assertRaises(ValueError): ws.savings(((1, True),))

if __name__ == '__main__': unittest.main()
