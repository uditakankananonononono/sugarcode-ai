import sys, unittest
sys.path.insert(0, 'src')
from sugarcode.extra_doc import inventory_position as ip

class Aud(unittest.TestCase):
    def test_audpin_scope_453(self):
        got = ip.position(10, 5, 3, 20, 30)
        self.assertEqual(got['inventory_position_validated'], False)
        self.assertEqual(got['not_claimed'], ('optimal_policy', 'lead_times', 'demand_model'))
    def test_audpin_behavior_453(self):
        got = ip.position(10, 5, 3, 20, 30)
        self.assertEqual(got['position'], 12)
        self.assertEqual(got['reorder'], True)
        self.assertEqual(got['top_up'], 18)
        self.assertEqual(got['backlog'], 0)
    def test_audpin_backlog_453(self):
        got = ip.position(10, 5, 20, 5, 10)
        self.assertEqual(got['position'], -5)
        self.assertEqual(got['backlog'], 5)
        self.assertEqual(got['top_up'], 15)
    def test_audpin_edges_453(self):
        # position == reorder_point: no reorder
        got = ip.position(5, 5, 0, 10, 10)
        self.assertEqual(got['reorder'], False)
        self.assertEqual(got['top_up'], 0)
        # target == reorder_point allowed
        self.assertEqual(ip.position(0, 0, 0, 5, 5)['reorder'], True)
        # zero backlog at zero position
        self.assertEqual(ip.position(0, 0, 0, 0, 0)['backlog'], 0)
    def test_audpin_refusals_453(self):
        with self.assertRaises(ValueError): ip.position(0, 0, 0, 5, 4)
        with self.assertRaises(ValueError): ip.position(-1, 0, 0, 0, 0)
        with self.assertRaises(ValueError): ip.position(10001, 0, 0, 0, 0)
        with self.assertRaises(ValueError): ip.position(True, 0, 0, 0, 0)
        with self.assertRaises(ValueError): ip.position(0, 0, 0, 0, 1.0)

if __name__ == '__main__': unittest.main()
