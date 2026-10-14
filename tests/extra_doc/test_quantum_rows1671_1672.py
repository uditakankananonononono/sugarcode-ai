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
a=load('bio_fraction1671');b=load('ecosystem_value1672')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand(self):
        for rows in ([['B',1,2],('A',1,3)],[('B',1,2),['A',1,3]]):
            self.assertEqual(a.remaining(rows,3),{'remaining':(('B',F(3,2),F(-3,2)),('A',F(1,2),F(-1))),'final':F(1,2),'total_change':F(-5,2),'scope':'caller staged remaining-fraction arithmetic only; no bioremediation claims'})
        self.assertEqual(a.remaining([],1)['final'],1)
        for rows in ([['B',3,2],('A',0,1),['B',1,4]],[('B',1,4),['A',0,1],('B',3,2)]):
            self.assertEqual(b.values(rows),{'values':(('A',0,0),('B',4,10)),'total_value':10,'zero_value':('A',),'scope':'caller area-unit-value ledger only; no ecosystem valuation claims'})
        self.assertEqual(b.values([('x',1,1)])['zero_value'],())
    def test_caps(self):
        a.remaining([(str(i),1000000,1000000) for i in range(64)],1000000);a.remaining([('x'*40,0,1)],0)
        b.values([('x'*40,1000000,1000000)]*64)
    def test_precedence(self):
        with self.assertRaises(ValueError) as c:a.remaining([('x',1,1),('x',True,None)],0)
        self.assertEqual(str(c.exception),'labels must be unique')
        for fn,tail in ((a.remaining,(0,)),(b.values,())):
            with self.assertRaises(ValueError) as c:fn([('',True,None)],*tail)
            self.assertEqual(str(c.exception),'label must be exactstr printable Unicode length1..40')

def seeded(seed):
    def test(self):
        r=random.Random(seed);rows=[]
        for i in range(r.randrange(40)):
            d=r.randrange(1,1000001);rows.append(('Ω'+str(i),r.randrange(d+1),d))
        initial=r.randrange(1000001);stocks=[F(initial)*F(prod(n for label,n,d in rows[:i+1]),prod(d for label,n,d in rows[:i+1])) for i in range(len(rows))];previous=[F(initial)]+stocks[:-1];result=tuple((row[0],stock,stock-before) for row,stock,before in zip(rows,stocks,previous));final=stocks[-1] if stocks else F(initial);out={'remaining':result,'final':final,'total_change':sum(stock-before for before,stock in zip(previous,stocks)),'scope':a.SCOPE}
        self.assertEqual(a.remaining(rows,initial),out);self.assertEqual(a.remaining(tuple(list(row) if i%2 else row for i,row in enumerate(rows)),initial),out)
        rows=[('É'+str(r.randrange(5)),r.randrange(1000001),r.randrange(1000001)) for i in range(r.randrange(1,40))];result=[]
        for name in sorted(set(row[0] for row in rows)):
            sub=[(q,c) for label,q,c in rows if label==name];result.append((name,sum(q for q,c in sub),sum(q*c for q,c in sub)))
        out={'values':tuple(result),'total_value':sum(q*c for name,q,c in rows),'zero_value':tuple(name for name,q,c in result if not c),'scope':b.SCOPE}
        self.assertEqual(b.values(rows),out);self.assertEqual(b.values(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))
def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for bad in (True,False,I(0),1.,None,'1',-1,1000001):cases.append((a.remaining,([],bad),'initial must be exactint0..1000000'))
for fn,row,tail in ((b.values,('a',1,1),()),(a.remaining,('a',1,1),(0,))):
    for bad in ([row]*65,{},set(),iter([]),'x',None,L([row]),T((row,)))+(([],) if fn==b.values else ()) :cases.append((fn,(bad,)+tail,'rows must be exactlist/tuple '+('length1..64' if fn==b.values else 'atmost64')))
    for bad in ([],row[:-1],row+(0,),'abc',None,L(row),T(row)):cases.append((fn,([bad],)+tail,'row must be exactlist/tuple triple'))
    for bad in ('','x'*41,'\n','\x00',S('a'),0,None):cases.append((fn,([(bad,)+row[1:]],)+tail,'label must be exactstr printable Unicode length1..40'))
    for slot in (1,2):
        for bad in (True,False,I(0),1.,None,'1',-1,1000001):
            altered=list(row);altered[slot]=bad;cases.append((fn,([altered],)+tail,'quantities must be exactint0..1000000' if fn==b.values else 'fraction must be exactint0<=numerator<=denominator<=1000000 with denominator>0'))
for row in (('a',0,0),('a',2,1)):cases.append((a.remaining,([row],0),'fraction must be exactint0<=numerator<=denominator<=1000000 with denominator>0'))
cases.append((a.remaining,([('a',0,1),('a',0,1)],0),'labels must be unique'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))
def charset(char):
    def test(self):b.values([(char,0,1)]);a.remaining([(char,0,1)],0)
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))


def disclaimer(self):
    self.assertEqual(a.__doc__,'Bioremediation.\n\nPARTIAL: caller staged remaining-fraction arithmetic only, not bioremediation,\nmicrobial kinetics, contaminant degradation, treatment effectiveness or safety.\nCaller fractions are abstract, not measured biological degradation rates.\n')
    self.assertEqual(b.__doc__,'Ecosystem Services.\n\nPARTIAL: caller area/unit-value ledger only, not ecosystem services,\neconomic valuation, ecological modeling or environmental benefit assessment.\nCaller compatible values are abstract, not verified market or ecosystem data.\n')
Tests.test_disclaimer=disclaimer
def zero_unit_value(self):
    self.assertEqual(b.values([('x',1,0)]),{'values':(('x',1,0),),'total_value':0,'zero_value':('x',),'scope':b.SCOPE})
Tests.test_zero_unit_value=zero_unit_value
