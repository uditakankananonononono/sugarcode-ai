import sys, unittest
sys.path.insert(0, 'src')
from sugarcode.extra_doc.customer_success import check_accounts

class Aud(unittest.TestCase):
    def test_audpin_behavior_445(self):
        got = check_accounts([('a',39,0),('b',80,31),('c',80,30),('a',100,0)])
        self.assertEqual(got['problems'], [(0,'at_risk'),(1,'neglected_win')])
        self.assertEqual(got['accounts'], ['a','b','c'])
        self.assertEqual(got['total'], 4)
    def test_audpin_boundaries_445(self):
        self.assertEqual(check_accounts([('a',40,365)])['problems'], [])
        self.assertEqual(check_accounts([('a',39,0)])['problems'], [(0,'at_risk')])
        self.assertEqual(check_accounts([('a',79,31)])['problems'], [])
        self.assertEqual(check_accounts([('a',80,30)])['problems'], [])
        self.assertEqual(check_accounts([('a',80,31)])['problems'], [(0,'neglected_win')])
        self.assertEqual(check_accounts([('a',0,365)])['problems'], [(0,'at_risk')])
    def test_audpin_both_rules_445(self):
        self.assertEqual(check_accounts([('a',39,31)])['problems'], [(0,'at_risk')])
        self.assertEqual(check_accounts([('a',100,31)])['problems'], [(0,'neglected_win')])
    def test_audpin_sort_total_445(self):
        got = check_accounts([('z',50,0),('a',50,0),('z',50,0)])
        self.assertEqual(got['accounts'], ['a','z'])
        self.assertEqual(got['total'], 3)
        self.assertEqual(got['problems'], [])
    def test_audpin_refusals_445(self):
        with self.assertRaises(TypeError): check_accounts(None)
        with self.assertRaises(ValueError): check_accounts([('a',1,2)]*41)
        with self.assertRaises(ValueError): check_accounts([('a',101,2)])
        with self.assertRaises(ValueError): check_accounts([('a',1,366)])
        with self.assertRaises(ValueError): check_accounts([('a'*25,1,2)])
    def test_audpin_types_445(self):
        class L(list): pass
        class T(tuple): pass
        class S(str): pass
        class N(int): pass
        with self.assertRaises(TypeError): check_accounts(L([('a',1,2)]))
        with self.assertRaises(TypeError): check_accounts([T(('a',1,2))])
        with self.assertRaises(TypeError): check_accounts([(S('a'),1,2)])
        with self.assertRaises(TypeError): check_accounts([('a',N(1),2)])
        with self.assertRaises(TypeError): check_accounts([('a',1,True)])

if __name__ == '__main__': unittest.main()
