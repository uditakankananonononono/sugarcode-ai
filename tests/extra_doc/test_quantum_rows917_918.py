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


import cmath
import random
a=load('quantum_simulation917')
b=load('quantum_crypto918')
class IntSubclass(int): pass
class QuantumTests(unittest.TestCase):
    def test_axes_and_signs(self):
        self.assertAlmostEqual(a.evolve([1,0],[1,0,0],math.pi/2)['state'][1],-1j)
        self.assertAlmostEqual(a.evolve([1,0],[0,1,0],math.pi/2)['state'][1],1)
        self.assertAlmostEqual(a.evolve([1,0],[0,0,1],math.pi/2)['state'][0],-1j)
        self.assertEqual(a.evolve([1,0],[0,0,0],1)['state'],(1+0j,0j))
    def test_qber_hand(self):
        out=b.audit_bb84([0,1,0,1],[0,0,1,1],[0,0,1,1],[0,0,0,1],[1,0])
        self.assertEqual(out['sifted_indices'],(0,1,3));self.assertEqual(out['disclosed_indices'],(0,1))
        self.assertEqual(out['error_count'],1);self.assertEqual(out['sample_size'],2)
        self.assertEqual(out['qber'],.5);self.assertEqual(out['candidate_indices'],(3,))
        self.assertEqual(out['alice_candidate'],(1,));self.assertEqual(out['bob_candidate'],(1,))
        self.assertIs(out['secure_key'],False)
    def test_caps(self):
        z=[0]*10000
        self.assertEqual(len(b.audit_bb84(z,z,z,z,[9999])['alice_candidate']),9999)
        with self.assertRaisesRegex(ValueError,'^binary sequences must be lists/tuples of length 1..10000$'):b.audit_bb84(z+[0],z,z,z,[0])
        self.assertEqual(a.evolve([1,0],[0,0,0],1e6)['state'],(1+0j,0j))
    def test_schema(self):
        for value in (True,IntSubclass(0),1.,-1,2):
            with self.assertRaisesRegex(ValueError,'^binary entries must be built-in int 0 or 1$'):b.audit_bb84([value],[0],[0],[0],[0])
        for d in ([],[True],[IntSubclass(0)],[-1],[1],[0,0]):
            with self.assertRaises(ValueError):b.audit_bb84([0],[0],[0],[0],d)
        for state,field,t in [([0,0],[0]*3,0),([True,0],[0]*3,0),([1,0],[True,0,0],0),([1,0],[0]*3,IntSubclass(0)),([1,0],[0]*3,float('nan')),([1,0],[0]*3,1e101),([1],[0]*3,0),([1,0],[0]*2,0)]:
            with self.assertRaises(ValueError):a.evolve(state,field,t)

