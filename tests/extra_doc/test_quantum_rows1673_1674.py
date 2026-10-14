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
a=load('biodiversity_counts1673');b=load('conservation_change1674')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand(self):
        for rows in ([['B',1],('A',0),['B',1],('C',2)],[('B',1),['A',0],('B',1),['C',2]]):
            self.assertEqual(a.diversity(rows),{'counts':(('A',0),('B',2),('C',2)),'total':4,'richness':2,'diversity':F(1,2),'scope':'caller category-count diversity arithmetic only; no biodiversity assessment claims'})
        self.assertEqual(a.diversity([('x',0)])['diversity'],None);self.assertEqual(a.diversity([('x',1)])['richness'],1)
        for rows in ([['B',2,1],('A',0,1)],[('B',2,1),['A',0,1]]):
            self.assertEqual(b.changes(rows),{'changes':(('A',1,None),('B',-1,F(1,2))),'declining':('B',),'total_change':0,'scope':'caller initial-final count arithmetic only; no conservation biology claims'})
        self.assertEqual(b.changes([('x',0,0)])['declining'],());self.assertEqual(b.changes([('x',1,2)])['declining'],())
    def test_caps(self):
        a.diversity([('x'*40,1000000)]*64)
        b.changes([(str(i),1000000,1000000) for i in range(64)]);b.changes([('x'*40,0,0)])
    def test_precedence(self):
        with self.assertRaises(ValueError) as c:b.changes([('x',1,1),('x',True,None)])
        self.assertEqual(str(c.exception),'labels must be unique')

def seeded(seed):
    def test(self):
        r=random.Random(seed);rows=[('Ω'+str(r.randrange(5)),r.randrange(1000001)) for i in range(r.randrange(1,40))];counts=tuple((name,sum(v for label,v in rows if label==name)) for name in sorted(set(label for label,v in rows)));total=sum(v for name,v in counts);cross=sum(x*y for i,(name,x) in enumerate(counts) for j,(other,y) in enumerate(counts) if i!=j);out={'counts':counts,'total':total,'richness':len([v for name,v in counts if v]),'diversity':F(cross,total*total) if total else None,'scope':a.SCOPE}
        self.assertEqual(a.diversity(rows),out);self.assertEqual(a.diversity(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
        rows=[('É'+str(i),r.randrange(1000001),r.randrange(1000001)) for i in range(r.randrange(1,40))];r.shuffle(rows);result=tuple((name,final-initial,F(final,initial) if initial else None) for name,initial,final in sorted(rows));out={'changes':result,'declining':tuple(name for name,i,f in sorted(rows) if i>f),'total_change':sum(f for name,i,f in rows)-sum(i for name,i,f in rows),'scope':b.SCOPE}
        self.assertEqual(b.changes(rows),out);self.assertEqual(b.changes(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))
def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for fn,row in ((a.diversity,('a',1)),(b.changes,('a',1,1))):
    for bad in ([],[row]*65,{},set(),iter([]),'x',None,L([row]),T((row,))):cases.append((fn,(bad,),'rows must be exactlist/tuple length1..64'))
    for bad in ([],row[:-1],row+(0,),'abc',None,L(row),T(row)):cases.append((fn,([bad],),'row must be exactlist/tuple '+('pair' if fn==a.diversity else 'triple')))
    for bad in ('','x'*41,'\n','\x00',S('a'),0,None):cases.append((fn,([(bad,)+row[1:]],),'label must be exactstr printable Unicode length1..40'))
    for slot in range(1,len(row)):
        for bad in (True,False,I(0),1.,None,'1',-1,1000001):
            altered=list(row);altered[slot]=bad;cases.append((fn,([altered],),('count' if fn==a.diversity else 'counts')+' must be exactint0..1000000'))
cases.append((b.changes,([('a',0,0),('a',0,0)],),'labels must be unique'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))
def charset(char):
    def test(self):a.diversity([(char,0)]);b.changes([(char,0,0)])
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))

def disclaimer(self):
    self.assertEqual(a.__doc__,'Biodiversity.\n\nPARTIAL: caller category-count diversity arithmetic only, not biodiversity\nsurveying, species identification, ecosystem health or conservation assessment.\nCaller categories and counts are not verified biological observations.\n')
    self.assertEqual(b.__doc__,'Conservation Biology.\n\nPARTIAL: caller category initial/final count arithmetic only, not conservation\nbiology, population viability, extinction risk or management recommendations.\nCaller counts are declarations, not verified wildlife population measurements.\n')
Tests.test_disclaimer=disclaimer
