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
a=load('renewable_mix1641');b=load('efficiency_delta1642')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand_scope_mix(self):
        for rows in ([['B',2,False],('A',1,True)],[('A',1,True),['B',2,False]]):
            self.assertEqual(a.mix(rows),{'portfolio':(('A',1,True),('B',2,False)),'total':3,'flagged_total':1,'unflagged_total':2,'flagged_fraction':F(1,3),'scope':'caller generation-unit portfolio arithmetic only; no renewable output or emissions claims'})
        for rows in ([['B',1,2],('A',3,1)],[('A',3,1),['B',1,2]]):
            self.assertEqual(b.changes(rows),{'changes':(('A',2,F(2,3)),('B',-1,F(-1))),'before_total':4,'after_total':3,'difference':1,'aggregate_fraction':F(1,4),'scope':'caller before-after input arithmetic only; no verified energy savings or efficiency claims'})
        self.assertIsNone(a.mix([('x',0,False)])['flagged_fraction']);self.assertIsNone(b.changes([('x',0,1)])['aggregate_fraction'])
    def test_caps(self):
        a.mix([(str(i),1000000,True) for i in range(64)]);a.mix([('a'*40,0,False)])
        b.changes([(str(i),1000000,1000000) for i in range(64)]);b.changes([('a'*40,0,0)])
    def test_precedence(self):
        for fn,rows in ((a.mix,[('a',0,False),('a',True,None)]),(b.changes,[('a',0,0),('a',True,None)])):
            with self.assertRaises(ValueError) as c:fn(rows)
            self.assertEqual(str(c.exception),'labels must be unique')

def seeded(seed):
    def test(self):
        rng=random.Random(seed);rows=[('Ω'+str(i),rng.randrange(1000001),rng.choice((False,True))) for i in range(rng.randrange(1,40))];flagged=sum(amount for name,amount,flag in rows if flag is True);unflagged=sum(amount for name,amount,flag in rows if flag is False);total=flagged+unflagged;out={'portfolio':tuple(sorted(rows)),'total':total,'flagged_total':flagged,'unflagged_total':unflagged,'flagged_fraction':F(flagged,total) if total else None,'scope':a.SCOPE};self.assertEqual(a.mix(rows),out);self.assertEqual(a.mix(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
        rows=[('É'+str(i),rng.randrange(1000001),rng.randrange(1000001)) for i in range(rng.randrange(1,40))];result=tuple(sorted((name,before-after,1-F(after,before) if before else None) for name,before,after in rows));before=sum(x[1] for x in rows);after=sum(x[2] for x in rows);delta=sum(x[1] for x in result);out={'changes':result,'before_total':before,'after_total':after,'difference':delta,'aggregate_fraction':1-F(after,before) if before else None,'scope':b.SCOPE};self.assertEqual(b.changes(rows),out);self.assertEqual(b.changes(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))
def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for fn,row in ((a.mix,('a',0,False)),(b.changes,('a',0,0))):
    for bad in ([],[row]*65,{},set(),iter([]),'x',L([row]),T((row,))):cases.append((fn,(bad,),'rows must be exactlist/tuple length1..64'))
    for bad in ([],[1,2],(1,2,3,4),'abc',L(row),T(row)):cases.append((fn,([bad],),'row must be exactlist/tuple triple'))
    for bad in ('','a'*41,'\n','\x00',S('a'),0,None):cases.append((fn,([(bad,)+row[1:]],),'label must be exactstr printable Unicode length1..40'))
    cases.append((fn,([row,row],),'labels must be unique'))
for bad in (False,True,I(1),1.,None,'1',-1,1000001):cases.append((a.mix,([('a',bad,False)],),'amount must be exactint0..1000000'))
for bad in (0,1,I(1),1.,None,'True',[],{}):cases.append((a.mix,([('a',0,bad)],),'renewable flag must be exactbool'))
for slot in (1,2):
    for bad in (False,True,I(1),1.,None,'1',-1,1000001):
        row=['a',0,0];row[slot]=bad;cases.append((b.changes,([row],),'inputs must be exactint0..1000000'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))
def charset(char):
    def test(self):a.mix([(char,0,False)]);b.changes([(char,0,0)])
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))

def exact_disclaimers(self):
    self.assertEqual(a.__doc__,'Renewable Energy.\n\nPARTIAL: caller generation-unit portfolio arithmetic only, not renewable energy\nproduction,grid integration,emissions savings or validated resource forecasts.\nAmounts/source flags caller declarations,not measured or certified generation.\n')
    self.assertEqual(b.__doc__,'Energy Efficiency.\n\nPARTIAL: caller before/after input arithmetic only, not energy efficiency,\nnormalized performance,verified savings or financial/environmental impacts.\nValues caller declarations,no equal-service or comparable conditions validated.\n')
Tests.test_exact_disclaimers=exact_disclaimers
