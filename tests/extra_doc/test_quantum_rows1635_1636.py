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
a=load('ocean_limits1635');b=load('afforestation_grid1636')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand_scope_mix(self):
        for rows in ([['B',1,3],('A',2,6),['C',2,1]],[('C',2,1),['A',2,6],('B',1,3)]):
            self.assertEqual(a.limits(rows),{'limits':(('A',F(1,3)),('B',F(1,3)),('C',F(2))),'supported_units':F(1,3),'limiting':('A','B'),'scope':'caller abstract limiting-resource ratios only; no ocean productivity or uptake claims'})
        for rows in ([['B',0,3],('A',4,5)],[('A',4,5),['B',0,3]]):
            self.assertEqual(b.plots(rows,2),{'plots':(('A',1,2,2),('B',0,1,0)),'total_sites':2,'scope':'caller rectangular interior lattice counts only; no planting or carbon recommendations'})
        self.assertEqual(b.plots([('x',1,1)],1)['total_sites'],0)
    def test_caps(self):
        a.limits([(str(i),1000000,1000000) for i in range(64)]);a.limits([('a'*40,0,1)])
        b.plots([(str(i),1000000,1000000) for i in range(64)],1000000);b.plots([('a'*40,0,0)],1)
    def test_precedence(self):
        with self.assertRaises(ValueError) as c:a.limits([('a',0,1),('a',True,None)])
        self.assertEqual(str(c.exception),'labels must be unique')
        with self.assertRaises(ValueError) as c:b.plots([],True)
        self.assertEqual(str(c.exception),'spacing must be exactint1..1000000')

def seeded(seed):
    def test(self):
        rng=random.Random(seed);rows=[('Ω'+str(i),rng.randrange(1000001),rng.randrange(1,1000001)) for i in range(rng.randrange(1,40))];result=tuple(sorted((name,F(available,unit)) for name,available,unit in rows));minimum=min(value for name,value in result);out={'limits':result,'supported_units':minimum,'limiting':tuple(name for name,value in result if value==minimum),'scope':a.SCOPE};self.assertEqual(a.limits(rows),out);self.assertEqual(a.limits(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
        spacing=rng.randrange(1,30);rows=[('É'+str(i),rng.randrange(100),rng.randrange(100)) for i in range(rng.randrange(1,40))];result=[]
        for name,length,width in rows:
            xs=[x for x in range(1,length) if x%spacing==0];ys=[y for y in range(1,width) if y%spacing==0];result.append((name,len(xs),len(ys),len(list(itertools.product(xs,ys)))))
        out={'plots':tuple(sorted(result)),'total_sites':sum(x[3] for x in result),'scope':b.SCOPE};self.assertEqual(b.plots(rows,spacing),out);self.assertEqual(b.plots(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1])),spacing),out)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))
def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for fn,row,tail in ((a.limits,('a',0,1),()),(b.plots,('a',0,0),(1,))):
    for bad in ([],[row]*65,{},set(),iter([]),'x',L([row]),T((row,))):cases.append((fn,(bad,)+tail,'rows must be exactlist/tuple length1..64'))
    for bad in ([],[1,2],(1,2,3,4),'abc',L(row),T(row)):cases.append((fn,([bad],)+tail,'row must be exactlist/tuple triple'))
    for bad in ('','a'*41,'\n','\x00',S('a'),0,None):cases.append((fn,([(bad,)+row[1:]],)+tail,'label must be exactstr printable Unicode length1..40'))
    cases.append((fn,([row,row],)+tail,'labels must be unique'))
for slot,low in ((1,0),(2,1)):
    for bad in (False,True,I(1),1.,None,'1',low-1,1000001):
        row=['a',0,1];row[slot]=bad;cases.append((a.limits,([row],),('available must be exactint0..1000000' if slot==1 else 'per_unit must be exactint1..1000000')))
for slot in (1,2):
    for bad in (False,True,I(1),1.,None,'1',-1,1000001):
        row=['a',0,0];row[slot]=bad;cases.append((b.plots,([row],1),'dimensions must be exactint0..1000000'))
for bad in (False,True,I(1),1.,None,'1',0,1000001):cases.append((b.plots,([('a',0,0)],bad),'spacing must be exactint1..1000000'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))
def charset(char):
    def test(self):a.limits([(char,0,1)]);b.plots([(char,0,0)],1)
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))

def exact_disclaimers(self):
    self.assertEqual(a.__doc__,'Ocean Fertilization.\n\nPARTIAL: caller abstract resource/requirement limiting-ratio arithmetic only,\nnot ocean fertilization,biological productivity,carbon uptake or intervention\nsafety. Resources/requirements caller declarations,not validated ocean chemistry.\n')
    self.assertEqual(b.__doc__,'Afforestation.\n\nPARTIAL: caller rectangular interior lattice count arithmetic only, not\nafforestation,ecological suitability,planting recommendations or carbon estimates.\nPlot dimensions/spacing are caller abstractions,no terrain or species inferred.\n')
Tests.test_exact_disclaimers=exact_disclaimers
