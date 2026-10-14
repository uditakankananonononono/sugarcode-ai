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
a=load('soil_removed1667');b=load('land_exceedance1668')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand(self):
        for rows in ([['B',3,2],('A',0,0),['B',1,1]],[('B',1,1),['A',0,0],('B',3,2)]):
            self.assertEqual(a.remaining(rows),{'remaining':(('A',0,0,0,None),('B',4,3,1,F(3,4))),'total_residual':1,'removal_fraction':F(3,4),'scope':'caller initial-removed mass ledger only; no soil remediation claims'})
        self.assertEqual(a.remaining([('x',0,0)])['removal_fraction'],None)
        for rows in ([['B',3,2],('A',2,2),['C',0,1]],[('B',3,2),['A',2,2],('C',0,1)]):
            self.assertEqual(b.exceedances(rows),{'exceedances':(('A',F(1),0),('B',F(3,2),1),('C',F(0),0)),'above':('B',),'total_excess':1,'scope':'caller measurement-limit comparisons only; no contaminated land or safety claims'})
        self.assertEqual(b.exceedances([('x',2,1)])['above'],('x',))
    def test_caps(self):
        a.remaining([('x'*40,1000000,1000000)]*64)
        b.exceedances([(str(i),1000000,1000000) for i in range(64)]);b.exceedances([('x'*40,0,1)])
    def test_precedence(self):
        with self.assertRaises(ValueError) as c:b.exceedances([('x',1,1),('x',True,None)])
        self.assertEqual(str(c.exception),'labels must be unique')
        for fn in (a.remaining,b.exceedances):
            with self.assertRaises(ValueError) as c:fn([('',True,None)])
            self.assertEqual(str(c.exception),'label must be exactstr printable Unicode length1..40')

def seeded(seed):
    def test(self):
        r=random.Random(seed);rows=[]
        for i in range(r.randrange(1,40)):
            q=r.randrange(1000001);rows.append(('Ω'+str(r.randrange(5)),q,r.randrange(q+1)))
        result=[]
        for name in sorted(set(row[0] for row in rows)):
            sub=[(q,v) for label,q,v in rows if label==name];initial=sum(q for q,v in sub);removed=sum(v for q,v in sub);result.append((name,initial,removed,sum(q-v for q,v in sub),F(removed,initial) if initial else None))
        initial=sum(q for name,q,v in rows);removed=sum(v for name,q,v in rows);out={'remaining':tuple(result),'total_residual':sum(q-v for name,q,v in rows),'removal_fraction':F(removed,initial) if initial else None,'scope':a.SCOPE}
        self.assertEqual(a.remaining(rows),out);self.assertEqual(a.remaining(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
        rows=[('É'+str(i),r.randrange(1000001),r.randrange(1,1000001)) for i in range(r.randrange(1,40))];r.shuffle(rows);result=tuple((name,F(v,l),v-l if v>l else 0) for name,v,l in sorted(rows));out={'exceedances':result,'above':tuple(name for name,v,l in sorted(rows) if v>l),'total_excess':sum(v-l for name,v,l in rows if v>l),'scope':b.SCOPE}
        self.assertEqual(b.exceedances(rows),out);self.assertEqual(b.exceedances(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))
def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for fn,message in ((a.remaining,'masses must be exactint0<=removed<=initial<=1000000'),(b.exceedances,'value must be exactint0..1000000 and limit exactint1..1000000')):
    row=('a',1,1)
    for bad in ([],[row]*65,{},set(),iter([]),'x',None,L([row]),T((row,))):cases.append((fn,(bad,),'rows must be exactlist/tuple length1..64'))
    for bad in ([],row[:-1],row+(0,),'abc',None,L(row),T(row)):cases.append((fn,([bad],),'row must be exactlist/tuple triple'))
    for bad in ('','x'*41,'\n','\x00',S('a'),0,None):cases.append((fn,([(bad,)+row[1:]],),'label must be exactstr printable Unicode length1..40'))
    for slot in (1,2):
        for bad in (True,False,I(0),1.,None,'1',-1,1000001):
            altered=list(row);altered[slot]=bad;cases.append((fn,([altered],),message))
cases.append((a.remaining,([('a',0,1)],),'masses must be exactint0<=removed<=initial<=1000000'))
cases.append((b.exceedances,([('a',0,1),('a',0,1)],),'labels must be unique'))
cases.append((b.exceedances,([('a',0,0)],),'value must be exactint0..1000000 and limit exactint1..1000000'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))
def charset(char):
    def test(self):a.remaining([(char,0,0)]);b.exceedances([(char,0,1)])
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))

def disclaimer(self):
    self.assertEqual(a.__doc__,'Soil Remediation.\n\nPARTIAL: caller initial/removed mass ledger only, not soil remediation,\ncontaminant testing, treatment selection, land safety or regulatory compliance.\nCaller compatible masses are declarations, not verified cleanup outcomes.\n')
    self.assertEqual(b.__doc__,'Contaminated Land.\n\nPARTIAL: caller measurement/limit exceedance arithmetic only, not contaminated\nland assessment, contaminant testing, exposure modeling or regulatory advice.\nCaller limits are arbitrary comparisons, not legal or health standards.\n')
Tests.test_disclaimer=disclaimer
