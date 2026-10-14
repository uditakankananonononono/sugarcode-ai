import sys, unittest
from fractions import Fraction as F
sys.path.insert(0, 'src'); sys.path.insert(0, 'tests')
from sugarcode.extra_doc import indoor_turnover1665 as m65, soil_moisture1666 as m66

class Aud(unittest.TestCase):
    def test_audpin_behavior_1665(self):
        got = m65.turnover([('a',10,4),('b',3,3)], 2)
        self.assertEqual(got['turnover'], (('a',F(5,2)),('b',F(1))))
        self.assertEqual(got['below'], ('b',))
        self.assertEqual(got['minimum'], F(1))
    def test_audpin_refusals_1665(self):
        with self.assertRaises(ValueError): m65.turnover([('a',1,0)], 1)  # volume 0
        with self.assertRaises(ValueError): m65.turnover([('a',1,1)], -1)
        with self.assertRaises(ValueError): m65.turnover([('a',1,1),('a',2,1)], 1)
        with self.assertRaises(ValueError): m65.turnover([], 1)
    def test_audpin_behavior_1666(self):
        got = m66.moisture([('a',10,8),('a',6,2),('b',5,5)])
        self.assertEqual(got['moisture'], (('a',16,10,6,F(3,5)),('b',5,5,0,F(0))))
        self.assertEqual(got['total_water'], 6)
        self.assertEqual(got['dry_basis_fraction'], F(2,5))
    def test_audpin_zerodry_1666(self):
        # zero dry -> None ratio; wet=dry=0 allowed
        got = m66.moisture([('a',5,0)])
        self.assertEqual(got['moisture'], (('a',5,0,5,None),))
        self.assertIsNone(got['dry_basis_fraction'])
        with self.assertRaises(ValueError): m66.moisture([('a',1,2)])  # dry>wet
    def test_audpin_extra_1665(self):
        # ratio equal to threshold not below
        self.assertEqual(m65.turnover([('a',4,2)], 2)['below'], ())

if __name__ == '__main__': unittest.main()
