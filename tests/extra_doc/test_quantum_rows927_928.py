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
import random
a=load('biological927');b=load('swarm928')
class I(int):pass
class S(str):pass
class Tests(unittest.TestCase):
    def test_scopes_and_mix(self):
        for rules in ([['A','NOT',['A']],('B','COPY',('A',))],[('A','NOT',('A',)),['B','COPY',['A']]]):
            out=a.run_circuit({'A':0,'B':0},rules);self.assertEqual(out['states'],((0,0),(1,0),(0,1),(1,0)));self.assertEqual(out['period'],2);self.assertEqual(out['cycle_start'],1);self.assertEqual(out['scope'],'synchronous Boolean gene circuit and cycle detection; no living substrate')
        for rows in ([['a',0,0,0,0],('b',1,0,0,0)],[('b',1,0,0,0),['a',0,0,0,0]]):
            out=b.step_swarm(rows);self.assertEqual(out['agents'],(('a',F(0),F(0),F(0),F(0)),('b',F(1),F(0),F(0),F(0))));self.assertEqual(out['scope'],'synchronous rational 2D separation alignment cohesion step; no physical swarm')
    def test_defaults_zero_and_exact_boundary(self):
        initial={'A':0};rules=[('A','NOT',['A'])]
        self.assertEqual(a.run_circuit(initial,rules),a.run_circuit(initial,rules,100));self.assertIsNone(a.run_circuit(initial,rules,0)['period'])
        self.assertEqual(b.step_swarm([('A',0,0,1,1)]),b.step_swarm([('A',0,0,1,1)],1,1,1,1,1))
        self.assertEqual(b.step_swarm([('A',0,0,1,1)])['agents'][0][3:],(F(1,2),F(1,2)))
        self.assertEqual(b.step_swarm([('a',0,0,0,0),('b',0,0,0,0)])['neighbors'],(('a',('b',)),('b',('a',))))

def seeded(seed):
    def test(self):
        rng=random.Random(seed);names=list('ABCD');initial={key:rng.randrange(2) for key in names};rules=[]
        for key in names:
            op=rng.choice(['COPY','NOT','AND','OR','XOR']);inputs=rng.sample(names,1 if op in ('COPY','NOT') else rng.randrange(1,5));rules.append((key,op,inputs))
        steps=rng.randrange(10);out=a.run_circuit(initial,rules,steps);state=initial.copy();states=[tuple(state[k] for k in names)];seen={states[0]:0};start=period=None
        for tick in range(1,steps+1):
            new={}
            for key,op,inputs in rules:
                bits=[state[x] for x in inputs]
                if op=='COPY':val=bits[0]
                elif op=='NOT':val=int(bits[0]==0)
                elif op=='AND':val=int(0 not in bits)
                elif op=='OR':val=int(1 in bits)
                else:val=0
                if op=='XOR':
                    for bit in bits:val^=bit
                new[key]=val
            state=new;vector=tuple(state[k] for k in names);states.append(vector)
            if vector in seen:start=seen[vector];period=tick-start;break
            seen[vector]=tick
        self.assertEqual(out['states'],tuple(states));self.assertEqual(out['period'],period);self.assertEqual(out['cycle_start'],start)
        rows=[(key,*[rng.randrange(-5,6) for _ in range(4)]) for key in names];r=rng.randrange(1,11);weights=[rng.randrange(4) for _ in range(3)];speed=rng.randrange(1,5)
        out=b.step_swarm(rows,r,*weights,speed);expected=[];neigh=[]
        for key,x,y,vx,vy in rows:
            close=[];sep=[F(0),F(0)];align=[F(0),F(0)];cohesion=[F(0),F(0)]
            for other,xx,yy,ux,uy in rows:
                d=(x-xx)**2+(y-yy)**2
                if other==key or d>r*r:continue
                close.append(other)
                if d:sep[0]+=F(x-xx,d);sep[1]+=F(y-yy,d)
                align[0]+=ux-vx;align[1]+=uy-vy;cohesion[0]+=xx-x;cohesion[1]+=yy-y
            v=[F(vx),F(vy)]
            if close:
                for axis in range(2):v[axis]+=sum(w*f[axis] for w,f in zip(weights,[sep,align,cohesion]))/len(close)
            norm=sum(abs(z) for z in v)
            if norm>speed:v=[z*F(speed)/norm for z in v]
            expected.append((key,F(x)+v[0],F(y)+v[1],*v));neigh.append((key,tuple(sorted(close))))
        self.assertEqual(out['agents'],tuple(expected));self.assertEqual(out['neighbors'],tuple(neigh))
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))

