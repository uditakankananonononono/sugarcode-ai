import itertools
import math
import unittest
import b446_sequences as m


def dyck_count(n,flat):
    # lattice paths of length n staying >=0, ending at 0; flat steps allowed if flat
    ways={0:1}
    for _ in range(n):
        new={}
        for h,c in ways.items():
            for d in ((1,-1,0) if flat else (1,-1)):
                if h+d>=0:new[h+d]=new.get(h+d,0)+c
        ways=new
    return ways.get(0,0)


def set_partitions(items):
    if not items:yield [];return
    first,rest=items[0],items[1:]
    for p in set_partitions(rest):
        yield [[first]]+p
        for i in range(len(p)):yield p[:i]+[[first]+p[i]]+p[i+1:]


def cycles(perm):
    seen=set();c=0
    for i in range(len(perm)):
        if i not in seen:
            c+=1;j=i
            while j not in seen:seen.add(j);j=perm[j]
    return c


def surj(n,k):
    return sum((-1)**(k-j)*math.comb(k,j)*j**n for j in range(k+1))


def poly_rising(n):
    poly=[1]
    for i in range(n):
        new=[0]*(len(poly)+1)
        for d,c in enumerate(poly):
            new[d+1]+=c;new[d]+=i*c
        poly=new
    return poly


