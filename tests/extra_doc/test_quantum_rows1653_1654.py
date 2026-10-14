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
a=load('water_residual1653');b=load('wastewater_load1654')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand(self):
        for rows in ([['B',3,2,4],('A',0,1,1)],[('B',3,2,4),['A',0,1,1]]):
            self.assertEqual(a.residuals(rows),{'residuals':(('A',F(0),F(0)),('B',F(3,2),F(3,2))),'total_residual':F(3,2),'scope':'caller concentration-removal arithmetic only; no water safety claims'})
        for rows in ([['B',3,2],('A',0,1),['B',1,4]],[('B',1,4),['A',0,1],('B',3,2)]):
            self.assertEqual(b.loads(rows),{'loads':(('A',0,0),('B',4,10)),'total_load':10,'zero_flow':('A',),'scope':'caller flow-concentration load ledger only; no wastewater compliance claims'})
        self.assertEqual(b.loads([('x',1,0)])['zero_flow'],())
    def test_caps(self):
        a.residuals([(str(i),1000000,1000000,1000000) for i in range(64)]);a.residuals([('x'*40,0,0,1)])
        b.loads([('x'*40,1000000,1000000)]*64)
    def test_precedence(self):
        with self.assertRaises(ValueError) as c:a.residuals([('x',1,1,1),('x',True,None,None)])
        self.assertEqual(str(c.exception),'labels must be unique')
        for fn,row in ((a.residuals,('',True,None,None)),(b.loads,('',True,None))):
            with self.assertRaises(ValueError) as c:fn([row])
            self.assertEqual(str(c.exception),'label must be exactstr printable Unicode length1..40')

def seeded(seed):
    def test(self):
        r=random.Random(seed);rows=[]
        for i in range(r.randrange(1,40)):
            d=r.randrange(1,1000001);rows.append(('Ω'+str(i),r.randrange(1000001),r.randrange(d+1),d))
        r.shuffle(rows);result=tuple((name,F(q*(d-n),d),F(q)-F(q*(d-n),d)) for name,q,n,d in sorted(rows));out={'residuals':result,'total_residual':sum(x for name,x,y in result),'scope':a.SCOPE}
        self.assertEqual(a.residuals(rows),out);self.assertEqual(a.residuals(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
        rows=[('É'+str(r.randrange(5)),r.randrange(1000001),r.randrange(1000001)) for i in range(r.randrange(1,40))];result=[]
        for name in sorted(set(row[0] for row in rows)):
            sub=[(q,c) for label,q,c in rows if label==name];result.append((name,sum(q for q,c in sub),sum(q*c for q,c in sub)))
        out={'loads':tuple(result),'total_load':sum(q*c for name,q,c in rows),'zero_flow':tuple(name for name,q,c in result if not q),'scope':b.SCOPE}
        self.assertEqual(b.loads(rows),out);self.assertEqual(b.loads(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))
def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for fn,row,quantity_message in ((a.residuals,('a',1,1,1),'initial must be exactint0..1000000 and removal exactint0<=numerator<=denominator<=1000000 with denominator>0'),(b.loads,('a',1,1),'quantities must be exactint0..1000000')):
    for bad in ([],[row]*65,{},set(),iter([]),'x',None,L([row]),T((row,))):cases.append((fn,(bad,),'rows must be exactlist/tuple length1..64'))
    for bad in ([],row[:-1],row+(0,),'abcd',None,L(row),T(row)):cases.append((fn,([bad],),'row must be exactlist/tuple '+('quadruple' if fn==a.residuals else 'triple')))
    for bad in ('','x'*41,'\n','\x00',S('a'),0,None):cases.append((fn,([(bad,)+row[1:]],),'label must be exactstr printable Unicode length1..40'))
    for slot in range(1,len(row)):
        for bad in (True,False,I(0),1.,None,'1',-1,1000001):
            altered=list(row);altered[slot]=bad;cases.append((fn,([altered],),quantity_message))
for row in (('a',0,0,0),('a',0,2,1)):cases.append((a.residuals,([row],),'initial must be exactint0..1000000 and removal exactint0<=numerator<=denominator<=1000000 with denominator>0'))
cases.append((a.residuals,([('a',0,0,1),('a',0,0,1)],),'labels must be unique'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))
def charset(char):
    def test(self):a.residuals([(char,0,0,1)]);b.loads([(char,0,0)])
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))

def disclaimer(self):
    self.assertEqual(a.__doc__,'Water Treatment.\n\nPARTIAL: caller concentration/removal-fraction arithmetic only, not water\npurification, contaminant testing, potability or treatment recommendations.\nNo drinking-water limits, health conclusions or process efficiency are inferred.\n')
    self.assertEqual(b.__doc__,'Wastewater Treatment.\n\nPARTIAL: caller flow/concentration load ledger only, not wastewater treatment,\nplant design, pollutant testing, discharge compliance or environmental advice.\nNo unit conversion, removal efficiency or regulatory limit is inferred.\n')
Tests.test_disclaimer=disclaimer
