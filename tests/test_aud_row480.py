import sys, unittest
sys.path.insert(0, 'src')
from sugarcode.extra_doc.matrix_organization import check_members

class Aud(unittest.TestCase):
    def test_audpin_behavior_480(self):
        got = check_members([('p1',2,3),('p2',1,4),('p1',5,10)])
        self.assertEqual(got['problems'], [(1,'overloaded'),(1,'unmatrixed'),(2,'overloaded')])
        self.assertEqual(got['members'], ['p1','p2'])
        self.assertEqual(got['total'], 3)
    def test_audpin_boundaries_480(self):
        self.assertEqual(check_members([('a',2,3)])['problems'], [])
        self.assertEqual(check_members([('a',1,3)])['problems'], [(0,'unmatrixed')])
        self.assertEqual(check_members([('a',2,4)])['problems'], [(0,'overloaded')])
        self.assertEqual(check_members([('a',0,10)])['problems'], [(0,'overloaded'),(0,'unmatrixed')])
        self.assertEqual(check_members([('a',5,10)])['problems'], [(0,'overloaded')])
    def test_audpin_sort_total_480(self):
        got = check_members([('z',2,3),('a',2,3),('z',2,3)])
        self.assertEqual(got['members'], ['a','z'])
        self.assertEqual(got['total'], 3)
        self.assertEqual(got['problems'], [])
    def test_audpin_refusals_480(self):
        with self.assertRaises(TypeError): check_members(None)
        with self.assertRaises(ValueError): check_members([('a',2,3)]*41)
        with self.assertRaises(ValueError): check_members([('a',2,3,9)])
        with self.assertRaises(ValueError): check_members([('a',6,3)])
        with self.assertRaises(ValueError): check_members([('a',2,11)])
        with self.assertRaises(ValueError): check_members([('a'*25,2,3)])
    def test_audpin_types_480(self):
        class L(list): pass
        class T(tuple): pass
        class S(str): pass
        class N(int): pass
        with self.assertRaises(TypeError): check_members(L([('a',2,3)]))
        with self.assertRaises(TypeError): check_members([T(('a',2,3))])
        with self.assertRaises(TypeError): check_members([(S('a'),2,3)])
        with self.assertRaises(TypeError): check_members([('a',N(2),3)])
        with self.assertRaises(TypeError): check_members([('a',2,True)])

if __name__ == '__main__': unittest.main()
