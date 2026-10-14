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
a=load('neuromorphic921')
b=load('spiking922')
class QuantumTests(unittest.TestCase):
    def test_hand_delay_reset_and_ties(self):
        out=a.simulate_array([[1,0],[0,0],[0,0]],[[0,0],[1,0]],leak=1)
        self.assertEqual(out['spikes'],((1,0),(0,1),(0,0)))
        self.assertEqual(out['potentials'],((0,0),(0,0),(0,0)))
        self.assertEqual(out['spike_counts'],(1,1))
        self.assertEqual(b.event_neuron([(0,.5),(0,.5),(1,1),(2,1)],refractory=2)['spike_times'],(0,2))
        self.assertEqual(b.event_neuron([])['trace'],())
        self.assertEqual(a.simulate_array([[1]],[[0]]),a.simulate_array([[1]],[[0]],.9,1,0))
        self.assertEqual(b.event_neuron([(0,1)]),b.event_neuron([(0,1)],10,1,0,0))
    def test_caps(self):
        a.simulate_array([[0]*64],[[0]*64 for _ in range(64)])
        self.assertEqual(len(a.simulate_array([[0]]*1000,[[0]])['spikes']),1000)
        b.event_neuron([(0,0)]*1000,tau=1e-6,threshold=100,reset=-100,refractory=1e6)
        b.event_neuron([(1e6,100)],tau=1e6)

