import sys, unittest
sys.path.insert(0, 'src')
from sugarcode.extra_doc import kb_article_check as kb

class Aud(unittest.TestCase):
    def test_audpin_scope_449(self):
        got = kb.check('t', ('a', 'b'), ('x',))
        self.assertEqual(got['kb_article_check_validated'], False)
        self.assertEqual(got['not_claimed'], ('accuracy', 'clarity', 'problem_solved'))
    def test_audpin_behavior_449(self):
        got = kb.check('ab', ('xy', ' ', 'é'), ('t1', 't2'))
        self.assertEqual(got['blank_sections'], (1,))
        self.assertEqual(got['total_chars'], 2+2+1+1)
        self.assertEqual(got['complete'], False)
        self.assertEqual(got['section_count'], 3)
        self.assertEqual(got['tag_count'], 2)
    def test_audpin_blank_edges_449(self):
        # whitespace-only variants count as blank
        got = kb.check('t', ('\t', '\u2003', 'a'), ('x',))
        self.assertEqual(got['blank_sections'], (0, 1))
        self.assertEqual(kb.check('t', ('a', 'b'), ('x',))['complete'], True)
    def test_audpin_refusals_449(self):
        with self.assertRaises(ValueError): kb.check('a'*81, ('a','b'), ('x',))
        with self.assertRaises(ValueError): kb.check('t', ('a',), ('x',))
        with self.assertRaises(ValueError): kb.check('t', ('a','b'), ())
        with self.assertRaises(ValueError): kb.check('t', ('a','b'), ('x',)*9)
        with self.assertRaises(ValueError): kb.check(True, ('a','b'), ('x',))
    def test_audpin_subclass_refused_449(self):
        class Text(str): pass
        class Items(tuple): pass
        with self.assertRaises(ValueError): kb.check(Text('t'), ('a','b'), ('x',))
        with self.assertRaises(ValueError): kb.check('t', Items(('a','b')), ('x',))

if __name__ == '__main__': unittest.main()
