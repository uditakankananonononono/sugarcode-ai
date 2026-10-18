import itertools
import math
import unittest
from fractions import Fraction as F
import b446_games as m


class GameTests(unittest.TestCase):
    def test_exact_oracles(self):
        examples=[(0,(0,)),(1,(0,3))]
        examples += [(2,(0,)+v) for v in itertools.product((-1,0,2),repeat=3)]
        examples += [(3,tuple(mask.bit_count()**2 for mask in range(8))),(3,tuple(int(mask==7)*6 for mask in range(8)))]
        for n,data in examples:
            for mask in range(1<<n):
                self.assertEqual(m.coalition_value(n,data,mask),data[mask])
                for i in range(n):
                    if not mask>>i&1:self.assertEqual(m.marginal_contribution(n,data,mask,i),data[mask+2**i]-data[mask])
            totals=[0]*n
            for order in itertools.permutations(range(n)):
                mask=0
                for i in order:
                    new=mask+2**i;totals[i]+=data[new]-data[mask];mask=new
            expected=tuple(F(x,math.factorial(n)) for x in totals)
            self.assertEqual(m.shapley_values(n,data),expected)
            subsets=[tuple(i for i in range(n) if mask>>i&1) for mask in range(1<<n)]
            banzhaf=[]
            for i in range(n):
                increments=[]
                for subset in subsets:
                    if i not in subset:
                        mask=sum(2**j for j in subset);increments.append(data[mask+2**i]-data[mask])
                banzhaf.append(F(sum(increments),len(increments)))
            self.assertEqual(m.banzhaf_values(n,data),tuple(banzhaf))
            dividends=[];reconstructed=[]
            for mask in range(1<<n):
                terms=[sub for sub in range(1<<n) if sub&mask==sub]
                dividends.append(sum((-1)**(mask.bit_count()-sub.bit_count())*data[sub] for sub in terms))
                reconstructed.append(sum(data[sub] for sub in terms))
            self.assertEqual(m.mobius_dividends(n,data),tuple(dividends))
            self.assertEqual(m.reconstruct_values(n,data),tuple(reconstructed))
            self.assertEqual(m.reconstruct_values(n,dividends),data)
            full=(1<<n)-1
            dual=tuple(data[full]-data[sum(2**i for i in range(n) if not mask>>i&1)] for mask in range(1<<n))
            self.assertEqual(m.dual_values(n,data),dual)
            monotone=all(data[a]<=data[b] for a in range(1<<n) for b in range(1<<n) if a&b==a)
            self.assertEqual(m.is_monotone(n,data),monotone)
            superadd=True
            for assignment in itertools.product((0,1,2),repeat=n):
                a=sum(2**i for i,x in enumerate(assignment) if x==1)
                b=sum(2**i for i,x in enumerate(assignment) if x==2)
                if data[a]+data[b]>data[a+b]:superadd=False
            self.assertEqual(m.is_superadditive(n,data),superadd)
            self.assertEqual(m.efficiency_gap(n,data,expected),0)
            self.assertEqual(m.efficiency_gap(n,data,[0]*n),data[-1])

    def test_refusals_caps_order(self):
        funcs=[lambda n,d:m.coalition_value(n,d,0),lambda n,d:m.marginal_contribution(n,d,0,0),m.shapley_values,m.banzhaf_values,m.mobius_dividends,m.reconstruct_values,m.dual_values,m.is_monotone,m.is_superadditive,lambda n,d:m.efficiency_gap(n,d,[])]
        bads=[(True,None,TypeError,'players must be an integer'),(1.0,[],TypeError,'players must be an integer'),(-1,None,ValueError,'players out of range'),(6,None,ValueError,'players out of range'),(1,None,TypeError,'values must be a list or tuple'),(1,[True],ValueError,'values size mismatch'),(1,[0,True],TypeError,'value must be an integer'),(1,[0,1.0],TypeError,'value must be an integer'),(1,[0,101],ValueError,'value out of range'),(1,[0,-101],ValueError,'value out of range'),(1,[1,0],ValueError,'empty coalition must have value zero')]
        for call in funcs:
            for n,data,error,msg in bads:
                with self.assertRaisesRegex(error,'^'+msg+'$'):call(n,data)
        data=[0]+[100]*31
        for call in funcs[:-1]:call(5,data)
        m.efficiency_gap(5,data,[100,-100,F(1,100),0,0])
        for func in (lambda x:m.coalition_value(1,[0,1],x),lambda x:m.marginal_contribution(1,[0,1],x,0)):
            for bad in (True,1.0):
                with self.assertRaisesRegex(TypeError,'^mask must be an integer$'):func(bad)
            for bad in (-1,2):
                with self.assertRaisesRegex(ValueError,'^mask out of range$'):func(bad)
        for bad in (True,1.0):
            with self.assertRaisesRegex(TypeError,'^player must be an integer$'):m.marginal_contribution(1,[0,1],0,bad)
        for bad in (-1,1):
            with self.assertRaisesRegex(ValueError,'^player out of range$'):m.marginal_contribution(1,[0,1],0,bad)
        with self.assertRaisesRegex(ValueError,'^player already in coalition$'):m.marginal_contribution(1,[0,1],1,0)
        with self.assertRaisesRegex(ValueError,'^mask out of range$'):m.marginal_contribution(1,[0,1],2,True)
        for a,error,msg in [(None,TypeError,'allocation must be a list or tuple'),([True,False],ValueError,'allocation size mismatch'),([True],TypeError,'allocation must be int or Fraction'),([1.0],TypeError,'allocation must be int or Fraction'),([101],ValueError,'allocation magnitude out of range'),([-101],ValueError,'allocation magnitude out of range'),([F(1,101)],ValueError,'allocation denominator out of range')]:
            with self.assertRaisesRegex(error,'^'+msg+'$'):m.efficiency_gap(1,[0,1],a)
        for i in range(5):
            with self.assertRaisesRegex(ValueError, "^player already in coalition$"):
                m.marginal_contribution(5, data, 1<<i, i)
        for n in (0, 5):
            additive = tuple(3*mask.bit_count() for mask in range(1<<n))
            dividends = m.mobius_dividends(n, additive)
            self.assertEqual(m.reconstruct_values(n, dividends), additive)
            self.assertEqual(m.shapley_values(n, additive), (F(3),)*n)
            self.assertEqual(m.banzhaf_values(n, additive), (F(3),)*n)
            self.assertEqual(m.efficiency_gap(n, additive, m.shapley_values(n, additive)), 0)
            self.assertEqual(m.dual_values(n, m.dual_values(n, additive)), additive)
        self.assertFalse(m.CLAIMS)

if __name__=='__main__':unittest.main()
