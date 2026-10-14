import sys, unittest
sys.path.insert(0, 'src'); sys.path.insert(0, 'tests')
from sugarcode.extra_doc import brownfield_cost1669 as m69, phyto_uptake1670 as m70

class Aud(unittest.TestCase):
    def test_audpin_behavior_1669(self):
        got = m69.budgets([('a',10,3,25),('b',0,100,0)])
        self.assertEqual(got['budgets'], (('a',30,-5),('b',0,0)))
        self.assertEqual(got['over_budget'], ('a',))
        self.assertEqual(got['total_cost'], 30)
    def test_audpin_refusals_1669(self):
        with self.assertRaises(ValueError): m69.budgets([('a',1,1,1),('a',2,2,2)])
        with self.assertRaises(ValueError): m69.budgets([('a',-1,1,1)])
        with self.assertRaises(ValueError): m69.budgets([])
        with self.assertRaises(ValueError): m69.budgets([('a',1,1)])
    def test_audpin_behavior_1670(self):
        got = m70.uptake([('a',10,3),('a',2,5),('b',0,9)])
        self.assertEqual(got['uptake'], (('a',12,40),('b',0,0)))
        self.assertEqual(got['total_product'], 40)
        self.assertEqual(got['positive'], ('a',))
    def test_audpin_aggregation_1670(self):
        # repeated labels aggregate; biomass 0 allowed
        got = m70.uptake([('x',5,2),('x',5,2)])
        self.assertEqual(got['uptake'], (('x',10,20),))
    def test_audpin_extra_1669_1670(self):
        # 1669 budget==cost: not over
        self.assertEqual(m69.budgets([('a',2,3,6)])['over_budget'], ())
        # 1670 concentration 0 -> zero product not positive
        self.assertEqual(m70.uptake([('a',5,0)])['positive'], ())

if __name__ == '__main__': unittest.main()
