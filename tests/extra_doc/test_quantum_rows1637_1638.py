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
a=load('reforest_cohorts1637');b=load('biochar_yield1638')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand_scope_mix(self):
        for rows in ([['B',0,0],('A',3,1)],[('A',3,1),['B',0,0]]):
            self.assertEqual(a.cohorts(rows),{'cohorts':(('A',2,F(1,3)),('B',0,None)),'initial_total':3,'surviving_total':1,'lost_total':2,'fraction':F(1,3),'scope':'caller cohort count ledger only; no ecological recovery or carbon claims'})
        self.assertIsNone(a.cohorts([('x',0,0)])['fraction'])
        for rows in ([['B',3,1],('A',1,1)],[('A',1,1),['B',3,1]]):
            self.assertEqual(b.yield_ratio(rows),{'yields':(('A',F(1),0),('B',F(1,3),2)),'feed_total':4,'product_total':2,'aggregate_ratio':F(1,2),'scope':'caller feedstock-product mass ratios only; no biochar stability or soil claims'})
    def test_caps(self):
        a.cohorts([(str(i),1000000,1000000) for i in range(64)]);a.cohorts([('a'*40,0,0)])
        b.yield_ratio([(str(i),1000000,1000000) for i in range(64)]);b.yield_ratio([('a'*40,1,0)])
    def test_precedence(self):
        for fn,rows in ((a.cohorts,[('a',0,0),('a',True,None)]),(b.yield_ratio,[('a',1,0),('a',True,None)])):
            with self.assertRaises(ValueError) as c:fn(rows)
            self.assertEqual(str(c.exception),'labels must be unique')

def seeded(seed):
    def test(self):
        rng=random.Random(seed);rows=[]
        for i in range(rng.randrange(1,40)):
            initial=rng.randrange(100);rows.append(('Ω'+str(i),initial,rng.randrange(initial+1)))
        result=tuple(sorted((name,initial-surviving,F(surviving,initial) if initial else None) for name,initial,surviving in rows));initial=sum(x[1] for x in rows);surviving=sum(x[2] for x in rows);out={'cohorts':result,'initial_total':initial,'surviving_total':surviving,'lost_total':sum(x[1] for x in result),'fraction':F(surviving,initial) if initial else None,'scope':a.SCOPE};self.assertEqual(a.cohorts(rows),out);self.assertEqual(a.cohorts(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
        rows=[]
        for i in range(rng.randrange(1,40)):
            feed=rng.randrange(1,1000001);rows.append(('É'+str(i),feed,rng.randrange(feed+1)))
        result=tuple(sorted((name,F(product,feed),feed-product) for name,feed,product in rows));feed=sum(x[1] for x in rows);product=sum(x[2] for x in rows);out={'yields':result,'feed_total':feed,'product_total':product,'aggregate_ratio':F(product,feed),'scope':b.SCOPE};self.assertEqual(b.yield_ratio(rows),out);self.assertEqual(b.yield_ratio(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))
def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for fn,row in ((a.cohorts,('a',0,0)),(b.yield_ratio,('a',1,0))):
    for bad in ([],[row]*65,{},set(),iter([]),'x',L([row]),T((row,))):cases.append((fn,(bad,),'rows must be exactlist/tuple length1..64'))
    for bad in ([],[1,2],(1,2,3,4),'abc',L(row),T(row)):cases.append((fn,([bad],),'row must be exactlist/tuple triple'))
    for bad in ('','a'*41,'\n','\x00',S('a'),0,None):cases.append((fn,([(bad,)+row[1:]],),'label must be exactstr printable Unicode length1..40'))
    cases.append((fn,([row,row],),'labels must be unique'))
    for slot in (1,2):
        for bad in (False,True,I(1),1.,None,'1',-1,1000001):
            changed=['a',1,0];changed[slot]=bad;cases.append((fn,([changed],),('counts must be exactint0<=surviving<=initial<=1000000' if fn==a.cohorts else 'masses must be exactint1<=feed<=1000000 and0<=product<=feed')))
    cases.append((fn,([('a',1,2)],),('counts must be exactint0<=surviving<=initial<=1000000' if fn==a.cohorts else 'masses must be exactint1<=feed<=1000000 and0<=product<=feed')))
cases.append((b.yield_ratio,([('a',0,0)],),'masses must be exactint1<=feed<=1000000 and0<=product<=feed'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))
def charset(char):
    def test(self):a.cohorts([(char,0,0)]);b.yield_ratio([(char,1,0)])
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))

def exact_disclaimers(self):
    self.assertEqual(a.__doc__,'Reforestation.\n\nPARTIAL: caller cohort surviving-count ledger only, not reforestation,\necological recovery,species suitability,carbon estimates or field validation.\nCounts caller-declared,not proof of survival or restoration success.\n')
    self.assertEqual(b.__doc__,'Biochar.\n\nPARTIAL: caller feedstock/product mass-ratio arithmetic only, not biochar,\npyrolysis chemistry,carbon stability,soil benefit or process safety.\nMasses caller declarations in matching units,not verified production data.\n')
Tests.test_exact_disclaimers=exact_disclaimers
