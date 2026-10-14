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
a=load('sequestration_decay1631');b=load('negative_net1632')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand_scope_mix(self):
        for additions in ([2,0],(2,0)):
            self.assertEqual(a.retain(additions,2,1,2),{'stocks':(F(3),F(3,2)),'losses':(F(1),F(3,2)),'final_stock':F(3,2),'total_losses':F(5,2),'scope':'caller stock-retention recurrence only; no sequestration permanence or emissions claims'})
        for rows in ([['B',1,3],('A',3,1),['C',0,0]],[('C',0,0),['A',3,1],('B',1,3)]):
            self.assertEqual(b.net(rows),{'net':(('A',2),('B',-2),('C',0)),'removed_total':4,'emitted_total':4,'net_total':0,'positive':('A',),'scope':'caller removal-emission bookkeeping only; no carbon credits or net-zero certification'})
    def test_caps(self):
        a.retain([1000000]*64,1000000,1000,1000);a.retain([0],0,0,1)
        b.net([(str(i),1000000,1000000) for i in range(64)]);b.net([('a'*40,0,0)])
    def test_precedence(self):
        with self.assertRaises(ValueError) as c:a.retain([],True,False,0)
        self.assertEqual(str(c.exception),'initial must be exactint0..1000000')
        with self.assertRaises(ValueError) as c:b.net([('a',0,0),('a',True,None)])
        self.assertEqual(str(c.exception),'labels must be unique')

def seeded(seed):
    def test(self):
        rng=random.Random(seed);additions=[rng.randrange(100) for _ in range(rng.randrange(1,30))];initial=rng.randrange(100);den=rng.randrange(1,1001);num=rng.randrange(den+1);f=F(num,den);stocks=tuple(initial*f**k+sum(additions[j]*f**(k-j-1) for j in range(k)) for k in range(1,len(additions)+1));previous=(F(initial),)+stocks[:-1];losses=tuple(before-after+addition for before,after,addition in zip(previous,stocks,additions));expected={'stocks':stocks,'losses':losses,'final_stock':stocks[-1],'total_losses':F(initial)+sum(additions)-stocks[-1],'scope':a.SCOPE};self.assertEqual(a.retain(additions,initial,num,den),expected);self.assertEqual(a.retain(tuple(additions),initial,num,den),expected)
        rows=[('Ω'+str(i),rng.randrange(1000001),rng.randrange(1000001)) for i in range(rng.randrange(1,40))];result=tuple(sorted((name,r-e) for name,r,e in rows));r=sum(x[1] for x in rows);e=sum(x[2] for x in rows);expected={'net':result,'removed_total':r,'emitted_total':e,'net_total':sum(delta for _,delta in result),'positive':tuple(sorted(name for name,r,e in rows if r>e)),'scope':b.SCOPE};self.assertEqual(b.net(rows),expected);self.assertEqual(b.net(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),expected)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))
def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for position in (0,1):
    for bad in (False,True,I(1),1.,None,'1',-1,1000001):cases.append((a.retain,([bad],0,0,1) if position==0 else ([0],bad,0,1),('addition' if position==0 else 'initial')+' must be exactint0..1000000'))
for position in (2,3):
    for bad in (False,True,I(1),1.,None,'1',-1,1001):
        args=[[0],0,0,1];args[position]=bad;cases.append((a.retain,tuple(args),'retention components must be exactint0<=num<=den<=1000 and den>0'))
for args in (([0],0,0,0),([0],0,2,1)):cases.append((a.retain,args,'retention components must be exactint0<=num<=den<=1000 and den>0'))
for bad in ([],[0]*65,{},set(),iter([]),'x',L([0]),T((0,))):cases.append((a.retain,(bad,0,0,1),'additions must be exactlist/tuple length1..64'))
for bad in ([],[('a',0,0)]*65,{},set(),iter([]),'x',L([('a',0,0)]),T((('a',0,0),))):cases.append((b.net,(bad,),'rows must be exactlist/tuple length1..64'))
for bad in ([],[1,2],(1,2,3,4),'abc',L(['a',0,0]),T(('a',0,0))):cases.append((b.net,([bad],),'row must be exactlist/tuple triple'))
for bad in ('','a'*41,'\n','\x00',S('a'),0,None):cases.append((b.net,([(bad,0,0)],),'label must be exactstr printable Unicode length1..40'))
for slot in (1,2):
    for bad in (False,True,I(1),1.,None,'1',-1,1000001):
        row=['a',0,0];row[slot]=bad;cases.append((b.net,([row],),'amounts must be exactint0..1000000'))
cases.append((b.net,([('a',0,0),('a',0,0)],),'labels must be unique'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))
def charset(char):
    def test(self):b.net([(char,0,0)])
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))

def exact_disclaimers(self):
    self.assertEqual(a.__doc__,'Carbon Sequestration.\n\nPARTIAL: caller stock-retention recurrence only, not carbon sequestration,\npermanence certification,decay measurement or lifecycle emissions accounting.\nRetention/additions supplied by caller,not validated storage process data.\n')
    self.assertEqual(b.__doc__,'Negative Emissions.\n\nPARTIAL: caller removal/emission bookkeeping only, not negative-emissions\nvalidation,carbon credits,lifecycle analysis or net-zero certification.\nAmounts supplied by caller,not verified removals or emissions inventories.\n')
Tests.test_exact_disclaimers=exact_disclaimers

def one_positive(self):self.assertEqual(b.net([('x',1,0)])['positive'],('x',))
Tests.test_one_positive=one_positive