class SequenceTests(unittest.TestCase):
    def test_fibonacci_lucas(self):
        ref=[]
        for n in range(42):
            a,b,c,d=1,0,0,1
            for _ in range(n):a,b,c,d=a+b,a,c+d,c
            ref.append(c)
        for n in range(41):
            self.assertEqual(m.fibonacci(n),ref[n])
            self.assertEqual(m.lucas(n),2 if n==0 else ref[n-1]+ref[n+1])
            if n:self.assertEqual(ref[n]**2-ref[n-1]*ref[n+1],-(-1)**n)
            self.assertEqual(ref[n],sum(math.comb(n-1-k,k) for k in range(n) if n-1-k>=k) if n else 0)
        self.assertEqual((m.fibonacci(40),m.lucas(40)),(102334155,228826127))

    def test_pisano(self):
        for k in range(1,65):
            seq=[0,1%k];i=0
            while True:
                seq.append((seq[-1]+seq[-2])%k);i+=1
                if seq[-2:]==[0,1%k] and len(seq)>2:break
            self.assertEqual(m.pisano_period(k),len(seq)-2)
        self.assertEqual([m.pisano_period(k) for k in (1,2,3,10,64)],[1,3,8,60,96])

    def test_catalan_motzkin(self):
        for n in range(41):
            self.assertEqual(m.catalan(n),math.comb(2*n,n)//(n+1))
            self.assertEqual(m.catalan(n)*(n+1),math.comb(2*n,n))
            if n<=14:
                self.assertEqual(m.catalan(n),dyck_count(2*n,False))
                self.assertEqual(m.motzkin(n),dyck_count(n,True))
            self.assertEqual(m.motzkin(n),sum(math.comb(n,2*k)*m.catalan(k) for k in range(n//2+1)))

    def test_stirling_bell(self):
        for n in range(0,8):
            parts=list(set_partitions(list(range(n))))
            self.assertEqual(m.bell(n),len(parts))
            perms=list(itertools.permutations(range(n)))
            for k in range(0,n+3):
                self.assertEqual(m.stirling2(n,k),sum(len(p)==k for p in parts))
                self.assertEqual(m.stirling1_unsigned(n,k),sum(cycles(p)==k for p in perms))
        for n in range(0,41):
            self.assertEqual(m.bell(n),sum(m.stirling2(n,k) for k in range(41)))
            self.assertEqual(sum(m.stirling1_unsigned(n,k) for k in range(41)),math.factorial(n))
            poly=poly_rising(n)
            for k in range(41):
                self.assertEqual(m.stirling1_unsigned(n,k),poly[k] if k<len(poly) else 0)
                self.assertEqual(m.stirling2(n,k)*math.factorial(k),surj(n,k))
        self.assertEqual(m.stirling2(40,40),1);self.assertEqual(m.stirling1_unsigned(40,0),0)

    def test_delannoy_recurrence(self):
        for a in range(0,9):
            for b in range(0,9):
                self.assertEqual(m.delannoy(a,b),sum(math.comb(a,k)*math.comb(b,k)*2**k for k in range(min(a,b)+1)))
                self.assertEqual(m.delannoy(a,b),m.delannoy(b,a))
        self.assertEqual(m.delannoy(40,40),sum(math.comb(40,k)**2*2**k for k in range(41)))
        self.assertEqual(m.delannoy(0,40),1)
        for n in range(41):
            self.assertEqual(m.linear_recurrence_term([1,1],[0,1],n),m.fibonacci(n))
            self.assertEqual(m.linear_recurrence_term((1,1),(2,1),n),m.lucas(n))
        for n in range(41):
            self.assertEqual(m.linear_recurrence_term([2,-1],[0,1],n),n)
            self.assertEqual(m.linear_recurrence_term([3],[1],n),3**n)
        coef=[100,-100,1,2,3,4,5,6];seq=[1,2,3,4,5,6,7,8]
        for _ in range(33):seq.append(sum(c*seq[-1-i] for i,c in enumerate(coef)))
        self.assertEqual(m.linear_recurrence_term(coef,[1,2,3,4,5,6,7,8],40),seq[40])
        self.assertEqual(m.linear_recurrence_term(tuple(coef),tuple(seq[:8]),39),seq[39])

    def test_refusals_and_caps(self):
        one=[m.fibonacci,m.lucas,m.catalan,m.bell,m.motzkin,lambda n:m.stirling2(n,0),lambda n:m.stirling1_unsigned(n,0),lambda n:m.linear_recurrence_term([1],[1],n)]
        for f in one:
            for bad in (True,1.0,float('nan'),'1',None):
                with self.assertRaisesRegex(TypeError,'^n must be an integer$'):f(bad)
            for bad in (-1,41):
                with self.assertRaisesRegex(ValueError,'^n out of range$'):f(bad)
            f(0);f(40)
        for bad in (True,1.0):
            with self.assertRaisesRegex(TypeError,'^k must be an integer$'):m.stirling2(1,bad)
            with self.assertRaisesRegex(TypeError,'^k must be an integer$'):m.stirling1_unsigned(1,bad)
            with self.assertRaisesRegex(TypeError,'^m must be an integer$'):m.delannoy(bad,1)
            with self.assertRaisesRegex(TypeError,'^n must be an integer$'):m.delannoy(1,bad)
            with self.assertRaisesRegex(TypeError,'^modulus must be an integer$'):m.pisano_period(bad)
        for bad in (-1,41):
            with self.assertRaisesRegex(ValueError,'^k out of range$'):m.stirling2(1,bad)
            with self.assertRaisesRegex(ValueError,'^k out of range$'):m.stirling1_unsigned(1,bad)
            with self.assertRaisesRegex(ValueError,'^m out of range$'):m.delannoy(bad,1)
            with self.assertRaisesRegex(ValueError,'^n out of range$'):m.delannoy(1,bad)
        for bad in (0,65):
            with self.assertRaisesRegex(ValueError,'^modulus out of range$'):m.pisano_period(bad)
        m.pisano_period(1);m.pisano_period(64);m.stirling2(0,40);m.stirling2(40,0);m.delannoy(40,0);m.delannoy(0,40)
        # both-bad order: first argument reported first
        with self.assertRaisesRegex(TypeError,'^n must be an integer$'):m.stirling2(True,41)
        with self.assertRaisesRegex(ValueError,'^n out of range$'):m.stirling2(41,True)
        with self.assertRaisesRegex(ValueError,'^m out of range$'):m.delannoy(41,True)
        with self.assertRaisesRegex(TypeError,'^m must be an integer$'):m.delannoy(True,41)

    def test_recurrence_refusals(self):
        f=m.linear_recurrence_term
        for bad in (None,iter([1]),'1',{1:1}):
            with self.assertRaisesRegex(TypeError,'^coefficients must be a list or tuple$'):f(bad,[1],0)
            with self.assertRaisesRegex(TypeError,'^initial must be a list or tuple$'):f([1],bad,0)
        with self.assertRaisesRegex(TypeError,'^coefficients must be a list or tuple$'):f(None,None,True)
        for bad in ([],[1]*9):
            with self.assertRaisesRegex(ValueError,'^order out of range$'):f(bad,[1]*len(bad),0)
        f([1]*8,[1]*8,0)
        with self.assertRaisesRegex(ValueError,'^initial length must equal order$'):f([1,1],[1],0)
        with self.assertRaisesRegex(ValueError,'^initial length must equal order$'):f([1],[1,1],0)
        for bad in (True,1.0,None):
            with self.assertRaisesRegex(TypeError,'^coefficient must be an integer$'):f([bad],[1],0)
            with self.assertRaisesRegex(TypeError,'^initial value must be an integer$'):f([1],[bad],0)
        for bad in (-101,101):
            with self.assertRaisesRegex(ValueError,'^coefficient out of range$'):f([bad],[1],0)
            with self.assertRaisesRegex(ValueError,'^initial value out of range$'):f([1],[bad],0)
        f([100,-100],[-100,100],0);f([-100],[100],0)
        # ordering: coefficients before initial before n
        with self.assertRaisesRegex(ValueError,'^coefficient out of range$'):f([101],[101],41)
        with self.assertRaisesRegex(ValueError,'^initial value out of range$'):f([1],[101],41)
        with self.assertRaisesRegex(TypeError,'^coefficient must be an integer$'):f([True],[101],41)
        with self.assertRaisesRegex(ValueError,'^order out of range$'):f([],[1],41)
        with self.assertRaisesRegex(ValueError,'^n out of range$'):f([1],[1],41)
        self.assertFalse(m.CLAIMS)

if __name__=='__main__':unittest.main()
