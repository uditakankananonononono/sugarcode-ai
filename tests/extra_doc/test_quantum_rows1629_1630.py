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
a=load('adaptation_regret1629');b=load('capture_fraction1630')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand_scope_mix(self):
        for rows in ([['B',[3,0]],('A',(0,3))],[('A',[0,3]),['B',(3,0)]]):
            self.assertEqual(a.regret(rows),{'regrets':(('A',(0,3),3),('B',(3,0),3)),'minimax':3,'ties':('A','B'),'scope':'caller scenario cost regret arithmetic only; no climate adaptation or policy advice'})
        for rows in ([['B',3,1,2],('A',1,1,3)],[('A',1,1,3),['B',3,1,2]]):
            self.assertEqual(b.streams(rows),{'streams':(('A',F(1,3),F(2,3)),('B',F(3,2),F(3,2))),'input_total':4,'retained_total':F(11,6),'remainder_total':F(13,6),'retained_fraction':F(11,24),'scope':'caller stream fraction ledger only; no capture efficiency or emissions claims'})
        self.assertIsNone(b.streams([('x',0,0,1)])['retained_fraction'])
    def test_caps(self):
        a.regret([(str(i),[1000000]*32) for i in range(32)]);a.regret([('a'*40,[0])])
        b.streams([(str(i),1000000,1000000,1000000) for i in range(64)]);b.streams([('a'*40,0,0,1)])
    def test_precedence(self):
        with self.assertRaises(ValueError) as c:a.regret([('a',[0]),('a',None)])
        self.assertEqual(str(c.exception),'labels must be unique')
        with self.assertRaises(ValueError) as c:b.streams([('a',0,0,1),('a',True,None,0)])
        self.assertEqual(str(c.exception),'labels must be unique')

def seeded(seed):
    def test(self):
        rng=random.Random(seed);width=rng.randrange(1,15);rows=[('Ω'+str(i),[rng.randrange(100) for j in range(width)]) for i in range(rng.randrange(1,20))];result=[]
        for name,costs in rows:
            regrets=tuple(max(costs[j]-other[j] for _,other in rows) for j in range(width));result.append((name,regrets,max(regrets)))
        result.sort();best=min(score for name,r,score in result);out={'regrets':tuple(result),'minimax':best,'ties':tuple(name for name,r,score in result if score==best),'scope':a.SCOPE};self.assertEqual(a.regret(rows),out);self.assertEqual(a.regret(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
        rows=[]
        for i in range(rng.randrange(1,40)):
            den=rng.randrange(1,1000001);rows.append(('É'+str(i),rng.randrange(1000001),rng.randrange(den+1),den))
        result=tuple(sorted((name,F(amount*num,den),F(amount*(den-num),den)) for name,amount,num,den in rows));total=sum(amount for _,amount,num,den in rows);retained=sum(x[1] for x in result);out={'streams':result,'input_total':total,'retained_total':retained,'remainder_total':F(total)-retained,'retained_fraction':retained/total if total else None,'scope':b.SCOPE};self.assertEqual(b.streams(rows),out);self.assertEqual(b.streams(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))
def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for fn,row,cap in ((a.regret,('a',[0]),32),(b.streams,('a',0,0,1),64)):
    for bad in ([],[row]*(cap+1),{},set(),iter([]),'x',L([row]),T((row,))):cases.append((fn,(bad,),'rows must be exactlist/tuple length1..'+str(cap)))
    for bad in ([],list(row[:-1]),tuple(row)+(1,),'abcd',L(row),T(row)):cases.append((fn,([bad],),'row must be exactlist/tuple '+('pair' if fn==a.regret else 'four values')))
    for bad in ('','a'*41,'\n','\x00',S('a'),0,None):cases.append((fn,([(bad,)+row[1:]],),'label must be exactstr printable Unicode length1..40'))
    cases.append((fn,([row,row],),'labels must be unique'))
for bad in ([],[0]*33,{},set(),iter([]),'x',L([0]),T((0,))):cases.append((a.regret,([('a',bad)],),'costs must be exactlist/tuple length1..32'))
for bad in (False,True,I(1),1.,None,'1',-1,1000001):cases.append((a.regret,([('a',[bad])],),'cost must be exactint0..1000000'))
cases.append((a.regret,([('a',[0]),('b',[0,0])],),'cost vectors must have equal width'))
for bad in (False,True,I(1),1.,None,'1',-1,1000001):cases.append((b.streams,([('a',bad,0,1)],),'amount must be exactint0..1000000'))
for slot in (2,3):
    for bad in (False,True,I(1),1.,None,'1',-1,1000001):
        row=['a',0,0,1];row[slot]=bad;cases.append((b.streams,([row],),'fraction components must be exactint0<=num<=den<=1000000 and den>0'))
for row in (('a',0,0,0),('a',0,2,1)):cases.append((b.streams,([row],),'fraction components must be exactint0<=num<=den<=1000000 and den>0'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))
def charset(char):
    def test(self):a.regret([(char,[0])]);b.streams([(char,0,0,1)])
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))

def exact_disclaimers(self):
    self.assertEqual(a.__doc__,'Adaptation Planning.\n\nPARTIAL: caller rectangular option/scenario cost regret arithmetic only, not\nadaptation planning,climate risks,economic evaluation or policy advice. Costs\nare abstract caller integers,not validated impacts,probabilities or preferences.\n')
    self.assertEqual(b.__doc__,'Carbon Capture.\n\nPARTIAL: caller stream fraction ledger arithmetic only, not carbon capture,\nseparation physics,efficiency certification,emissions accounting or cost analysis.\nInput quantities/fractions caller-declared,not measured or validated process data.\n')
Tests.test_exact_disclaimers=exact_disclaimers
