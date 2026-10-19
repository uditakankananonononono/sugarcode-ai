import itertools
import math
import random
import unittest
from fractions import Fraction
import b446_cfrac as m


class _Hostile:
    def _no(self,other):return False
    __lt__=__le__=__gt__=__ge__=__eq__=__ne__=_no
    def __index__(self):raise RuntimeError("hostile __index__")
    def __iter__(self):raise RuntimeError("hostile __iter__")


class HInt(_Hostile,int):
    __hash__=int.__hash__


class HList(_Hostile,list):
    pass


class HTuple(_Hostile,tuple):
    pass


class HDict(_Hostile,dict):
    pass


class HStr(_Hostile,str):
    __hash__=str.__hash__


class HFraction(_Hostile,Fraction):
    pass


def frac_expand(x):
    # oracle: floor-and-reciprocal on Fractions
    out=[]
    while True:
        f=math.floor(x);out.append(f);x-=f
        if x==0:return out
        x=1/x


def frac_value(terms):
    x=Fraction(terms[-1])
    for a in reversed(terms[:-1]):x=a+1/x
    return x


def best_oracle(x,bound):
    best=None
    for q in range(1,bound+1):
        f=math.floor(x*q)
        for p in (f,f+1):
            key=(abs(x-Fraction(p,q)),q)
            if best is None or key<best[0]:best=(key,(p,q))
    p,q=best[1];g=math.gcd(p,q)
    return (p//g,q//g)


def rand_rationals(seed,count,top=300):
    rnd=random.Random(seed)
    return [(rnd.randint(-top,top),rnd.randint(1,top)) for _ in range(count)]


class CfracTests(unittest.TestCase):
    def test_metadata(self):
        self.assertIs(m.CLAIMS,False)
        self.assertTrue(m.SCOPE and m.NOT_CLAIMED)

    def test_expand_value_convergents(self):
        for n,d in rand_rationals(1,400)+[(0,1),(5,1),(-5,1),(1,2),(-1,2),(10**6,1),(10**6,10**6-1),(-10**6,10**6),(832040,514229),(-832040,514229)]:
            t=m.cf_expand(n,d);x=Fraction(n,d)
            self.assertEqual(list(t),frac_expand(x))
            self.assertEqual(frac_value(t),x)
            self.assertTrue(m.is_canonical(t))
            p,q=m.cf_value(t)
            self.assertEqual((p,q),(x.numerator,x.denominator))
            cv=m.convergents(t)
            self.assertEqual(cv,tuple((frac_value(t[:k+1]).numerator,frac_value(t[:k+1]).denominator) for k in range(len(t))))
            for (a,b),(c,e) in zip(cv,cv[1:]):self.assertEqual(abs(a*e-b*c),1)
        self.assertEqual(m.cf_expand(415,93),(4,2,6,7))
        self.assertEqual(m.cf_expand(-7,3),(-3,1,2))
        self.assertEqual(len(m.cf_expand(832040,514229)),28)

    def test_canonical_and_value_of_noncanonical(self):
        self.assertTrue(m.is_canonical([3]));self.assertTrue(m.is_canonical((1,2)))
        self.assertFalse(m.is_canonical((1,1)));self.assertFalse(m.is_canonical([0,3,1]))
        self.assertEqual(m.cf_value((2,1)),(3,1))
        self.assertEqual(m.cf_value((0,1)),(1,1))
        rnd=random.Random(5)
        for _ in range(300):
            t=[rnd.randint(-9,9)]+[rnd.randint(1,9) for _ in range(rnd.randint(0,6))]
            x=frac_value(t);self.assertEqual(m.cf_value(t),(x.numerator,x.denominator))
            self.assertEqual(m.is_canonical(t),len(t)==1 or t[-1]>1)

    def test_semiconvergents(self):
        rnd=random.Random(2)
        for _ in range(200):
            t=[rnd.randint(-5,5)]+[rnd.randint(1,6) for _ in range(rnd.randint(0,5))]
            got=m.semiconvergents(t)
            want=[(t[0],1)]
            cv=[(1,0)]+[(m.convergents(t)[k]) for k in range(len(t))]
            # cv[k+1] is convergent k; between convergents k-1 and k use parameter s
            for k in range(1,len(t)):
                (pm,qm),(pk,qk)=cv[k],cv[k+1]
                (pp,qp)=cv[k-1]
                for s in range(1,t[k]+1):want.append((s*pm+pp,s*qm+qp))
            self.assertEqual(got,tuple(want))
            self.assertEqual([c for c in got if c in m.convergents(t)][-1],m.cf_value(t))
        self.assertEqual(m.semiconvergents([2,3]),((2,1),(3,1),(5,2),(7,3)))

    def test_best_approximation(self):
        for n,d in rand_rationals(3,120,60):
            for bound in (1,2,3,5,8,13,40,200):
                x=Fraction(n,d)
                self.assertEqual(m.best_approximation(n,d,bound),best_oracle(x,bound),(n,d,bound))
        self.assertEqual(m.best_approximation(355,113,50),(22,7))
        self.assertEqual(m.best_approximation(1,2,1),(0,1))
        self.assertEqual(m.best_approximation(3,2,1),(1,1))
        self.assertEqual(m.best_approximation(7,5,10**6),(7,5))
        p,q=m.best_approximation(832040,514229,10**6);self.assertEqual((p,q),(832040,514229))

    def test_compare_negate(self):
        pool=[(n,d) for n in range(-9,10) for d in range(1,8)]
        pool+= [(10**6,1),(10**6-1,10**6),(-10**6,3)]
        exp={}
        for n,d in pool:exp[(n,d)]=m.cf_expand(n,d)
        rnd=random.Random(4)
        for _ in range(600):
            a,b=rnd.choice(pool),rnd.choice(pool)
            x,y=Fraction(*a),Fraction(*b)
            want=(x>y)-(x<y)
            self.assertEqual(m.cf_compare(exp[a],exp[b]),want)
            self.assertEqual(m.cf_compare(exp[b],exp[a]),-want)
        for a in pool:
            neg=m.cf_negate(exp[a]);x=Fraction(*a)
            self.assertEqual(neg,tuple(frac_expand(-x)),a)
            self.assertEqual(m.cf_negate(neg),exp[a])
        self.assertEqual(m.cf_negate([0,2]),(-1,2))
        self.assertEqual(m.cf_compare([1],[1,2]),-1)
        self.assertEqual(m.cf_compare([1,2],[1,3]),1)

    def test_gcd_and_steps(self):
        for a in range(0,40):
            for b in range(0,40):
                if a==0 and b==0:
                    for f in (m.extended_gcd,m.euclid_step_count):
                        with self.assertRaisesRegex(ValueError,"^a and b must not both be zero$"):f(a,b)
                    continue
                g,x,y=m.extended_gcd(a,b)
                self.assertEqual([type(v) for v in (g,x,y)],[int,int,int])
                self.assertEqual(g,math.gcd(a,b));self.assertEqual(a*x+b*y,g)
                if b>0:
                    self.assertTrue(0<=x<b//g)
                    sols=[s for s in range(b//g) if (g-a*s)%b==0]
                    self.assertEqual(sols,[x])
                else:self.assertEqual((x,y),(1,0))
                steps=0;u,v=a,b
                while v:u,v=v,u%v;steps+=1
                self.assertEqual(m.euclid_step_count(a,b),steps)
        g,x,y=m.extended_gcd(10**6,999999);self.assertEqual((g,10**6*x+999999*y),(1,1))
        self.assertEqual(m.extended_gcd(240,46),(2,14,-73))
        self.assertEqual(m.euclid_step_count(832040,514229),28)
        # composition: each Euclid division is one continued-fraction term (n>=0)
        for n in range(0,60):
            for d in range(1,60):
                self.assertEqual(len(m.cf_expand(n,d)),m.euclid_step_count(n,d))
        for n,d in rand_rationals(9,200):
            if n>=0:self.assertEqual(len(m.cf_expand(n,d)),m.euclid_step_count(n,d))

    def test_refusals_and_caps(self):
        C=10**6
        for f in (lambda v:m.cf_expand(v,1),lambda v:m.best_approximation(v,1,1)):
            for bad in (None,"1",1.0,True,[1],Fraction(1)):
                with self.assertRaisesRegex(TypeError,"^numerator must be an integer$"):f(bad)
            for bad in (C+1,-C-1):
                with self.assertRaisesRegex(ValueError,"^numerator out of range$"):f(bad)
            f(C);f(-C)
        for f in (lambda v:m.cf_expand(1,v),lambda v:m.best_approximation(1,v,1)):
            for bad in (None,"1",1.0,False,[1]):
                with self.assertRaisesRegex(TypeError,"^denominator must be an integer$"):f(bad)
            for bad in (0,-1,C+1):
                with self.assertRaisesRegex(ValueError,"^denominator out of range$"):f(bad)
            f(1);f(C)
        for bad in (None,"1",1.0,True):
            with self.assertRaisesRegex(TypeError,"^max_den must be an integer$"):m.best_approximation(1,2,bad)
        for bad in (0,-1,C+1):
            with self.assertRaisesRegex(ValueError,"^max_den out of range$"):m.best_approximation(1,2,bad)
        m.best_approximation(1,2,C)
        # both-bad order: numerator, then denominator, then max_den
        with self.assertRaisesRegex(TypeError,"^numerator must be an integer$"):m.cf_expand(None,0)
        with self.assertRaisesRegex(ValueError,"^numerator out of range$"):m.cf_expand(C+1,0)
        with self.assertRaisesRegex(TypeError,"^denominator must be an integer$"):m.best_approximation(1,None,0)
        with self.assertRaisesRegex(ValueError,"^denominator out of range$"):m.best_approximation(1,0,0)
        tf=(m.cf_value,m.convergents,m.is_canonical,m.semiconvergents)
        for f in tf+(lambda t:m.cf_compare(t,[1]),lambda t:m.cf_negate(t)):
            for bad in (None,5,"12",{1:2},{3},bytes([1,2])):
                with self.assertRaisesRegex(TypeError,"^terms must be a list or tuple$"):f(bad)
            for bad in ([],(),[1]*33):
                with self.assertRaisesRegex(ValueError,"^term count out of range$"):f(bad)
            f([1]*31+[2]);f([1]*32) if f in tf else None
            for bad in (None,"1",1.0,True,[1]):
                with self.assertRaisesRegex(TypeError,"^term must be an integer$"):f([bad,1])
                with self.assertRaisesRegex(TypeError,"^term must be an integer$"):f([1,bad])
            for bad in (C+1,-C-1):
                with self.assertRaisesRegex(ValueError,"^term out of range$"):f([bad,2])
            for bad in (0,-1):
                with self.assertRaisesRegex(ValueError,"^terms after the first must be positive$"):f([1,bad,2])
            f([C]);f([-C]);f([1,C])
            with self.assertRaisesRegex(ValueError,"^term out of range$"):f([1,C+1])
        # first-term errors come before later-term errors
        with self.assertRaisesRegex(TypeError,"^term must be an integer$"):m.cf_value([None,0])
        with self.assertRaisesRegex(ValueError,"^term out of range$"):m.cf_value([C+1,0])
        with self.assertRaisesRegex(ValueError,"^terms after the first must be positive$"):m.cf_value([1,0,2])
        for f in (lambda t:m.cf_compare(t,[1]),lambda t:m.cf_compare([1],t),m.cf_negate):
            with self.assertRaisesRegex(ValueError,"^terms must be canonical$"):f([1,1])
            with self.assertRaisesRegex(ValueError,"^terms must be canonical$"):f([0,2,1])
        with self.assertRaisesRegex(TypeError,"^terms must be a list or tuple$"):m.cf_compare(None,None)
        with self.assertRaisesRegex(TypeError,"^terms must be a list or tuple$"):m.cf_compare([1],None)
        for f in (m.extended_gcd,m.euclid_step_count):
            for bad in (None,"1",1.0,True,[1]):
                with self.assertRaisesRegex(TypeError,"^a must be an integer$"):f(bad,1)
                with self.assertRaisesRegex(TypeError,"^b must be an integer$"):f(1,bad)
            for bad in (-1,C+1):
                with self.assertRaisesRegex(ValueError,"^a out of range$"):f(bad,1)
                with self.assertRaisesRegex(ValueError,"^b out of range$"):f(1,bad)
            f(C,C);f(0,C);f(C,0)
            with self.assertRaisesRegex(ValueError,"^a out of range$"):f(C+1,-1)
            with self.assertRaisesRegex(TypeError,"^a must be an integer$"):f(None,-1)

    def test_cap_composition(self):
        C=10**6
        for n,d in ((C,1),(C,C-1),(C-1,C),(-C,C-1),(832040,514229),(C,999999),(1,C)):
            t=m.cf_expand(n,d)
            self.assertLessEqual(len(t),m.MAX_TERMS)
            self.assertEqual(m.cf_value(t),(Fraction(n,d).numerator,Fraction(n,d).denominator))
            self.assertEqual(m.cf_value(m.cf_negate(t)),(-Fraction(n,d).numerator,Fraction(n,d).denominator))
            m.convergents(t);m.semiconvergents(t);m.best_approximation(n,d,C)
            self.assertEqual(m.best_approximation(n,d,C),(Fraction(n,d).numerator,Fraction(n,d).denominator))
        # a 30-term maximum-length expansion still fits the 32-term cap, and all-ones 32 terms is accepted
        self.assertEqual(m.cf_value([1]*32),(3524578,2178309))
        self.assertEqual(len(m.semiconvergents([1]*32)),32)

    def test_hostile_subclasses_refused_per_function(self):
        calls={
         "cf_expand":(lambda a,b:m.cf_expand(a,b),[7,3]),
         "cf_value":(lambda a:m.cf_value(a),[[2,3,4]]),
         "convergents":(lambda a:m.convergents(a),[[2,3,4]]),
         "is_canonical":(lambda a:m.is_canonical(a),[[2,3,4]]),
         "semiconvergents":(lambda a:m.semiconvergents(a),[[2,3,4]]),
         "best_approximation":(lambda a,b,c:m.best_approximation(a,b,c),[7,3,5]),
         "cf_compare":(lambda a,b:m.cf_compare(a,b),[[2,3],[2,4]]),
         "cf_negate":(lambda a:m.cf_negate(a),[[2,3,4]]),
         "extended_gcd":(lambda a,b:m.extended_gcd(a,b),[12,18]),
         "euclid_step_count":(lambda a,b:m.euclid_step_count(a,b),[12,18]),
        }
        for name,(f,args) in calls.items():
            f(*args)
            for pos,a in enumerate(args):
                if type(a) is list:
                    for bad in (HList(a),HTuple(a),HDict(),HStr("ab"),"ab",{},HFraction(1,2)):
                        new=list(args);new[pos]=bad
                        with self.assertRaises(TypeError):f(*new)
                    for i in range(len(a)):
                        for bad in (HInt(a[i]),HFraction(a[i]),HInt(10**9)):
                            q=list(a);q[i]=bad;new=list(args);new[pos]=q
                            with self.assertRaisesRegex(TypeError,"^term must be an integer$"):f(*new)
                else:
                    for bad in (HInt(a),HInt(10**9),HInt(0),HFraction(a),HStr("1"),HList([a]),HTuple((a,)),HDict()):
                        new=list(args);new[pos]=bad
                        with self.assertRaisesRegex(TypeError," must be an integer$"):f(*new)


if __name__=="__main__":unittest.main()
