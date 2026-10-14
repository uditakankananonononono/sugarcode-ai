import sys, unittest
sys.path.insert(0, 'src')
from sugarcode.extra_doc.training_design import check_programs

class Aud(unittest.TestCase):
    def test_audpin_behavior_477(self):
        got = check_programs([('m1',2,70),('m2',1,69),('m1',40,100)])
        self.assertEqual(got['problems'], [(1,'low_pass'),(1,'too_brief')])
        self.assertEqual(got['modules'], ['m1','m2'])
        self.assertEqual(got['total'], 3)
    def test_audpin_boundaries_477(self):
        self.assertEqual(check_programs([('a',2,70)])['problems'], [])
        self.assertEqual(check_programs([('a',1,70)])['problems'], [(0,'too_brief')])
        self.assertEqual(check_programs([('a',2,69)])['problems'], [(0,'low_pass')])
        self.assertEqual(check_programs([('a',0,0)])['problems'], [(0,'low_pass'),(0,'too_brief')])
        self.assertEqual(check_programs([('a',40,100)])['problems'], [])
    def test_audpin_sort_total_477(self):
        got = check_programs([('z',5,80),('a',5,80),('z',5,80)])
        self.assertEqual(got['modules'], ['a','z'])
        self.assertEqual(got['total'], 3)
        self.assertEqual(got['problems'], [])
    def test_audpin_refusals_477(self):
        with self.assertRaises(TypeError): check_programs(None)
        with self.assertRaises(ValueError): check_programs([('a',2,70)]*41)
        with self.assertRaises(ValueError): check_programs([('a',2,70,9)])
        with self.assertRaises(ValueError): check_programs([('a',41,70)])
        with self.assertRaises(ValueError): check_programs([('a',2,101)])
        with self.assertRaises(ValueError): check_programs([('a'*25,2,70)])
    def test_audpin_types_477(self):
        class L(list): pass
        class T(tuple): pass
        class S(str): pass
        class N(int): pass
        with self.assertRaises(TypeError): check_programs(L([('a',2,70)]))
        with self.assertRaises(TypeError): check_programs([T(('a',2,70))])
        with self.assertRaises(TypeError): check_programs([(S('a'),2,70)])
        with self.assertRaises(TypeError): check_programs([('a',N(2),70)])
        with self.assertRaises(TypeError): check_programs([('a',2,True)])

if __name__ == '__main__': unittest.main()
