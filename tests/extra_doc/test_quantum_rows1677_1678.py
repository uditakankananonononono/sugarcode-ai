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
a=load('fisheries_effort1677');b=load('forest_area1678')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand(self):
        for rows in ([['B',3,2],('A',0,1),['B',1,1]],[('B',1,1),['A',0,1],('B',3,2)]):
            self.assertEqual(a.effort(rows),{'effort':(('A',0,1,F(0)),('B',4,3,F(4,3))),'total_catch':4,'total_effort':4,'overall_ratio':F(1),'scope':'caller catch-effort ratio ledger only; no fisheries management advice'})
        self.assertEqual(a.effort([('x',0,1)])['overall_ratio'],0)
        for rows in ([['B',0,0,1],('A',2,1,1)],[('B',0,0,1),['A',2,1,1]]):
            self.assertEqual(b.areas(rows),{'areas':(('A',2,0),('B',-1,-1)),'negative':('B',),'total_final':1,'total_change':-1,'scope':'caller initial-planted-lost area ledger only; no forestry advice'})
        self.assertEqual(b.areas([('x',0,0,0)])['negative'],());self.assertEqual(b.areas([('x',1,0,0)])['negative'],())
    def test_caps(self):
        a.effort([('x'*40,1000000,1000000)]*64)
        b.areas([(str(i),1000000,1000000,1000000) for i in range(64)]);b.areas([('x'*40,0,0,0)])
    def test_precedence(self):
        with self.assertRaises(ValueError) as c:b.areas([('x',1,1,1),('x',True,None,None)])
        self.assertEqual(str(c.exception),'labels must be unique')

def seeded(seed):
    def test(self):
        r=random.Random(seed);rows=[]
        rows=[('Ω'+str(r.randrange(5)),r.randrange(1000001),r.randrange(1,1000001)) for i in range(r.randrange(1,40))];result=[]
        for name in sorted(set(row[0] for row in rows)):
            sub=[(q,v) for label,q,v in rows if label==name];catch=sum(q for q,v in sub);effort=sum(v for q,v in sub);result.append((name,catch,effort,F(catch,effort)))
        catch=sum(q for name,q,v in rows);effort=sum(v for name,q,v in rows);out={'effort':tuple(result),'total_catch':catch,'total_effort':effort,'overall_ratio':F(catch,effort),'scope':a.SCOPE}
        self.assertEqual(a.effort(rows),out);self.assertEqual(a.effort(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
        rows=[('É'+str(i),r.randrange(1000001),r.randrange(1000001),r.randrange(1000001)) for i in range(r.randrange(1,40))];r.shuffle(rows);result=tuple((name,q-(re-ad),-(re-ad)) for name,q,ad,re in sorted(rows));out={'areas':result,'negative':tuple(name for name,q,ad,re in sorted(rows) if re>q+ad),'total_final':sum(q+ad for name,q,ad,re in rows)-sum(re for name,q,ad,re in rows),'total_change':sum(ad for name,q,ad,re in rows)-sum(re for name,q,ad,re in rows),'scope':b.SCOPE}
        self.assertEqual(b.areas(rows),out);self.assertEqual(b.areas(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))
def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for fn,row,message in ((a.effort,('a',1,1),'catch must be exactint0..1000000 and effort exactint1..1000000'),(b.areas,('a',1,1,1),'areas must be exactint0..1000000')):
    for bad in ([],[row]*65,{},set(),iter([]),'x',None,L([row]),T((row,))):cases.append((fn,(bad,),'rows must be exactlist/tuple length1..64'))
    for bad in ([],row[:-1],row+(0,),'abcd',None,L(row),T(row)):cases.append((fn,([bad],),'row must be exactlist/tuple '+('triple' if fn==a.effort else 'quadruple')))
    for bad in ('','x'*41,'\n','\x00',S('a'),0,None):cases.append((fn,([(bad,)+row[1:]],),'label must be exactstr printable Unicode length1..40'))
    for slot in range(1,len(row)):
        for bad in (True,False,I(0),1.,None,'1',-1,1000001):
            altered=list(row);altered[slot]=bad;cases.append((fn,([altered],),message))
cases.append((a.effort,([('a',0,0)],),'catch must be exactint0..1000000 and effort exactint1..1000000'))
cases.append((b.areas,([('a',0,0,0),('a',0,0,0)],),'labels must be unique'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))
def charset(char):
    def test(self):a.effort([(char,0,1)]);b.areas([(char,0,0,0)])
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))


def disclaimer(self):
    self.assertEqual(a.__doc__,'Fisheries Management.\n\nPARTIAL: caller catch/effort ratio ledger only, not fisheries management,\nstock assessment, sustainable catch limits or ecological recommendations.\nCaller compatible quantities are not verified catches or fishing effort data.\n')
    self.assertEqual(b.__doc__,'Forestry.\n\nPARTIAL: caller initial/planted/lost area ledger only, not forestry,\nforest growth, habitat assessment, carbon accounting or harvest advice.\nCaller areas are abstract compatible units, not verified forest measurements.\n')
Tests.test_disclaimer=disclaimer
