import sys, unittest
sys.path.insert(0, 'src')
from sugarcode.extra_doc.upselling import check_offers

class Aud(unittest.TestCase):
    def test_audpin_behavior_443(self):
        got = check_offers([('basic',100,50),('pro',100,400),('x',0,1000000),('pro',200,600)])
        self.assertEqual(got['problems'], [(0,'no_upgrade'),(1,'too_steep')])
        self.assertEqual(got['offers'], ['basic','pro','x'])
        self.assertEqual(got['total'], 4)
    def test_audpin_both_rules_443(self):
        # target <= current AND > 3*current impossible; but equal target and steep are exclusive - pin steep boundary: 3x ok, 3x+1 steep
        self.assertEqual(check_offers([('a',100,300)])['problems'], [])
        self.assertEqual(check_offers([('a',100,301)])['problems'], [(0,'too_steep')])
        self.assertEqual(check_offers([('a',100,100)])['problems'], [(0,'no_upgrade')])
        self.assertEqual(check_offers([('a',100,101)])['problems'], [])
    def test_audpin_zero_current_443(self):
        self.assertEqual(check_offers([('z',0,1000000)])['problems'], [])
        self.assertEqual(check_offers([('z',0,0)])['problems'], [(0,'no_upgrade')])
    def test_audpin_sort_order_443(self):
        got = check_offers([('b',10,5),('a',10,20),('b',1,100)])
        self.assertEqual(got['problems'], [(0,'no_upgrade'),(2,'too_steep')])
        self.assertEqual(got['offers'], ['a','b'])
        self.assertEqual(got['total'], 3)
    def test_audpin_refusals_443(self):
        with self.assertRaises(TypeError): check_offers(('a',1,2))
        with self.assertRaises(ValueError): check_offers([('a',1,2)]*41)
        with self.assertRaises(ValueError): check_offers([('a',1000001,2)])
        with self.assertRaises(ValueError): check_offers([('A',1,2)])
        with self.assertRaises(ValueError): check_offers([('a'*25,1,2)])
    def test_audpin_types_443(self):
        class L(list): pass
        class T(tuple): pass
        class S(str): pass
        class N(int): pass
        with self.assertRaises(TypeError): check_offers(L([('a',1,2)]))
        with self.assertRaises(TypeError): check_offers([T(('a',1,2))])
        with self.assertRaises(TypeError): check_offers([(S('a'),1,2)])
        with self.assertRaises(TypeError): check_offers([('a',N(1),2)])
        with self.assertRaises(TypeError): check_offers([('a',True,2)])

if __name__ == '__main__': unittest.main()
