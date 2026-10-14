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


a = load('quantum_error915')
b = load('quantum_ml916')

class IntSubclass(int): pass

class QuantumTests(unittest.TestCase):
    def test_correction_all_error_patterns(self):
        for mask in range(8):
            ps=[(mask>>i)&1 for i in range(3)]
            out=a.recover_bit_flip(1,0,ps)
            fail=int(sum(ps)>=2)
            self.assertEqual(out['logical_flip_probability'],fail)
            self.assertEqual(out['density_matrix'],((1-fail,0j),(0j,fail)))
            self.assertEqual(out['fidelity'],1-fail)
            syndrome=(ps[0]^ps[1])+2*(ps[1]^ps[2])
            self.assertEqual(out['syndrome_probabilities'],tuple(int(i==syndrome) for i in range(4)))
        for p in (0,.01,.2,.5,1):
            out=a.recover_bit_flip(1/math.sqrt(2),1j/math.sqrt(2),[p]*3)
            q=3*p*p-2*p**3
            self.assertAlmostEqual(out['logical_flip_probability'],q)
            self.assertAlmostEqual(out['fidelity'],1-q)
            rho=out['density_matrix']
            self.assertAlmostEqual(rho[0][1].imag,(2*q-1)/2)
            self.assertAlmostEqual(rho[1][0].imag,(1-2*q)/2)
            self.assertAlmostEqual(sum(out['syndrome_probabilities']),1)
        self.assertAlmostEqual(a.recover_bit_flip(1/math.sqrt(2),1/math.sqrt(2),[1]*3)['fidelity'],1)
    def test_error_validation(self):
        for alpha,beta,p in [(True,0,[0]*3),(IntSubclass(1),0,[0]*3),(0,0,[0]*3),(float('nan'),0,[0]*3),(1,0,[0,0]),(1,0,[True,0,0]),(1,0,[-.1,0,0]),(1,0,[1.1,0,0]),(1,0,[float('inf'),0,0])]:
            with self.assertRaises(ValueError):a.recover_bit_flip(alpha,beta,p)
    def test_gradient_oracle_and_training(self):
        xs=[-.8,.2,1.1,2.7];ys=[0,0,1,1]
        for theta in (-2,-.1,0,1,3):
            loss,g=b.loss_gradient(xs,ys,theta)
            wanted=sum(((1-math.cos(x+theta))/2-y)**2 for x,y in zip(xs,ys))/4
            grad=sum(((1-math.cos(x+theta))/2-y)*math.sin(x+theta) for x,y in zip(xs,ys))/4
            self.assertAlmostEqual(loss,wanted)
            self.assertAlmostEqual(g,grad)
            delta=1e-5
            fd=(b.loss_gradient(xs,ys,theta+delta)[0]-b.loss_gradient(xs,ys,theta-delta)[0])/(2*delta)
            self.assertAlmostEqual(g,fd,places=8)
        out=b.fit([0,math.pi],[0,1],theta=1,learning_rate=.2,steps=100)
        self.assertLess(out['loss_history'][-1],out['loss_history'][0])
        self.assertEqual(out['predictions'],(0,1))
        self.assertEqual(len(out['loss_history']),101)
        self.assertEqual(b.fit([0],[0],steps=0)['loss_history'],(0,))
        self.assertAlmostEqual(b.probability(math.pi,0),1)
    def test_ml_validation(self):
        for xs,ys in [([],[]),([0],[True]),([0],[IntSubclass(0)]),([0],[2]),([0],[]),([float('inf')],[0]),([True],[0])]:
            with self.assertRaises(ValueError): b.fit(xs,ys)
        for k in (True,IntSubclass(1),-1,10001,1.):
            with self.assertRaises(ValueError): b.fit([0],[0],steps=k)
        for rate in (0,-1,1.1,True,float('nan')):
            with self.assertRaises(ValueError): b.fit([0],[0],learning_rate=rate)
        with self.assertRaises(ValueError):b.probability(0,complex(1))

if __name__ == '__main__': unittest.main()

# Independent seeded matrix/channel oracle. Every seed is its own reported test.
import random

