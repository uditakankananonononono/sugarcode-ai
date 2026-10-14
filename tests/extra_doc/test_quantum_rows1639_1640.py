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
a=load('soil_weighted1639');b=load('blue_area1640')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand_scope_mix(self):
        for rows in ([['B',2,3],('A',1,1)],[('A',1,1),['B',2,3]]):
            self.assertEqual(a.layers(rows),{'weighted':(('A',1),('B',6)),'weight_total':3,'weighted_total':7,'mean':F(7,3),'scope':'caller weighted layer-value arithmetic only; no soil carbon stock or sequestration claims'})
        for rows in ([['B',2,1,3],('A',1,1,2)],[('A',1,1,2),['B',2,1,3]]):
            self.assertEqual(b.products(rows),{'products':(('A',F(1,2)),('B',F(2,3))),'area_total':3,'product_total':F(7,6),'weighted_intensity':F(7,18),'scope':'caller area-intensity products only; no coastal carbon stocks or credit claims'})
        self.assertIsNone(b.products([('x',0,0,1)])['weighted_intensity'])
    def test_caps(self):
        a.layers([(str(i),1000000,1000000) for i in range(64)]);a.layers([('a'*40,1,0)])
        b.products([(str(i),1000000,1000000,1000000) for i in range(64)]);b.products([('a'*40,0,0,1)])
    def test_precedence(self):
        for fn,rows in ((a.layers,[('a',1,0),('a',True,None)]),(b.products,[('a',0,0,1),('a',True,None,0)])):
            with self.assertRaises(ValueError) as c:fn(rows)
            self.assertEqual(str(c.exception),'labels must be unique')

def seeded(seed):
    def test(self):
        rng=random.Random(seed);rows=[('Ω'+str(i),rng.randrange(1,1000001),rng.randrange(1000001)) for i in range(rng.randrange(1,40))];weights=sum(weight for _,weight,value in rows);mean=sum(F(weight,weights)*value for _,weight,value in rows);out={'weighted':tuple(sorted((name,weight*value) for name,weight,value in rows)),'weight_total':weights,'weighted_total':int(mean*weights),'mean':mean,'scope':a.SCOPE};self.assertEqual(a.layers(rows),out);self.assertEqual(a.layers(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
        rows=[('É'+str(i),rng.randrange(1000001),rng.randrange(1000001),rng.randrange(1,1000001)) for i in range(rng.randrange(1,40))];result=tuple(sorted((name,area*F(num,den)) for name,area,num,den in rows));area=sum(x[1] for x in rows);total=sum(x[1] for x in result);out={'products':result,'area_total':area,'product_total':total,'weighted_intensity':sum(F(a,area)*F(num,den) for name,a,num,den in rows) if area else None,'scope':b.SCOPE};self.assertEqual(b.products(rows),out);self.assertEqual(b.products(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))
def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for fn,row in ((a.layers,('a',1,0)),(b.products,('a',0,0,1))):
    for bad in ([],[row]*65,{},set(),iter([]),'x',L([row]),T((row,))):cases.append((fn,(bad,),'rows must be exactlist/tuple length1..64'))
    for bad in ([],list(row[:-1]),tuple(row)+(1,),'abcd',L(row),T(row)):cases.append((fn,([bad],),'row must be exactlist/tuple '+('triple' if fn==a.layers else 'four values')))
    for bad in ('','a'*41,'\n','\x00',S('a'),0,None):cases.append((fn,([(bad,)+row[1:]],),'label must be exactstr printable Unicode length1..40'))
    cases.append((fn,([row,row],),'labels must be unique'))
for slot,low in ((1,1),(2,0)):
    for bad in (False,True,I(1),1.,None,'1',low-1,1000001):
        row=['a',1,0];row[slot]=bad;cases.append((a.layers,([row],),('weight must be exactint1..1000000' if slot==1 else 'value must be exactint0..1000000')))
for slot in (1,2):
    for bad in (False,True,I(1),1.,None,'1',-1,1000001):
        row=['a',0,0,1];row[slot]=bad;cases.append((b.products,([row],),'area and numerator must be exactint0..1000000'))
for bad in (False,True,I(1),1.,None,'1',0,1000001):cases.append((b.products,([('a',0,0,bad)],),'denominator must be exactint1..1000000'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))
def charset(char):
    def test(self):a.layers([(char,1,0)]);b.products([(char,0,0,1)])
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))

def exact_disclaimers(self):
    self.assertEqual(a.__doc__,'Soil Carbon.\n\nPARTIAL: caller weighted layer-value arithmetic only, not soil carbon,\nstock measurement,bulk-density inference,sequestration or field validation.\nWeights/values caller abstractions,not measured soil depths or concentrations.\n')
    self.assertEqual(b.__doc__,'Blue Carbon.\n\nPARTIAL: caller area/intensity product arithmetic only, not blue carbon,\necosystem stocks,sequestration rates,restoration benefits or credit validation.\nArea/intensity caller declarations,not scientifically verified coastal data.\n')
Tests.test_exact_disclaimers=exact_disclaimers
