import itertools
import unittest
from fractions import Fraction as F
import b446_matrices as m


def permutation_det(a):
    total=0
    for p in itertools.permutations(range(len(a))):
        inversions=sum(p[i]>p[j] for i in range(len(p)) for j in range(i+1,len(p)))
        term=(-1)**inversions
        for i,j in enumerate(p):term*=a[i][j]
        total+=term
    return total


def multiply(a,b):
    return tuple(tuple(sum(x*y for x,y in zip(row,col)) for col in zip(*b)) for row in a)


def rank_by_minors(a):
    n=len(a);width=len(a[0])
    for size in range(min(n,width),0,-1):
        for rows in itertools.combinations(range(n),size):
            for cols in itertools.combinations(range(width),size):
                if permutation_det([[a[i][j] for j in cols] for i in rows]):return size
    return 0


def permanent_subsets(a):
    # Ryser's inclusion-exclusion algorithm, not permutation enumeration.
    n=len(a);total=0
    for mask in range(1<<n):
        term=(-1)**(n-mask.bit_count())
        for row in a:term*=sum(row[j] for j in range(n) if mask>>j&1)
        total+=term
    return total


class MatrixTests(unittest.TestCase):
    def test_independent_oracles(self):
        matrices=[((x,),) for x in (-2,-1,0,1,2)]
        matrices += [tuple(tuple(v[i*2:i*2+2]) for i in range(2)) for v in itertools.product((-1,0,1),repeat=4)]
        matrices += [((0,1,2),(1,0,1),(2,1,0)),((1,2,3),(2,4,6),(0,0,0)),((0,0,1),(0,1,0),(1,0,0)),((1,2,0,0),(0,1,3,0),(0,0,1,4),(0,0,0,1))]
        for a in matrices:
            n=len(a);d=permutation_det(a);r=rank_by_minors(a)
            identity=tuple(tuple(int(i==j) for j in range(n)) for i in range(n))
            self.assertEqual(m.determinant(a),d)
            self.assertEqual(m.permanent(a),permanent_subsets(a))
            self.assertEqual(m.rank(a),r);self.assertEqual(m.nullity(a),n-r)
            self.assertEqual(m.trace(a),sum(a[i][i] for i in range(n)))
            self.assertEqual(m.gram_matrix(a),multiply(tuple(zip(*a)),a))
            adj=m.adjugate(a)
            self.assertEqual(multiply(a,adj),tuple(tuple(d*x for x in row) for row in identity))
            self.assertEqual(multiply(adj,a),tuple(tuple(d*x for x in row) for row in identity))
            # Each adjugate entry is independently the signed determinant derivative.
            expected=[]
            for i in range(n):
                row=[]
                for j in range(n):
                    changed=[list(row) for row in a];changed[j][i]+=1
                    row.append(permutation_det(changed)-d)
                expected.append(tuple(row))
            self.assertEqual(adj,tuple(expected))
            reduced=m.rref(a)
            self.assertEqual(rank_by_minors(tuple(a)+reduced),r)
            nonzero=[row for row in reduced if any(row)]
            self.assertEqual(len(nonzero),r)
            pivots=[next(i for i,x in enumerate(row) if x) for row in nonzero]
            self.assertEqual(pivots,sorted(set(pivots)))
            for i,col in enumerate(pivots):self.assertEqual(tuple(row[col] for row in reduced),tuple(int(j==i) for j in range(n)))
            if d:
                inv=m.inverse(a)
                self.assertEqual(inv,tuple(tuple(F(x,d) for x in row) for row in adj))
                self.assertEqual(reduced,identity)
                b=tuple(range(n))
                result=m.solve(a,b)
                self.assertEqual(multiply(a,tuple((x,) for x in result)),tuple((x,) for x in b))
                cramer=[]
                for j in range(n):
                    changed=[list(row) for row in a]
                    for i in range(n):changed[i][j]=b[i]
                    cramer.append(F(permutation_det(changed),d))
                self.assertEqual(result,tuple(cramer))
            else:
                with self.assertRaisesRegex(ValueError,'^matrix is singular$'):m.inverse(a)
                with self.assertRaisesRegex(ValueError,'^matrix is singular$'):m.solve(a,[0]*n)

    def test_maximum_bounds_and_composition_contract(self):
        a = ((100, 0, 0, 0), (0, -100, 0, 0), (0, 0, 100, 0), (0, 0, 0, 100))
        identity = tuple(tuple(int(i==j) for j in range(4)) for i in range(4))
        self.assertEqual(multiply(a, m.inverse(a)), identity)
        self.assertEqual(multiply(a, tuple((x,) for x in m.solve(a, (100,-100,100,-100)))), ((100,),(-100,),(100,),(-100,)))
        self.assertEqual(m.determinant(a), -100**4)
        # Public inputs are capped integers; Fraction outputs are not promised closed.
        with self.assertRaisesRegex(TypeError, "^entry must be an integer$"):
            m.determinant(m.inverse(a))
        with self.assertRaisesRegex(ValueError, "^entry out of range$"):
            m.determinant(m.gram_matrix(a))
        with self.assertRaisesRegex(ValueError, "^entry out of range$"):
            m.determinant(m.adjugate(a))
        self.assertEqual(m.determinant(identity), 1)

    def test_refusals_caps_and_rhs(self):
        funcs=[m.determinant,m.permanent,m.rank,m.nullity,m.inverse,m.adjugate,lambda a:m.solve(a,[0]*len(a)),m.trace,m.gram_matrix,m.rref]
        # solve wrapper must not pre-read invalid input before matrix validation.
        funcs[6]=lambda a:m.solve(a,[0,0])
        bads=[(None,TypeError,'matrix must be a list or tuple'),(iter([]),TypeError,'matrix must be a list or tuple'),([],ValueError,'dimension out of range'),([None]*5,ValueError,'dimension out of range'),([None],TypeError,'row must be a list or tuple'),([[True,False]],ValueError,'matrix must be square'),([[True]],TypeError,'entry must be an integer'),([[1.0]],TypeError,'entry must be an integer'),([[101]],ValueError,'entry out of range'),([[-101]],ValueError,'entry out of range')]
        cap=((100,0,0,0),(0,-100,0,0),(0,0,100,0),(0,0,0,100))
        for call in funcs:
            for bad,error,msg in bads:
                with self.assertRaisesRegex(error,'^'+msg+'$'):call(bad)
            if call!=funcs[6]:call(cap)
        m.solve(cap,[100,-100,100,100])
        for rhs,error,msg in [(None,TypeError,'rhs must be a list or tuple'),([True]*5,ValueError,'rhs size mismatch'),([True],TypeError,'entry must be an integer'),([1.0],TypeError,'entry must be an integer'),([101],ValueError,'entry out of range'),([-101],ValueError,'entry out of range')]:
            with self.assertRaisesRegex(error,'^'+msg+'$'):m.solve([[1]],rhs)
        with self.assertRaisesRegex(TypeError,'^matrix must be a list or tuple$'):m.solve(None,True)
        with self.assertRaisesRegex(ValueError,'^matrix must be square$'):m.trace([[True,0],[0]])
        self.assertFalse(m.CLAIMS)

if __name__=='__main__':unittest.main()
