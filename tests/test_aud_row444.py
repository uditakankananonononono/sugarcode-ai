import sys, unittest
sys.path.insert(0, 'src')
from sugarcode.extra_doc.cross_selling import check_pairs

class Aud(unittest.TestCase):
    def test_audpin_behavior_444(self):
        got = check_pairs([('a','a',10),('b','c',4),('b','c',5),('a','b',-100)])
        self.assertEqual(got['problems'], [(0,'self_pair'),(1,'weak_pair'),(3,'weak_pair')])
        self.assertEqual(got['products'], ['a','b','c'])
        self.assertEqual(got['total'], 4)
    def test_audpin_lift_boundary_444(self):
        self.assertEqual(check_pairs([('a','b',4)])['problems'], [(0,'weak_pair')])
        self.assertEqual(check_pairs([('a','b',5)])['problems'], [])
        self.assertEqual(check_pairs([('a','b',-100)])['problems'], [(0,'weak_pair')])
        self.assertEqual(check_pairs([('a','b',1000)])['problems'], [])
    def test_audpin_both_rules_444(self):
        self.assertEqual(check_pairs([('a','a',0)])['problems'], [(0,'self_pair'),(0,'weak_pair')])
    def test_audpin_products_union_444(self):
        got = check_pairs([('z','a',10),('m','z',10)])
        self.assertEqual(got['products'], ['a','m','z'])
        self.assertEqual(got['total'], 2)
    def test_audpin_refusals_444(self):
        with self.assertRaises(TypeError): check_pairs(None)
        with self.assertRaises(ValueError): check_pairs([('a','b',5)]*41)
        with self.assertRaises(ValueError): check_pairs([('a','b',-101)])
        with self.assertRaises(ValueError): check_pairs([('a','b',1001)])
        with self.assertRaises(ValueError): check_pairs([('a b','b',5)])
    def test_audpin_types_444(self):
        class L(list): pass
        class T(tuple): pass
        class S(str): pass
        class N(int): pass
        with self.assertRaises(TypeError): check_pairs(L([('a','b',5)]))
        with self.assertRaises(TypeError): check_pairs([T(('a','b',5))])
        with self.assertRaises(TypeError): check_pairs([('a',S('b'),5)])
        with self.assertRaises(TypeError): check_pairs([('a','b',N(5))])
        with self.assertRaises(TypeError): check_pairs([('a','b',True)])

if __name__ == '__main__': unittest.main()
