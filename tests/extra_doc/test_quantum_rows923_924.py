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


from fractions import Fraction as F
from decimal import Decimal,localcontext
import cmath
import random
a=load('memristor923');b=load('optical924')
class I(int):pass
class S(str):pass
class Tests(unittest.TestCase):
    def test_scope_and_hand_crossbar(self):
        out=a.crossbar([[.2,.5]],[2,-1],[[100,-100]])
        self.assertEqual(out['currents_before'],(F(-1,10),));self.assertEqual(out['currents_after'],(F(2),))
        self.assertEqual(out['conductances_after'],((F(1),F(0)),));self.assertEqual(out['power_before'],F(13,10))
        self.assertEqual(out['scope'],'ideal passive crossbar and clipped linear conductance model; no hardware')
        self.assertEqual(b.fourier_process([1],[0])['scope'],'coherent discrete Fourier mode processing; double precision; no hardware')
        self.assertEqual(a.crossbar([[.2]],[1]),a.crossbar([[.2]],[1],None,.01,0,1))
    def test_mixed_rows_both_orders(self):
        for g in ([[.2,.3],(.4,.5)],[(.2,.3),[.4,.5]]):
            for p in ([[1,2],(3,4)],[(1,2),[3,4]]):
                self.assertEqual(a.crossbar(g,[1,2],p),a.crossbar([[.2,.3],[.4,.5]],[1,2],[[1,2],[3,4]]))
        self.assertEqual(b.fourier_process([1,0],(0,0)),b.fourier_process((1,0),[0,0]))
    def test_optical_hand(self):
        out=b.fourier_process([1,0],[0,math.pi])
        self.assertAlmostEqual(abs(out['amplitudes'][0]),0);self.assertAlmostEqual(out['amplitudes'][1].real,1)
        self.assertAlmostEqual(out['intensities'][1],1)
        self.assertEqual(b.fourier_process([2j],[math.pi])['input_power'],4)
    def test_caps(self):
        a.crossbar([[0]*32 for _ in range(32)],[10]*32)
        a.crossbar([[100]],[-10],gain=1,minimum=0,maximum=100)
        b.fourier_process([10+10j]*32,[1e6]*32)

def seeded(seed):
    def test(self):
        rng=random.Random(seed);rows=rng.randrange(1,5);cols=rng.randrange(1,5)
        g=[[rng.randrange(101)/100 for _ in range(cols)] for _ in range(rows)]
        volts=[rng.randrange(-100,101)/10 for _ in range(cols)];p=[[rng.randrange(-100,101) for _ in range(cols)] for _ in range(rows)]
        step=rng.randrange(11)/100;out=a.crossbar(g,volts,p,step)
        # Decimal independent high-precision direct scalar arithmetic.
        with localcontext() as ctx:
            ctx.prec=60
            dec=lambda x:Decimal(str(x))
            before=[];after=[];updated=[];pb=pa=Decimal(0)
            for row,ps in zip(g,p):
                cur0=cur1=Decimal(0);new=[]
                for x,voltage,pulse in zip(row,volts,ps):
                    y=max(Decimal(0),min(Decimal(1),dec(x)+dec(step)*dec(pulse)))
                    cur0+=dec(x)*dec(voltage);cur1+=y*dec(voltage);pb+=dec(x)*dec(voltage)**2;pa+=y*dec(voltage)**2;new.append(F(y))
                before.append(F(cur0));after.append(F(cur1));updated.append(tuple(new))
            self.assertEqual(out['currents_before'],tuple(before));self.assertEqual(out['currents_after'],tuple(after));self.assertEqual(out['conductances_after'],tuple(updated));self.assertEqual(out['power_before'],F(pb));self.assertEqual(out['power_after'],F(pa))
        n=rng.randrange(1,9);amps=[complex(rng.uniform(-2,2),rng.uniform(-2,2)) for _ in range(n)];phases=[rng.uniform(-3,3) for _ in range(n)]
        out=b.fourier_process(amps,phases)
        # Independent combined transfer matrix U^-1 diag(exp(ip)) U.
        expected=[]
        for dest in range(n):
            total=0j
            for src in range(n):
                element=sum(cmath.exp(1j*(phases[k]+2*math.pi*k*(dest-src)/n)) for k in range(n))/n
                total+=element*amps[src]
            expected.append(total)
        for actual,want in zip(out['amplitudes'],expected):self.assertAlmostEqual(abs(actual-want),0,places=11)
        self.assertAlmostEqual(out['input_power'],out['output_power'],places=10)
        self.assertAlmostEqual(sum(out['fourier_intensities']),out['input_power'],places=10)
        for actual,amplitude in zip(out['intensities'],expected):self.assertAlmostEqual(actual,abs(amplitude)**2,places=10)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))

