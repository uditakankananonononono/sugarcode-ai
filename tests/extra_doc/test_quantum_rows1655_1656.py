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
a=load('desal_partition1655');b=load('conservation_periods1656')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand(self):
        for rows in ([['B',3,2],('A',0,0)],[('B',3,2),['A',0,0]]):
            self.assertEqual(a.partition(rows),{'partition':(('A',0,None),('B',1,F(2,3))),'feed':3,'product':2,'remainder':1,'recovery_fraction':F(2,3),'scope':'caller feed-product partition arithmetic only; no desalination performance claims'})
        self.assertEqual(a.partition([('x',0,0)])['recovery_fraction'],None)
        self.assertEqual(a.partition([('a',1,1),('b',3,1)])['recovery_fraction'],F(1,2))
        for rows in ([['B',1,2,3],('A',2,1,1),['B',0,0,1]],[('B',0,0,1),['A',2,1,1],('B',1,2,3)]):
            self.assertEqual(b.savings(rows),{'savings':(('A',2,1,1),('B',3,6,-3)),'total_savings':-2,'negative':('B',),'scope':'caller baseline-current-period arithmetic only; no verified water conservation claims'})
        self.assertEqual(b.savings([('x',0,0,1)])['negative'],())
    def test_caps(self):
        a.partition([(str(i),1000000,1000000) for i in range(64)]);a.partition([('x'*40,0,0)])
        b.savings([('x'*40,1000000,1000000,1000000)]*64)
    def test_precedence(self):
        with self.assertRaises(ValueError) as c:a.partition([('x',1,1),('x',True,None)])
        self.assertEqual(str(c.exception),'labels must be unique')
        for fn,row in ((a.partition,('',True,None)),(b.savings,('',True,None,None))):
            with self.assertRaises(ValueError) as c:fn([row])
            self.assertEqual(str(c.exception),'label must be exactstr printable Unicode length1..40')

def seeded(seed):
    def test(self):
        r=random.Random(seed);rows=[]
        for i in range(r.randrange(1,40)):
            f=r.randrange(1000001);rows.append(('Ω'+str(i),f,r.randrange(f+1)))
        r.shuffle(rows);f=sum(q for label,q,p in rows);p=sum(v for label,q,v in rows);out={'partition':tuple((label,q-v,F(v,q) if q else None) for label,q,v in sorted(rows)),'feed':f,'product':p,'remainder':sum(q-v for label,q,v in rows),'recovery_fraction':F(p,f) if f else None,'scope':a.SCOPE}
        self.assertEqual(a.partition(rows),out);self.assertEqual(a.partition(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
        rows=[('É'+str(r.randrange(5)),r.randrange(1000001),r.randrange(1000001),r.randrange(1,1000001)) for i in range(r.randrange(1,40))];result=[]
        for name in sorted(set(row[0] for row in rows)):
            sub=[(q,c,p) for label,q,c,p in rows if label==name];base=sum(q*p for q,c,p in sub);current=sum(c*p for q,c,p in sub);result.append((name,base,current,sum((q-c)*p for q,c,p in sub)))
        out={'savings':tuple(result),'total_savings':sum((q-c)*p for label,q,c,p in rows),'negative':tuple(name for name,q,c,s in result if c>q),'scope':b.SCOPE}
        self.assertEqual(b.savings(rows),out);self.assertEqual(b.savings(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))
def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for fn,row,quantity_message in ((a.partition,('a',1,1),'quantities must be exactint0<=product<=feed<=1000000'),(b.savings,('a',1,1,1),'quantities must be exactint0..1000000 and periods exactint1..1000000')):
    for bad in ([],[row]*65,{},set(),iter([]),'x',None,L([row]),T((row,))):cases.append((fn,(bad,),'rows must be exactlist/tuple length1..64'))
    for bad in ([],row[:-1],row+(0,),'abcd',None,L(row),T(row)):cases.append((fn,([bad],),'row must be exactlist/tuple '+('triple' if fn==a.partition else 'quadruple')))
    for bad in ('','x'*41,'\n','\x00',S('a'),0,None):cases.append((fn,([(bad,)+row[1:]],),'label must be exactstr printable Unicode length1..40'))
    for slot in range(1,len(row)):
        for bad in (True,False,I(0),1.,None,'1',-1,1000001):
            altered=list(row);altered[slot]=bad;cases.append((fn,([altered],),quantity_message))
cases.append((a.partition,([('a',0,1)],),'quantities must be exactint0<=product<=feed<=1000000'))
cases.append((a.partition,([('a',0,0),('a',0,0)],),'labels must be unique'))
cases.append((b.savings,([('a',0,0,0)],),'quantities must be exactint0..1000000 and periods exactint1..1000000'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))
def charset(char):
    def test(self):a.partition([(char,0,0)]);b.savings([(char,0,0,1)])
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))

def disclaimer(self):
    self.assertEqual(a.__doc__,'Desalination.\n\nPARTIAL: caller feed/product quantity partition only, not desalination,\nmembrane performance, salt removal, drinking-water safety or plant design.\nCaller compatible units and product quantities are not verified process data.\n')
    self.assertEqual(b.__doc__,'Water Conservation.\n\nPARTIAL: caller baseline/current/period savings arithmetic only, not water\nconservation, verified consumption, environmental benefit or policy advice.\nQuantities and periods are caller abstractions, not measured water-use data.\n')
Tests.test_disclaimer=disclaimer
def unit_nonnegative(self):self.assertEqual(b.savings([('x',1,0,1)])['negative'],())
Tests.test_unit_nonnegative=unit_nonnegative
def unit_negative(self):self.assertEqual(b.savings([('x',0,1,1)])['negative'],('x',))
Tests.test_unit_negative=unit_negative
