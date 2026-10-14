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

import random,string
from fractions import Fraction as F
a=load('regenerative_changes1683');b=load('precision_targets1684')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand(self):
        for rows in ([['B',2,3],('A',0,0)],[('B',2,3),['A',0,0]]):
            self.assertEqual(a.changes(rows),{'changes':(('A',0,None),('B',1,F(1,2))),'increased':('B',),'total_change':1,'scope':'caller before-after indicator changes only; no regenerative agriculture claims'})
        self.assertEqual(a.changes([('x',1,0)])['increased'],())
        for rows in ([['B',2,1,2],('A',1,2,1)],[('B',2,1,2),['A',1,2,1]]):
            self.assertEqual(b.adjustments(rows),{'adjustments':(('A',2,1,-1),('B',2,4,2)),'total_adjustment':1,'positive':('B',),'scope':'caller area-current-target input arithmetic only; no precision agriculture advice'})
        self.assertEqual(b.adjustments([('x',1,1,2)])['positive'],('x',));self.assertEqual(b.adjustments([('x',1,1,1)])['positive'],())
    def test_caps(self):
        a.changes([(str(i),1000000,1000000) for i in range(64)]);a.changes([('x'*40,0,0)])
        b.adjustments([(str(i),1000000,1000000,1000000) for i in range(64)]);b.adjustments([('x'*40,0,0,0)])
    def test_precedence(self):
        for fn,row in ((a.changes,('x',1,1)),(b.adjustments,('x',1,1,1))):
            with self.assertRaises(ValueError) as c:fn([row,('x',)+(True,)*(len(row)-1)])
            self.assertEqual(str(c.exception),'labels must be unique')
            with self.assertRaises(ValueError) as c:fn([('',)+(True,)*(len(row)-1)])
            self.assertEqual(str(c.exception),'label must be exactstr printable Unicode length1..40')
def seeded(seed):
    def test(self):
        r=random.Random(seed);rows=[('Ω'+str(i),r.randrange(1000001),r.randrange(1000001)) for i in range(r.randrange(1,40))];r.shuffle(rows);result=tuple((name,y-x,F(y,x)-1 if x else None) for name,x,y in sorted(rows));out={'changes':result,'increased':tuple(name for name,x,y in sorted(rows) if y>x),'total_change':sum(y for name,x,y in rows)-sum(x for name,x,y in rows),'scope':a.SCOPE}
        self.assertEqual(a.changes(rows),out);self.assertEqual(a.changes(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
        rows=[('É'+str(i),r.randrange(1000001),r.randrange(1000001),r.randrange(1000001)) for i in range(r.randrange(1,40))];r.shuffle(rows);result=tuple((name,q*c,q*t,q*(t-c)) for name,q,c,t in sorted(rows));out={'adjustments':result,'total_adjustment':sum(q*(t-c) for name,q,c,t in rows),'positive':tuple(name for name,q,c,t in sorted(rows) if q and t>c),'scope':b.SCOPE}
        self.assertEqual(b.adjustments(rows),out);self.assertEqual(b.adjustments(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))
def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for fn,row in ((a.changes,('a',1,1)),(b.adjustments,('a',1,1,1))):
    for bad in ([],[row]*65,{},set(),iter([]),'x',None,L([row]),T((row,))):cases.append((fn,(bad,),'rows must be exactlist/tuple length1..64'))
    for bad in ([],row[:-1],row+(0,),'abcd',None,L(row),T(row)):cases.append((fn,([bad],),'row must be exactlist/tuple '+('triple' if fn==a.changes else 'quadruple')))
    for bad in ('','x'*41,'\n','\x00',S('a'),0,None):cases.append((fn,([(bad,)+row[1:]],),'label must be exactstr printable Unicode length1..40'))
    for slot in range(1,len(row)):
        for bad in (True,False,I(0),1.,None,'1',-1,1000001):
            altered=list(row);altered[slot]=bad;cases.append((fn,([altered],),('values' if fn==a.changes else 'quantities')+' must be exactint0..1000000'))
    cases.append((fn,([row,row],),'labels must be unique'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))
def charset(char):
    def test(self):a.changes([(char,0,0)]);b.adjustments([(char,0,0,0)])
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))

def disclaimer(self):
    self.assertEqual(a.__doc__,'Regenerative Agriculture.\n\nPARTIAL: caller before/after indicator changes only, not regenerative\nagriculture, soil recovery, carbon sequestration or farming recommendations.\nCaller indicators are abstract, not verified environmental measurements.\n')
    self.assertEqual(b.__doc__,'Precision Agriculture.\n\nPARTIAL: caller area/current/target input arithmetic only, not precision\nagriculture, sensor calibration, crop optimization or application advice.\nCaller rates are declarations, not agronomic targets or verified measurements.\n')
Tests.test_disclaimer=disclaimer
