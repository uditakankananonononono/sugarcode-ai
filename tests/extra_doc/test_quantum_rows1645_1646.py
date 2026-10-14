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
from math import prod
a=load('hydrogen_chain1645');b=load('circular_flows1646')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand_scope_mix(self):
        for rows in ([['B',1,2],('A',1,3)],[('B',1,2),['A',1,3]]):
            self.assertEqual(a.chain(rows,3),{'stages':(('B',F(3,2),F(3,2)),('A',F(1,2),F(1))),'final':F(1,2),'total_losses':F(5,2),'scope':'caller staged conversion-factor chain only; no hydrogen performance or cost claims'})
        self.assertEqual(a.chain([],1)['final'],1)
        for rows in ([['B',1,2],('A',2,0),['B',0,1]],[('B',0,1),['A',2,0],('B',1,2)]):
            self.assertEqual(b.flows(rows),{'flows':(('A',2,0,2),('B',1,3,-2)),'positive':('A',),'negative':('B',),'net_total':0,'scope':'caller incoming-outgoing resource ledger only; no circularity or sustainability claims'})
        self.assertEqual(b.flows([('x',1,0)])['positive'],('x',));self.assertEqual(b.flows([('x',0,1)])['negative'],('x',));self.assertEqual(b.flows([('x',0,0)])['positive'],())
    def test_caps(self):
        a.chain([(str(i),1000000,1000000) for i in range(64)],1000000);a.chain([('a'*40,0,1)],0)
        b.flows([('a'*40,1000000,1000000)]*64)
    def test_precedence(self):
        with self.assertRaises(ValueError) as c:a.chain([('a',1,1),('a',True,0)],0)
        self.assertEqual(str(c.exception),'labels must be unique')
        with self.assertRaises(ValueError) as c:b.flows([('',True,None)])
        self.assertEqual(str(c.exception),'label must be exactstr printable Unicode length1..40')

def seeded(seed):
    def test(self):
        rng=random.Random(seed);rows=[]
        for i in range(rng.randrange(40)):
            den=rng.randrange(1,1000001);rows.append(('Ω'+str(i),rng.randrange(den+1),den))
        initial=rng.randrange(1000001);stocks=[F(initial)*F(prod(n for _,n,d in rows[:i+1]),prod(d for _,n,d in rows[:i+1])) for i in range(len(rows))];previous=[F(initial)]+stocks[:-1];stages=tuple((row[0],stock,before-stock) for row,stock,before in zip(rows,stocks,previous));final=stocks[-1] if stocks else F(initial);out={'stages':stages,'final':final,'total_losses':sum(before-stock for before,stock in zip(previous,stocks)),'scope':a.SCOPE};self.assertEqual(a.chain(rows,initial),out);self.assertEqual(a.chain(tuple(list(row) if i%2 else row for i,row in enumerate(rows)),initial),out)
        rows=[('É'+str(rng.randrange(5)),rng.randrange(1000001),rng.randrange(1000001)) for i in range(rng.randrange(1,40))];result=[]
        for name in sorted(set(name for name,i,o in rows)):
            incoming=sum(i for label,i,o in rows if label==name);outgoing=sum(o for label,i,o in rows if label==name);result.append((name,incoming,outgoing,incoming-outgoing))
        out={'flows':tuple(result),'positive':tuple(x[0] for x in result if x[1]>x[2]),'negative':tuple(x[0] for x in result if x[1]<x[2]),'net_total':sum(i-o for name,i,o in rows),'scope':b.SCOPE};self.assertEqual(b.flows(rows),out);self.assertEqual(b.flows(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))
def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for bad in (False,True,I(1),1.,None,'1',-1,1000001):cases.append((a.chain,([],bad),'initial must be exactint0..1000000'))
for fn,row,tail,empty in ((a.chain,('a',0,1),(0,),False),(b.flows,('a',0,0),(),True)):
    bads=([row]*65,{},set(),iter([]),'x',L([row]),T((row,)))+(([],) if empty else ())
    for bad in bads:cases.append((fn,(bad,)+tail,'rows must be exactlist/tuple '+('length1..64' if empty else 'atmost64')))
    for bad in ([],[1,2],(1,2,3,4),'abc',L(row),T(row)):cases.append((fn,([bad],)+tail,'row must be exactlist/tuple triple'))
    for bad in ('','a'*41,'\n','\x00',S('a'),0,None):cases.append((fn,([(bad,)+row[1:]],)+tail,'label must be exactstr printable Unicode length1..40'))
for slot in (1,2):
    for bad in (False,True,I(1),1.,None,'1',-1,1000001):
        row=['a',0,1];row[slot]=bad;cases.append((a.chain,([row],0),'factor components must be exactint0<=num<=den<=1000000 and den>0'))
        row=['a',0,0];row[slot]=bad;cases.append((b.flows,([row],),'flows must be exactint0..1000000'))
for row in (('a',0,0),('a',2,1)):cases.append((a.chain,([row],0),'factor components must be exactint0<=num<=den<=1000000 and den>0'))
cases.append((a.chain,([('a',1,1),('a',1,1)],0),'labels must be unique'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))
def charset(char):
    def test(self):a.chain([(char,1,1)],0);b.flows([(char,0,0)])
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))

def exact_disclaimers(self):
    self.assertEqual(a.__doc__,'Hydrogen Economy.\n\nPARTIAL: caller staged conversion-factor chain only, not hydrogen economy,\nproduction/storage/transport physics,efficiency validation or cost analysis.\nInput/factors caller abstractions,no actual hydrogen quantities inferred.\n')
    self.assertEqual(b.__doc__,'Circular Economy.\n\nPARTIAL: caller incoming/outgoing resource ledger only, not circular economy,\nmaterial-flow certification,lifecycle analysis or sustainability assessment.\nFlows are caller-declared,not verified sourcing,reuse,recycling or disposal data.\n')
Tests.test_exact_disclaimers=exact_disclaimers

def zero_excluded(self):self.assertEqual(b.flows([('x',0,0)])['negative'],())
Tests.test_zero_excluded=zero_excluded
