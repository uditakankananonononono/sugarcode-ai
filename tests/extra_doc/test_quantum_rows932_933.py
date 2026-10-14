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
import inspect
import random
a=load('cuckoo932');b=load('bat933')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_scopes_decimal_ties_and_mixed(self):
        for nests in ([[2],(1,)],[(2,),[1]]):
            out=a.generation(nests,[[.1],(.05,)],[0,0],[[3]],1)
            self.assertEqual(out['nests'],((F(1,20),),(F(3),)));self.assertEqual(out['accepted'],((0,0),(1,0)));self.assertEqual(out['abandoned'],(1,))
            self.assertEqual(out['scope'],'one rational cuckoo replacement and abandonment generation on sphere')
        out=a.generation(((1,),(-1,)),((1,),),(0,),((0,),),1);self.assertEqual(out['accepted'],());self.assertEqual(out['abandoned'],(1,))
        for rows in ([ [[2],[0]],([1],[0]) ],[ ([2],[0]),[[1],[0]] ]):
            out=b.generation(rows,[0,0],[1,1],[0,0],[[0],(0,)])
            self.assertEqual(out['bats'][0][0],(1.,));self.assertEqual(out['local_search'],(0,1));self.assertEqual(out['accepted'],(0,));self.assertEqual(out['best_index_before'],1)
            self.assertEqual(out['scope'],'one synchronous bat frequency velocity and acceptance generation on sphere')
            for state in out['bats']:
                for vector in state:
                    for value in vector:self.assertIs(type(value),float)
    def test_default_and_cap(self):
        self.assertEqual(inspect.signature(a.generation).parameters['abandon'].default,1)
        for key,value in [('pulse_rate',.5),('loudness',.5),('bound',10.)]:self.assertEqual(inspect.signature(b.generation).parameters[key].default,value)
        a.generation([[100]*4]*16,[[0]*4]*32,[0]*32,[[0]*4]*16,16)
        b.generation([([100]*4,[100]*4)]*16,[2]*16,[1]*16,[1]*16,[[1]*4]*16,pulse_rate=0,loudness=1,bound=100)
        self.assertEqual(a.generation([[1]],[[0]],[0],[],0)['nests'],((F(0),),))
    def test_strict_draw_boundaries(self):
        rows=[([2],[0]),([1],[0])]
        out=b.generation(rows,[0,0],[.5,.5],[.5,.5],[[0],[0]])
        self.assertEqual(out['local_search'],());self.assertEqual(out['accepted'],())
    def test_tuple_levels_and_validation_order(self):
        self.assertEqual(a.generation(((1,),),((.1,),),(0,),(),0)['nests'],((F(1,10),),))
        self.assertEqual(b.generation((((1,),(0,)),),(0,),(0,),(0,),((0,),))['bats'],(((1.,),(0.,)),))
        with self.assertRaises(ValueError) as caught:a.generation([[float('nan')]],[],[],[])
        self.assertEqual(str(caught.exception),'finite built-in cuckoo coordinate in[-100,100] required')
        with self.assertRaises(ValueError) as caught:b.generation([([float('nan')],[0])],[],[],[],[])
        self.assertEqual(str(caught.exception),'finite built-in bat real outside range')

def seeded(seed):
    def test(self):
        rng=random.Random(seed);n=rng.randrange(1,8);d=rng.randrange(1,5);nests=[[rng.randrange(-10,11)/2 for _ in range(d)] for _ in range(n)];flights=[[rng.randrange(-10,11)/2 for _ in range(d)] for _ in range(10)];targets=[rng.randrange(n) for _ in flights];abandon=rng.randrange(n+1);discoveries=[[rng.randrange(-10,11)/2 for _ in range(d)] for _ in range(abandon)]
        out=a.generation(nests,flights,targets,discoveries,abandon);expected=[tuple(F(str(x)) for x in row) for row in nests];score=lambda row:sum(x*x for x in row);accepted=[]
        for i,(row,target) in enumerate(zip(flights,targets)):
            candidate=tuple(F(str(x)) for x in row)
            if score(candidate)<score(expected[target]):expected[target]=candidate;accepted.append((i,target))
        worst=tuple(sorted(range(n),key=lambda i:(-score(expected[i]),-i))[:abandon])
        for i,row in zip(worst,discoveries):expected[i]=tuple(F(str(x)) for x in row)
        self.assertEqual(out['nests'],tuple(expected));self.assertEqual(out['scores'],tuple(score(row) for row in expected));self.assertEqual(out['accepted'],tuple(accepted));self.assertEqual(out['abandoned'],worst)
        velocities=[[rng.uniform(-2,2) for _ in range(d)] for _ in range(n)];states=list(zip(nests,velocities));freq=[rng.random()*2 for _ in range(n)];pulse=[rng.random() for _ in range(n)];draws=[rng.random() for _ in range(n)];offset=[[rng.uniform(-1,1) for _ in range(d)] for _ in range(n)];pr=rng.random();la=rng.random();out=b.generation(states,freq,pulse,draws,offset,pr,la)
        best=min(range(n),key=lambda i:(sum(x*x for x in nests[i]),i));wanted=[];accepted=[];local=[]
        for i,(x,v) in enumerate(states):
            vel=[v[k]+(x[k]-nests[best][k])*freq[i] for k in range(d)]
            cand=[x[k]+vel[k] for k in range(d)]
            if pulse[i]>pr:local.append(i);cand=[nests[best][k]+offset[i][k] for k in range(d)]
            cand=[max(-10,min(10,z)) for z in cand]
            if sum(z*z for z in cand)<sum(z*z for z in x) and draws[i]<la:accepted.append(i);pos=cand
            else:pos=x
            wanted.append((pos,vel))
        for actual,want in zip(out['bats'],wanted):
            for av,wv in zip(actual,want):
                for x,y in zip(av,wv):self.assertAlmostEqual(x,y,places=12)
        self.assertEqual(out['accepted'],tuple(accepted));self.assertEqual(out['local_search'],tuple(local));self.assertEqual(out['best_index_before'],best)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))

