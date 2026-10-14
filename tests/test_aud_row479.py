import sys, unittest
sys.path.insert(0, 'src')
from sugarcode.extra_doc.span_of_control import check_teams

class Aud(unittest.TestCase):
    def test_audpin_behavior_479(self):
        got = check_teams([('boss',10),('lead',3),('vp',11),('ic',2)])
        self.assertEqual(got['problems'], [(2,'overloaded'),(3,'narrow')])
        self.assertEqual(got['managers'], ['boss','ic','lead','vp'])
        self.assertEqual(got['total'], 4)
    def test_audpin_boundaries_479(self):
        self.assertEqual(check_teams([('a',10)])['problems'], [])
        self.assertEqual(check_teams([('a',11)])['problems'], [(0,'overloaded')])
        self.assertEqual(check_teams([('a',3)])['problems'], [])
        self.assertEqual(check_teams([('a',2)])['problems'], [(0,'narrow')])
        self.assertEqual(check_teams([('a',0)])['problems'], [(0,'narrow')])
        self.assertEqual(check_teams([('a',100)])['problems'], [(0,'overloaded')])
    def test_audpin_sort_total_479(self):
        got = check_teams([('z',5),('a',5),('z',5)])
        self.assertEqual(got['managers'], ['a','z'])
        self.assertEqual(got['total'], 3)
        self.assertEqual(got['problems'], [])
    def test_audpin_refusals_479(self):
        with self.assertRaises(TypeError): check_teams(None)
        with self.assertRaises(ValueError): check_teams([('a',5)]*41)
        with self.assertRaises(ValueError): check_teams([('a',)])
        with self.assertRaises(ValueError): check_teams([('a',101)])
        with self.assertRaises(ValueError): check_teams([('a'*25,5)])
    def test_audpin_types_479(self):
        class L(list): pass
        class T(tuple): pass
        class S(str): pass
        class N(int): pass
        with self.assertRaises(TypeError): check_teams(L([('a',5)]))
        with self.assertRaises(TypeError): check_teams([T(('a',5))])
        with self.assertRaises(TypeError): check_teams([(S('a'),5)])
        with self.assertRaises(TypeError): check_teams([('a',N(5))])
        with self.assertRaises(TypeError): check_teams([('a',True)])

if __name__ == '__main__': unittest.main()
