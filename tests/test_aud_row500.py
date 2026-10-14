import sys, unittest
sys.path.insert(0, 'src')
from sugarcode.extra_doc import cash_runway as cr

class Aud(unittest.TestCase):
    def test_audpin_scope_500(self):
        got = cr.runway(((100,50),(20,80),(0,10)), 30)
        self.assertEqual(got['cash_runway_validated'], False)
        self.assertEqual(got['not_claimed'], ('financial_prediction','business_model','accounting_validation'))
    def test_audpin_behavior_500(self):
        got = cr.runway(((100,50),(20,80),(0,10)), 30)
        self.assertEqual(got['closing_balances'], (80, 20, 10))
        self.assertEqual(got['final_cash'], 10)
        self.assertEqual(got['first_negative'], None)
        self.assertEqual(got['nonnegative_throughout'], True)
    def test_audpin_negative_500(self):
        got = cr.runway(((0,50),(100,0),(0,200)), 30)
        self.assertEqual(got['closing_balances'], (-20, 80, -120))
        self.assertEqual(got['first_negative'], 0)
        self.assertEqual(got['nonnegative_throughout'], False)
        self.assertEqual(got['final_cash'], -120)
    def test_audpin_refusals_500(self):
        with self.assertRaises(ValueError): cr.runway((), 0)
        with self.assertRaises(ValueError): cr.runway(((0,0),)*25, 0)
        with self.assertRaises(ValueError): cr.runway(((0,0),), -1)
        with self.assertRaises(ValueError): cr.runway(((0,0),), 1000001)
        with self.assertRaises(ValueError): cr.runway(((0,1000001),), 0)
        with self.assertRaises(ValueError): cr.runway(((0,),), 0)
    def test_audpin_types_500(self):
        class Items(tuple): pass
        class Number(int): pass
        with self.assertRaises(ValueError): cr.runway(Items(((0,0),)), 0)
        with self.assertRaises(ValueError): cr.runway(((0,0),), Number(1))
        with self.assertRaises(ValueError): cr.runway(((Number(0),0),), 0)
        with self.assertRaises(ValueError): cr.runway(((0,0),), True)

if __name__ == '__main__': unittest.main()
