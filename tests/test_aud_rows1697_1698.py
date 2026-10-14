import sys, unittest
from fractions import Fraction as F
sys.path.insert(0, 'src'); sys.path.insert(0, 'tests')
from sugarcode.extra_doc import epi_counts1697 as m97, justice_weights1698 as m98

class Aud(unittest.TestCase):
    def test_audpin_behavior_1697(self):
        got = m97.fractions([('a',3,10),('b',0,5)])
        self.assertEqual(got['fractions'], (('a',F(3,10)),('b',F(0))))
        self.assertEqual(got['cases'], 3)
        self.assertEqual(got['population'], 15)
        self.assertEqual(got['aggregate_fraction'], F(1,5))
    def test_audpin_refusals_1697(self):
        with self.assertRaises(ValueError): m97.fractions([('a',1,0)])
        with self.assertRaises(ValueError): m97.fractions([('a',2,1)])
        with self.assertRaises(ValueError): m97.fractions([('a',1,1),('a',1,1)])
    def test_audpin_behavior_1698(self):
        got = m98.weights([('a',10,2),('a',4,1),('b',0,3)])
        self.assertEqual(got['weights'], (('a',3,F(8)),('b',3,F(0))))
        self.assertEqual(got['overall_mean'], F(4))
        self.assertEqual(got['range'], F(8))
    def test_audpin_refusals_1698(self):
        with self.assertRaises(ValueError): m98.weights([('a',1,0)])
        with self.assertRaises(ValueError): m98.weights([])
    def test_audpin_extra_1698(self):
        # equal means: range 0
        self.assertEqual(m98.weights([('a',2,1),('b',2,5)])['range'], F(0))

if __name__ == '__main__': unittest.main()
