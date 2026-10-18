import itertools
import unittest
from fractions import Fraction as F
import b446_quaternion as m


def oracle(a,b):
    # Basis multiplication sign/index table, separate from coordinate formula.
    table=(((1,0),(1,1),(1,2),(1,3)),((1,1),(-1,0),(1,3),(-1,2)),((1,2),(-1,3),(-1,0),(1,1)),((1,3),(1,2),(-1,1),(-1,0)))
    out=[F(0)]*4
    for i,x in enumerate(a):
        for j,y in enumerate(b):
            sign,k=table[i][j];out[k]+=sign*x*y
    return tuple(out)


class QuaternionTests(unittest.TestCase):
    def test_independent_oracles(self):
        qs=list(itertools.product((-1,0,1),repeat=4))+[(F(1,10),10,-10,0)]
        selected=[(0,0,0,0),(1,0,0,0),(0,1,0,0),(0,0,1,0),(0,0,0,1),(1,2,3,4)]
        one=(1,0,0,0)
        for a in qs:
            conj=(a[0],)+tuple(-x for x in a[1:]);norm=sum(x*x for x in a)
            self.assertEqual(m.conjugate(a),conj);self.assertEqual(m.norm_squared(a),norm)
            for b in selected:
                self.assertEqual(m.add(a,b),tuple(a[i]+b[i] for i in range(4)))
                self.assertEqual(m.subtract(a,b),tuple(a[i]-b[i] for i in range(4)))
                self.assertEqual(m.multiply(a,b),oracle(a,b))
                self.assertEqual(m.commutator(a,b),tuple(x-y for x,y in zip(oracle(a,b),oracle(b,a))))
                if any(b):
                    inv=tuple(F(x,sum(y*y for y in b)) for x in (b[0],-b[1],-b[2],-b[3]))
                    self.assertEqual(m.divide(a,b),oracle(a,inv))
            for exponent in range(9):
                result=one
                for _ in range(exponent):result=oracle(a,result)
                self.assertEqual(m.integer_power(a,exponent),result)
            if norm:
                inv=tuple(F(x,norm) for x in conj)
                self.assertEqual(m.inverse(a),inv);self.assertEqual(oracle(a,inv),one)
                vector=(1,2,3);w,x,y,z=a
                rotation=((w*w+x*x-y*y-z*z,2*(x*y-w*z),2*(x*z+w*y)),(2*(x*y+w*z),w*w-x*x+y*y-z*z,2*(y*z-w*x)),(2*(x*z-w*y),2*(y*z+w*x),w*w-x*x-y*y+z*z))
                expected=tuple(F(sum(c*v for c,v in zip(row,vector)),norm) for row in rotation)
                self.assertEqual(m.rotate_vector(a,vector),expected)
                self.assertEqual(sum(v*v for v in expected),14)

    def test_refusals_and_caps(self):
        funcs=[lambda a:m.add(a,None),lambda a:m.subtract(a,None),lambda a:m.multiply(a,None),m.conjugate,m.norm_squared,m.inverse,lambda a:m.divide(a,None),lambda a:m.commutator(a,None),lambda a:m.integer_power(a,True),lambda a:m.rotate_vector(a,None)]
        bads=[(None,TypeError,'quaternion must be a list or tuple'),(iter([]),TypeError,'quaternion must be a list or tuple'),([True]*5,ValueError,'quaternion size mismatch'),([True,0,0,0],TypeError,'component must be int or Fraction'),([0.0,0,0,0],TypeError,'component must be int or Fraction'),([11,True,0,0],ValueError,'component magnitude out of range'),([-11,0,0,0],ValueError,'component magnitude out of range'),([F(1,11),0,0,0],ValueError,'component denominator out of range')]
        for call in funcs:
            for a,error,msg in bads:
                with self.assertRaisesRegex(error,'^'+msg+'$'):call(a)
        for call in (m.add,m.subtract,m.multiply,m.divide,m.commutator):
            for a,error,msg in bads:
                with self.assertRaisesRegex(error,'^'+msg+'$'):call((1,0,0,0),a)
        cap=(10,-10,F(1,10),0)
        for call in (m.conjugate,m.norm_squared,m.inverse):call(cap)
        self.assertEqual(m.integer_power((10,0,0,0),8),(10**8,0,0,0))
        for exponent in (True,1.0):
            with self.assertRaisesRegex(TypeError,'^exponent must be an integer$'):m.integer_power(cap,exponent)
        for exponent in (-1,9):
            with self.assertRaisesRegex(ValueError,'^exponent out of range$'):m.integer_power(cap,exponent)
        for call in (m.inverse,lambda a:m.divide(cap,a),lambda a:m.rotate_vector(a,(0,0,0))):
            with self.assertRaisesRegex(ValueError,'^quaternion must be nonzero$'):call((0,0,0,0))
        for vector,error,msg in [(None,TypeError,'vector must be a list or tuple'),([True]*4,ValueError,'vector size mismatch'),([True,0,0],TypeError,'component must be int or Fraction'),([11,0,0],ValueError,'component magnitude out of range')]:
            with self.assertRaisesRegex(error,'^'+msg+'$'):m.rotate_vector(cap,vector)
        self.assertFalse(m.CLAIMS)

if __name__=='__main__':unittest.main()
