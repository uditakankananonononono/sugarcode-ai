import itertools
import unittest
import b446_knapsack as m


class KnapsackTests(unittest.TestCase):
    def test_enumerative_oracles(self):
        for size in range(4):
            for ws in itertools.product((1,2,3),repeat=size):
                for target in range(7):
                    totals=[sum(w*k for w,k in zip(ws,bits)) for bits in itertools.product((0,1),repeat=size)]
                    hist=tuple(totals.count(t) for t in range(target+1))
                    self.assertEqual(m.subset_sum_count(ws,target),hist[-1])
                    self.assertEqual(m.subset_sum_histogram(ws,target),hist)
                    self.assertEqual(m.feasible_subset_count(ws,target),sum(t<=target for t in totals))
                    for k in range(5):
                        expected=sum(sum(bits)==k and sum(w*x for w,x in zip(ws,bits))==target for bits in itertools.product((0,1),repeat=size))
                        self.assertEqual(m.exact_cardinality_count(ws,target,k),expected)
                    counts=tuple(i%3 for i in range(size))
                    bounded=[sum(w*x for w,x in zip(ws,xs)) for xs in itertools.product(*(range(c+1) for c in counts))]
                    bh=tuple(bounded.count(t) for t in range(target+1))
                    self.assertEqual(m.bounded_sum_count(ws,target,counts),bh[-1])
                    self.assertEqual(m.bounded_sum_histogram(ws,target,counts),bh)
                    multis=[xs for xs in itertools.product(*(range(target//w+1) for w in ws)) if sum(w*x for w,x in zip(ws,xs))==target]
                    self.assertEqual(m.unbounded_sum_count(ws,target),len(multis))
                    self.assertEqual(m.minimum_coin_count(ws,target),min(map(sum,multis),default=None))
                    values=tuple((-1)**i*(i+1) for i in range(size))
                    feasible=[sum(v*x for v,x in zip(values,bits)) for bits in itertools.product((0,1),repeat=size) if sum(w*x for w,x in zip(ws,bits))<=target]
                    self.assertEqual(m.knapsack_max_value(ws,target,values),max(feasible))
                    self.assertEqual(m.optimal_knapsack_count(ws,target,values),feasible.count(max(feasible)))

    def test_refusals_caps_and_composition(self):
        funcs=[m.subset_sum_count,m.subset_sum_histogram,lambda w,t:m.bounded_sum_count(w,t,[0]*len(w)),lambda w,t:m.bounded_sum_histogram(w,t,[0]*len(w)),m.unbounded_sum_count,m.minimum_coin_count,lambda w,t:m.exact_cardinality_count(w,t,0),lambda w,t:m.knapsack_max_value(w,t,[0]*len(w)),lambda w,t:m.optimal_knapsack_count(w,t,[0]*len(w)),m.feasible_subset_count]
        funcs[2]=lambda w,t:m.bounded_sum_count(w,t,[])
        funcs[3]=lambda w,t:m.bounded_sum_histogram(w,t,[])
        funcs[7]=lambda w,t:m.knapsack_max_value(w,t,[])
        funcs[8]=lambda w,t:m.optimal_knapsack_count(w,t,[])
        bads=[(None,True,TypeError,'weights must be a list or tuple'),([True]*9,True,ValueError,'item count out of range'),([],True,TypeError,'target must be an integer'),([],1.0,TypeError,'target must be an integer'),([True],33,ValueError,'target out of range'),([],-1,ValueError,'target out of range'),([True],0,TypeError,'weight must be an integer'),([1.0],0,TypeError,'weight must be an integer'),([0],0,ValueError,'weight out of range'),([33],0,ValueError,'weight out of range')]
        for call in funcs:
            for w,t,error,msg in bads:
                with self.assertRaisesRegex(error,'^'+msg+'$'):call(w,t)
        ws=[4]*8
        self.assertEqual(m.subset_sum_count(ws,32),1)
        self.assertEqual(m.exact_cardinality_count(ws,32,8),1)
        self.assertEqual(m.subset_sum_histogram(ws,32)[-1],m.subset_sum_count(ws,32))
        self.assertEqual(sum(m.subset_sum_histogram(ws,32)),m.feasible_subset_count(ws,32))
        self.assertEqual(m.bounded_sum_histogram([32]*8,32,[8]*8)[-1],8)
        self.assertEqual(m.knapsack_max_value(ws,32,[100]*8),800)
        self.assertEqual(m.optimal_knapsack_count(ws,32,[0]*8),256)
        self.assertEqual(m.minimum_coin_count([32]*8,32),1)
        for call,name in [(lambda x:m.bounded_sum_count([1],1,x),'counts'),(lambda x:m.bounded_sum_histogram([1],1,x),'counts'),(lambda x:m.knapsack_max_value([1],1,x),'values'),(lambda x:m.optimal_knapsack_count([1],1,x),'values')]:
            with self.assertRaisesRegex(TypeError,'^'+name+' must be a list or tuple$'):call(None)
            with self.assertRaisesRegex(ValueError,'^'+name+' size mismatch$'):call([True,False])
            for bad in (True,1.0):
                with self.assertRaisesRegex(TypeError,'^'+('count' if name=='counts' else 'value')+' must be an integer$'):call([bad])
            for bad in ((-1,9) if name=='counts' else (-101,101)):
                with self.assertRaisesRegex(ValueError,'^'+('count' if name=='counts' else 'value')+' out of range$'):call([bad])
        for bad in (True,1.0):
            with self.assertRaisesRegex(TypeError,'^cardinality must be an integer$'):m.exact_cardinality_count([],0,bad)
        for bad in (-1,9):
            with self.assertRaisesRegex(ValueError,'^cardinality out of range$'):m.exact_cardinality_count([],0,bad)
        m.knapsack_max_value([1],1,[-100]);self.assertFalse(m.CLAIMS)

if __name__=='__main__':unittest.main()