def refusal(fn,args,kw,message):
    def test(self):
        with self.assertRaises(ValueError) as caught:fn(*args,**kw)
        self.assertEqual(str(caught.exception),message)
    return test
cases=[]
for x in (True,I(1),S('1'),float('nan'),10**10000,101):cases.append((a.crossbar,([[x]],[0]),{},'finite built-in crossbar real outside supported range'))
for args,kw,msg in [(([],[1]),{},'conductances must have 1..32 output rows'),(([[0]],[]),{},'voltages must have 1..32 input entries'),(([[0,0]],[1]),{},'conductance rows must match input count'),(([[0]],[1],[[0,0]]),{},'pulse matrix must match conductances'),(([[0]],[1]),{'minimum':1,'maximum':1},'minimum must be below maximum')]:cases.append((a.crossbar,args,kw,msg))
for args in (([],[]),([1],[0,0]),([1]*33,[0]*33),(S('1'),[0])):cases.append((b.fourier_process,args,{},'equal mode/phase sequences of length 1..32 required'))
for x in (True,I(1),S('1'),float('nan'),complex(0,float('nan')),10**10000,10.1):cases.append((b.fourier_process,([x],[0]),{},'finite built-in complex components with magnitude <=10 required'))
for x in (True,I(1),S('1'),float('nan'),10**10000,1e6+1):cases.append((b.fourier_process,([1],[x]),{},'finite built-in real phase magnitude <=1e6 required'))
for i,(fn,args,kw,msg) in enumerate(cases):setattr(Tests,'test_refusal_%02d'%i,refusal(fn,args,kw,msg))

def boundary_diagnostics(self):
    self.assertEqual(a.crossbar([[.5]],[1])['currents_after'],(F(1,2),))
    for kwargs in ({'minimum':-.1},{'maximum':100.5},{'minimum':100.5},{'gain':-.1},{'gain':1.1}):
        with self.assertRaises(ValueError) as caught:a.crossbar([[.5]],[1],**kwargs)
        self.assertEqual(str(caught.exception),'finite built-in crossbar real outside supported range')
    a.crossbar([[99.5]],[1],minimum=99,maximum=100)
    for voltage in (-10.5,10.5):
        with self.assertRaises(ValueError):a.crossbar([[.5]],[voltage])
    for pulse in (-100.5,100.5):
        with self.assertRaises(ValueError):a.crossbar([[.5]],[1],[[pulse]])
    for raw in ({0:[0]},[[0]]*33):
        with self.assertRaises(ValueError):a.crossbar(raw,[1])
    with self.assertRaises(ValueError):a.crossbar([[0]*33],[0]*33)
    with self.assertRaises(ValueError) as caught:a.crossbar([[0]],[1],{0:[1]})
    self.assertEqual(str(caught.exception),'pulse matrix must match conductances')
    for value in (10.5,10.5j,-10.5,-10.5j):
        with self.assertRaises(ValueError):b.fourier_process([value],[0])
    a.crossbar([[0]],[0],[[0]],minimum=0,maximum=1,gain=0)
Tests.test_boundary_diagnostics=boundary_diagnostics

def scalar_parameter_caps_and_sequence_types(self):
    a.crossbar([[99.5]],[1],minimum=99.5,maximum=100)
    a.crossbar([[.5]],[1],maximum=.5)
    for kwargs in ({'maximum':-.1},{'maximum':0},{'minimum':-.1}):
        with self.assertRaises(ValueError):a.crossbar([[0]],[1],**kwargs)
    # A dict can have correct cardinality and yields list values through a custom
    # iteration protocol; it must still be refused as a matrix outer container.
    class DictRows(dict):
        def __iter__(self):return iter(self.values())
    with self.assertRaises(ValueError) as caught:a.crossbar([[0]],[1],DictRows({0:[0]}))
    self.assertEqual(str(caught.exception),'pulse matrix must match conductances')
Tests.test_scalar_parameter_caps_and_sequence_types=scalar_parameter_caps_and_sequence_types

def maximum_negative_diagnostic(self):
    with self.assertRaises(ValueError) as caught:a.crossbar([[0]],[1],maximum=-.1)
    self.assertEqual(str(caught.exception),'finite built-in crossbar real outside supported range')
Tests.test_maximum_negative_diagnostic=maximum_negative_diagnostic
