import importlib
import importlib.util
import itertools
import math
import os
import sys
import unittest


def load(name):
    full = 'sugarcode.extra_doc.' + name
    if os.environ.get('MUTANT_MODULE') == full:
        spec = importlib.util.spec_from_file_location(full, os.environ['MUTANT_PATH'])
        module = importlib.util.module_from_spec(spec)
        sys.modules[full] = module
        spec.loader.exec_module(module)
        return module
    return importlib.import_module(full)


import random
a=load('quantum_sensing919')
b=load('quantum_network920')
class IntSubclass(int):pass
class QuantumTests(unittest.TestCase):
    def test_sensing_edges(self):
        for n in (1,2,10,10**12):
            for k in (0,n):
                out=a.ramsey_estimate(k,n)
                self.assertAlmostEqual(out['frequency'],0 if k==0 else math.pi)
                self.assertEqual(out['fisher_information_per_shot'],1)
                self.assertFalse(out['clipped'])
        self.assertAlmostEqual(a.ramsey_estimate(5,10)['frequency'],math.pi/2)
        self.assertEqual(a.ramsey_estimate(0,10,contrast=.5)['clipped'],True)
        self.assertEqual(a.ramsey_estimate(0,10,contrast=.5)['fisher_information_per_shot'],0)
        self.assertAlmostEqual(a.ramsey_estimate(1,2,interrogation=1e-12)['frequency'],math.pi/2*1e12,places=2)
        a.ramsey_estimate(1,2,interrogation=1e12,z=10)
    def test_routes_hand(self):
        edges=[('a','b',.8,.9),('b','c',.5,.8)]
        out=b.best_entanglement_route(edges,'a','c',.7)
        self.assertEqual(out['path'],('a','b','c'));self.assertAlmostEqual(out['success_probability'],.28)
        self.assertAlmostEqual(out['fidelity'],(1+3*((4*.9-1)/3)*((4*.8-1)/3))/4)
        self.assertEqual(out['swaps'],1)
        self.assertIsNone(b.best_entanglement_route([('a','b',1,1),('c','d',1,1)],'a','c'))
        self.assertEqual(b.best_entanglement_route([('a','c',1,1),('c','d',1,1),('a','b',1,1),('b','d',1,1)],'a','d')['path'],('a','b','d'))
        self.assertEqual(b.best_entanglement_route([('a','b',0,.25)],'a','b')['yield'],0)
    def test_defaults(self):
        self.assertEqual(a.ramsey_estimate(3,10),a.ramsey_estimate(3,10,1.,1.,1.959963984540054))
        self.assertEqual(b.best_entanglement_route([('a','b',.5,.5)],'a','b'),b.best_entanglement_route([('a','b',.5,.5)],'a','b',1.))

def sensing_seed(seed):
    def test(self):
        rng=random.Random(seed);n=rng.randrange(1,100000);k=rng.randrange(n+1);t=10**rng.uniform(-3,3);c=rng.uniform(.1,1);z=rng.uniform(.1,10)
        out=a.ramsey_estimate(k,n,t,c,z)
        p=k/n;d=1+z*z/n;center=(p+z*z/(2*n))/d;width=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
        inv=lambda q:math.acos(min(1,max(-1,(1-2*q)/c)))/t
        self.assertAlmostEqual(out['frequency'],inv(p),places=11)
        for got,want in zip(out['wilson_probability_interval'],[max(0,center-width),min(1,center+width)]):self.assertAlmostEqual(got,want,places=12)
        for got,want in zip(out['frequency_interval'],[inv(max(0,center-width)),inv(min(1,center+width))]):self.assertAlmostEqual(got,want,places=11)
        self.assertEqual(out['observed_probability'],p)
        self.assertEqual(out['clipped'],not (1-c)/2<=p<=(1+c)/2)
        # Complete four-node graph: enumerate all simple paths independently.
        nodes=['a','b','c','d'];edges=[(u,v,rng.random(),rng.uniform(.25,1)) for i,u in enumerate(nodes) for v in nodes[i+1:]];swap=rng.random()
        lookup={frozenset((u,v)):(p,f) for u,v,p,f in edges};candidates=[]
        for count in range(3):
            for inner in itertools.permutations(['b','c'],count):
                path=('a',)+inner+('d',);ps=1;vis=1
                for u,v in zip(path,path[1:]):
                    pp,ff=lookup[frozenset((u,v))];ps*=pp;vis*=(4*ff-1)/3
                ps*=swap**count;ff=(1+3*vis)/4
                candidates.append((ps*ff,path,ps,ff,count))
        want=sorted(candidates,key=lambda x:(-x[0],x[1]))[0];got=b.best_entanglement_route(edges,'a','d',swap)
        self.assertEqual(got['path'],want[1]);self.assertAlmostEqual(got['yield'],want[0]);self.assertAlmostEqual(got['success_probability'],want[2]);self.assertAlmostEqual(got['fidelity'],want[3]);self.assertEqual(got['swaps'],want[4])
    return test
