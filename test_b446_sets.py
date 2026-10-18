import itertools
import unittest
from fractions import Fraction as F
import b446_sets as m


class SetTests(unittest.TestCase):
    def test_membership_mask_oracles(self):
        choices=[tuple(x for x in (-1,0,2) if mask>>(x+1 if x<1 else 2)&1) for mask in range(8)]
        for a,b in itertools.product(choices,repeat=2):
            rows=[(int(x in a),int(x in b)) for x in (-1,0,2)]
            inter=sum(p*q for p,q in rows)
            union=sum(min(1,p+q) for p,q in rows)
            self.assertEqual(m.union_size(a,b),union)
            self.assertEqual(m.intersection_size(a,b),inter)
            self.assertEqual(m.symmetric_difference_size(a,b),sum(abs(p-q) for p,q in rows))
            self.assertEqual(m.jaccard_similarity(a,b),F(inter,union) if union else F(1))
            self.assertEqual(m.dice_similarity(a,b),F(2*inter,len(a)+len(b)) if len(a)+len(b) else F(1))
            expected=F(1) if not a and not b else F(inter,min(len(a),len(b))) if a and b else F(0)
            self.assertEqual(m.overlap_coefficient(a,b),expected)
            self.assertEqual(m.containment_fraction(a,b),F(inter,len(a)) if a else F(1))
        for groups in itertools.product(choices,repeat=3):
            degrees=[sum(x in group for group in groups) for x in (-1,0,2)]
            self.assertEqual(m.incidence_histogram(groups),{k:degrees.count(k) for k in (1,2,3)})
            for k in range(9):
                self.assertEqual(m.exact_membership_count(groups,k),degrees.count(k) if k else 0)
            self.assertEqual(m.inclusion_exclusion_union_size(groups),sum(d>0 for d in degrees))

    def test_set_refusals_and_caps(self):
        funcs=[m.union_size,m.intersection_size,m.symmetric_difference_size,m.jaccard_similarity,m.dice_similarity,m.overlap_coefficient,m.containment_fraction]
        bads=[(None,TypeError,'set must be a list or tuple'),(set(),TypeError,'set must be a list or tuple'),(iter([]),TypeError,'set must be a list or tuple'),([True]*17,ValueError,'set size out of range'),([True],TypeError,'id must be an integer'),([1.0],TypeError,'id must be an integer'),([101],ValueError,'id out of range'),([-101],ValueError,'id out of range'),([1,1],ValueError,'ids must be distinct')]
        for call in funcs:
            self.assertEqual(call(list(range(16)),list(range(16))),16 if call in funcs[:2] else 0 if call==m.symmetric_difference_size else 1)
            self.assertIsInstance(call([-100],[100]),(int,F))
            for bad,error,message in bads:
                for left,right in ((bad,None),([],bad)):
                    with self.assertRaisesRegex(error,'^'+message+'$'):call(left,right)
        for call in (m.incidence_histogram,lambda g:m.exact_membership_count(g,0),m.inclusion_exclusion_union_size):
            for bad,error,message in bads:
                with self.assertRaisesRegex(error,'^'+message+'$'):call([bad])

    def test_maximum_composition(self):
        groups = [tuple(range(i, i+16)) for i in range(8)]
        histogram = m.incidence_histogram(groups)
        self.assertEqual(sum(histogram.values()), m.inclusion_exclusion_union_size(groups))
        self.assertEqual(sum(k*v for k,v in histogram.items()), 8*16)
        self.assertEqual(histogram, {k:m.exact_membership_count(groups,k) for k in range(1,9)})
        self.assertEqual(m.inclusion_exclusion_union_size(groups), 23)

    def test_group_caps_and_degree(self):
        funcs=[m.incidence_histogram,lambda g:m.exact_membership_count(g,0),m.inclusion_exclusion_union_size]
        for call in funcs:
            for value,error,message in [(None,TypeError,'groups must be a list or tuple'),(iter([]),TypeError,'groups must be a list or tuple'),([],ValueError,'group count out of range'),([None]*9,ValueError,'group count out of range')]:
                with self.assertRaisesRegex(error,'^'+message+'$'):call(value)
            call([[]]);call([list(range(16))]*8)
        for degree in (True,1.0,float('inf'),float('nan')):
            with self.assertRaisesRegex(TypeError,'^degree must be an integer$'):m.exact_membership_count([[]],degree)
        for degree in (-1,9):
            with self.assertRaisesRegex(ValueError,'^degree out of range$'):m.exact_membership_count([[]],degree)
        self.assertEqual(m.exact_membership_count([[1]]*8,8),1)
        self.assertEqual(m.exact_membership_count([[1]]*8,0),0)
        with self.assertRaisesRegex(ValueError,'^group count out of range$'):m.exact_membership_count([],True)
        self.assertFalse(m.CLAIMS)

if __name__=='__main__': unittest.main()