def refuse(fn,args,kw,message):
    def test(self):
        with self.assertRaises(ValueError) as caught:fn(*args,**kw)
        self.assertEqual(str(caught.exception),message)
    return test
cases=[]
for nests in ([],[[0]]*17,L([[0]]),T([[0]])):
 cases.append((a.generation,(nests,[[0]],[0],[]),{'abandon':0},'nests must contain1..16 vectors'))
for abandon in (-1,2,True,I(0),1.):cases.append((a.generation,([[0]],[[0]],[0],[]),{'abandon':abandon},'abandon must be built-in int0..nestcount'))
for flights,targets in (([],[]),([[0]]*33,[0]*33),([[0]],[]),(L([[0]]),[0]),([[0]],T([0]))):cases.append((a.generation,([[0]],flights,targets,[]),{'abandon':0},'flights1..32 and matching target sequence required'))
for targets in ([True],[I(0)],[-1],[1]):cases.append((a.generation,([[0]],[[0]],targets,[]),{'abandon':0},'targets must be built-in int nest indices'))
for discoveries in ([],[[0],[0]],L([[0]]),T([[0]])):cases.append((a.generation,([[0]],[[0]],[0],discoveries),{},'exactly abandon discovery vectors required'))
for value in (True,I(0),S('1'),float('nan'),10**10000,100.5,-100.5):cases.append((a.generation,([[value]],[[0]],[0],[]),{'abandon':0},'finite built-in cuckoo coordinate in[-100,100] required'))
for row in ([],[0]*5,L([0]),T([0])):cases.append((a.generation,([row],[[0]],[0],[]),{'abandon':0},'vectors must have1..4 equal dimensions'))
for nests in ([[0,0],[0]],):cases.append((a.generation,(nests,[[0,0]],[0],[]),{'abandon':0},'vectors must have1..4 equal dimensions'))
base=([([0],[0])],[0],[0],[0],[[0]])
for rows in ([],[([0],[0])]*17,L([([0],[0])]),T([([0],[0])])):cases.append((b.generation,(rows,*base[1:]),{},'rows must contain1..16 bats'))
for rows in ([([0],)],[([0],[0,0])],[L(([0],[0]))],[([0],[0]),([0,0],[0])]):cases.append((b.generation,(rows,*base[1:]),{},'bat rows require two equal1..4 dimensional vectors'))
for key,value in [('pulse_rate',-.1),('pulse_rate',1.1),('loudness',-.1),('loudness',1.1),('bound',-.1),('bound',100.5),('bound',True),('bound',10**10000)]:cases.append((b.generation,base,{key:value},'finite built-in bat real outside range'))
cases.append((b.generation,base,{'bound':0},'bound must be positive'))
for slot in range(1,5):
 for make in (L,T):
  args=list(base);args[slot]=make(args[slot]);cases.append((b.generation,tuple(args),{},'one frequency/draw/offset per bat required'))
for slot,value in ((1,2.1),(1,-.1),(2,1.1),(2,-.1),(3,1.1),(3,-.1),(1,True),(2,I(0))):
 args=list(base);args[slot]=[value];cases.append((b.generation,tuple(args),{},'finite built-in bat real outside range'))
for value in (True,I(0),S('1'),float('nan'),10**10000,10.5,-10.5):cases.append((b.generation,([([value],[0])],*base[1:]),{},'finite built-in bat real outside range'))
for offsets in ([[1.1]],[[-1.1]]):cases.append((b.generation,(*base[:4],offsets),{},'finite built-in bat real outside range'))
for i,(fn,args,kw,msg) in enumerate(cases):setattr(Tests,'test_refusal_%02d'%i,refuse(fn,args,kw,msg))

def endpoint_acceptance(self):
    a.generation([[-100]],[[-100]],[0],[],0)
    b.generation([([-100],[-100])],[2],[1],[1],[[-1]],0,1,100)
Tests.test_endpoint_acceptance=endpoint_acceptance

