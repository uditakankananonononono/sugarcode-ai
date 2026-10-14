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
a=load('water_bounds1657');b=load('groundwater_balance1658')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand(self):
        for rows in ([['B',3,0,2],('A',0,1,1)],[('B',3,0,2),['A',0,1,1]]):
            self.assertEqual(a.compare(rows),{'comparisons':(('A','below',-1,1),('B','above',3,-1)),'outside':('A','B'),'within_count':0,'scope':'caller measurement-bound comparisons only; no water quality or safety claims'})
        self.assertEqual(a.compare([('a',0,0,0),('b',1,0,1)])['within_count'],2)
        for rows in ([['B',0,0,1],('A',2,1,1)],[('B',0,0,1),['A',2,1,1]]):
            self.assertEqual(b.balances(rows),{'balances':(('A',2,0),('B',-1,-1)),'negative':('B',),'total_final':1,'total_change':-1,'scope':'caller initial-recharge-withdrawal balances only; no groundwater management advice'})
        self.assertEqual(b.balances([('x',0,0,0)])['negative'],())
        self.assertEqual(b.balances([('x',1,0,0)])['negative'],())
    def test_caps(self):
        for fn in (a.compare,b.balances):fn([(str(i),1000000,1000000,1000000) for i in range(64)]);fn([('x'*40,0,0,0)])
    def test_precedence(self):
        for fn in (a.compare,b.balances):
            with self.assertRaises(ValueError) as c:fn([('x',1,1,1),('x',True,None,None)])
            self.assertEqual(str(c.exception),'labels must be unique')
            with self.assertRaises(ValueError) as c:fn([('',True,None,None)])
            self.assertEqual(str(c.exception),'label must be exactstr printable Unicode length1..40')

def seeded(seed):
    def test(self):
        r=random.Random(seed);rows=[]
        for i in range(r.randrange(1,40)):
            low=r.randrange(1000001);rows.append(('Ω'+str(i),r.randrange(1000001),low,r.randrange(low,1000001)))
        r.shuffle(rows);result=tuple((name,'within' if lo<=v<=hi else ('above' if hi<v else 'below'),v-lo,hi-v) for name,v,lo,hi in sorted(rows));out={'comparisons':result,'outside':tuple(name for name,v,lo,hi in sorted(rows) if not lo<=v<=hi),'within_count':len(rows)-sum(not lo<=v<=hi for name,v,lo,hi in rows),'scope':a.SCOPE}
        self.assertEqual(a.compare(rows),out);self.assertEqual(a.compare(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
        rows=[('É'+str(i),r.randrange(1000001),r.randrange(1000001),r.randrange(1000001)) for i in range(r.randrange(1,40))];r.shuffle(rows);result=tuple((name,q-(w-re),-(w-re)) for name,q,re,w in sorted(rows));out={'balances':result,'negative':tuple(name for name,q,re,w in sorted(rows) if w>q+re),'total_final':sum(q+re for name,q,re,w in rows)-sum(w for name,q,re,w in rows),'total_change':sum(re for name,q,re,w in rows)-sum(w for name,q,re,w in rows),'scope':b.SCOPE}
        self.assertEqual(b.balances(rows),out);self.assertEqual(b.balances(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))
def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for fn,quantity_message in ((a.compare,'values must be exactint0..1000000 with lower<=upper'),(b.balances,'quantities must be exactint0..1000000')):
    row=('a',1,1,1)
    for bad in ([],[row]*65,{},set(),iter([]),'x',None,L([row]),T((row,))):cases.append((fn,(bad,),'rows must be exactlist/tuple length1..64'))
    for bad in ([],row[:-1],row+(0,),'abcd',None,L(row),T(row)):cases.append((fn,([bad],),'row must be exactlist/tuple quadruple'))
    for bad in ('','x'*41,'\n','\x00',S('a'),0,None):cases.append((fn,([(bad,)+row[1:]],),'label must be exactstr printable Unicode length1..40'))
    for slot in range(1,len(row)):
        for bad in (True,False,I(0),1.,None,'1',-1,1000001):
            altered=list(row);altered[slot]=bad;cases.append((fn,([altered],),quantity_message))
    cases.append((fn,([row,row],),'labels must be unique'))
cases.append((a.compare,([('a',0,1,0)],),'values must be exactint0..1000000 with lower<=upper'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))
def charset(char):
    def test(self):a.compare([(char,0,0,0)]);b.balances([(char,0,0,0)])
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))

def disclaimer(self):
    self.assertEqual(a.__doc__,'Water Quality.\n\nPARTIAL: caller measurement/bound comparison only, not water quality testing,\npotability, contaminant identification, health advice or regulatory compliance.\nCaller bounds are arbitrary comparisons, not drinking-water standards.\n')
    self.assertEqual(b.__doc__,'Groundwater Management.\n\nPARTIAL: caller initial/recharge/withdrawal balance only, not groundwater\nmanagement, aquifer modeling, sustainable yield or ecological assessment.\nCaller compatible quantities are not verified hydrological measurements.\n')
Tests.test_disclaimer=disclaimer
