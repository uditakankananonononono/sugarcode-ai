import itertools
import unittest
from fractions import Fraction as F
import b446_metric as m


def defect_oracle(a):
    n=len(a);count=0
    for i in range(n):count+=a[i][i]!=0
    for i in range(n):
        for j in range(i+1,n):count+=not(a[i][j]>0 and a[i][j]==a[j][i])
    for i in range(n):
        for j in range(n):
            for k in range(n):count+=a[i][j]-a[i][k]-a[k][j]>0
    return count


class MetricTests(unittest.TestCase):
    def test_finite_oracles(self):
        examples=[((0,),)]
        for x,y,z in itertools.product(range(1,5),repeat=3):examples.append(((0,x,y),(x,0,z),(y,z,0)))
        examples+=[tuple(tuple(abs(i-j) for j in range(6)) for i in range(6)),tuple(tuple(0 if i==j else 100 for j in range(6)) for i in range(6)),((0,1,2,1),(1,0,1,2),(2,1,0,1),(1,2,1,0))]
        for a in examples:
            n=len(a);defects=defect_oracle(a)
            self.assertEqual(m.metric_defect_count(a),defects);self.assertEqual(m.is_metric(a),defects==0)
            if defects:
                with self.assertRaisesRegex(ValueError,'^matrix must be a metric$'):m.diameter(a)
                continue
            ecc=tuple(max(a[i][j] for j in range(n)) for i in range(n))
            self.assertEqual(m.diameter(a),max(x for row in a for x in row));self.assertEqual(m.eccentricities(a),ecc)
            self.assertEqual(m.radius(a),min(ecc));self.assertEqual(m.centers(a),tuple(i for i in range(n) if ecc[i]==min(ecc)))
            triangles=[sorted((a[i][j],a[i][k],a[j][k])) for i,j,k in itertools.combinations(range(n),3)]
            self.assertEqual(m.is_ultrametric(a),all(t[1]==t[2] for t in triangles))
            # Four distinct points suffice; repeated-point quadruples give zero.
            values=[0]
            for i,j,k,l in itertools.combinations(range(n),4):
                s=sorted((a[i][j]+a[k][l],a[i][k]+a[j][l],a[i][l]+a[j][k]))
                values.append(F(s[-1]-s[-2],2))
            self.assertEqual(m.four_point_hyperbolicity(a),max(values))
            for r in (0,1,2,100):
                subsets=[{i for i in range(n) if mask>>i&1} for mask in range(1<<n)]
                balls=[{j for j in range(n) if a[i][j]<=r} for i in range(n)]
                covers=[len(s) for s in subsets if set().union(*(balls[i] for i in s))==set(range(n))]
                packs=[len(s) for s in subsets if not any(a[i][j]<=r for i in s for j in s if i!=j)]
                self.assertEqual(m.covering_number(a,r),min(covers));self.assertEqual(m.packing_number(a,r),max(packs))
            self.assertEqual(m.covering_number(a,m.diameter(a)),1)
            self.assertEqual(m.packing_number(a,m.diameter(a)),1)

    def test_refusals_and_caps(self):
        funcs=[m.metric_defect_count,m.is_metric,m.diameter,m.eccentricities,m.radius,m.centers,m.is_ultrametric,m.four_point_hyperbolicity,lambda a:m.covering_number(a,True),lambda a:m.packing_number(a,True)]
        bads=[(None,TypeError,'matrix must be a list or tuple'),(iter([]),TypeError,'matrix must be a list or tuple'),([],ValueError,'point count out of range'),([None]*7,ValueError,'point count out of range'),([None],TypeError,'row must be a list or tuple'),([[True,False]],ValueError,'matrix must be square'),([[True]],TypeError,'distance must be an integer'),([[0.0]],TypeError,'distance must be an integer'),([[-1]],ValueError,'distance out of range'),([[101]],ValueError,'distance out of range')]
        for call in funcs:
            for a,error,msg in bads:
                with self.assertRaisesRegex(error,'^'+msg+'$'):call(a)
        invalid=[((1,),),((0,0),(0,0)),((0,1),(2,0)),((0,5,1),(5,0,1),(1,1,0))]
        for a in invalid:
            self.assertFalse(m.is_metric(a))
            for call in funcs[2:]:
                with self.assertRaisesRegex(ValueError,'^matrix must be a metric$'):call(a)
        for call in (m.covering_number,m.packing_number):
            for r in (True,1.0):
                with self.assertRaisesRegex(TypeError,'^radius must be an integer$'):call(((0,),),r)
            for r in (-1,101):
                with self.assertRaisesRegex(ValueError,'^radius out of range$'):call(((0,),),r)
        simultaneous=((1,0),(0,1))
        self.assertEqual(m.metric_defect_count(simultaneous),defect_oracle(simultaneous))
        self.assertEqual(m.metric_defect_count(simultaneous),5)
        self.assertFalse(m.CLAIMS)

if __name__=='__main__':unittest.main()