import inspect

def explicit_defaults_caps(self):
    self.assertEqual(inspect.signature(a.run_circuit).parameters['steps'].default,100)
    expected={'radius':1.,'separation':1.,'alignment':1.,'cohesion':1.,'max_speed':1.}
    for key,value in expected.items():self.assertEqual(inspect.signature(b.step_swarm).parameters[key].default,value)
    initial={str(i):0 for i in range(16)};rules=[(key,'AND',list(initial)) for key in initial]
    a.run_circuit(initial,rules,10000)
    for bad in (10001,-1,True,I(1),1.):
        with self.assertRaises(ValueError) as caught:a.run_circuit(initial,rules,bad)
        self.assertEqual(str(caught.exception),'steps must be built-in int0..10000')
    label='a'*24;a.run_circuit({label:0},[(label,'NOT',[label])])
    rows=[(str(i),100,-100,100,-100) for i in range(32)]
    b.step_swarm(rows,radius=100,separation=10,alignment=10,cohesion=10,max_speed=100)
    b.step_swarm([('a_'+'x'*22,0,0,0,0)])
    for kw in ({'radius':-.1},{'radius':100.5},{'max_speed':-.1},{'max_speed':100.5},{'separation':-.1},{'separation':10.5},{'alignment':-.1},{'alignment':10.5},{'cohesion':-.1},{'cohesion':10.5}):
        with self.assertRaises(ValueError) as caught:b.step_swarm([('a',0,0,0,0)],**kw)
        self.assertEqual(str(caught.exception),'finite built-in swarm real outside range')
    for value in (100.5,-100.5):
        with self.assertRaises(ValueError):b.step_swarm([('a',value,0,0,0)])
Tests.test_explicit_defaults_caps=explicit_defaults_caps

def refuse(fn,args,kwargs,message):
    def test(self):
        with self.assertRaises(ValueError) as caught:fn(*args,**kwargs)
        self.assertEqual(str(caught.exception),message)
    return test
cases=[]
for initial in ({},{str(i):0 for i in range(17)},[('A',0)]):cases.append((a.run_circuit,(initial,[]),{},'initial must be exactdict1..16 genes'))
for value in (True,I(0),2,-1):cases.append((a.run_circuit,({'A':value},[('A','NOT',['A'])]),{},'gene values must be built-in int0/1'))
for rules in ([],{0:('A','NOT',['A'])}):cases.append((a.run_circuit,({'A':0},rules),{},'exactly one rule per gene required'))
for row in (('A','NOT'),{'gene':'A'}):cases.append((a.run_circuit,({'A':0},[row]),{},'rule must be list/tuple triple'))
for rules in ([('B','NOT',['A'])],[('A','NOT',['A']),('A','COPY',['A'])]):
 initial={'A':0} if len(rules)==1 else {'A':0,'B':0};cases.append((a.run_circuit,(initial,rules),{},'rule genes must be known and unique'))
for op in ('bad',S('NOT'),True):cases.append((a.run_circuit,({'A':0},[('A',op,['A'])]),{},'operation must be exactstr COPY/NOT/AND/OR/XOR'))
for inputs in ([],['B'],['A','A'],{'A'}):cases.append((a.run_circuit,({'A':0},[('A','AND',inputs)]),{},'rule inputs must contain1..16 known unique genes'))
cases.append((a.run_circuit,({'A':0,'B':0},[('A','COPY',['A','B']),('B','NOT',['B'])]),{},'COPY/NOT require exactly one input'))
for label in ('a-b','é','a'*25,S('a')):
 cases.append((a.run_circuit,({label:0},[(label,'NOT',[label])]),{},'exact ASCII alphanumeric/underscore label length1..24 required'))
 cases.append((b.step_swarm,([(label,0,0,0,0)],),{},'exact ASCII alphanumeric/underscore label length1..24 required'))
for rows in ([],[('a',0,0,0,0)]*33,{'a':(0,0,0,0)}):cases.append((b.step_swarm,(rows,),{},'rows must contain1..32 agents'))
for row in (('a',0),{'a':0}):cases.append((b.step_swarm,([row],),{},'agent must be list/tuple five-item row'))
cases.append((b.step_swarm,([('a',0,0,0,0)]*2,),{},'agent labels must be unique'))
for value in (True,I(0),S('1'),float('nan'),10**10000):cases.append((b.step_swarm,([('a',value,0,0,0)],),{},'finite built-in swarm real outside range'))
for kw in ({'radius':0},{'max_speed':0}):cases.append((b.step_swarm,([('a',0,0,0,0)],),kw,'radius and max_speed must be positive'))
for i,(fn,args,kw,msg) in enumerate(cases):setattr(Tests,'test_refusal_%02d'%i,refuse(fn,args,kw,msg))

