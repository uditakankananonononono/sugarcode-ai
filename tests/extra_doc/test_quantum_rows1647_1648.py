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
a=load('waste_delta1647');b=load('recovery_ledger1648')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand(self):
        for rows in ([['B',2,3],('A',3,2)],[('B',2,3),['A',3,2]]):
            self.assertEqual(a.reductions(rows),{'reductions':(('A',1,F(1,3)),('B',-1,F(-1,2))),'total_delta':0,'increased':('B',),'scope':'caller baseline-current arithmetic only; no verified waste reduction claims'})
        for rows in ([['B',2,1],('A',0,0),['B',1,1]],[('B',1,1),['A',0,0],('B',2,1)]):
            self.assertEqual(b.recovery(rows),{'recovery':(('A',0,0,0,None),('B',3,2,1,F(2,3))),'total_residual':1,'scope':'caller input-recovered ledger only; no verified recycling claims'})
        self.assertEqual(a.reductions([('x',0,0)]),{'reductions':(('x',0,None),),'total_delta':0,'increased':(),'scope':a.SCOPE})
        self.assertEqual(a.reductions([('x',0,1)])['increased'],('x',))
        self.assertEqual(a.reductions([('x',1,1)])['increased'],())
    def test_caps(self):
        a.reductions([(str(i),1000000,1000000) for i in range(64)]);a.reductions([('x'*40,0,0)])
        b.recovery([('x'*40,1000000,1000000)]*64)
    def test_precedence(self):
        with self.assertRaises(ValueError) as c:a.reductions([('x',1,0),('x',True,None)])
        self.assertEqual(str(c.exception),'labels must be unique')
        for fn in (a.reductions,b.recovery):
            with self.assertRaises(ValueError) as c:fn([('',True,None)])
            self.assertEqual(str(c.exception),'label must be exactstr printable Unicode length1..40')

def seeded(seed):
    def test(self):
        r=random.Random(seed);rows=[('Ω'+str(i),r.randrange(1000001),r.randrange(1000001)) for i in range(r.randrange(1,40))];r.shuffle(rows)
        result=tuple((label,x-y,F(x-y,x) if x else None) for label,x,y in sorted(rows));out={'reductions':result,'total_delta':sum(x for _,x,_ in result),'increased':tuple(label for label,x,y in sorted(rows) if y>x),'scope':a.SCOPE}
        self.assertEqual(a.reductions(rows),out);self.assertEqual(a.reductions(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
        rows=[]
        for i in range(r.randrange(1,40)):
            q=r.randrange(1000001);rows.append(('É'+str(r.randrange(5)),q,r.randrange(q+1)))
        result=[]
        for label in sorted(set(row[0] for row in rows)):
            qs=[q for name,q,v in rows if name==label];vs=[v for name,q,v in rows if name==label];q=sum(qs);v=sum(vs);result.append((label,q,v,sum(x-y for x,y in zip(qs,vs)),F(v,q) if q else None))
        out={'recovery':tuple(result),'total_residual':sum(q-v for label,q,v in rows),'scope':b.SCOPE}
        self.assertEqual(b.recovery(rows),out);self.assertEqual(b.recovery(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))
def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for fn in (a.reductions,b.recovery):
    for bad in ([],[('a',1,0)]*65,{},set(),iter([]),'x',None,L([('a',1,0)]),T((('a',1,0),))):cases.append((fn,(bad,),'rows must be exactlist/tuple length1..64'))
    for bad in ([],[1,2],(1,2,3,4),'abc',None,L(('a',1,0)),T(('a',1,0))):cases.append((fn,([bad],),'row must be exactlist/tuple triple'))
    for bad in ('','x'*41,'\n','\x00',S('a'),0,None):cases.append((fn,([(bad,1,0)],),'label must be exactstr printable Unicode length1..40'))
    for slot in (1,2):
        for bad in (True,False,I(0),1.,None,'1',-1,1000001):
            row=['a',1,0];row[slot]=bad;cases.append((fn,([row],),'quantities must be exactint0..1000000' if fn==a.reductions else 'quantities must be exactint0<=recovered<=input<=1000000'))
cases.append((a.reductions,([('a',0,0),('a',0,0)],),'labels must be unique'))
cases.append((b.recovery,([('a',0,1)],),'quantities must be exactint0<=recovered<=input<=1000000'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))
def charset(char):
    def test(self):a.reductions([(char,0,0)]);b.recovery([(char,0,0)])
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))

def disclaimer(self):
    self.assertEqual(a.__doc__,'Waste Reduction.\n\nPARTIAL: caller baseline/current waste arithmetic only, not waste prevention,\nverified measurements, environmental benefit or regulatory compliance.\nQuantities are caller-defined units, not independently verified waste data.\n')
    self.assertEqual(b.__doc__,'Recycling.\n\nPARTIAL: caller input/recovered quantity ledger only, not recycling operations,\nmaterial identification, contamination testing or recovery certification.\nRecovered amounts are caller declarations, not verified recycling outcomes.\n')
Tests.test_disclaimer=disclaimer
