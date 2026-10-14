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
a=load('sea_contributions1625');b=load('extreme_counts1626')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand_scopes_mix(self):
        for rows in ([['B',-1,3],('A',1,2)],[('A',1,2),['B',-1,3]]):
            self.assertEqual(a.contributions(rows,1),{'contributions':(('A',F(1,2)),('B',F(-1,3))),'positive':F(1,2),'negative':F(-1,3),'total':F(1,6),'scenario':F(7,6),'scope':'caller additive contribution arithmetic only; no sea-level or coastal projections'})
        self.assertEqual(a.contributions([],0)['total'],0)
        for values in ([-1,0,2,3],(-1,0,2,3)):
            self.assertEqual(b.exceedance(values,2),{'indices':(3,),'count':1,'fraction':F(1,4),'excess_sum':1,'max_excess':1,'scope':'caller integer threshold counts only; no weather forecasts or hazard warnings'})
        self.assertEqual(b.exceedance([0],0)['count'],0);self.assertEqual(b.exceedance([1],0)['fraction'],1)
    def test_caps(self):
        a.contributions([(str(i),1000000,1000000) for i in range(64)],1000000);a.contributions([('a'*40,-1000000,1)],-1000000)
        b.exceedance([1000000]*90,-1000000);b.exceedance([-1000000],1000000)
    def test_precedence(self):
        with self.assertRaises(ValueError) as c:a.contributions([('a',0,1),('a',True,0)],0)
        self.assertEqual(str(c.exception),'labels must be unique')
        with self.assertRaises(ValueError) as c:b.exceedance([],True)
        self.assertEqual(str(c.exception),'threshold must be exactint-1000000..1000000')

def seeded(seed):
    def test(self):
        rng=random.Random(seed);rows=[('Ω'+str(i),rng.randrange(-1000000,1000001),rng.randrange(1,1000001)) for i in range(rng.randrange(40))];baseline=rng.randrange(-1000000,1000001);result=tuple(sorted((name,F(num,den)) for name,num,den in rows));positive=sum((F(num,den) for name,num,den in rows if num>0),F(0));negative=sum((F(num,den) for name,num,den in rows if num<0),F(0));out={'contributions':result,'positive':positive,'negative':negative,'total':positive+negative,'scenario':F(baseline)+positive+negative,'scope':a.SCOPE};self.assertEqual(a.contributions(rows,baseline),out);self.assertEqual(a.contributions(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1])),baseline),out)
        values=[rng.randrange(-1000000,1000001) for _ in range(rng.randrange(1,90))];threshold=rng.randrange(-1000000,1000001);diffs=[value-threshold for value in values];indices=tuple(i for i,diff in enumerate(diffs) if diff>0);out={'indices':indices,'count':len(indices),'fraction':F(len(indices),len(values)),'excess_sum':sum(diff for diff in diffs if diff>0),'max_excess':max(diffs+[0]),'scope':b.SCOPE};self.assertEqual(b.exceedance(values,threshold),out);self.assertEqual(b.exceedance(tuple(values),threshold),out)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))
def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for bad in (False,True,I(1),1.,None,'1',-1000001,1000001):cases.append((a.contributions,([],bad),'baseline must be exactint-1000000..1000000'))
for bad in ([('a',0,1)]*65,{},set(),iter([]),'x',L([]),T(())):cases.append((a.contributions,(bad,0),'rows must be exactlist/tuple atmost64'))
for bad in ([],[1,2],(1,2,3,4),'abc',L(['a',0,1]),T(('a',0,1))):cases.append((a.contributions,([bad],0),'row must be exactlist/tuple triple'))
for bad in ('','a'*41,'\n','\x00',S('a'),0,None):cases.append((a.contributions,([(bad,0,1)],0),'label must be exactstr printable Unicode length1..40'))
for bad in (False,True,I(1),1.,None,'1',-1000001,1000001):cases.append((a.contributions,([('a',bad,1)],0),'numerator must be exactint-1000000..1000000'))
for bad in (False,True,I(1),1.,None,'1',0,1000001):cases.append((a.contributions,([('a',0,bad)],0),'denominator must be exactint1..1000000'))
cases.append((a.contributions,([('a',0,1),('a',0,1)],0),'labels must be unique'))
for bad in (False,True,I(1),1.,None,'1',-1000001,1000001):cases.extend([(b.exceedance,([bad],0),'value must be exactint-1000000..1000000'),(b.exceedance,([0],bad),'threshold must be exactint-1000000..1000000')])
for bad in ([],[0]*91,{},set(),iter([]),'x',L([0]),T((0,))):cases.append((b.exceedance,(bad,0),'values must be exactlist/tuple length1..90'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))
def charset(char):
    def test(self):a.contributions([(char,0,1)],0)
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))

def exact_disclaimers(self):
    self.assertEqual(a.__doc__,'Sea Level Rise.\n\nPARTIAL: caller additive scenario contribution arithmetic only, not sea-level\nrise modeling,coastal inundation,climate projections or risk assessment.\nCaller values have no inferred units,physical components or scientific validity.\n')
    self.assertEqual(b.__doc__,'Extreme Weather.\n\nPARTIAL: caller integer observation threshold count arithmetic only, not extreme\nweather detection,return periods,climate attribution,forecasting or warnings.\nThreshold/observations supplied by caller,no hazard classifications inferred.\n')
Tests.test_exact_disclaimers=exact_disclaimers