def underscore_and_budget_scope(self):
    self.assertEqual(a.run_circuit({'A_':0},[('A_','NOT',['A_'])],0)['scope'],'synchronous Boolean gene circuit and cycle detection; no living substrate')
    self.assertEqual(b.step_swarm([('A_',0,0,0,0)])['agents'][0][0],'A_')
Tests.test_underscore_and_budget_scope=underscore_and_budget_scope

def empty_label_refusal(self):
    for fn,args in ((a.run_circuit,({'':0},[('','NOT',[''])])),(b.step_swarm,([('',0,0,0,0)],))):
        with self.assertRaises(ValueError) as caught:fn(*args)
        self.assertEqual(str(caught.exception),'exact ASCII alphanumeric/underscore label length1..24 required')
Tests.test_empty_label_refusal=empty_label_refusal

def biological_audit_contracts(self):
    for steps in (0,5):self.assertEqual(a.run_circuit({'a':0},[('a','NOT',['a'])],steps)['genes'],('a',))
    with self.assertRaises(ValueError) as caught:a.run_circuit({'a':0,'b':0},[('a','NOT',['a','b']),('b','COPY',['b'])])
    self.assertEqual(str(caught.exception),'COPY/NOT require exactly one input')
    class D(dict):pass
    with self.assertRaises(ValueError) as caught:a.run_circuit(D({'a':0}),[('a','NOT',['a'])])
    self.assertEqual(str(caught.exception),'initial must be exactdict1..16 genes')
Tests.test_biological_audit_contracts=biological_audit_contracts

def swarm_audit_exact_container_contracts(self):
    class L(list):pass
    class T(tuple):pass
    for make in (L,T):
        for rows,message in ((make([('a',0,0,0,0)]),'rows must contain1..32 agents'),([make(('a',0,0,0,0))],'agent must be list/tuple five-item row')):
            with self.assertRaises(ValueError) as caught:b.step_swarm(rows)
            self.assertEqual(str(caught.exception),message)
Tests.test_swarm_audit_exact_container_contracts=swarm_audit_exact_container_contracts

def exact_module_docstrings(self):
    self.assertEqual(a.__doc__,'Biological Computing - Living systems as computers.\n\nPARTIAL: deterministic synchronous Boolean gene-regulatory circuit model, not\nliving cells, biological substrate computation or an experimentally validated\nsynthetic circuit. No host context, kinetic/noise or wet-lab design.\n')
    self.assertEqual(b.__doc__,'Swarm Intelligence - Collective behavior algorithms.\n\nPARTIAL: exact-rational synchronous two-dimensional separation/alignment/cohesion\nswarm update with L1 speed clipping. No physical agents, learning, collision-\navoidance proof or global optimum guarantee. Caller-supplied state only.\n')
Tests.test_exact_module_docstrings=exact_module_docstrings

def biological_all_container_levels(self):
    class L(list):pass
    class T(tuple):pass
    for make in (L,T):
        for rules,message in ((make([('a','NOT',['a'])]),'exactly one rule per gene required'),([make(('a','NOT',['a']))],'rule must be list/tuple triple'),([('a','NOT',make(['a']))],'rule inputs must contain1..16 known unique genes')):
            with self.assertRaises(ValueError) as caught:a.run_circuit({'a':0},rules)
            self.assertEqual(str(caught.exception),message)
Tests.test_biological_all_container_levels=biological_all_container_levels


def biological_label_validation_precedes_membership(self):
    label_message='exact ASCII alphanumeric/underscore label length1..24 required'
    cases=[({'bad!label':0},[],0,label_message),
           ({'A':0},[('bad!','NOT',['bad!'])],0,label_message),
           ({'A':0},[('A','AND',['A','bad!'])],0,label_message),
           ({'A':0},[('A','AND',['A','B'])],0,'rule inputs must contain1..16 known unique genes')]
    for initial,rules,steps,message in cases:
        with self.assertRaises(ValueError) as caught:a.run_circuit(initial,rules,steps)
        self.assertEqual(str(caught.exception),message)
Tests.test_biological_label_validation_precedes_membership=biological_label_validation_precedes_membership
