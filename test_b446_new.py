import itertools
import unittest
from fractions import Fraction as F
import b446_new as m


def population(law):
    return [x for x, w in law.items() for _ in range(w)]


class ProbabilityTests(unittest.TestCase):
    def test_all_operations_against_population_oracles(self):
        for weights in itertools.product(range(3), repeat=3):
            if not any(weights):
                continue
            law = dict(zip((-2, 0, 3), weights))
            xs = population(law)
            n = len(xs)
            mean = sum(map(F, xs))/n
            self.assertEqual(m.normalize(law), {x: F(xs.count(x), n) for x in law})
            self.assertEqual(m.expectation(law), mean)
            self.assertEqual(m.variance(law), F(sum(x*x for x in xs), n)-mean*mean)
            for k in range(9):
                self.assertEqual(m.raw_moment(law, k), sum((F(x)**k for x in xs), F())/n)
            for event in ([], [-2], [0, 3], [100]):
                self.assertEqual(m.event_probability(law, event), F(sum(x in event for x in xs), n))
            for t in (-100, -2, -1, 0, 3, 100):
                self.assertEqual(m.cumulative_probability(law, t), F(sum(x <= t for x in xs), n))
            for a in range(5):
                ordered = sorted(xs)
                index = max(0, (a*n+3)//4-1)
                self.assertEqual(m.quantile(law, a, 4), ordered[index])
            other = {-1: 2, 2: 1}
            ys = population(other)
            for operation, combine in ((m.convolution, lambda x,y:x+y), (m.independent_product, lambda x,y:x*y)):
                products = [combine(x,y) for x in xs for y in ys]
                expected = {combine(x,y): F(products.count(combine(x,y)), len(products)) for x in law for y in other}
                self.assertEqual(operation(law, other), expected)
            self.assertEqual(m.collision_probability(law), F(sum(a == b for a in xs for b in xs), n*n))

    def test_maximum_bounds_and_composition_contract(self):
        law = {x: 100 for x in range(85, 101)}
        normalized = m.normalize(law)
        self.assertEqual(sum(normalized.values()), 1)
        self.assertEqual(m.expectation(law), F(185, 2))
        for operation in (m.convolution, m.independent_product):
            result = operation(law, law)
            self.assertEqual(sum(result.values()), 1)
            self.assertEqual(list(result), sorted(result))
        # Outputs are probability laws, not integer-weight inputs; no closure promised.
        with self.assertRaisesRegex(TypeError, "^weight must be an integer$"):
            m.normalize(normalized)
        self.assertEqual(m.raw_moment({-100: 100, 100: 100}, 8), 100**8)
        self.assertEqual(m.variance({-100: 100, 100: 100}), 10000)
        self.assertEqual(m.quantile({-100: 100, 100: 100}, 100, 100), 100)

    def test_output_key_order(self):
        law = {3: 1, -2: 2, 0: 1}
        self.assertEqual(list(m.normalize(law)), [-2, 0, 3])
        other = {4: 1, -1: 1}
        sums = sorted({a+b for a in law for b in other})
        products = sorted({a*b for a in law for b in other})
        self.assertEqual(list(m.convolution(law, other)), sums)
        self.assertEqual(list(m.independent_product(law, other)), products)

    def test_law_refusals_all_entry_points(self):
        funcs = [lambda x:m.normalize(x), m.expectation, m.variance, lambda x:m.raw_moment(x, 0), lambda x:m.event_probability(x, []), lambda x:m.cumulative_probability(x, 0), lambda x:m.quantile(x, 0, 1), lambda x:m.convolution(x, {}), lambda x:m.independent_product(x, {}), m.collision_probability]
        cases = [(None, TypeError, 'law must be a dict'), ({}, ValueError, 'law size out of range'), (dict.fromkeys(range(17), 1), ValueError, 'law size out of range'), ({True: 1}, TypeError, 'value must be an integer'), ({1.0: 1}, TypeError, 'value must be an integer'), ({101: True}, ValueError, 'value out of range'), ({-101: 1}, ValueError, 'value out of range'), ({0: True}, TypeError, 'weight must be an integer'), ({0: 1.0}, TypeError, 'weight must be an integer'), ({0: -1}, ValueError, 'weight out of range'), ({0: 101}, ValueError, 'weight out of range'), ({0: 0}, ValueError, 'law must have positive mass')]
        for func in funcs:
            for value, error, message in cases:
                with self.subTest(func=func, value=value), self.assertRaisesRegex(error, '^'+message+'$'):
                    func(value)
        self.assertEqual(len(m.normalize(dict.fromkeys(range(16), 100))), 16)
        self.assertEqual(m.expectation({-100: 1, 100: 1}), 0)
        for func in (m.convolution, m.independent_product):
            with self.assertRaisesRegex(TypeError, '^law must be a dict$'):
                func({0: 1}, None)

    def test_argument_refusals_and_boundaries(self):
        law = {0: 1}
        for field, call, low, high in [('order', lambda x:m.raw_moment(law,x), 0,8), ('threshold',lambda x:m.cumulative_probability(law,x),-100,100), ('numerator',lambda x:m.quantile(law,x,100),0,100), ('denominator',lambda x:m.quantile(law,0,x),1,100)]:
            for bad in (True, 0.5, float('inf'), float('nan')):
                with self.assertRaisesRegex(TypeError, '^'+field+' must be an integer$'): call(bad)
            for bad in (low-1, high+1):
                with self.assertRaisesRegex(ValueError, '^'+field+' out of range$'): call(bad)
            call(low); call(high)
        for bad in (None, iter([1]), {1}):
            with self.assertRaisesRegex(TypeError, '^values must be a list or tuple$'):m.event_probability(law,bad)
        m.event_probability(law,list(range(16)))
        with self.assertRaisesRegex(ValueError,'^event size out of range$'):m.event_probability(law,[True]*17)
        for bad, error, text in [([True],TypeError,'value must be an integer'),([1.5],TypeError,'value must be an integer'),([101],ValueError,'value out of range'),([-101],ValueError,'value out of range'),([1,1],ValueError,'event values must be distinct')]:
            with self.assertRaisesRegex(error,'^'+text+'$'):m.event_probability(law,bad)
        with self.assertRaisesRegex(ValueError,'^quantile out of range$'):m.quantile(law,2,1)
        with self.assertRaisesRegex(TypeError,'^numerator must be an integer$'):m.quantile(law,True,False)
        with self.assertRaisesRegex(TypeError,'^law must be a dict$'):m.raw_moment(None,True)
        self.assertEqual(m.quantile({-100:0, 0:1, 100:0},0,1),0)
        self.assertFalse(m.CLAIMS)

if __name__ == '__main__': unittest.main()
