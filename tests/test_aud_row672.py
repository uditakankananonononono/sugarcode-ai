import sys, unittest
sys.path.insert(0, 'src')
from sugarcode.extra_doc.bounded_context672 import audit

class Aud(unittest.TestCase):
    def test_audpin_scope_672(self):
        got = audit({'a':'x','b':'y','c':'x'}, [('a','b'),('b','a'),('a','c')])
        self.assertEqual(got['claim'], 'PARTIAL')
        self.assertEqual(got['boundaries_validated'], False)
    def test_audpin_behavior_672(self):
        got = audit({'a':'x','b':'y','c':'x'}, [('a','b'),('b','a'),('a','c')])
        self.assertEqual(got['same_context'], [2])
        self.assertEqual(got['cross_context'], [0, 1])
        self.assertEqual(got['context_edges'], [('x','y',1), ('y','x',1)])
    def test_audpin_edge_aggregation_sort_672(self):
        got = audit({'e':'z','f':'a'}, [('e','f'),('f','e'),('e','f')])
        self.assertEqual(got['same_context'], [])
        self.assertEqual(got['cross_context'], [0, 1, 2])
        self.assertEqual(got['context_edges'], [('a','z',1), ('z','a',2)])
    def test_audpin_empty_672(self):
        got = audit({}, [])
        self.assertEqual(got['same_context'], [])
        self.assertEqual(got['cross_context'], [])
        self.assertEqual(got['context_edges'], [])
    def test_audpin_refusals_672(self):
        with self.assertRaises(ValueError): audit({str(i):'x' for i in range(101)}, [])
        with self.assertRaises(ValueError): audit({'\t':'x'}, [])
        with self.assertRaises(ValueError): audit({'x'*81:'x'}, [])
        with self.assertRaises(ValueError): audit({}, [('a','b')])
        with self.assertRaises(ValueError): audit({'a':'x'}, [('a','b')])
        with self.assertRaises(ValueError): audit({}, [['a','b']])
    def test_audpin_types_672(self):
        class D(dict): pass
        class L(list): pass
        class S(str): pass
        with self.assertRaises(ValueError): audit(D(), [])
        with self.assertRaises(ValueError): audit({}, L())
        with self.assertRaises(ValueError): audit({S('a'):'x'}, [])
        with self.assertRaises(ValueError): audit({'a':'x'}, [(S('a'),'a')])
        # zero-width space is nonblank and accepted
        self.assertEqual(audit({'\u200b':'\u200b'}, [('\u200b','\u200b')])['same_context'], [0])

if __name__ == '__main__': unittest.main()
