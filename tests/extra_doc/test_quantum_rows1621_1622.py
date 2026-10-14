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
import string
from fractions import Fraction as F
a=load('climate_recurrence1621');b=load('warming_scenarios1622')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand_scope_mix(self):
        self.assertEqual(a.evolve([1,-1],2,1,2),{'states':(F(2),F(2),F(0)),'final':F(0),'scope':'caller scalar affine recurrence only; no climate modeling or forecasts'})
        for rows in ([['B',0,-1,2],('A',1,1,2)],[('A',1,1,2),['B',0,-1,2]]):
            self.assertEqual(b.scenarios(rows,[2,0]),{'scenarios':(('A',((0,F(1)),(2,F(2)))),('B',((0,F(0)),(2,F(-1))))),'envelope':((0,F(0),F(1)),(2,F(-1),F(2))),'scope':'caller linear scenario arithmetic only; no global-warming projections'})
    def test_caps(self):
        a.evolve([1000000]*64,1000000,1000,1000);a.evolve([-1000000],-1000000,0,1)
        b.scenarios([(str(i),1000000,1000000,1000000) for i in range(32)],list(range(32)));b.scenarios([('a'*40,-1000000,-1000000,1)],[100000])
    def test_precedence(self):
        with self.assertRaises(ValueError) as c:a.evolve([],True,False,0)
        self.assertEqual(str(c.exception),'initial must be exactint-1000000..1000000')
        with self.assertRaises(ValueError) as c:b.scenarios({},[0,0])
        self.assertEqual(str(c.exception),'steps must be unique')
        with self.assertRaises(ValueError) as c:b.scenarios([('a',0,0,1),('a',True,None,0)],[0])
        self.assertEqual(str(c.exception),'labels must be unique')

def seeded(seed):
    def test(self):
        rng=random.Random(seed);forcing=[rng.randrange(-100,101) for _ in range(rng.randrange(1,30))];initial=rng.randrange(-100,101);den=rng.randrange(1,1001);num=rng.randrange(den+1);coef=F(num,den);states=tuple(F(initial)*coef**k+sum(F(forcing[j])*coef**(k-j-1) for j in range(k)) for k in range(len(forcing)+1));expected={'states':states,'final':states[-1],'scope':a.SCOPE};self.assertEqual(a.evolve(forcing,initial,num,den),expected);self.assertEqual(a.evolve(tuple(forcing),initial,num,den),expected)
        rows=[('Ω'+str(i),rng.randrange(-100,101),rng.randrange(-100,101),rng.randrange(1,1001)) for i in range(rng.randrange(1,15))];steps=rng.sample(range(100001),rng.randrange(1,15));series=tuple(sorted((name,tuple((step,F(intercept*den+step*num,den)) for step in sorted(steps))) for name,intercept,num,den in rows));envelope=tuple((step,min(F(intercept*den+step*num,den) for name,intercept,num,den in rows),max(F(intercept*den+step*num,den) for name,intercept,num,den in rows)) for step in sorted(steps));expected={'scenarios':series,'envelope':envelope,'scope':b.SCOPE};self.assertEqual(b.scenarios(rows,steps),expected);self.assertEqual(b.scenarios(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1])),tuple(steps[::-1])),expected)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))

def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for position in (0,1):
    for bad in (False,True,I(1),1.,None,'1',-1000001,1000001):
        args=([bad],0,0,1) if position==0 else ([0],bad,0,1);cases.append((a.evolve,args,('forcing value' if position==0 else 'initial')+' must be exactint-1000000..1000000'))
for position in (2,3):
    for bad in (False,True,I(1),1.,None,'1',-1,1001):
        args=[[0],0,0,1];args[position]=bad;cases.append((a.evolve,tuple(args),'coefficient must be exactint0<=num<=den<=1000 and den>0'))
for args in (([0],0,0,0),([0],0,2,1)):cases.append((a.evolve,args,'coefficient must be exactint0<=num<=den<=1000 and den>0'))
for bad in ([],[0]*65,{},set(),iter([]),'x',L([0]),T((0,))):cases.append((a.evolve,(bad,0,0,1),'forcing must be exactlist/tuple length1..64'))
for bad in ([],list(range(33)),{},set(),iter([]),'x',L([0]),T((0,))):cases.append((b.scenarios,([('a',0,0,1)],bad),'steps must be exactlist/tuple length1..32'))
for bad in (False,True,I(1),1.,None,'1',-1,100001):cases.append((b.scenarios,([('a',0,0,1)],[bad]),'step must be exactint0..100000'))
cases.append((b.scenarios,([('a',0,0,1)],[0,0]),'steps must be unique'))
for bad in ([],[('a',0,0,1)]*33,{},set(),iter([]),'x',L([('a',0,0,1)]),T((('a',0,0,1),))):cases.append((b.scenarios,(bad,[0]),'rows must be exactlist/tuple length1..32'))
for bad in ([],[1,2,3],(1,2,3,4,5),'abcd',L(['a',0,0,1]),T(('a',0,0,1))):cases.append((b.scenarios,([bad],[0]),'row must be exactlist/tuple four values'))
for bad in ('','a'*41,'\n','\x00',S('a'),0,None):cases.append((b.scenarios,([(bad,0,0,1)],[0]),'label must be exactstr printable Unicode length1..40'))
for position in (1,2):
    for bad in (False,True,I(1),1.,None,'1',-1000001,1000001):
        row=['a',0,0,1];row[position]=bad;cases.append((b.scenarios,([row],[0]),'intercept and numerator must be exactint-1000000..1000000'))
for bad in (False,True,I(1),1.,None,'1',0,1000001):cases.append((b.scenarios,([('a',0,0,bad)],[0]),'denominator must be exactint1..1000000'))
cases.append((b.scenarios,([('a',0,0,1),('a',0,0,1)],[0]),'labels must be unique'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))
def charset(char):
    def test(self):b.scenarios([(char,0,0,1)],[0])
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))

def exact_disclaimers(self):
    self.assertEqual(a.__doc__,'Climate Modeling.\n\nPARTIAL: caller scalar affine recurrence arithmetic only, not climate modeling,\nphysical simulation,forecasting or validated temperature dynamics. Initial state,\ncoefficients and forcing are caller abstractions,not calibrated climate data.\n')
    self.assertEqual(b.__doc__,'Global Warming Projections.\n\nPARTIAL: caller linear scenario arithmetic only, not warming projections,\nclimate forecasts,emissions-response estimates or scientific confidence bounds.\nSlopes/intercepts supplied by caller without physical calibration or validation.\n')
Tests.test_exact_disclaimers=exact_disclaimers
