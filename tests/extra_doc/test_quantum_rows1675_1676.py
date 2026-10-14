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
a=load('protected_fraction1675');b=load('wildlife_balance1676')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand(self):
        for rows in ([['B',3,2],('A',0,0),['B',1,1]],[('B',1,1),['A',0,0],('B',3,2)]):
            self.assertEqual(a.coverage(rows),{'coverage':(('A',0,0,0,None),('B',4,3,1,F(3,4))),'unprotected':1,'protected_fraction':F(3,4),'scope':'caller total-protected area arithmetic only; no protected-area status claims'})
        self.assertEqual(a.coverage([('x',0,0)])['protected_fraction'],None)
        for rows in ([['B',0,0,1],('A',2,1,1)],[('B',0,0,1),['A',2,1,1]]):
            self.assertEqual(b.counts(rows),{'counts':(('A',2,0),('B',-1,-1)),'negative':('B',),'total_final':1,'total_change':-1,'scope':'caller initial-additions-removals count ledger only; no wildlife management advice'})
        self.assertEqual(b.counts([('x',0,0,0)])['negative'],());self.assertEqual(b.counts([('x',1,0,0)])['negative'],())
    def test_caps(self):
        a.coverage([('x'*40,1000000,1000000)]*64)
        b.counts([(str(i),1000000,1000000,1000000) for i in range(64)]);b.counts([('x'*40,0,0,0)])
    def test_precedence(self):
        with self.assertRaises(ValueError) as c:b.counts([('x',1,1,1),('x',True,None,None)])
        self.assertEqual(str(c.exception),'labels must be unique')

def seeded(seed):
    def test(self):
        r=random.Random(seed);rows=[]
        for i in range(r.randrange(1,40)):
            q=r.randrange(1000001);rows.append(('Ω'+str(r.randrange(5)),q,r.randrange(q+1)))
        result=[]
        for name in sorted(set(row[0] for row in rows)):
            sub=[(q,v) for label,q,v in rows if label==name];total=sum(q for q,v in sub);protected=sum(v for q,v in sub);result.append((name,total,protected,sum(q-v for q,v in sub),F(protected,total) if total else None))
        total=sum(q for name,q,v in rows);protected=sum(v for name,q,v in rows);out={'coverage':tuple(result),'unprotected':sum(q-v for name,q,v in rows),'protected_fraction':F(protected,total) if total else None,'scope':a.SCOPE}
        self.assertEqual(a.coverage(rows),out);self.assertEqual(a.coverage(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
        rows=[('É'+str(i),r.randrange(1000001),r.randrange(1000001),r.randrange(1000001)) for i in range(r.randrange(1,40))];r.shuffle(rows);result=tuple((name,q-(re-ad),-(re-ad)) for name,q,ad,re in sorted(rows));out={'counts':result,'negative':tuple(name for name,q,ad,re in sorted(rows) if re>q+ad),'total_final':sum(q+ad for name,q,ad,re in rows)-sum(re for name,q,ad,re in rows),'total_change':sum(ad for name,q,ad,re in rows)-sum(re for name,q,ad,re in rows),'scope':b.SCOPE}
        self.assertEqual(b.counts(rows),out);self.assertEqual(b.counts(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))
def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for fn,row,message in ((a.coverage,('a',1,1),'areas must be exactint0<=protected<=total<=1000000'),(b.counts,('a',1,1,1),'counts must be exactint0..1000000')):
    for bad in ([],[row]*65,{},set(),iter([]),'x',None,L([row]),T((row,))):cases.append((fn,(bad,),'rows must be exactlist/tuple length1..64'))
    for bad in ([],row[:-1],row+(0,),'abcd',None,L(row),T(row)):cases.append((fn,([bad],),'row must be exactlist/tuple '+('triple' if fn==a.coverage else 'quadruple')))
    for bad in ('','x'*41,'\n','\x00',S('a'),0,None):cases.append((fn,([(bad,)+row[1:]],),'label must be exactstr printable Unicode length1..40'))
    for slot in range(1,len(row)):
        for bad in (True,False,I(0),1.,None,'1',-1,1000001):
            altered=list(row);altered[slot]=bad;cases.append((fn,([altered],),message))
cases.append((a.coverage,([('a',0,1)],),'areas must be exactint0<=protected<=total<=1000000'))
cases.append((b.counts,([('a',0,0,0),('a',0,0,0)],),'labels must be unique'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))
def charset(char):
    def test(self):a.coverage([(char,0,0)]);b.counts([(char,0,0,0)])
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))

def disclaimer(self):
    self.assertEqual(a.__doc__,'Protected Areas.\n\nPARTIAL: caller total/protected area arithmetic only, not protected-area\nmapping, legal designation, conservation effectiveness or management advice.\nCaller areas are declarations, not verified boundaries or legal protections.\n')
    self.assertEqual(b.__doc__,'Wildlife Management.\n\nPARTIAL: caller initial/additions/removals count ledger only, not wildlife\nmanagement, population forecasting, ecological assessment or harvest advice.\nCaller counts are abstract, not verified animal population measurements.\n')
Tests.test_disclaimer=disclaimer
