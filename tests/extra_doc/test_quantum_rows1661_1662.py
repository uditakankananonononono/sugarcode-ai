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
from math import prod
a=load('air_weighted1661');b=load('pollution_stages1662')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand(self):
        for rows in ([['B',3,2],('A',0,1),['B',1,1]],[('B',1,1),['A',0,1],('B',3,2)]):
            self.assertEqual(a.means(rows),{'means':(('A',1,F(0)),('B',3,F(7,3))),'duration':4,'overall_mean':F(7,4),'scope':'caller observation-duration weighted means only; no air quality or health claims'})
        for rows in ([['B',1,2],('A',1,3)],[('B',1,2),['A',1,3]]):
            self.assertEqual(b.stages(rows,3),{'stages':(('B',F(3,2),F(3,2)),('A',F(1),F(1,2))),'final':F(1),'total_removed':F(2),'scope':'caller staged removal-fraction arithmetic only; no air pollution control claims'})
        self.assertEqual(b.stages([],1)['final'],1)
    def test_caps(self):
        a.means([('x'*40,1000000,1000000)]*64)
        b.stages([(str(i),1000000,1000000) for i in range(64)],1000000);b.stages([('x'*40,0,1)],0)
    def test_precedence(self):
        with self.assertRaises(ValueError) as c:b.stages([('x',1,1),('x',True,None)],0)
        self.assertEqual(str(c.exception),'labels must be unique')
        for fn,tail in ((a.means,()),(b.stages,(0,))):
            with self.assertRaises(ValueError) as c:fn([('',True,None)],*tail)
            self.assertEqual(str(c.exception),'label must be exactstr printable Unicode length1..40')

def seeded(seed):
    def test(self):
        r=random.Random(seed);rows=[('Ω'+str(r.randrange(5)),r.randrange(1000001),r.randrange(1,1000001)) for i in range(r.randrange(1,40))];result=[]
        for name in sorted(set(row[0] for row in rows)):
            sub=[(v,d) for label,v,d in rows if label==name];duration=sum(d for v,d in sub);result.append((name,duration,sum(F(v*d,duration) for v,d in sub)))
        duration=sum(d for label,v,d in rows);out={'means':tuple(result),'duration':duration,'overall_mean':sum(F(v*d,duration) for label,v,d in rows),'scope':a.SCOPE}
        self.assertEqual(a.means(rows),out);self.assertEqual(a.means(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
        rows=[]
        for i in range(r.randrange(40)):
            d=r.randrange(1,1000001);rows.append(('É'+str(i),r.randrange(d+1),d))
        initial=r.randrange(1000001);stocks=[F(initial)*F(prod(d-n for label,n,d in rows[:i+1]),prod(d for label,n,d in rows[:i+1])) for i in range(len(rows))];previous=[F(initial)]+stocks[:-1];result=tuple((row[0],stock,before-stock) for row,stock,before in zip(rows,stocks,previous));final=stocks[-1] if stocks else F(initial);out={'stages':result,'final':final,'total_removed':sum(before-stock for before,stock in zip(previous,stocks)),'scope':b.SCOPE}
        self.assertEqual(b.stages(rows,initial),out);self.assertEqual(b.stages(tuple(list(row) if i%2 else row for i,row in enumerate(rows)),initial),out)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))
def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for bad in (True,False,I(0),1.,None,'1',-1,1000001):cases.append((b.stages,([],bad),'initial must be exactint0..1000000'))
for fn,row,tail in ((a.means,('a',1,1),()),(b.stages,('a',1,1),(0,))):
    for bad in ([row]*65,{},set(),iter([]),'x',None,L([row]),T((row,)))+(([],) if fn==a.means else ()) :cases.append((fn,(bad,)+tail,'rows must be exactlist/tuple '+('length1..64' if fn==a.means else 'atmost64')))
    for bad in ([],row[:-1],row+(0,),'abc',None,L(row),T(row)):cases.append((fn,([bad],)+tail,'row must be exactlist/tuple triple'))
    for bad in ('','x'*41,'\n','\x00',S('a'),0,None):cases.append((fn,([(bad,)+row[1:]],)+tail,'label must be exactstr printable Unicode length1..40'))
    for slot in (1,2):
        for bad in (True,False,I(0),1.,None,'1',-1,1000001):
            altered=list(row);altered[slot]=bad;cases.append((fn,([altered],)+tail,'value must be exactint0..1000000 and duration exactint1..1000000' if fn==a.means else 'removal must be exactint0<=numerator<=denominator<=1000000 with denominator>0'))
cases.append((a.means,([('a',0,0)],),'value must be exactint0..1000000 and duration exactint1..1000000'))
for row in (('a',0,0),('a',2,1)):cases.append((b.stages,([row],0),'removal must be exactint0<=numerator<=denominator<=1000000 with denominator>0'))
cases.append((b.stages,([('a',0,1),('a',0,1)],0),'labels must be unique'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))
def charset(char):
    def test(self):a.means([(char,0,1)]);b.stages([(char,0,1)],0)
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))

def disclaimer(self):
    self.assertEqual(a.__doc__,'Air Quality.\n\nPARTIAL: caller observation/duration weighted mean only, not air quality\nmeasurement, pollutant identification, exposure assessment or health advice.\nCaller values have no inferred units, safety bands or regulatory thresholds.\n')
    self.assertEqual(b.__doc__,'Air Pollution Control.\n\nPARTIAL: caller staged removal-fraction arithmetic only, not pollution control,\nequipment performance, emissions compliance or health/environmental advice.\nCaller removal factors are not measured or certified control efficiencies.\n')
Tests.test_disclaimer=disclaimer