def seeded(seed):
    def test(self):
        rng=random.Random(seed); angle=rng.uniform(-3,3);phase=rng.uniform(-3,3)
        state=[math.cos(angle),math.sin(angle)*cmath.exp(1j*phase)]
        field=[rng.uniform(-2,2) for _ in range(3)];t=rng.uniform(-1,1)
        out=a.evolve(state,field,t)
        # Independent matrix exponential Taylor series (small bounded norm).
        hx,hy,hz=field; matrix=[[hz,hx-1j*hy],[hx+1j*hy,-hz]]
        result=state[:];term=state[:]
        for k in range(1,70):
            term=[(-1j*t/k)*sum(matrix[i][j]*term[j] for j in range(2)) for i in range(2)]
            result=[result[i]+term[i] for i in range(2)]
        for x,y in zip(result,out['state']):self.assertAlmostEqual(abs(x-y),0,places=12)
        back=a.evolve(out['state'],field,-t)
        for x,y in zip(state,back['state']):self.assertAlmostEqual(abs(x-y),0,places=12)
        self.assertAlmostEqual(out['norm'],1,places=12)
        self.assertAlmostEqual(sum(x*x for x in out['bloch']),1,places=12)
        initial_energy=hz*(abs(state[0])**2-abs(state[1])**2)+2*(state[0].conjugate()*state[1]).real*hx+2*(state[0].conjugate()*state[1]).imag*hy
        self.assertAlmostEqual(out['energy'],initial_energy,places=12)
        n=rng.randrange(2,80);ab=[rng.randrange(2) for _ in range(n)];bb=[rng.randrange(2) for _ in range(n)]
        bases=[rng.randrange(2) for _ in range(n)];other=[rng.randrange(2) for _ in range(n)];other[0]=bases[0]
        sift=[i for i in range(n) if bases[i]==other[i]]; disclose=rng.sample(sift,rng.randrange(1,len(sift)+1))
        audit=b.audit_bb84(ab,bases,bb,other,disclose)
        remaining=[i for i in sift if i not in disclose]
        self.assertEqual(audit['sifted_indices'],tuple(sift));self.assertEqual(audit['candidate_indices'],tuple(remaining))
        self.assertEqual(audit['alice_candidate'],tuple(ab[i] for i in remaining));self.assertEqual(audit['bob_candidate'],tuple(bb[i] for i in remaining))
        self.assertEqual(audit['error_count'],sum(ab[i]!=bb[i] for i in disclose));self.assertEqual(audit['sample_size'],len(disclose))
        self.assertEqual(audit['qber'],sum(ab[i]!=bb[i] for i in disclose)/len(disclose));self.assertIs(audit['secure_key'],False)
    return test
for seed in range(400):setattr(QuantumTests,'test_seed_%03d'%seed,seeded(seed))

# Pin schema errors before numeric processing, with exact messages.
def refuse(function,args,message):
    def test(self):
        with self.assertRaises(ValueError) as caught:function(*args)
        self.assertEqual(str(caught.exception),message)
    return test
for i,(fn,args,msg) in enumerate([
 (a.evolve,([1], [0,0,0],0),'state must have two amplitudes'),
 (a.evolve,({0:1,1:0},[0,0,0],0),'state must have two amplitudes'),
 (a.evolve,([1,0],[0,0],0),'field must have three components'),
 (a.evolve,([1,0],{0:0,1:0,2:0},0),'field must have three components'),
 (a.evolve,([True,0],[0,0,0],0),'finite built-in amplitudes required'),
 (a.evolve,([0,0],[0,0,0],0),'state must have unit norm'),
 (a.evolve,([1,0],[0,0,0],True),'finite built-in real with magnitude <=1e6 required'),
 (b.audit_bb84,([],[],[],[],[0]),'binary sequences must be lists/tuples of length 1..10000'),
 (b.audit_bb84,([0],[0],[0,0],[0],[0]),'binary sequences must have equal lengths'),
 (b.audit_bb84,([0],[0],[0],[0],[]),'nonempty disclosed list/tuple required'),
 (b.audit_bb84,([0],[0],[0],[1],[0]),'disclosed indices must be built-in ints in sifted positions'),
 (b.audit_bb84,([0],[0],[0],[0],[0,0]),'disclosed indices must be unique'),
]):setattr(QuantumTests,'test_exact_refusal_%02d'%i,refuse(fn,args,msg))


def magnitude_policy(self):
    for value in (1e6+1,1e100,1e308,10**10000):
        for field,t in (([value,0,0],0),([0,0,0],value)):
            with self.assertRaises(ValueError) as caught:a.evolve([1,0],field,t)
            self.assertEqual(str(caught.exception),'finite built-in real with magnitude <=1e6 required')
        with self.assertRaises(ValueError) as caught:a.evolve([value,0],[0,0,0],0)
        self.assertEqual(str(caught.exception),'state must have unit norm')
    a.evolve([1,0],[1e6,0,0],1e6)
QuantumTests.test_magnitude_policy=magnitude_policy
