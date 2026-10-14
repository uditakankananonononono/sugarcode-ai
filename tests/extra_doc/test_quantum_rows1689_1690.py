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
a=load('food_supply1689');b=load('food_transfers1690')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand(self):
        for rows in ([['B',1,2],('A',2,1)],[('B',1,2),['A',2,1]]):
            self.assertEqual(a.allocations(rows),{'allocations':(('A',1,0,1),('B',1,1,0)),'total_unmet':1,'total_unused':1,'unmet':('B',),'scope':'caller food supply-demand bucket arithmetic only; no food security claims'})
        self.assertEqual(a.allocations([('x',0,0)])['unmet'],())
        for rows in ([['B','A',1],('A','B',2),['A','A',3]],[('B','A',1),['A','B',2],('A','A',3)]):
            self.assertEqual(b.transfers(rows),{'transfers':(('A',4,5,-1),('B',2,1,1)),'total_transferred':6,'positive':('B',),'scope':'caller directed food-quantity transfer ledger only; no food systems claims'})
        self.assertEqual(b.transfers([('x','x',0)])['positive'],())
    def test_caps(self):
        a.allocations([(str(i),1000000,1000000) for i in range(64)]);a.allocations([('x'*40,0,0)]);b.transfers([('x'*40,'y'*40,1000000)]*64)
    def test_precedence(self):
        with self.assertRaises(ValueError) as c:b.transfers([('',None,True)])
        self.assertEqual(str(c.exception),'source must be exactstr printable Unicode length1..40')

def seeded(seed):
    def test(self):
        r=random.Random(seed);rows=[('Ω'+str(i),r.randrange(1000001),r.randrange(1000001)) for i in range(r.randrange(1,40))];r.shuffle(rows);result=tuple((name,d if supply>=d else supply,max(d-supply,0),max(supply-d,0)) for name,supply,d in sorted(rows));out={'allocations':result,'total_unmet':sum(max(d-supply,0) for name,supply,d in rows),'total_unused':sum(max(supply-d,0) for name,supply,d in rows),'unmet':tuple(name for name,supply,d in sorted(rows) if d>supply),'scope':a.SCOPE}
        self.assertEqual(a.allocations(rows),out);self.assertEqual(a.allocations(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
        rows=[('É'+str(r.randrange(5)),'É'+str(r.randrange(5)),r.randrange(1000001)) for i in range(r.randrange(1,40))];result=[]
        for name in sorted(set(s for s,t,q in rows)|set(t for s,t,q in rows)):
            incoming=sum(q for s,t,q in rows if t==name);outgoing=sum(q for s,t,q in rows if s==name);result.append((name,incoming,outgoing,incoming-outgoing))
        out={'transfers':tuple(result),'total_transferred':sum(q for s,t,q in rows),'positive':tuple(name for name,i,o,n in result if i>o),'scope':b.SCOPE}
        self.assertEqual(b.transfers(rows),out);self.assertEqual(b.transfers(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))
def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for fn,row in ((a.allocations,('a',1,1)),(b.transfers,('a','b',1))):
    for bad in ([],[row]*65,{},set(),iter([]),'x',None,L([row]),T((row,))):cases.append((fn,(bad,),'rows must be exactlist/tuple length1..64'))
    for bad in ([],row[:-1],row+(0,),'abc',None,L(row),T(row)):cases.append((fn,([bad],),'row must be exactlist/tuple triple'))
    for slot,name in ((0,'label'),) if fn==a.allocations else ((0,'source'),(1,'target')):
        for bad in ('','x'*41,'\n','\x00',S('a'),0,None):
            altered=list(row);altered[slot]=bad;cases.append((fn,([altered],),name+' must be exactstr printable Unicode length1..40'))
    for slot in (1,2) if fn==a.allocations else (2,):
        for bad in (True,False,I(0),1.,None,'1',-1,1000001):
            altered=list(row);altered[slot]=bad;cases.append((fn,([altered],),('quantities' if fn==a.allocations else 'quantity')+' must be exactint0..1000000'))
cases.append((a.allocations,([('a',0,0),('a',0,0)],),'labels must be unique'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))
def charset(char):
    def test(self):a.allocations([(char,0,0)]);b.transfers([(char,'x',0)]);b.transfers([('x',char,0)])
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))


def disclaimer(self):
    self.assertEqual(a.__doc__,'Food Security.\n\nPARTIAL: caller food supply/demand bucket arithmetic only, not food security,\nnutritional adequacy, access assessment, food safety or distribution advice.\nCaller quantities are abstract, not verified food availability or needs.\n')
    self.assertEqual(b.__doc__,'Food Systems.\n\nPARTIAL: caller directed food-quantity transfer ledger only, not food systems,\nsupply-chain validation, distribution optimization, nutrition or food safety.\nCaller endpoints are abstract buckets, not verified producers or consumers.\n')
Tests.test_disclaimer=disclaimer
