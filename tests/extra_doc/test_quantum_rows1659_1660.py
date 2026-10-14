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
a=load('watershed_weights1659');b=load('water_allocations1660')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand(self):
        for rows in ([['B',3,2,4],('A',0,1,1)],[('B',3,2,4),['A',0,1,1]]):
            self.assertEqual(a.weights(rows),{'weighted_areas':(('A',F(0)),('B',F(3,2))),'area':3,'weighted_total':F(3,2),'weighted_average':F(1,2),'scope':'caller area-weight ledger only; no watershed or runoff prediction'})
        self.assertEqual(a.weights([('x',0,0,1)])['weighted_average'],None)
        self.assertEqual(a.weights([('a',1,1,1),('b',3,1,3)])['weighted_average'],F(1,2))
        for rows in ([['B',1,2],('A',2,1)],[('B',1,2),['A',2,1]]):
            self.assertEqual(b.allocations(rows),{'allocations':(('A',1,0,1),('B',1,1,0)),'total_unmet':1,'total_unused':1,'unmet':('B',),'scope':'caller supply-demand allocation ledger only; no water resources planning advice'})
        self.assertEqual(b.allocations([('x',0,0)])['unmet'],())
    def test_caps(self):
        a.weights([(str(i),1000000,1000000,1000000) for i in range(64)]);a.weights([('x'*40,0,0,1)])
        b.allocations([(str(i),1000000,1000000) for i in range(64)]);b.allocations([('x'*40,0,0)])
    def test_precedence(self):
        for fn,row in ((a.weights,('x',1,1,1)),(b.allocations,('x',1,1))):
            with self.assertRaises(ValueError) as c:fn([row,('x',)+(True,)*(len(row)-1)])
            self.assertEqual(str(c.exception),'labels must be unique')
            with self.assertRaises(ValueError) as c:fn([('',)+(True,)*(len(row)-1)])
            self.assertEqual(str(c.exception),'label must be exactstr printable Unicode length1..40')

def seeded(seed):
    def test(self):
        r=random.Random(seed);rows=[]
        for i in range(r.randrange(1,40)):
            d=r.randrange(1,1000001);rows.append(('Ω'+str(i),r.randrange(1000001),r.randrange(d+1),d))
        r.shuffle(rows);result=tuple((name,F(q)*F(n,d)) for name,q,n,d in sorted(rows));area=sum(q for name,q,n,d in rows);total=sum(v for name,v in result);out={'weighted_areas':result,'area':area,'weighted_total':total,'weighted_average':total/F(area) if area else None,'scope':a.SCOPE}
        self.assertEqual(a.weights(rows),out);self.assertEqual(a.weights(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
        rows=[('É'+str(i),r.randrange(1000001),r.randrange(1000001)) for i in range(r.randrange(1,40))];r.shuffle(rows);result=tuple((name,d if s>=d else s,max(d-s,0),max(s-d,0)) for name,s,d in sorted(rows));out={'allocations':result,'total_unmet':sum(max(d-s,0) for name,s,d in rows),'total_unused':sum(max(s-d,0) for name,s,d in rows),'unmet':tuple(name for name,s,d in sorted(rows) if d>s),'scope':b.SCOPE}
        self.assertEqual(b.allocations(rows),out);self.assertEqual(b.allocations(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))
def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for fn,row,quantity_message in ((a.weights,('a',1,1,1),'area must be exactint0..1000000 and weight exactint0<=numerator<=denominator<=1000000 with denominator>0'),(b.allocations,('a',1,1),'quantities must be exactint0..1000000')):
    for bad in ([],[row]*65,{},set(),iter([]),'x',None,L([row]),T((row,))):cases.append((fn,(bad,),'rows must be exactlist/tuple length1..64'))
    for bad in ([],row[:-1],row+(0,),'abcd',None,L(row),T(row)):cases.append((fn,([bad],),'row must be exactlist/tuple '+('quadruple' if fn==a.weights else 'triple')))
    for bad in ('','x'*41,'\n','\x00',S('a'),0,None):cases.append((fn,([(bad,)+row[1:]],),'label must be exactstr printable Unicode length1..40'))
    for slot in range(1,len(row)):
        for bad in (True,False,I(0),1.,None,'1',-1,1000001):
            altered=list(row);altered[slot]=bad;cases.append((fn,([altered],),quantity_message))
    cases.append((fn,([row,row],),'labels must be unique'))
for row in (('a',0,0,0),('a',0,2,1)):cases.append((a.weights,([row],),'area must be exactint0..1000000 and weight exactint0<=numerator<=denominator<=1000000 with denominator>0'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))
def charset(char):
    def test(self):a.weights([(char,0,0,1)]);b.allocations([(char,0,0)])
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))

def disclaimer(self):
    self.assertEqual(a.__doc__,'Watershed Management.\n\nPARTIAL: caller area/weight ledger only, not watershed management, runoff\nprediction, catchment modeling, erosion assessment or hydrological advice.\nCaller weights and compatible areas are abstract, not calibrated coefficients.\n')
    self.assertEqual(b.__doc__,'Integrated Water Resources.\n\nPARTIAL: caller supply/demand allocation ledger only, not integrated water\nresources planning, optimization, water rights or environmental assessment.\nCaller declarations are not verified availability or authorized allocations.\n')
Tests.test_disclaimer=disclaimer
