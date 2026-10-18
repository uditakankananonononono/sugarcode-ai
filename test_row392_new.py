import itertools
import unittest
from fractions import Fraction as F
import row392_new as m


def determinant(matrix):
    if not matrix: return 1
    return sum((-1)**j*matrix[0][j]*determinant([r[:j]+r[j+1:] for r in matrix[1:]]) for j in range(len(matrix)))


def recursive_value(ts):
    return F(ts[0]) if len(ts)==1 else ts[0]+1/recursive_value(ts[1:])


class ContinuedTests(unittest.TestCase):
    def test_sequences_independent_algorithms(self):
        for size in range(1,5):
            for tail in itertools.product((1,2,3), repeat=size-1):
                for first in (-2,0,2):
                    ts=(first,)+tail
                    self.assertEqual(m.evaluate(ts), recursive_value(ts))
                    self.assertEqual(m.convergents(ts),tuple(recursive_value(ts[:i]) for i in range(1,size+1)))
                    matrix=[[ts[i] if i==j else 1 if j==i+1 else -1 if i==j+1 else 0 for j in range(size)] for i in range(size)]
                    self.assertEqual(m.continuant(ts),determinant(matrix))
                    self.assertEqual(m.convergent_determinants(ts),tuple((-1)**(i+1) for i in range(size)))
                    expected=[]
                    for i in range(1,size):
                        for k in range(1,ts[i]+1):expected.append(recursive_value(ts[:i]+(k,)))
                    self.assertEqual(m.intermediate_convergents(ts),tuple(expected))

    def test_rationals_and_brute_approximation(self):
        for p in range(-15,16):
            for q in range(1,13):
                target=F(p,q); ts=m.expand(p,q)
                self.assertEqual(recursive_value(ts),target)
                self.assertTrue(len(ts)==1 or ts[-1]>=2)
                self.assertEqual(m.convergent_errors(p,q),tuple(target-recursive_value(ts[:i]) for i in range(1,len(ts)+1)))
                self.assertEqual(m.rational_floor(p,q),target.numerator//target.denominator)
                for r,s in ((0,1),(-3,2),(5,7)):
                    other=F(r,s)
                    self.assertEqual(m.rational_compare(p,q,r,s),int(target>other)-int(target<other))
                for limit in (1,2,5):
                    candidates={F(n,d) for d in range(1,limit+1) for n in range(-16*limit,16*limit+1)}
                    best=sorted(candidates,key=lambda x:(abs(x-target),x.denominator,x.numerator))[0]
                    self.assertEqual(m.best_approximation(p,q,limit),best)

    def test_long_euclidean_expansion_composition(self):
        for p, q in ((4181, 6765), (6765, 4181), (-4181, 6765), (9999, 10000), (-10000, 9999)):
            ts = m.expand(p, q)
            target = F(p, q)
            self.assertEqual(recursive_value(ts), target)
            self.assertEqual(m.convergent_errors(p, q), tuple(target-recursive_value(ts[:i]) for i in range(1, len(ts)+1)))
            self.assertEqual(m.convergent_errors(p, q)[-1], 0)
        self.assertGreater(len(m.expand(4181, 6765)), 16)
        with self.assertRaisesRegex(ValueError, "^terms size out of range$"):
            m.convergents(m.expand(4181, 6765))

    def test_pair_refusals(self):
        funcs=[m.expand,m.convergent_errors,m.rational_floor,lambda p,q:m.best_approximation(p,q,1),lambda p,q:m.rational_compare(p,q,0,1),lambda p,q:m.rational_compare(0,1,p,q)]
        for call in funcs:
            for p,q,err,msg in [(True,0,TypeError,'numerator must be an integer'),(1.0,1,TypeError,'numerator must be an integer'),(10001,False,ValueError,'numerator out of range'),(-10001,1,ValueError,'numerator out of range'),(0,True,TypeError,'denominator must be an integer'),(0,1.0,TypeError,'denominator must be an integer'),(0,0,ValueError,'denominator out of range'),(0,10001,ValueError,'denominator out of range')]:
                with self.assertRaisesRegex(err,'^'+msg+'$'):call(p,q)
            call(-10000,10000);call(10000,1)

    def test_terms_refusals_and_caps(self):
        funcs=[m.evaluate,m.convergents,m.continuant,m.convergent_determinants,m.intermediate_convergents]
        for call in funcs:
            for ts,err,msg in [(None,TypeError,'terms must be a list or tuple'),(iter([1]),TypeError,'terms must be a list or tuple'),([],ValueError,'terms size out of range'),([True]*17,ValueError,'terms size out of range'),([True],TypeError,'coefficient must be an integer'),([1.0],TypeError,'coefficient must be an integer'),([10001],ValueError,'coefficient out of range'),([-10001],ValueError,'coefficient out of range'),([0,True],TypeError,'coefficient must be an integer'),([0,0],ValueError,'coefficient out of range'),([0,10001],ValueError,'coefficient out of range')]:
                with self.assertRaisesRegex(err,'^'+msg+'$'):call(ts)
            call([1]*16);call([-10000]);call([10000])
            if call!=m.intermediate_convergents:call([0,10000])
        self.assertEqual(len(m.intermediate_convergents([0,512])),512)
        with self.assertRaisesRegex(ValueError,'^intermediate count out of range$'):m.intermediate_convergents([0,513])
        for bad in (True,1.0,float('nan'),float('inf')):
            with self.assertRaisesRegex(TypeError,'^limit must be an integer$'):m.best_approximation(1,2,bad)
        for bad in (0,33):
            with self.assertRaisesRegex(ValueError,'^limit out of range$'):m.best_approximation(1,2,bad)
        self.assertEqual(m.best_approximation(1,2,1),0)
        self.assertEqual(m.best_approximation(1,2,32),F(1,2))
        with self.assertRaisesRegex(TypeError,'^numerator must be an integer$'):m.best_approximation(True,0,False)
        self.assertFalse(m.CLAIMS)

if __name__ == '__main__': unittest.main()
