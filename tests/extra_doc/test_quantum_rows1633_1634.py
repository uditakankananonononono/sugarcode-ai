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
a=load('geo_sensitivity1633');b=load('solar_balance1634')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand_scope_mix(self):
        for rows in ([['B',-2,1],('A',3,1)],[('A',3,1),['B',-2,1]]):
            self.assertEqual(a.slopes(rows),{'slopes':(('A',F(1,3)),('B',F(-1,2))),'minimum':F(-1,2),'maximum':F(1,3),'scope':'caller perturbation sensitivity arithmetic only; no geoengineering effects or safety'})
        for rows in ([['B',2,1,2],('A',1,1,3)],[('A',1,1,3),['B',2,1,2]]):
            self.assertEqual(b.balance(rows),{'balance':(('A',F(1,3),F(2,3)),('B',F(1),F(1))),'incoming_total':3,'reflected_total':F(4,3),'remainder_total':F(5,3),'scope':'caller incoming/reflected arithmetic only; no radiative forcing or intervention claims'})
        self.assertEqual(b.balance([('x',0,0,1)])['reflected_total'],0)
    def test_caps(self):
        a.slopes([(str(i),1000000,-1000000) for i in range(64)]);a.slopes([('a'*40,-1000000,1000000)])
        b.balance([(str(i),1000000,1000000,1000000) for i in range(64)]);b.balance([('a'*40,0,0,1)])
    def test_precedence(self):
        for fn,rows in ((a.slopes,[('a',1,0),('a',True,None)]),(b.balance,[('a',0,0,1),('a',True,None,0)])):
            with self.assertRaises(ValueError) as c:fn(rows)
            self.assertEqual(str(c.exception),'labels must be unique')

def seeded(seed):
    def test(self):
        rng=random.Random(seed);rows=[]
        for i in range(rng.randrange(1,40)):
            dx=rng.choice((-1,1))*rng.randrange(1,1000001);rows.append(('Ω'+str(i),dx,rng.randrange(-1000000,1000001)))
        result=tuple(sorted((name,F(dy,abs(dx))*(1 if dx>0 else -1)) for name,dx,dy in rows));out={'slopes':result,'minimum':min(x[1] for x in result),'maximum':max(x[1] for x in result),'scope':a.SCOPE};self.assertEqual(a.slopes(rows),out);self.assertEqual(a.slopes(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
        rows=[]
        for i in range(rng.randrange(1,40)):
            den=rng.randrange(1,1000001);rows.append(('É'+str(i),rng.randrange(1000001),rng.randrange(den+1),den))
        result=tuple(sorted((name,incoming*F(num,den),incoming*F(den-num,den)) for name,incoming,num,den in rows));total=sum(x[1] for x in rows);reflected=sum(x[1] for x in result);out={'balance':result,'incoming_total':total,'reflected_total':reflected,'remainder_total':F(total)-reflected,'scope':b.SCOPE};self.assertEqual(b.balance(rows),out);self.assertEqual(b.balance(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))
def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for fn,row in ((a.slopes,('a',1,0)),(b.balance,('a',0,0,1))):
    for bad in ([],[row]*65,{},set(),iter([]),'x',L([row]),T((row,))):cases.append((fn,(bad,),'rows must be exactlist/tuple length1..64'))
    for bad in ([],list(row[:-1]),tuple(row)+(1,),'abcd',L(row),T(row)):cases.append((fn,([bad],),'row must be exactlist/tuple '+('triple' if fn==a.slopes else 'four values')))
    for bad in ('','a'*41,'\n','\x00',S('a'),0,None):cases.append((fn,([(bad,)+row[1:]],),'label must be exactstr printable Unicode length1..40'))
    cases.append((fn,([row,row],),'labels must be unique'))
for slot in (1,2):
    for bad in (False,True,I(1),1.,None,'1',-1000001,1000001):
        row=['a',1,0];row[slot]=bad;cases.append((a.slopes,([row],),'deltas must be exactint-1000000..1000000'))
cases.append((a.slopes,([('a',0,1)],),'input delta must be nonzero'))
for bad in (False,True,I(1),1.,None,'1',-1,1000001):cases.append((b.balance,([('a',bad,0,1)],),'incoming must be exactint0..1000000'))
for slot in (2,3):
    for bad in (False,True,I(1),1.,None,'1',-1,1000001):
        row=['a',0,0,1];row[slot]=bad;cases.append((b.balance,([row],),'fraction components must be exactint0<=num<=den<=1000000 and den>0'))
for row in (('a',0,0,0),('a',0,2,1)):cases.append((b.balance,([row],),'fraction components must be exactint0<=num<=den<=1000000 and den>0'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))
def charset(char):
    def test(self):a.slopes([(char,1,0)]);b.balance([(char,0,0,1)])
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))

def exact_disclaimers(self):
    self.assertEqual(a.__doc__,'Geoengineering.\n\nPARTIAL: caller finite perturbation sensitivity arithmetic only, not\ngeoengineering,intervention modeling,climate effects,feasibility or safety.\nPerturbations/responses supplied by caller,not validated physical experiments.\n')
    self.assertEqual(b.__doc__,'Solar Radiation Management.\n\nPARTIAL: caller incoming/reflected arithmetic only, not solar radiation\nmanagement,radiative forcing,climate response,interventions or safety.\nInputs are caller abstractions,no physical calibration or planetary assumptions.\n')
Tests.test_exact_disclaimers=exact_disclaimers
