import sys, unittest
sys.path.insert(0, 'src')
from sugarcode.extra_doc.ubiquitous_language673 import audit

class Aud(unittest.TestCase):
    def test_audpin_scope_673(self):
        got = audit([('c1','t','d1'),('c2','t','d2'),('c3','t','d1'),('c1','u','d1')])
        self.assertEqual(got['claim'], 'PARTIAL')
        self.assertEqual(got['semantic_equivalence_validated'], False)
    def test_audpin_behavior_673(self):
        got = audit([('c1','t','d1'),('c2','t','d2'),('c3','t','d1'),('c1','u','d1')])
        self.assertEqual(got['conflicts'], [('t', [('c1','d1'),('c2','d2'),('c3','d1')])])
        self.assertEqual(got['shared'], [])
        self.assertEqual(got['definition_aliases'], [('d1', ['t','u'])])
    def test_audpin_shared_673(self):
        got = audit([('z','t','d'),('a','t','d'),('m','t','d')])
        self.assertEqual(got['shared'], [('t','d',['a','m','z'])])
        self.assertEqual(got['conflicts'], [])
    def test_audpin_empty_673(self):
        got = audit([])
        self.assertEqual(got, {'conflicts': [], 'shared': [], 'definition_aliases': [], 'claim': 'PARTIAL', 'semantic_equivalence_validated': False})
    def test_audpin_refusals_673(self):
        with self.assertRaises(ValueError): audit([('c','t','d')]*2)
        with self.assertRaises(ValueError): audit([('c','t','d1'),('c','t','d2')])  # gap witness: kills row[:3] mutant
        with self.assertRaises(ValueError): audit([('c',str(i),'d') for i in range(101)])
        with self.assertRaises(ValueError): audit([['c','t','d']])
        with self.assertRaises(ValueError): audit([('c','t')])
        with self.assertRaises(ValueError): audit([('\t','t','d')])
        with self.assertRaises(ValueError): audit([('c','x'*121,'d')])
    def test_audpin_types_673(self):
        class L(list): pass
        class T(tuple): pass
        class S(str): pass
        with self.assertRaises(ValueError): audit(L())
        with self.assertRaises(ValueError): audit([T(('c','t','d'))])
        with self.assertRaises(ValueError): audit([(S('c'),'t','d')])
        self.assertEqual(audit([('\u200b','\u200b','\u200b')])['conflicts'], [])

if __name__ == '__main__': unittest.main()
