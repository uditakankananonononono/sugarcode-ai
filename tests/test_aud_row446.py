import sys, unittest
sys.path.insert(0, 'src')
from sugarcode.extra_doc.onboarding_optimization import check_steps

class Aud(unittest.TestCase):
    def test_audpin_behavior_446(self):
        got = check_steps([('welcome',0,1),('setup',2,3)])
        self.assertEqual(got['problems'], [(1,'drop_inverted')])
        self.assertEqual(got['steps'], ['setup','welcome'])
        self.assertEqual(got['total'], 2)
    def test_audpin_first_step_exempt_446(self):
        self.assertEqual(check_steps([('a',100000,0)])['problems'], [])
        self.assertEqual(check_steps([('a',100000,31)])['problems'], [(0,'slow_step')])
    def test_audpin_drop_steep_446(self):
        # half boundary: c*2 < prev strictly; prev=10: c=4 steep, c=5 ok
        self.assertEqual(check_steps([('a',10,0),('b',4,0)])['problems'], [(1,'drop_steep')])
        self.assertEqual(check_steps([('a',10,0),('b',5,0)])['problems'], [])
        # zero previous never raises drop_steep
        self.assertEqual(check_steps([('a',0,0),('b',0,0)])['problems'], [])
        # inverted beats steep (elif): c>prev can never be steep anyway; pin inverted boundary
        self.assertEqual(check_steps([('a',10,0),('b',10,0)])['problems'], [])
        self.assertEqual(check_steps([('a',10,0),('b',11,0)])['problems'], [(1,'drop_inverted')])
    def test_audpin_slow_boundary_446(self):
        self.assertEqual(check_steps([('a',5,30),('b',5,31)])['problems'], [(1,'slow_step')])
    def test_audpin_refusals_446(self):
        with self.assertRaises(TypeError): check_steps(None)
        with self.assertRaises(ValueError): check_steps([('a',1,2)]*41)
        with self.assertRaises(ValueError): check_steps([('a',100001,2)])
        with self.assertRaises(ValueError): check_steps([('a',1,1441)])
        with self.assertRaises(ValueError): check_steps([('a-','1',2)] if False else [('a-',1,2)])
    def test_audpin_types_446(self):
        class L(list): pass
        class T(tuple): pass
        class S(str): pass
        class N(int): pass
        with self.assertRaises(TypeError): check_steps(L([('a',1,2)]))
        with self.assertRaises(TypeError): check_steps([T(('a',1,2))])
        with self.assertRaises(TypeError): check_steps([(S('a'),1,2)])
        with self.assertRaises(TypeError): check_steps([('a',N(1),2)])
        with self.assertRaises(TypeError): check_steps([('a',1,True)])

if __name__ == '__main__': unittest.main()
