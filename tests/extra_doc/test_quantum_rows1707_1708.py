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
a=load('lifecycle_terms1707');b=load('carbon_factors1708')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand(self):
        for rows in ([['B',2,-1],('A',0,1),['B',1,1]],[('B',1,1),['A',0,1],('B',2,-1)]):
            self.assertEqual(a.terms(rows),{'terms':(('A',0,0),('B',3,-1)),'total':-1,'negative':('B',),'scope':'caller stage quantity-signed-factor ledger only; no life cycle assessment claims'})
        self.assertEqual(a.terms([('x',1,1)])['negative'],());self.assertEqual(a.terms([('x',0,-1)])['negative'],())
        for rows in ([['B',3,2,4],('A',0,1,1)],[('B',3,2,4),['A',0,1,1]]):
            self.assertEqual(b.footprint(rows),{'footprint':(('A',F(0)),('B',F(3,2))),'total':F(3,2),'positive':('B',),'scope':'caller activity-emission-factor arithmetic only; no verified carbon footprint claims'})
        self.assertEqual(b.footprint([('x',1,1,1)])['positive'],('x',));self.assertEqual(b.footprint([('x',1,0,1)])['positive'],())
    def test_caps(self):
        a.terms([('x'*40,1000000,-1000000)]*64);a.terms([('x',0,1000000)])
        b.footprint([(str(i),1000000,1000000,1000000) for i in range(64)]);b.footprint([('x'*40,0,0,1)])
    def test_precedence(self):
        with self.assertRaises(ValueError) as c:b.footprint([('x',1,1,1),('x',True,None,None)])
        self.assertEqual(str(c.exception),'labels must be unique')
def seeded(seed):
    def test(self):
        r=random.Random(seed);rows=[('Ω'+str(r.randrange(5)),r.randrange(1000001),r.randrange(-1000000,1000001)) for i in range(r.randrange(1,40))];result=[]
        for name in sorted(set(row[0] for row in rows)):
            sub=[(q,v) for label,q,v in rows if label==name];result.append((name,sum(q for q,v in sub),sum(q*v for q,v in sub)))
        out={'terms':tuple(result),'total':sum(q*v for name,q,v in rows),'negative':tuple(name for name,q,v in result if v<0),'scope':a.SCOPE}
        self.assertEqual(a.terms(rows),out);self.assertEqual(a.terms(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
        rows=[('É'+str(i),r.randrange(1000001),r.randrange(1000001),r.randrange(1,1000001)) for i in range(r.randrange(1,40))];r.shuffle(rows);result=tuple((name,F(q)*F(n,d)) for name,q,n,d in sorted(rows));out={'footprint':result,'total':sum(v for name,v in result),'positive':tuple(name for name,q,n,d in sorted(rows) if q and n),'scope':b.SCOPE}
        self.assertEqual(b.footprint(rows),out);self.assertEqual(b.footprint(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))
def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for fn,row,message in ((a.terms,('a',1,1),'quantity must be exactint0..1000000 and factor exactint-1000000..1000000'),(b.footprint,('a',1,1,1),'activity and numerator must be exactint0..1000000 and denominator exactint1..1000000')):
    for bad in ([],[row]*65,{},set(),iter([]),'x',None,L([row]),T((row,))):cases.append((fn,(bad,),'rows must be exactlist/tuple length1..64'))
    for bad in ([],row[:-1],row+(0,),'abcd',None,L(row),T(row)):cases.append((fn,([bad],),'row must be exactlist/tuple '+('triple' if fn==a.terms else 'quadruple')))
    for bad in ('','x'*41,'\n','\x00',S('a'),0,None):cases.append((fn,([(bad,)+row[1:]],),'label must be exactstr printable Unicode length1..40'))
    for slot in range(1,len(row)):
        for bad in (True,False,I(0),1.,None,'1',-1000001,1000001)+((-1,) if fn!=a.terms or slot!=2 else ()):
            altered=list(row);altered[slot]=bad;cases.append((fn,([altered],),message))
cases.append((b.footprint,([('a',0,0,0)],),'activity and numerator must be exactint0..1000000 and denominator exactint1..1000000'))
cases.append((b.footprint,([('a',0,0,1),('a',0,0,1)],),'labels must be unique'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))
def charset(char):
    def test(self):a.terms([(char,0,0)]);b.footprint([(char,0,0,1)])
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))

def disclaimer(self):
    self.assertEqual(a.__doc__,'Life Cycle Assessment.\n\nPARTIAL: caller stage quantity/signed-factor ledger only, not life cycle\nassessment, boundary validation, inventory verification or impact certification.\nCaller factors are abstract, not verified environmental characterization data.\n')
    self.assertEqual(b.__doc__,'Carbon Footprinting.\n\nPARTIAL: caller activity/emission-factor products only, not carbon footprinting,\nverified emissions, greenhouse-gas accounting or environmental certification.\nCaller factors are abstract, not verified inventory or emission-factor data.\n')
Tests.test_disclaimer=disclaimer