def _seed_case(seed):
    def test(self):
        rng=random.Random(seed)
        phi=rng.uniform(-math.pi,math.pi); angle=rng.uniform(-math.pi,math.pi)
        alpha=complex(math.cos(angle),0)
        beta=math.sin(angle)*complex(math.cos(phi),math.sin(phi))
        ps=[rng.random() for _ in range(3)]
        out=a.recover_bit_flip(alpha,beta,ps)
        # Independent majority-failure inclusion-exclusion polynomial.
        q=ps[0]*ps[1]+ps[1]*ps[2]+ps[0]*ps[2]-2*ps[0]*ps[1]*ps[2]
        expected=[[0j]*2 for _ in range(2)]
        for prob,vec in ((1-q,[alpha,beta]),(q,[beta,alpha])):
            for i in range(2):
                for j in range(2):expected[i][j]+=prob*vec[i]*vec[j].conjugate()
        for i in range(2):
            for j in range(2):self.assertAlmostEqual(abs(out['density_matrix'][i][j]-expected[i][j]),0,places=12)
        fidelity=sum([alpha,beta][i].conjugate()*expected[i][j]*[alpha,beta][j] for i in range(2) for j in range(2)).real
        self.assertAlmostEqual(out['fidelity'],fidelity,places=12)
        xs=[rng.uniform(-5,5) for _ in range(7)];ys=[rng.randrange(2) for _ in xs];theta=rng.uniform(-4,4)
        loss,g=b.loss_gradient(xs,ys,theta)
        direct=sum((((1-math.cos(x+theta))/2)-y)*math.sin(x+theta) for x,y in zip(xs,ys))/7
        self.assertAlmostEqual(g,direct,places=12)
        rate=rng.uniform(.001,1)
        trained=b.fit(xs,ys,theta=theta,learning_rate=rate,steps=1)
        self.assertAlmostEqual(trained['theta'],theta-rate*direct,places=12)
        self.assertEqual(trained['loss_history'][0],loss)
        self.assertAlmostEqual(trained['loss_history'][-1],b.loss_gradient(xs,ys,trained['theta'])[0])
    return test
for _seed in range(400):setattr(QuantumTests,'test_seed_%03d'%_seed,_seed_case(_seed))

def _bounds(self):
    self.assertEqual(len(b.fit([0],[0])['loss_history']),101)
    b.fit([0],[0],learning_rate=1,steps=0)
    self.assertEqual(len(b.fit([0],[0],steps=10000)['loss_history']),10001)
    b.loss_gradient([0]*10000,[0]*10000,0)
    with self.assertRaisesRegex(ValueError,'^equal nonempty feature/label sequences of at most 10000 required$'):
        b.loss_gradient([0]*10001,[0]*10001,0)
    # Find a representable angle with exactly cos(angle)=0 by controlling the
    # probability function at its public consumer boundary. This pins >= ties.
    original=b.probability
    try:
        b.probability=lambda x,t: .5
        self.assertEqual(b.fit([0],[0],steps=0)['predictions'],(1,))
    finally:b.probability=original
QuantumTests.test_numeric_caps_defaults_and_tie=_bounds


def _refusal_case(function,args,text):
    def test(self):
        with self.assertRaises(ValueError) as caught:function(*args)
        self.assertEqual(str(caught.exception),text)
    return test
for _i,(_function,_args,_text) in enumerate([
 (a.recover_bit_flip,(True,0,[0]*3),'amplitudes must be finite built-in numbers'),
 (a.recover_bit_flip,(float('nan'),0,[0]*3),'amplitudes must be finite built-in numbers'),
 (a.recover_bit_flip,(0,0,[0]*3),'amplitudes must have unit norm'),
 (a.recover_bit_flip,(1,0,[]),'three flip probabilities required'),
 (a.recover_bit_flip,(1,0,[True,0,0]),'probabilities must be finite built-in reals in [0,1]'),
 (b.probability,(True,0),'finite built-in real required'),
 (b.probability,(0,float('inf')),'finite built-in real required'),
 (b.fit,([0],[True]),'labels must be built-in integer 0 or 1'),
 (b.fit,([],[]),'equal nonempty feature/label sequences of at most 10000 required'),
]):setattr(QuantumTests,'test_refusal_message_%02d'%_i,_refusal_case(_function,_args,_text))

def test_default_learning_rate_contract():
    """Pin omitted rate to 0.1 using a nonzero first-step gradient."""
    implicit = b.fit([0], [1], theta=1, steps=1)
    explicit = b.fit([0], [1], theta=1, learning_rate=0.1, steps=1)
    assert implicit == explicit
    expected = 1-0.1*((1-math.cos(1))/2-1)*math.sin(1)
    assert abs(implicit['theta']-expected) < 1e-14

# unittest also runs the pin; pytest can run its top-level form.
QuantumTests.test_default_learning_rate_contract = lambda self: test_default_learning_rate_contract()