def detailed_nested_types_and_acceptance_tie(self):
    for row in ([],[0]*5,L([0]),T([0]),{0:0}):
        with self.assertRaises(ValueError) as caught:a.generation([row],[[0]],[0],[],0)
        self.assertEqual(str(caught.exception),'vectors must have1..4 equal dimensions')
    for row in (L(([0],[0])),T(([0],[0])),([0]*5,[0]*5),([],[]),([L([0]),[0]]),([T([0]),[0]])):
        with self.assertRaises(ValueError) as caught:b.generation([row],[0],[0],[0],[[0]])
        self.assertEqual(str(caught.exception),'bat rows require two equal1..4 dimensional vectors')
    with self.assertRaises(ValueError) as caught:b.generation([([0],[0]),T(([0],[0]))],[0,0],[0,0],[0,0],[[0],[0]])
    self.assertEqual(str(caught.exception),'bat rows require two equal1..4 dimensional vectors')
    # Candidate improves via velocity while acceptance draw equals loudness.
    out=b.generation([([2],[-1])],[0],[0],[.5],[[0]],loudness=.5)
    self.assertEqual(out['accepted'],());self.assertEqual(out['bats'][0][0],(2.,))
    b.generation([([0],[0])],[0],[0],[0],[[0]],pulse_rate=0,loudness=0,bound=.5)
    for fn,args,kw,msg in [
      (b.generation,([],[],[],[],[]),{'bound':-.5},'finite built-in bat real outside range'),
      (b.generation,([([0],[100.5])],[0],[0],[0],[[0]]),{},'finite built-in bat real outside range'),
      (b.generation,([([0],[-100.5])],[0],[0],[0],[[0]]),{},'finite built-in bat real outside range'),
    ]:
        with self.assertRaises(ValueError) as caught:fn(*args,**kw)
        self.assertEqual(str(caught.exception),msg)
Tests.test_detailed_nested_types_and_acceptance_tie=detailed_nested_types_and_acceptance_tie

def first_dimension_caps(self):
    for sites in ([[]],[[0]*5]):
        with self.assertRaises(ValueError) as caught:a.generation(sites,[sites[0]],[0],[],0)
        self.assertEqual(str(caught.exception),'vectors must have1..4 equal dimensions')
    for vector in ([],[0]*5):
        with self.assertRaises(ValueError) as caught:b.generation([(vector,vector)],[0],[0],[0],[vector])
        self.assertEqual(str(caught.exception),'bat rows require two equal1..4 dimensional vectors')
    # Distinct position and velocity shapes force dimensions to come from position.
    with self.assertRaises(ValueError) as caught:b.generation([([0],[0,0])],[0],[0],[0],[[0]])
    self.assertEqual(str(caught.exception),'bat rows require two equal1..4 dimensional vectors')
Tests.test_first_dimension_caps=first_dimension_caps


def audit_malformed_vectors_and_bat_counts(self):
    vector_message='vectors must have1..4 equal dimensions'
    bat_message='bat rows require two equal1..4 dimensional vectors'
    count_message='one frequency/draw/offset per bat required'
    def check(fn,args,message,**kw):
        with self.assertRaises(ValueError) as caught:fn(*args,**kw)
        self.assertEqual(str(caught.exception),message)
    # Guard ordering must retain ValueError, never len/index TypeError/IndexError.
    for bad in (5,'ab',(),[],[0,0,0],L([0,0]),T([0,0])):
        for position in (0,1):
            nests=[(1,2),(3,4)];nests[position]=bad
            check(a.generation,(nests,[(0,0)],[0],[],0),vector_message)
    for bad in (5,'ab',(),[],[0,0,0],L([0,0]),T([0,0])):
        for slot in (1,3):
            args=[[(1,2)],[(0,0)],[0],[(0,0)],1];args[slot]=[bad]
            check(a.generation,args,vector_message)
    good=([1,2],[0,0])
    for bad in (5,(),[], 'ab',([1,2],),([1,2],[0,0],[0,0]),L(good),T(good)):
        for position in (0,1):
            rows=[good,good];rows[position]=bad
            check(b.generation,(rows,[0,0],[0,0],[0,0],[[0,0],[0,0]]),bat_message)
    for bad in (5,'ab',(),[],[0],L([0,0]),T([0,0])):
        for position in (0,1):
            for side in (0,1):
                rows=[[list(good[0]),list(good[1])],[list(good[0]),list(good[1])]]
                rows[position][side]=bad
                check(b.generation,(rows,[0,0],[0,0],[0,0],[[0,0],[0,0]]),bat_message)
    for slot in (1,2,3,4):
        for bad in (5,'ab',[],[0], [0,0,0],L([0,0]),T([0,0])):
            args=[[good,good],[0,0],[0,0],[0,0],[[0,0],[0,0]]]
            args[slot]=bad if slot!=4 or type(bad) not in (list,tuple) else [[0,0] for _ in bad]
            check(b.generation,args,count_message)
    for position in (0,1):
        for bad in (5,'ab',(),[],[0],L([0,0]),T([0,0])):
            offsets=[[0,0],[0,0]];offsets[position]=bad
            check(b.generation,([good,good],[0,0],[0,0],[0,0],offsets),bat_message)
Tests.test_audit_malformed_vectors_and_bat_counts=audit_malformed_vectors_and_bat_counts
