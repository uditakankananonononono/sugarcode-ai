import itertools
import unittest
from fractions import Fraction as F
import b446_intervals as m


def points(interval):
    a,b=interval
    return [a+(b-a)*F(k,4) for k in range(5)]


class IntervalTests(unittest.TestCase):
    def test_exact_extrema_oracles(self):
        endpoints=[F(-2),F(-1,2),F(0),F(1,2),F(2)]
        intervals=[(a,b) for a in endpoints for b in endpoints if a<=b]
        for a,b in itertools.product(intervals,repeat=2):
            xs,ys=points(a),points(b)
            for func,operation in [(m.interval_add,lambda x,y:x+y),(m.interval_subtract,lambda x,y:x-y),(m.interval_multiply,lambda x,y:x*y)]:
                values=[operation(x,y) for x in xs for y in ys]
                self.assertEqual(func(a,b),(min(values),max(values)))
            hull=m.interval_hull(a,b)
            self.assertEqual(hull,(min(xs+ys),max(xs+ys)))
            common=[x for x in xs+ys if a[0]<=x<=a[1] and b[0]<=x<=b[1]]
            self.assertEqual(m.interval_intersection(a,b),(min(common),max(common)) if common else None)
            if not b[0]<=0<=b[1]:
                values=[x/y for x in xs for y in ys]
                self.assertEqual(m.interval_divide(a,b),(min(values),max(values)))
        for a in intervals:
            xs=points(a)
            if a[0]<=0<=a[1]:xs.append(F(0))
            vals=list(map(abs,xs))
            self.assertEqual(m.interval_absolute(a),(min(vals),max(vals)))
            self.assertEqual(m.interval_width(a),sum(y-x for x,y in zip(points(a),points(a)[1:])))
            if not a[0]<=0<=a[1]:
                vals=[1/x for x in xs]
                self.assertEqual(m.interval_reciprocal(a),(min(vals),max(vals)))
            for e in range(9):
                vals=[x**e for x in xs]
                self.assertEqual(m.interval_power(a,e),(min(vals),max(vals)))

    def test_all_entry_refusals(self):
        binary=[m.interval_add,m.interval_subtract,m.interval_multiply,m.interval_divide,m.interval_intersection,m.interval_hull]
        unary=[m.interval_reciprocal,m.interval_absolute,m.interval_width,lambda a:m.interval_power(a,1)]
        bads=[(None,TypeError,'interval must be a list or tuple'),(iter([0,1]),TypeError,'interval must be a list or tuple'),([True],ValueError,'interval must have two endpoints'),([True,False,0],ValueError,'interval must have two endpoints'),([True,0],TypeError,'endpoint must be int or Fraction'),([0.0,0],TypeError,'endpoint must be int or Fraction'),([float('inf'),0],TypeError,'endpoint must be int or Fraction'),([float('nan'),0],TypeError,'endpoint must be int or Fraction'),([-101,True],ValueError,'endpoint magnitude out of range'),([0,101],ValueError,'endpoint magnitude out of range'),([0,F(1,101)],ValueError,'endpoint denominator out of range'),([1,0],ValueError,'interval endpoints out of order'),([0,True],TypeError,'endpoint must be int or Fraction')]
        for func in binary:
            for bad,error,msg in bads:
                for a,b in ((bad,None),((0,1),bad)):
                    with self.assertRaisesRegex(error,'^'+msg+'$'):func(a,b)
            func((-100,100),(F(1,100),1))
        for func in unary:
            for bad,error,msg in bads:
                with self.assertRaisesRegex(error,'^'+msg+'$'):func(bad)
            func((F(1,100),100))
        self.assertFalse(m.CLAIMS)

    def test_maximum_bounds_and_nonclosure(self):
        self.assertEqual(m.interval_reciprocal((F(1,100), 100)), (F(1,100), 100))
        self.assertEqual(m.interval_multiply((-100, 100), (-100, 100)), (-10000, 10000))
        self.assertEqual(m.interval_divide((-100, 100), (F(1,100), 100)), (-10000, 10000))
        self.assertEqual(m.interval_width((-100, 100)), 200)
        self.assertEqual(m.interval_power((-100, 100), 8), (0, 100**8))
        # Arithmetic outputs are exact but not promised closed under input caps.
        for result in (m.interval_add((100,100),(100,100)), m.interval_multiply((-100,100),(-100,100)), m.interval_power((100,100),8)):
            with self.assertRaisesRegex(ValueError, "^endpoint magnitude out of range$"):
                m.interval_width(result)
        product = m.interval_multiply((F(1,100),F(1,100)),(F(1,100),F(1,100)))
        with self.assertRaisesRegex(ValueError, "^endpoint denominator out of range$"):
            m.interval_width(product)
        self.assertEqual(m.interval_hull(m.interval_intersection((-100,100),(0,100)),(-100,0)), (-100,100))

    def test_equivalent_survivor_boundaries(self):
        for a in ((0, 0), (0, 3), (-3, 0)):
            expected = (0, 0) if a == (0, 0) else (0, 3)
            self.assertEqual(m.interval_absolute(a), expected)
            for exponent in (2, 4, 6, 8):
                self.assertEqual(m.interval_power(a, exponent), (0, 0 if a == (0, 0) else 3**exponent))
        self.assertEqual(m.interval_intersection((0, 1), (1, 2)), (1, 1))
        self.assertEqual(m.interval_intersection((0, 1), (2, 3)), None)

    def test_zero_and_exponent_refusals(self):
        for a in ((-1,0),(0,0),(0,1),(-1,1)):
            with self.assertRaisesRegex(ValueError,'^interval contains zero$'):m.interval_reciprocal(a)
            with self.assertRaisesRegex(ValueError,'^interval contains zero$'):m.interval_divide((0,1),a)
        for exponent in (True,1.0,float('inf'),float('nan')):
            with self.assertRaisesRegex(TypeError,'^exponent must be an integer$'):m.interval_power((0,1),exponent)
        for exponent in (-1,9):
            with self.assertRaisesRegex(ValueError,'^exponent out of range$'):m.interval_power((0,1),exponent)
        with self.assertRaisesRegex(TypeError,'^interval must be a list or tuple$'):m.interval_power(None,True)
        self.assertEqual(m.interval_power((-100,100),8),(0,100**8))
        self.assertEqual(m.interval_power((0,0),0),(1,1))

if __name__=='__main__':unittest.main()
