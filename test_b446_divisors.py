import itertools
import math
import unittest
import b446_divisors as m


def recursive_mu(n,cache=None):
    if n==1:return 1
    return -sum(recursive_mu(d) for d in range(1,n) if n%d==0)


def prime_factors(n):
    return [p for p in range(2,n+1) if n%p==0 and all(p%d for d in range(2,p))]


class DivisorTests(unittest.TestCase):
    def test_all_bounded_integers(self):
        for n in range(1,65):
            ds=tuple(d for d in range(1,n+1) if any(d*q==n for q in range(1,n+1)))
            self.assertEqual(m.divisors(n),ds)
            self.assertEqual(m.divisor_count(n),len(ds));self.assertEqual(m.divisor_sum(n),sum(ds))
            self.assertEqual(m.mobius(n),recursive_mu(n))
            phi=n
            for p in prime_factors(n):phi=phi//p*(p-1)
            self.assertEqual(m.totient(n),phi)
            jordan=sum(math.gcd(math.gcd(a,b),n)==1 for a in range(n) for b in range(n))
            self.assertEqual(m.jordan_totient_two(n),jordan)
            self.assertIs(type(m.jordan_totient_two(n)),int)
            for k in range(-64,65):
                # Orthogonality recurrence from all n-th roots, without complex floats.
                values={}
                for d in ds:
                    values[d]=(d if k%d==0 else 0)-sum(values[e] for e in values if d%e==0)
                self.assertEqual(m.ramanujan_sum(n,k),values[n])
                self.assertIs(type(m.ramanujan_sum(n,k)),int)
            self.assertEqual(sum(m.mobius(d) for d in ds),int(n==1))
            self.assertEqual(sum(m.totient(d) for d in ds),n)

    def test_vector_oracles_and_composition(self):
        examples=[(1,),(-2,3,0,1),tuple((i%5)-2 for i in range(64)),(1,)*64]
        for a in examples:
            size=len(a)
            z=[];inverted=[]
            for n in range(1,size+1):
                z.append(sum(a[d-1] for d in range(1,n+1) if n%d==0))
                inverted.append(a[n-1]-sum(inverted[d-1] for d in range(1,n) if n%d==0))
            self.assertEqual(m.divisor_zeta(a),tuple(z))
            self.assertEqual(m.divisor_mobius_inverse(a),tuple(inverted))
            self.assertTrue(all(type(x) is int for x in m.divisor_mobius_inverse(a)))
            self.assertEqual(m.divisor_mobius_inverse(z),a)
            b=tuple(reversed(a))
            expected=tuple(sum(a[i-1]*b[j-1] for i in range(1,n+1) for j in range(1,n+1) if i*j==n) for n in range(1,size+1))
            self.assertEqual(m.dirichlet_convolution(a,b),expected)
            identity=(1,)+(0,)*(size-1)
            self.assertEqual(m.dirichlet_convolution(a,identity),a)
        cap=(100,)*64
        self.assertEqual(m.divisor_zeta(cap)[-1],700)
        with self.assertRaisesRegex(ValueError,'^entry out of range$'):m.divisor_mobius_inverse(m.divisor_zeta(cap))

    def test_refusals_and_caps(self):
        funcs=[m.divisors,m.divisor_count,m.divisor_sum,m.mobius,m.totient,m.jordan_totient_two,lambda n:m.ramanujan_sum(n,True)]
        for call in funcs:
            for bad in (True,1.0,float('inf'),float('nan')):
                with self.assertRaisesRegex(TypeError,'^n must be an integer$'):call(bad)
            for bad in (0,65):
                with self.assertRaisesRegex(ValueError,'^n out of range$'):call(bad)
        for bad in (True,1.0):
            with self.assertRaisesRegex(TypeError,'^k must be an integer$'):m.ramanujan_sum(64,bad)
        for bad in (-65,65):
            with self.assertRaisesRegex(ValueError,'^k out of range$'):m.ramanujan_sum(64,bad)
        bads=[(None,TypeError,'values must be a list or tuple'),(iter([]),TypeError,'values must be a list or tuple'),([],ValueError,'vector size out of range'),([True]*65,ValueError,'vector size out of range'),([True],TypeError,'entry must be an integer'),([1.0],TypeError,'entry must be an integer'),([101],ValueError,'entry out of range'),([-101],ValueError,'entry out of range')]
        for call in (m.divisor_zeta,m.divisor_mobius_inverse,lambda a:m.dirichlet_convolution(a,None)):
            for bad,error,msg in bads:
                with self.assertRaisesRegex(error,'^'+msg+'$'):call(bad)
        for bad,error,msg in bads:
            with self.assertRaisesRegex(error,'^'+msg+'$'):m.dirichlet_convolution([1],bad)
        with self.assertRaisesRegex(ValueError,'^vector sizes must agree$'):m.dirichlet_convolution([1],[1,2])
        m.dirichlet_convolution([-100]*64,[100]*64)
        self.assertFalse(m.CLAIMS)

if __name__=='__main__':unittest.main()
