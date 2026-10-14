import sys, unittest
sys.path.insert(0, 'src')
from sugarcode.extra_doc import checkpoint_score_delta as csd

class Aud(unittest.TestCase):
    def test_audpin_scope_986(self):
        got = csd.deltas(((10,20),(50,50),(90,10)))
        self.assertEqual(got['checkpoint_score_delta_validated'], False)
        self.assertEqual(got['not_claimed'], ('immune_response','drug_efficacy','clinical_interpretation'))
    def test_audpin_behavior_986(self):
        got = csd.deltas(((10,20),(50,50),(90,10)))
        self.assertEqual(got['changes'], (10, 0, -80))
        self.assertEqual(got['positive_positions'], (0,))
        self.assertEqual(got['total_change'], -70)
        self.assertEqual(got['positive_count'], 1)
    def test_audpin_boundaries_986(self):
        got = csd.deltas(((0,100),))
        self.assertEqual(got['changes'], (100,))
        self.assertEqual(got['positive_positions'], (0,))
        got = csd.deltas(((100,0),))
        self.assertEqual(got['changes'], (-100,))
        self.assertEqual(got['positive_positions'], ())
        self.assertEqual(got['positive_count'], 0)
        self.assertEqual(got['total_change'], -100)
    def test_audpin_refusals_986(self):
        with self.assertRaises(ValueError): csd.deltas(())
        with self.assertRaises(ValueError): csd.deltas(((0,0),)*21)
        with self.assertRaises(ValueError): csd.deltas(((0,101),))
        with self.assertRaises(ValueError): csd.deltas(((-1,0),))
        with self.assertRaises(ValueError): csd.deltas(((0,0,0),))
    def test_audpin_types_986(self):
        class Items(tuple): pass
        class Number(int): pass
        with self.assertRaises(ValueError): csd.deltas(Items(((0,0),)))
        with self.assertRaises(ValueError): csd.deltas(((Number(0),0),))
        with self.assertRaises(ValueError): csd.deltas(((0,True),))
        with self.assertRaises(ValueError): csd.deltas([[0,0]])

if __name__ == '__main__': unittest.main()
