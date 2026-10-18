import itertools
import unittest
import b446_groups as m


def cyclic(n):return tuple(tuple((x+y)%n for y in range(n)) for x in range(n))


def subgroups(a,e):
    sets=[{i for i in range(len(a)) if mask>>i&1} for mask in range(1<<len(a))]
    return [s for s in sets if e in s and all(a[x][y] in s for x in s for y in s)]


class GroupTests(unittest.TestCase):
    def test_independent_oracles(self):
        permutations=list(itertools.permutations(range(3)))
        s3=tuple(tuple(permutations.index(tuple(p[q[i]] for i in range(3))) for q in permutations) for p in permutations)
        examples=[cyclic(n) for n in range(1,7)]+[tuple(tuple(x^y for y in range(4)) for x in range(4)),s3]
        for a in examples:
            n=len(a)
            # Reverse labels to exercise nonzero identities too.
            b=[[0]*n for _ in range(n)]
            for i in range(n):
                for j in range(n):b[n-1-i][n-1-j]=n-1-a[i][j]
            for table in (a,tuple(map(tuple,b))):
                e=next(i for i in range(n) if tuple(table[i])==tuple(range(n)))
                inv=tuple(table[x].index(e) for x in range(n))
                self.assertTrue(m.is_group(table));self.assertEqual(m.associativity_defect_count(table),0)
                self.assertEqual(m.identity_element(table),e);self.assertEqual(m.inverse_elements(table),inv)
                center=tuple(x for x in range(n) if all(table[x][y]==table[y][x] for y in range(n)))
                self.assertEqual(m.center_elements(table),center);self.assertEqual(m.is_abelian_group(table),len(center)==n)
                orders=[]
                for x in range(n):
                    power=x;order=1
                    while power!=e:power=table[power][x];order+=1
                    orders.append(order)
                self.assertEqual(m.element_orders(table),tuple(orders))
                classes={tuple(y for y in range(n) if any(table[g][x]==table[y][g] for g in range(n))) for x in range(n)}
                self.assertEqual(m.conjugacy_classes(table),tuple(sorted(classes,key=lambda c:c[0])))
                ss=subgroups(table,e)
                for seeds in ((),(0,),(n-1,),tuple(range(n))):
                    self.assertEqual(m.subgroup_generated(table,seeds),tuple(sorted(set.intersection(*(s for s in ss if set(seeds)<=s)))))
                candidates=[]
                for s in ss:
                    if not all(table[table[g][x]][inv[g]] in s for g in range(n) for x in s):continue
                    cosets={frozenset(table[g][h] for h in s) for g in range(n)}
                    def coset(x):return next(c for c in cosets if x in c)
                    if all(coset(table[x][y])==coset(table[y][x]) for x in range(n) for y in range(n)):candidates.append(s)
                self.assertEqual(m.commutator_subgroup(table),tuple(sorted(set.intersection(*candidates))))

    def test_asymmetric_inverse_magma(self):
        a=((0,1,2),(1,0,0),(2,1,0))
        self.assertEqual(m.identity_element(a),0)
        self.assertEqual(m.inverse_elements(a),(0,1,2))
        self.assertFalse(m.is_group(a))
        with self.assertRaisesRegex(ValueError,"^table must be a group$"):
            m.center_elements(a)

    def test_small_nongroups(self):
        for flat in itertools.product(range(2),repeat=4):
            a=(flat[:2],flat[2:]);n=2
            defects=sum(a[a[x][y]][z]!=a[x][a[y][z]] for x,y,z in itertools.product(range(n),repeat=3))
            identities=[e for e in range(n) if all(a[e][x]==x and a[x][e]==x for x in range(n))]
            e=identities[0] if identities else None
            inverses=None if e is None else tuple(next((y for y in range(n) if a[x][y]==e and a[y][x]==e),None) for x in range(n))
            group=e is not None and defects==0 and None not in inverses
            self.assertEqual(m.associativity_defect_count(a),defects);self.assertEqual(m.identity_element(a),e);self.assertEqual(m.is_group(a),group)
            if e is None:
                with self.assertRaisesRegex(ValueError,'^table has no identity$'):m.inverse_elements(a)
            else:self.assertEqual(m.inverse_elements(a),inverses)
            if not group:
                for call in (m.is_abelian_group,m.center_elements,m.conjugacy_classes,m.element_orders,lambda a:m.subgroup_generated(a,[]),m.commutator_subgroup):
                    with self.assertRaisesRegex(ValueError,'^table must be a group$'):call(a)

    def test_refusals_caps(self):
        funcs=[m.associativity_defect_count,m.identity_element,m.inverse_elements,m.is_group,m.is_abelian_group,m.center_elements,m.conjugacy_classes,m.element_orders,lambda a:m.subgroup_generated(a,[]),m.commutator_subgroup]
        bads=[(None,TypeError,'table must be a list or tuple'),(iter([]),TypeError,'table must be a list or tuple'),([],ValueError,'order out of range'),([None]*7,ValueError,'order out of range'),([None],TypeError,'row must be a list or tuple'),([[True,False]],ValueError,'table must be square'),([[True]],TypeError,'label must be an integer'),([[0.0]],TypeError,'label must be an integer'),([[-1]],ValueError,'label out of range'),([[1]],ValueError,'label out of range')]
        for call in funcs:
            for a,error,msg in bads:
                with self.assertRaisesRegex(error,'^'+msg+'$'):call(a)
            call(cyclic(6))
        for gens,error,msg in [(None,TypeError,'generators must be a list or tuple'),([True]*7,ValueError,'generator count out of range'),([True],TypeError,'label must be an integer'),([1.0],TypeError,'label must be an integer'),([-1],ValueError,'label out of range'),([6],ValueError,'label out of range'),([1,1],ValueError,'generators must be distinct')]:
            with self.assertRaisesRegex(error,'^'+msg+'$'):m.subgroup_generated(cyclic(6),gens)
        with self.assertRaisesRegex(ValueError,'^table must be a group$'):m.subgroup_generated(((0,0),(0,0)),None)
        self.assertFalse(m.CLAIMS)

if __name__=='__main__':unittest.main()
