import sys, unittest
sys.path.insert(0, 'src')
from sugarcode.extra_doc import acceptance_examples as ae

class Aud(unittest.TestCase):
    def test_audpin_scope_688(self):
        got = ae.examples(((5,5),(-3,2),(0,0)))
        self.assertEqual(got['acceptance_examples_validated'], False)
        self.assertEqual(got['not_claimed'], ('user_acceptance','test_generation','software_validation'))
    def test_audpin_behavior_688(self):
        got = ae.examples(((5,5),(-3,2),(0,0)))
        self.assertEqual(got['mismatch_positions'], (1,))
        self.assertEqual(got['differences'], (0, 5, 0))
        self.assertEqual(got['matched_count'], 2)
        self.assertEqual(got['all_match'], False)
    def test_audpin_all_match_688(self):
        got = ae.examples(((0,0),(-1000,-1000),(1000,1000)))
        self.assertEqual(got['all_match'], True)
        self.assertEqual(got['matched_count'], 3)
        self.assertEqual(got['mismatch_positions'], ())
        self.assertEqual(got['differences'], (0,0,0))
    def test_audpin_refusals_688(self):
        with self.assertRaises(ValueError): ae.examples(())
        with self.assertRaises(ValueError): ae.examples(((0,0),)*31)
        with self.assertRaises(ValueError): ae.examples(((0,1001),))
        with self.assertRaises(ValueError): ae.examples(((-1001,0),))
        with self.assertRaises(ValueError): ae.examples(((0,),))
    def test_audpin_types_688(self):
        class Items(tuple): pass
        class Number(int): pass
        with self.assertRaises(ValueError): ae.examples(Items(((0,0),)))
        with self.assertRaises(ValueError): ae.examples(((Number(0),0),))
        with self.assertRaises(ValueError): ae.examples(((True,0),))
        with self.assertRaises(ValueError): ae.examples([[0,0]])

if __name__ == '__main__': unittest.main()
