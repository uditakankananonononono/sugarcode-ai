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
a=load('diet_factors1691');b=load('food_waste1692')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand(self):
        for rows in ([['B',3,2],('A',0,1),['B',1,4]],[('B',1,4),['A',0,1],('B',3,2)]):
            self.assertEqual(a.impacts(rows),{'impacts':(('A',0,0),('B',4,10)),'total_impact':10,'positive':('B',),'scope':'caller food-quantity-impact-factor products only; no sustainable diet advice'})
        self.assertEqual(a.impacts([('x',1,1)])['positive'],('x',));self.assertEqual(a.impacts([('x',1,0)])['positive'],())
        for rows in ([['B',3,2],('A',0,0),['B',1,1]],[('B',1,1),['A',0,0],('B',3,2)]):
            self.assertEqual(b.waste(rows),{'waste':(('A',0,0,0,None),('B',4,3,1,F(3,4))),'total_retained':1,'discarded_fraction':F(3,4),'scope':'caller prepared-discarded quantity ledger only; no verified food waste claims'})
        self.assertEqual(b.waste([('x',0,0)])['discarded_fraction'],None)
    def test_caps(self):
        a.impacts([('x'*40,1000000,1000000)]*64);b.waste([('x'*40,1000000,1000000)]*64)
def seeded(seed):
    def test(self):
        r=random.Random(seed);rows=[('Ω'+str(r.randrange(5)),r.randrange(1000001),r.randrange(1000001)) for i in range(r.randrange(1,40))];result=[]
        for name in sorted(set(row[0] for row in rows)):
            sub=[(q,v) for label,q,v in rows if label==name];result.append((name,sum(q for q,v in sub),sum(q*v for q,v in sub)))
        out={'impacts':tuple(result),'total_impact':sum(q*v for name,q,v in rows),'positive':tuple(name for name,q,v in result if v!=0),'scope':a.SCOPE}
        self.assertEqual(a.impacts(rows),out);self.assertEqual(a.impacts(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
        rows=[]
        for i in range(r.randrange(1,40)):
            q=r.randrange(1000001);rows.append(('É'+str(r.randrange(5)),q,r.randrange(q+1)))
        result=[]
        for name in sorted(set(row[0] for row in rows)):
            sub=[(q,v) for label,q,v in rows if label==name];initial=sum(q for q,v in sub);removed=sum(v for q,v in sub);result.append((name,initial,removed,sum(q-v for q,v in sub),F(removed,initial) if initial else None))
        initial=sum(q for name,q,v in rows);removed=sum(v for name,q,v in rows);out={'waste':tuple(result),'total_retained':sum(q-v for name,q,v in rows),'discarded_fraction':F(removed,initial) if initial else None,'scope':b.SCOPE}
        self.assertEqual(b.waste(rows),out);self.assertEqual(b.waste(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))
def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for fn,row in ((a.impacts,('a',1,1)),(b.waste,('a',1,1))):
    for bad in ([],[row]*65,{},set(),iter([]),'x',None,L([row]),T((row,))):cases.append((fn,(bad,),'rows must be exactlist/tuple length1..64'))
    for bad in ([],row[:-1],row+(0,),'abc',None,L(row),T(row)):cases.append((fn,([bad],),'row must be exactlist/tuple '+('triple')))
    for bad in ('','x'*41,'\n','\x00',S('a'),0,None):cases.append((fn,([(bad,)+row[1:]],),'label must be exactstr printable Unicode length1..40'))
    for slot in range(1,len(row)):
        for bad in (True,False,I(0),1.,None,'1',-1,1000001):
            altered=list(row);altered[slot]=bad;cases.append((fn,([altered],),'quantities must be exactint0..1000000' if fn==a.impacts else 'masses must be exactint0<=discarded<=prepared<=1000000'))
cases.append((b.waste,([('a',0,1)],),'masses must be exactint0<=discarded<=prepared<=1000000'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))
def charset(char):
    def test(self):a.impacts([(char,0,0)]);b.waste([(char,0,0)])
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))



def disclaimer(self):
    self.assertEqual(a.__doc__,'Sustainable Diets.\n\nPARTIAL: caller food-quantity/impact-factor products only, not sustainable\ndiets, nutrition, health, lifecycle assessment or dietary recommendations.\nCaller factors are abstract, not verified food or environmental impact data.\n')
    self.assertEqual(b.__doc__,'Food Waste.\n\nPARTIAL: caller prepared/discarded quantity ledger only, not food waste\nmeasurement, food safety, prevention effectiveness or environmental benefit.\nCaller compatible quantities are declarations, not verified food waste data.\n')
Tests.test_disclaimer=disclaimer
