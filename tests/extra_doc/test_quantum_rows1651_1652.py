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
a=load('waste_energy1651');b=load('landfill_capacity1652')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand(self):
        for rows in ([['B',3,2,4],('A',0,1,1)],[('B',3,2,4),['A',0,1,1]]):
            self.assertEqual(a.energy(rows),{'energy':(('A',F(0)),('B',F(3,2))),'total':F(3,2),'positive':('B',),'scope':'caller mass-energy-factor arithmetic only; no waste-to-energy performance claims'})
        for rows in ([['B',3,2,2],('A',2,1,1)],[('B',3,2,2),['A',2,1,1]]):
            self.assertEqual(b.capacity(rows),{'capacity':(('A',1,0),('B',1,-1)),'overflow':('B',),'total_free_after':-1,'scope':'caller capacity-used-incoming ledger only; no landfill management advice'})
        self.assertEqual(a.energy([('x',1,0,1)])['positive'],())
        self.assertEqual(b.capacity([('x',0,0,0)])['overflow'],())
    def test_caps(self):
        a.energy([(str(i),1000000,1000000,1000000) for i in range(64)]);a.energy([('x'*40,0,0,1)])
        b.capacity([(str(i),1000000,1000000,1000000) for i in range(64)]);b.capacity([('x'*40,0,0,0)])
    def test_precedence(self):
        for fn,row in ((a.energy,('x',1,1,1)),(b.capacity,('x',1,0,0))):
            with self.assertRaises(ValueError) as c:fn([row,('x',True,None,None)])
            self.assertEqual(str(c.exception),'labels must be unique')
            with self.assertRaises(ValueError) as c:fn([('',True,None,None)])
            self.assertEqual(str(c.exception),'label must be exactstr printable Unicode length1..40')

def seeded(seed):
    def test(self):
        r=random.Random(seed);rows=[('Ω'+str(i),r.randrange(1000001),r.randrange(1000001),r.randrange(1,1000001)) for i in range(r.randrange(1,40))];r.shuffle(rows)
        result=tuple((name,F(m)*F(n,d)) for name,m,n,d in sorted(rows));out={'energy':result,'total':sum(value for name,value in result),'positive':tuple(name for name,m,n,d in sorted(rows) if m!=0 and n!=0),'scope':a.SCOPE}
        self.assertEqual(a.energy(rows),out);self.assertEqual(a.energy(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
        rows=[]
        for i in range(r.randrange(1,40)):
            cap=r.randrange(1000001);rows.append(('É'+str(i),cap,r.randrange(cap+1),r.randrange(1000001)))
        r.shuffle(rows);result=tuple((name,cap-used,cap-(used+incoming)) for name,cap,used,incoming in sorted(rows));out={'capacity':result,'overflow':tuple(name for name,cap,used,incoming in sorted(rows) if used+incoming>cap),'total_free_after':sum(cap for name,cap,u,i in rows)-sum(u+i for name,cap,u,i in rows),'scope':b.SCOPE}
        self.assertEqual(b.capacity(rows),out);self.assertEqual(b.capacity(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))
def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for fn,row in ((a.energy,('a',1,1,1)),(b.capacity,('a',1,0,0))):
    for bad in ([],[row]*65,{},set(),iter([]),'x',None,L([row]),T((row,))):cases.append((fn,(bad,),'rows must be exactlist/tuple length1..64'))
    for bad in ([],[1,2,3],(1,2,3,4,5),'abcd',None,L(row),T(row)):cases.append((fn,([bad],),'row must be exactlist/tuple quadruple'))
    for bad in ('','x'*41,'\n','\x00',S('a'),0,None):cases.append((fn,([(bad,)+row[1:]],),'label must be exactstr printable Unicode length1..40'))
    for slot in (1,2,3):
        for bad in (True,False,I(0),1.,None,'1',-1,1000001):
            altered=list(row);altered[slot]=bad;cases.append((fn,([altered],),'mass and numerator must be exactint0..1000000 and denominator exactint1..1000000' if fn==a.energy else 'quantities must be exactint0<=used<=capacity<=1000000 and incoming0..1000000'))
    cases.append((fn,([row,row],),'labels must be unique'))
cases.append((a.energy,([('a',0,0,0)],),'mass and numerator must be exactint0..1000000 and denominator exactint1..1000000'))
cases.append((b.capacity,([('a',0,1,0)],),'quantities must be exactint0<=used<=capacity<=1000000 and incoming0..1000000'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))
def charset(char):
    def test(self):a.energy([(char,0,0,1)]);b.capacity([(char,0,0,0)])
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))

def disclaimer(self):
    self.assertEqual(a.__doc__,'Waste-to-Energy.\n\nPARTIAL: caller mass/energy-factor multiplication only, not waste-to-energy,\ncombustion, gasification, emissions accounting or plant performance modeling.\nFactors and compatible units are caller declarations, not verified energy data.\n')
    self.assertEqual(b.__doc__,'Landfill Management.\n\nPARTIAL: caller capacity/used/incoming ledger only, not landfill management,\nsite engineering, leachate control, safety assessment or regulatory compliance.\nQuantities are caller-defined compatible units, not verified site measurements.\n')
Tests.test_disclaimer=disclaimer
def unit_positive(self):self.assertEqual(a.energy([('x',1,1,1)])['positive'],('x',))
Tests.test_unit_positive=unit_positive
