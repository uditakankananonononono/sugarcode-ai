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


import random,string
from fractions import Fraction as F
a=load('agro_categories1679');b=load('agriculture_inputs1680')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand(self):
        for rows in ([['B',1],('A',0),['B',1],('C',2)],[('B',1),['A',0],('B',1),['C',2]]):
            self.assertEqual(a.diversity(rows),{'counts':(('A',0),('B',2),('C',2)),'total':4,'richness':2,'diversity':F(1,2),'scope':'caller crop-category count diversity arithmetic only; no agroecology claims'})
        self.assertEqual(a.diversity([('x',0)])['diversity'],None);self.assertEqual(a.diversity([('x',1)])['richness'],1)
        for rows in ([['B',3,2],('A',0,0),['B',1,1]],[('B',1,1),['A',0,0],('B',3,2)]):
            self.assertEqual(b.remaining(rows),{'remaining':(('A',0,0,0,None),('B',4,3,1,F(3,4))),'total_residual':1,'removal_fraction':F(3,4),'scope':'caller baseline-reduced input ledger only; no sustainable agriculture claims'})
        self.assertEqual(b.remaining([('x',0,0)])['removal_fraction'],None)
    def test_caps(self):
        a.diversity([('x'*40,1000000)]*64);b.remaining([('x'*40,1000000,1000000)]*64)
def seeded(seed):
    def test(self):
        r=random.Random(seed);rows=[('Ω'+str(r.randrange(5)),r.randrange(1000001)) for i in range(r.randrange(1,40))];counts=tuple((name,sum(v for label,v in rows if label==name)) for name in sorted(set(label for label,v in rows)));total=sum(v for name,v in counts);cross=sum(x*y for i,(name,x) in enumerate(counts) for j,(other,y) in enumerate(counts) if i!=j);out={'counts':counts,'total':total,'richness':len([v for name,v in counts if v]),'diversity':F(cross,total*total) if total else None,'scope':a.SCOPE}
        self.assertEqual(a.diversity(rows),out);self.assertEqual(a.diversity(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
        rows=[]
        for i in range(r.randrange(1,40)):
            q=r.randrange(1000001);rows.append(('É'+str(r.randrange(5)),q,r.randrange(q+1)))
        result=[]
        for name in sorted(set(row[0] for row in rows)):
            sub=[(q,v) for label,q,v in rows if label==name];initial=sum(q for q,v in sub);removed=sum(v for q,v in sub);result.append((name,initial,removed,sum(q-v for q,v in sub),F(removed,initial) if initial else None))
        initial=sum(q for name,q,v in rows);removed=sum(v for name,q,v in rows);out={'remaining':tuple(result),'total_residual':sum(q-v for name,q,v in rows),'removal_fraction':F(removed,initial) if initial else None,'scope':b.SCOPE}
        self.assertEqual(b.remaining(rows),out);self.assertEqual(b.remaining(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))
def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for fn,row in ((a.diversity,('a',1)),(b.remaining,('a',1,1))):
    for bad in ([],[row]*65,{},set(),iter([]),'x',None,L([row]),T((row,))):cases.append((fn,(bad,),'rows must be exactlist/tuple length1..64'))
    for bad in ([],row[:-1],row+(0,),'abc',None,L(row),T(row)):cases.append((fn,([bad],),'row must be exactlist/tuple '+('pair' if fn==a.diversity else 'triple')))
    for bad in ('','x'*41,'\n','\x00',S('a'),0,None):cases.append((fn,([(bad,)+row[1:]],),'label must be exactstr printable Unicode length1..40'))
    for slot in range(1,len(row)):
        for bad in (True,False,I(0),1.,None,'1',-1,1000001):
            altered=list(row);altered[slot]=bad;cases.append((fn,([altered],),'count must be exactint0..1000000' if fn==a.diversity else 'masses must be exactint0<=removed<=initial<=1000000'))
cases.append((b.remaining,([('a',0,1)],),'masses must be exactint0<=removed<=initial<=1000000'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))
def charset(char):
    def test(self):a.diversity([(char,0)]);b.remaining([(char,0,0)])
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))

def disclaimer(self):
    self.assertEqual(a.__doc__,'Agroecology.\n\nPARTIAL: caller crop-category count diversity arithmetic only, not agroecology,\nfield surveying, ecosystem services, resilience or farming recommendations.\nCaller labels are abstract categories, not verified crop or ecological data.\n')
    self.assertEqual(b.__doc__,'Sustainable Agriculture.\n\nPARTIAL: caller baseline/reduced input quantity ledger only, not sustainable\nagriculture, farming recommendations, environmental benefit or certification.\nCaller compatible quantities are declarations, not verified agricultural data.\n')
Tests.test_disclaimer=disclaimer
