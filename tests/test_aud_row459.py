import sys, unittest
sys.path.insert(0, 'src')
from sugarcode.extra_doc import flow_waste as fw

class Aud(unittest.TestCase):
    def test_audpin_scope_459(self):
        got = fw.waste(((10, 5), (20, 0)), 20)
        self.assertEqual(got['flow_waste_validated'], False)
        self.assertEqual(got['not_claimed'], ('waste_elimination', 'production_model', 'lean_advice'))
    def test_audpin_behavior_459(self):
        got = fw.waste(((10, 5), (20, 0)), 20)
        self.assertEqual(got['work_total'], 30)
        self.assertEqual(got['wait_total'], 5)
        self.assertEqual(got['elapsed_total'], 35)
        self.assertEqual(got['wait_pct'], 14)
        self.assertEqual(got['within_limit'], True)
        self.assertEqual(got['waiting_positions'], (0,))
    def test_audpin_pct_boundary_459(self):
        # 15/45 = 33.33%: floored pct 33; within_limit exact via cross-mult
        got = fw.waste(((10, 5), (20, 10)), 33)
        self.assertEqual(got['wait_pct'], 33)
        self.assertEqual(got['within_limit'], False)
        self.assertEqual(fw.waste(((10, 5), (20, 10)), 34)['within_limit'], True)
    def test_audpin_zero_wait_459(self):
        got = fw.waste(((5, 0),), 0)
        self.assertEqual(got['wait_pct'], 0)
        self.assertEqual(got['waiting_positions'], ())
        self.assertEqual(got['within_limit'], True)
    def test_audpin_refusals_459(self):
        with self.assertRaises(ValueError): fw.waste((), 0)
        with self.assertRaises(ValueError): fw.waste(((1, 1),)*21, 0)
        with self.assertRaises(ValueError): fw.waste(((0, 1),), 0)
        with self.assertRaises(ValueError): fw.waste(((1, -1),), 0)
        with self.assertRaises(ValueError): fw.waste(((1, 1),), 101)

if __name__ == '__main__': unittest.main()
