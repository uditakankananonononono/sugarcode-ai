import itertools
import unittest
import b446_topology as m


def as_set(mask,n):return {i for i in range(n) if mask>>i&1}


def brute_topology(n,family):
    universe=set(range(n));sets=[as_set(x,n) for x in family]
    if set() not in sets or universe not in sets:return False
    # Check every subfamily union, not just binary closures.
    for bits in itertools.product((False,True),repeat=len(sets)):
        union=set().union(*(s for s,take in zip(sets,bits) if take))
        if union not in sets:return False
    return all(a&b in sets for a in sets for b in sets)


class TopologyTests(unittest.TestCase):
    def test_all_families_through_three_points(self):
        for n in range(4):
            full=(1<<n)-1;universe=set(range(n))
            for selection in range(1<<(1<<n)):
                opens=[o for o in range(1<<n) if selection>>o&1]
                valid=brute_topology(n,opens)
                self.assertEqual(m.is_topology(n,opens),valid)
                if not valid:continue
                sets=[as_set(o,n) for o in opens]
                closed=[universe-o for o in sets]
                for mask in range(1<<n):
                    s=as_set(mask,n)
                    inside=set().union(*(o for o in sets if o<=s))
                    close=set.intersection(*(c for c in closed if s<=c))
                    edge=close-inside
                    derived={x for x in universe if all((s-{x})&o for o in sets if x in o)}
                    pack=lambda x:sum(1<<i for i in x)
                    self.assertEqual(m.interior(n,opens,mask),pack(inside))
                    self.assertEqual(m.closure(n,opens,mask),pack(close))
                    self.assertEqual(m.boundary(n,opens,mask),pack(edge))
                    self.assertEqual(m.derived_set(n,opens,mask),pack(derived))
                    self.assertEqual(m.closure(n,opens,m.closure(n,opens,mask)),pack(close))
                    self.assertEqual(m.interior(n,opens,m.interior(n,opens,mask)),pack(inside))
                connected=not any(o and o!=universe and universe-o in sets for o in sets)
                self.assertEqual(m.is_connected(n,opens),connected)
                neighborhoods={x:tuple(i for i,o in enumerate(sets) if x in o) for x in universe}
                self.assertEqual(m.is_t0(n,opens),len(set(neighborhoods.values()))==n)
                self.assertEqual(m.is_t1(n,opens),all(universe-{x} in sets for x in universe))
                # A finite Hausdorff space is discrete.
                self.assertEqual(m.is_hausdorff(n,opens),len(opens)==1<<n)
                relation=tuple((x,y) for x in range(n) for y in range(n) if x in set.intersection(*(c for c in closed if y in c)))
                self.assertEqual(m.specialization_relation(n,opens),relation)

    def test_refusals_and_caps(self):
        funcs=[m.is_topology,lambda n,o:m.interior(n,o,0),lambda n,o:m.closure(n,o,0),lambda n,o:m.boundary(n,o,0),lambda n,o:m.derived_set(n,o,0),m.is_connected,m.is_t0,m.is_t1,m.is_hausdorff,m.specialization_relation]
        bads=[(True,None,TypeError,'points must be an integer'),(1.0,[],TypeError,'points must be an integer'),(-1,None,ValueError,'points out of range'),(5,None,ValueError,'points out of range'),(1,None,TypeError,'opens must be a list or tuple'),(1,[True]*17,ValueError,'open count out of range'),(1,[True],TypeError,'mask must be an integer'),(1,[1.0],TypeError,'mask must be an integer'),(1,[-1],ValueError,'mask out of range'),(1,[2],ValueError,'mask out of range'),(1,[0,0],ValueError,'open masks must be distinct')]
        for call in funcs:
            for n,opens,error,msg in bads:
                with self.assertRaisesRegex(error,'^'+msg+'$'):call(n,opens)
            call(0,[0]);call(4,list(range(16)))
        self.assertFalse(m.is_topology(2,[0,1,2,3][:3]))
        for call in funcs[1:]:
            with self.assertRaisesRegex(ValueError,'^opens must form a topology$'):call(2,[0,1,2])
        for call in (m.interior,m.closure,m.boundary,m.derived_set):
            call(4,list(range(16)),15)
            for bad in (True,1.0):
                with self.assertRaisesRegex(TypeError,'^mask must be an integer$'):call(4,list(range(16)),bad)
            for bad in (-1,16):
                with self.assertRaisesRegex(ValueError,'^mask out of range$'):call(4,list(range(16)),bad)
            with self.assertRaisesRegex(ValueError,'^opens must form a topology$'):call(1,[],True)
        self.assertFalse(m.CLAIMS)

if __name__=='__main__':unittest.main()
