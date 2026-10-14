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
a=load('compost_mix1649');b=load('digestion_retention1650')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand(self):
        for rows in ([['B',3,2],('A',0,0)],[('B',3,2),['A',0,0]]):
            self.assertEqual(a.mixture(rows),{'components':(('A',None),('B',F(3,2))),'carbon':3,'nitrogen':2,'ratio':F(3,2),'scope':'caller carbon-nitrogen mixture arithmetic only; no composting advice'})
        self.assertEqual(a.mixture([('x',2,0)])['ratio'],None)
        self.assertEqual(a.mixture([('a',1,1),('b',9,3)])['ratio'],F(5,2))
        for rows in ([['B',3,2],('A',2,1)],[('B',3,2),['A',2,1]]):
            self.assertEqual(b.retention(rows,2),{'retention':(('A',F(2)),('B',F(3,2))),'below':('B',),'maximum':F(2),'scope':'caller volume-flow retention arithmetic only; no anaerobic digestion advice'})
        self.assertEqual(b.retention([('x',0,1)],0)['below'],())
    def test_caps(self):
        a.mixture([(str(i),1000000,1000000) for i in range(64)]);a.mixture([('x'*40,0,0)])
        b.retention([(str(i),1000000,1000000) for i in range(64)],1000000);b.retention([('x'*40,0,1)],0)
    def test_precedence(self):
        for fn,tail in ((a.mixture,()),(b.retention,(0,))):
            with self.assertRaises(ValueError) as c:fn([('x',1,1),('x',True,None)],*tail)
            self.assertEqual(str(c.exception),'labels must be unique')
            with self.assertRaises(ValueError) as c:fn([('',True,None)],*tail)
            self.assertEqual(str(c.exception),'label must be exactstr printable Unicode length1..40')

def seeded(seed):
    def test(self):
        r=random.Random(seed);rows=[('Ω'+str(i),r.randrange(1000001),r.randrange(1000001)) for i in range(r.randrange(1,40))];r.shuffle(rows);c=sum(x for _,x,y in rows);n=sum(y for _,x,y in rows)
        out={'components':tuple((name,F(x,y) if y else None) for name,x,y in sorted(rows)),'carbon':c,'nitrogen':n,'ratio':F(c,n) if n else None,'scope':a.SCOPE}
        self.assertEqual(a.mixture(rows),out);self.assertEqual(a.mixture(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
        rows=[('É'+str(i),r.randrange(1000001),r.randrange(1,1000001)) for i in range(r.randrange(1,40))];r.shuffle(rows);threshold=r.randrange(1000001)
        result=tuple((name,F(v,q)) for name,v,q in sorted(rows));out={'retention':result,'below':tuple(name for name,v,q in sorted(rows) if v<threshold*q),'maximum':sorted(value for name,value in result)[-1],'scope':b.SCOPE}
        self.assertEqual(b.retention(rows,threshold),out);self.assertEqual(b.retention(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1])),threshold),out)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))
def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for bad in (True,False,I(0),1.,None,'1',-1,1000001):cases.append((b.retention,([],bad),'threshold must be exactint0..1000000'))
for fn,tail in ((a.mixture,()),(b.retention,(0,))):
    for bad in ([],[('a',1,1)]*65,{},set(),iter([]),'x',None,L([('a',1,1)]),T((('a',1,1),))):cases.append((fn,(bad,)+tail,'rows must be exactlist/tuple length1..64'))
    for bad in ([],[1,2],(1,2,3,4),'abc',None,L(('a',1,1)),T(('a',1,1))):cases.append((fn,([bad],)+tail,'row must be exactlist/tuple triple'))
    for bad in ('','x'*41,'\n','\x00',S('a'),0,None):cases.append((fn,([(bad,1,1)],)+tail,'label must be exactstr printable Unicode length1..40'))
    for slot in (1,2):
        for bad in (True,False,I(0),1.,None,'1',-1,1000001):
            row=['a',1,1];row[slot]=bad;cases.append((fn,([row],)+tail,'quantities must be exactint0..1000000' if fn==a.mixture else 'volume must be exactint0..1000000 and flow exactint1..1000000'))
    cases.append((fn,([('a',0,1),('a',0,1)],)+tail,'labels must be unique'))
cases.append((b.retention,([('a',0,0)],0),'volume must be exactint0..1000000 and flow exactint1..1000000'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))
def charset(char):
    def test(self):a.mixture([(char,0,0)]);b.retention([(char,0,1)],0)
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))

def disclaimer(self):
    self.assertEqual(a.__doc__,'Composting.\n\nPARTIAL: caller carbon/nitrogen mixture arithmetic only, not composting,\nfeedstock testing, biological activity, safety or process recommendations.\nCaller quantities have no inferred units or agronomic target ranges.\n')
    self.assertEqual(b.__doc__,'Anaerobic Digestion.\n\nPARTIAL: caller volume/flow retention arithmetic only, not anaerobic digestion,\nmicrobial kinetics, gas yield, equipment sizing or operational safety advice.\nCaller values are abstract compatible units, not verified process measurements.\n')
Tests.test_disclaimer=disclaimer
