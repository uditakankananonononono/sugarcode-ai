import sys, unittest
sys.path.insert(0, 'src')
from sugarcode.extra_doc.team_topology_design import check_flow

class Aud(unittest.TestCase):
    def test_audpin_behavior_481(self):
        got = check_flow([('t1',9,2),('t2',10,3),('t1',0,0)])
        self.assertEqual(got['problems'], [(1,'oversized'),(1,'tangled')])
        self.assertEqual(got['teams'], ['t1','t2'])
        self.assertEqual(got['total'], 3)
    def test_audpin_boundaries_481(self):
        self.assertEqual(check_flow([('a',9,2)])['problems'], [])
        self.assertEqual(check_flow([('a',10,2)])['problems'], [(0,'oversized')])
        self.assertEqual(check_flow([('a',9,3)])['problems'], [(0,'tangled')])
        self.assertEqual(check_flow([('a',20,10)])['problems'], [(0,'oversized'),(0,'tangled')])
        self.assertEqual(check_flow([('a',0,0)])['problems'], [])
    def test_audpin_sort_total_481(self):
        got = check_flow([('z',5,1),('a',5,1),('z',5,1)])
        self.assertEqual(got['teams'], ['a','z'])
        self.assertEqual(got['total'], 3)
        self.assertEqual(got['problems'], [])
    def test_audpin_refusals_481(self):
        with self.assertRaises(TypeError): check_flow(None)
        with self.assertRaises(ValueError): check_flow([('a',5,1)]*41)
        with self.assertRaises(ValueError): check_flow([('a',5)])
        with self.assertRaises(ValueError): check_flow([('a',21,1)])
        with self.assertRaises(ValueError): check_flow([('a',5,11)])
        with self.assertRaises(ValueError): check_flow([('a'*25,5,1)])
    def test_audpin_types_481(self):
        class L(list): pass
        class T(tuple): pass
        class S(str): pass
        class N(int): pass
        with self.assertRaises(TypeError): check_flow(L([('a',5,1)]))
        with self.assertRaises(TypeError): check_flow([T(('a',5,1))])
        with self.assertRaises(TypeError): check_flow([(S('a'),5,1)])
        with self.assertRaises(TypeError): check_flow([('a',N(5),1)])
        with self.assertRaises(TypeError): check_flow([('a',5,True)])

if __name__ == '__main__': unittest.main()
