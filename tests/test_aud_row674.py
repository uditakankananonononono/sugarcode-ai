import sys, unittest
sys.path.insert(0, 'src')
from sugarcode.extra_doc.aggregate_design674 import audit

class Aud(unittest.TestCase):
    def test_audpin_scope_674(self):
        got = audit({'e1':'agg1','e2':'agg2','e3':'agg1'}, [['e1','e2'],['e1','e3'],['e2']])
        self.assertEqual(got['claim'], 'PARTIAL')
        self.assertEqual(got['consistency_validated'], False)
    def test_audpin_behavior_674(self):
        got = audit({'e1':'agg1','e2':'agg2','e3':'agg1'}, [['e1','e2'],['e1','e3'],['e2']])
        self.assertEqual(got['aggregate_sets'], [['agg1','agg2'],['agg1'],['agg2']])
        self.assertEqual(got['cross_boundary'], [0])
    def test_audpin_empty_tx_674(self):
        got = audit({'a':'x'}, [])
        self.assertEqual(got['aggregate_sets'], [])
        self.assertEqual(got['cross_boundary'], [])
    def test_audpin_sort_674(self):
        got = audit({'e1':'z','e2':'a'}, [['e1','e2']])
        self.assertEqual(got['aggregate_sets'], [['a','z']])
    def test_audpin_refusals_674(self):
        with self.assertRaises(ValueError): audit({}, [])
        with self.assertRaises(ValueError): audit({str(i):'x' for i in range(51)}, [])
        with self.assertRaises(ValueError): audit({'a':'x'}, [[]])
        with self.assertRaises(ValueError): audit({'a':'x'}, [['a']]*101)  # gap witness: kills >101 mutant
        with self.assertRaises(ValueError): audit({'a':'x'}, [['a','a']])
        with self.assertRaises(ValueError): audit({'a':'x'}, [['b']])
        with self.assertRaises(ValueError): audit({'a':'x'}, [list(map(str,range(49)))+['49','49']] if False else [('a',)])
    def test_audpin_types_674(self):
        class D(dict): pass
        class L(list): pass
        class S(str): pass
        with self.assertRaises(ValueError): audit(D(a='x'), [])
        with self.assertRaises(ValueError): audit({'a':'x'}, L())
        with self.assertRaises(ValueError): audit({S('a'):'x'}, [])
        with self.assertRaises(ValueError): audit({'a':'x'}, [[S('a')]])
        o = {str(i):'x' for i in range(50)}
        with self.assertRaises(ValueError): audit(o, [list(map(str,range(50)))+['49']])
        self.assertEqual(audit({'\u200b':'\u200b'}, [['\u200b']])['aggregate_sets'], [['\u200b']])

if __name__ == '__main__': unittest.main()