def seeded(seed):
    def test(self):
        rng=random.Random(seed);n=3; ticks=15
        currents=[[rng.uniform(-.5,1.5) for _ in range(n)] for _ in range(ticks)]
        weights=[[rng.uniform(-.5,.5) for _ in range(n)] for _ in range(n)]
        leak=rng.random();threshold=rng.uniform(.2,2);reset=-rng.random()
        out=a.simulate_array(currents,weights,leak,threshold,reset)
        # Independent scalar loops, copy old states before synchronous step.
        v=[0.]*n;old=[0]*n;vs=[];ss=[]
        for row in currents:
            new=[];fired=[]
            for i in range(n):
                value=leak*v[i]+row[i]
                for j in range(n):value+=weights[i][j]*old[j]
                fire=int(value>=threshold);fired.append(fire);new.append(reset if fire else value)
            v=new;old=fired;vs.append(tuple(v));ss.append(tuple(old))
        self.assertEqual(out['spikes'],tuple(ss));self.assertEqual(out['spike_counts'],tuple(sum(r[i] for r in ss) for i in range(n)))
        for got,want in zip(out['potentials'],vs):
            for x,y in zip(got,want):self.assertAlmostEqual(x,y,places=12)
        tau=rng.uniform(.1,10);ref=rng.uniform(0,3);events=[(float(i//2),rng.uniform(-.5,2)) for i in range(20)]
        out=b.event_neuron(events,tau,threshold,reset,ref)
        # Closed form convolution between resets, ignore refractory arrivals.
        grouped={}
        for t,w in events:grouped[t]=grouped.get(t,0)+w
        last_spike=None;accepted=[];spikes=[];trace=[]
        for t,w in grouped.items():
            if last_spike is None:
                baseline=0;origin=0
            else:baseline=reset;origin=last_spike
            active=last_spike is None or t>=last_spike+ref
            if active:accepted.append((t,w))
            v=baseline*math.exp(-(t-origin)/tau)+sum(wi*math.exp(-(t-ti)/tau) for ti,wi in accepted)
            if active and v>=threshold:
                spikes.append(t);last_spike=t;accepted=[];v=reset
            trace.append((t,v))
        self.assertEqual(out['spike_times'],tuple(spikes))
        for got,want in zip(out['trace'],trace):
            self.assertEqual(got[0],want[0]);self.assertAlmostEqual(got[1],want[1],places=11)
    return test
for seed in range(400):setattr(QuantumTests,'test_seed_%03d'%seed,seeded(seed))

def rejection(fn,args,kwargs,message):
    def test(self):
        with self.assertRaises(ValueError) as caught:fn(*args,**kwargs)
        self.assertEqual(str(caught.exception),message)
    return test
cases=[]
for val in (True,101,-101,float('nan'),10**10000):cases.append((a.simulate_array,([[val]],[[0]]),{},'finite built-in real magnitude <=100 required'))
for kw in ({'leak':-.1},{'leak':1.1},{'threshold':0},{'reset':1}):cases.append((a.simulate_array,([[0]],[[0]]),kw,'invalid leak, threshold or reset'))
for w in ([],[[0]*65 for _ in range(65)],{0:[0]},[[0,0]],[[0],[0]]):cases.append((a.simulate_array,([[0]],w),{},'weights must be a square matrix with 1..64 cells'))
for current in ([],[[0]]*1001,{0:[0]}):cases.append((a.simulate_array,(current,[[0]]),{},'currents must contain 1..1000 ticks'))
for current in ([[0,0]],[[0],[]]):cases.append((a.simulate_array,(current,[[0]]),{},'each current tick must match cell count'))
for kw in ({'tau':0},{'tau':1e6+1},{'threshold':0},{'threshold':101},{'reset':-101},{'refractory':-1},{'refractory':1e6+1},{'tau':True}):cases.append((b.event_neuron,([],),kw,'finite built-in real outside supported range'))
cases.append((b.event_neuron,([],),{'reset':1},'reset must be below threshold'))
for events in ({0:(0,0)},[(0,0)]*1001):cases.append((b.event_neuron,(events,),{},'events must be a list/tuple of at most 1000 entries'))
for events in ([[0,0]],[(0,)],[(0,0,0)]):cases.append((b.event_neuron,(events,),{},'each event must be an exact pair tuple'))
for events in ([(-1,0)],[(1e6+1,0)],[(0,101)],[(0,-101)],[(0,True)]):cases.append((b.event_neuron,(events,),{},'finite built-in real outside supported range'))
cases.append((b.event_neuron,([(1,0),(0,0)],),{},'event times must be nondecreasing'))
for i,(fn,args,kw,msg) in enumerate(cases):setattr(QuantumTests,'test_refusal_%02d'%i,rejection(fn,args,kw,msg))

def defaults_and_boundaries(self):
    a.simulate_array([[100]],[[100]],leak=0,threshold=100,reset=-100)
    a.simulate_array([[-100]],[[-100]],leak=1,threshold=100,reset=-100)
    events=[(0,.6),(1,.5),(2,1)]
    self.assertEqual(b.event_neuron(events),b.event_neuron(events,10,1,0,0))
    self.assertEqual(b.event_neuron([(0,1),(0.5,1)])['spike_times'],(0,.5))
    self.assertEqual(b.event_neuron([(0,0)],reset=1e-301,threshold=1e-300)['trace'],((0,0.0),))
QuantumTests.test_defaults_and_boundaries=defaults_and_boundaries

def additional_boundary_pins(self):
    for events in ([(0,.5),(2,.6)],[(0,1),(2,.8)],[(0,.5),(0,.1),(2,.6)]):
        self.assertEqual(b.event_neuron(events),b.event_neuron(events,tau=10,threshold=1,reset=0,refractory=0))
    for reset in (-100,100):
        if reset==100:
            with self.assertRaises(ValueError):b.event_neuron([],reset=reset,threshold=100)
        else:b.event_neuron([],reset=reset)
    with self.assertRaises(ValueError):b.event_neuron([(0,-100.5)])
    b.event_neuron([(0,-100)])
    with self.assertRaises(ValueError):b.event_neuron([(1,0),(0.5,0)])
QuantumTests.test_additional_boundary_pins=additional_boundary_pins

def final_boundaries(self):
    self.assertEqual(b.event_neuron([(0,.1),(2,.1)]),b.event_neuron([(0,.1),(2,.1)],tau=10))
    for threshold in (0,-.1):
        with self.assertRaises(ValueError):a.simulate_array([[0]],[[0]],threshold=threshold,reset=-1)
    with self.assertRaises(ValueError):b.event_neuron([(0,0),(2,0),(1,0)])
QuantumTests.test_final_boundaries=final_boundaries

def upper_reset_boundary(self):
    b.event_neuron([],threshold=100,reset=99.5)
QuantumTests.test_upper_reset_boundary=upper_reset_boundary