for seed in range(400):setattr(QuantumTests,'test_seed_%03d'%seed,sensing_seed(seed))

def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as caught:fn(*args)
        self.assertEqual(str(caught.exception),message)
    return test
_cases=[]
for args in [(True,2),(IntSubclass(1),2),(1,True),(1.,2)]:_cases.append((a.ramsey_estimate,args,'counts must be built-in ints'))
for args in [(0,0),(0,10**12+1),(-1,1),(2,1)]:_cases.append((a.ramsey_estimate,args,'require 1<=shots<=10^12 and 0<=ones<=shots'))
for args in [(1,2,True),(1,2,1,True),(1,2,1,1,True),(1,2,float('inf'))]:_cases.append((a.ramsey_estimate,args,'finite built-in real parameters required'))
for args in [(1,2,0),(1,2,1e-13),(1,2,1e12+0.5),(1,2,1,0),(1,2,1,1.1),(1,2,1,1,0),(1,2,1,1,10.1)]:_cases.append((a.ramsey_estimate,args,'interrogation, contrast or z outside range'))
for source in ('',True,'a'*25,'é','a_'):_cases.append((b.best_entanglement_route,([('a','b',1,1)],source,'b'),'node labels must be 1..24 ASCII alphanumeric strings'))
_cases.extend([
(b.best_entanglement_route,([('a','b',1,1)],'a','a'),'source and target must differ'),
(b.best_entanglement_route,([('a','b',1,1)],'a','b',True),'swap_success must be finite built-in real in [0,1]'),
(b.best_entanglement_route,([],'a','b'),'edges must contain 1..20 edge tuples'),
(b.best_entanglement_route,([['a','b',1,1]],'a','b'),'each edge must be an exact four-item tuple'),
(b.best_entanglement_route,([('a','b',1,1),('b','a',1,1)],'a','b'),'self or parallel edges refused'),
(b.best_entanglement_route,([('a','a',1,1)],'a','b'),'self or parallel edges refused'),
(b.best_entanglement_route,([('a','b',True,1)],'a','b'),'edge probabilities must be finite built-in reals'),
(b.best_entanglement_route,([('a','b',1,True)],'a','b'),'edge probabilities must be finite built-in reals'),
(b.best_entanglement_route,([('a','b',-.1,1)],'a','b'),'success/fidelity outside [0,1]/[0.25,1]'),
(b.best_entanglement_route,([('a','b',1,.24)],'a','b'),'success/fidelity outside [0,1]/[0.25,1]'),
(b.best_entanglement_route,([('a','b',1,1)],'a','c'),'source and target must occur in edges'),
(b.best_entanglement_route,([(str(i),str(i+1),1,1) for i in range(10)],'0','1'),'at most 10 nodes supported'),
])
for i,(fn,args,message) in enumerate(_cases):setattr(QuantumTests,'test_refusal_%02d'%i,refusal(fn,args,message))

def fisher_seed(seed):
    def test(self):
        rng=random.Random(seed+500);n=10000;k=rng.randrange(2000,8000);t=rng.uniform(.1,5);c=rng.uniform(.7,.99)
        out=a.ramsey_estimate(k,n,t,c)
        phase=out['frequency']*t
        model=(1-c*math.cos(phase))/2
        derivative=c*t*math.sin(phase)/2
        want=derivative**2/(model*(1-model))
        self.assertAlmostEqual(out['fisher_information_per_shot'],want,places=10)
    return test
for seed in range(100):setattr(QuantumTests,'test_fisher_%03d'%seed,fisher_seed(seed))

