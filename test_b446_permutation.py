import itertools
import math
import unittest
import b446_permutation as m


def bubble_swaps(p):
    a=list(p);swaps=0
    for _ in a:
        for i in range(len(a)-1):
            if a[i]>a[i+1]:a[i],a[i+1]=a[i+1],a[i];swaps+=1
    return swaps


class PermutationTests(unittest.TestCase):
    def test_enumerative_oracles(self):
        for n in range(7):
            histogram=[0]*9
            for p in itertools.permutations(range(n)):
                differences=[p[i+1]-p[i] for i in range(n-1)]
                descent=sum(x<0 for x in differences);histogram[descent]+=1
                self.assertEqual(m.descent_count(p),descent)
                self.assertEqual(m.major_index(p),sum(i for i,x in enumerate(differences,1) if x<0))
                inv=bubble_swaps(p)
                self.assertEqual(m.inversion_count(p),inv)
                self.assertEqual(m.excedance_count(p),sum(i<x for x,i in zip(p,range(n))))
                self.assertEqual(m.fixed_point_count(p),n-sum(x!=i for i,x in enumerate(p)))
                orbits=set()
                for i in range(n):
                    orbit=set();j=i
                    while j not in orbit:orbit.add(j);j=p[j]
                    orbits.add(tuple(sorted(orbit)))
                self.assertEqual(m.cycle_count(p),len(orbits))
                self.assertEqual(m.permutation_sign(p),(-1)**(n-len(orbits)))
            for k in range(9):self.assertEqual(m.eulerian_number(n,k),histogram[k])
        for n in range(1,9):
            for step in range(1,9):
                alive=set(range(n));current=0;count=0;expected=[]
                while alive:
                    if current in alive:
                        count+=1
                        if count==step:alive.remove(current);expected.append(current);count=0
                    current=(current+1)%n
                self.assertEqual(m.josephus_order(n,step),tuple(expected))
                self.assertEqual(m.josephus_survivor(n,step),expected[-1])

    def test_caps_and_refusals(self):
        funcs=[m.inversion_count,m.major_index,m.descent_count,m.excedance_count,m.fixed_point_count,m.cycle_count,m.permutation_sign]
        for call in funcs:
            for p,error,msg in [(None,TypeError,'permutation must be a list or tuple'),(iter([]),TypeError,'permutation must be a list or tuple'),([True]*9,ValueError,'permutation size out of range'),([True],TypeError,'entry must be an integer'),([0.0],TypeError,'entry must be an integer'),([-1],ValueError,'entry out of range'),([1],ValueError,'entry out of range'),([0,0],ValueError,'entries must be distinct')]:
                with self.assertRaisesRegex(error,'^'+msg+'$'):call(p)
            call(tuple(reversed(range(8))));call(())
        self.assertEqual(m.inversion_count(tuple(reversed(range(8)))),28)
        self.assertEqual(m.major_index(tuple(reversed(range(8)))),28)
        self.assertEqual(m.cycle_count(tuple(range(8))),8)
        self.assertEqual(sum(m.eulerian_number(8,k) for k in range(9)),math.factorial(8))
        for call,low in [(m.eulerian_number,0),(m.josephus_survivor,1),(m.josephus_order,1)]:
            for bad in (True,1.0):
                with self.assertRaisesRegex(TypeError,'^n must be an integer$'):call(bad,True)
            for bad in (low-1,9):
                with self.assertRaisesRegex(ValueError,'^n out of range$'):call(bad,True)
            name='k' if call==m.eulerian_number else 'step'
            for bad in (True,1.0):
                with self.assertRaisesRegex(TypeError,'^'+name+' must be an integer$'):call(8,bad)
            for bad in (low-1,9):
                with self.assertRaisesRegex(ValueError,'^'+name+' out of range$'):call(8,bad)
            call(8,8)
        self.assertFalse(m.CLAIMS)

if __name__=='__main__':unittest.main()