def route_caps_and_ties(self):
    self.assertEqual(b.best_entanglement_route([('a','b',1,1),('b','c',1,1)],'a','c'),b.best_entanglement_route([('a','b',1,1),('b','c',1,1)],'a','c',1))
    label='a'*24;b.best_entanglement_route([(label,'b',1,1)],label,'b',0)
    edges=[(str(i),str(i+1),1,1) for i in range(9)]
    self.assertEqual(b.best_entanglement_route(edges,'0','9')['swaps'],8)
    nodes=list('abcdefg');edges=[(u,v,1,1) for i,u in enumerate(nodes) for v in nodes[i+1:]]
    b.best_entanglement_route(edges[:20],'a','b')
    with self.assertRaises(ValueError):b.best_entanglement_route(edges,'a','b')
    for swap in (-.1,1.1):
        with self.assertRaises(ValueError):b.best_entanglement_route([('a','b',1,1)],'a','b',swap)
    for p,f in [(1.1,1),(1,1.1)]:
        with self.assertRaises(ValueError):b.best_entanglement_route([('a','b',p,f)],'a','b')
    edges=[('a','c',1,1),('c','d',1,1),('a','b',1,1),('b','d',1,1)]
    self.assertEqual(b.best_entanglement_route(edges,'a','d')['path'],('a','b','d'))
    self.assertEqual(b.best_entanglement_route(edges[::-1],'a','d')['path'],('a','b','d'))
    edges=[('a','b',1,1),('b','d',1,1),('a','c',.5,1),('c','d',1,1)]
    self.assertEqual(b.best_entanglement_route(edges,'a','d')['path'],('a','b','d'))
    with self.assertRaises(ValueError):a.ramsey_estimate(1,2,interrogation=1e12+.5)
QuantumTests.test_route_caps_and_ties=route_caps_and_ties

def giant_inputs(self):
    for value in (1e100,1e308,10**10000):
        for args in ((1,2,value),(1,2,1,value),(1,2,1,1,value)):
            with self.assertRaises(ValueError) as caught:a.ramsey_estimate(*args)
            self.assertEqual(str(caught.exception),'finite built-in real parameters required')
        for args in (([('a','b',value,1)],'a','b'),([('a','b',1,value)],'a','b'),([('a','b',1,1)],'a','b',value)):
            with self.assertRaises(ValueError):b.best_entanglement_route(*args)
QuantumTests.test_giant_inputs=giant_inputs

def endpoint_roundoff_clamps(self):
    contrast=0.05076034842872479
    for p in (0,1):
        out=a.ramsey_estimate(p,1,contrast=contrast)
        self.assertEqual(out['fisher_information_per_shot'],0)
        self.assertAlmostEqual(out['frequency'],0 if p==0 else math.pi)
        self.assertTrue(out['clipped'])
    # Independently evaluate Wilson construction at count endpoints, including
    # tiny positive roundoff of center-half and high-end endpoint rounding.
    for n in (1,3,10,31,1000,10**12):
        for k in (0,n):
            for z in (.1,1.959963984540054,10):
                out=a.ramsey_estimate(k,n,z=z)
                p=k/n;denom=1+z*z/n
                center=(p+z*z/(2*n))/denom
                half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/denom
                wanted=(max(0.,center-half),min(1.,center+half))
                self.assertEqual(out['wilson_probability_interval'],wanted)
                self.assertGreaterEqual(wanted[0],0);self.assertLessEqual(wanted[1],1)
    with self.assertRaises(ValueError) as caught:a.ramsey_estimate(1,2,1e20)
    self.assertEqual(str(caught.exception),'interrogation, contrast or z outside range')
    for p,f in ((1.5,1),(1,1.5)):
        with self.assertRaises(ValueError) as caught:b.best_entanglement_route([('a','b',p,f)],'a','b')
        self.assertEqual(str(caught.exception),'edge probabilities must be finite built-in reals')
QuantumTests.test_endpoint_roundoff_clamps=endpoint_roundoff_clamps

def upper_roundoff_witness_and_guard_neighbors(self):
    # Seeded search found this upper-endpoint cosine >1 before min(1,...).
    contrast=.23933977348644617
    raw=(1-2*((1-contrast)/2))/contrast
    self.assertGreater(raw,1)
    self.assertEqual(a.ramsey_estimate(0,1,contrast=contrast)['fisher_information_per_shot'],0)
    for value,message in ((math.nextafter(1e20,0),'interrogation, contrast or z outside range'),(1e20,'interrogation, contrast or z outside range'),(math.nextafter(1e20,math.inf),'finite built-in real parameters required')):
        with self.assertRaises(ValueError) as caught:a.ramsey_estimate(1,2,value)
        self.assertEqual(str(caught.exception),message)
QuantumTests.test_upper_roundoff_witness_and_guard_neighbors=upper_roundoff_witness_and_guard_neighbors
