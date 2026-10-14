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
a=load('hydro_solution1687');b=load('urban_yield1688')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand(self):
        for rows in ([['B',3,2],('A',0,0),['B',1,1]],[('B',1,1),['A',0,0],('B',3,2)]):
            self.assertEqual(a.fractions(rows),{'fractions':(('A',0,0,0,None),('B',4,3,1,F(3,4))),'total_carrier':1,'solute_fraction':F(3,4),'scope':'caller solution-solute mass fraction ledger only; no hydroponics advice'})
        self.assertEqual(a.fractions([('x',0,0)])['solute_fraction'],None);self.assertEqual(a.fractions([('x',1,0)])['solute_fraction'],0)
        for rows in ([['B',3,2],('A',0,1),['B',1,1]],[('B',1,1),['A',0,1],('B',3,2)]):
            self.assertEqual(b.area(rows),{'area':(('A',0,1,F(0)),('B',4,3,F(4,3))),'total_harvest':4,'total_area':4,'overall_ratio':F(1),'scope':'caller harvest-area ratio ledger only; no urban agriculture claims'})
    def test_caps(self):
        a.fractions([('x'*40,1000000,1000000)]*64);b.area([('x'*40,1000000,1000000)]*64)
def seeded(seed):
    def test(self):
        r=random.Random(seed);rows=[]
        for i in range(r.randrange(1,40)):
            q=r.randrange(1000001);rows.append(('Ω'+str(r.randrange(5)),q,r.randrange(q+1)))
        result=[]
        for name in sorted(set(row[0] for row in rows)):
            sub=[(q,v) for label,q,v in rows if label==name];solution=sum(q for q,v in sub);solute=sum(v for q,v in sub);result.append((name,solution,solute,sum(q-v for q,v in sub),F(solute,solution) if solution else None))
        solution=sum(q for name,q,v in rows);solute=sum(v for name,q,v in rows);out={'fractions':tuple(result),'total_carrier':sum(q-v for name,q,v in rows),'solute_fraction':F(solute,solution) if solution else None,'scope':a.SCOPE}
        self.assertEqual(a.fractions(rows),out);self.assertEqual(a.fractions(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
        rows=[('É'+str(r.randrange(5)),r.randrange(1000001),r.randrange(1,1000001)) for i in range(r.randrange(1,40))];result=[]
        for name in sorted(set(row[0] for row in rows)):
            sub=[(q,v) for label,q,v in rows if label==name];harvest=sum(q for q,v in sub);area=sum(v for q,v in sub);result.append((name,harvest,area,F(harvest,area)))
        harvest=sum(q for name,q,v in rows);area=sum(v for name,q,v in rows);out={'area':tuple(result),'total_harvest':harvest,'total_area':area,'overall_ratio':F(harvest,area),'scope':b.SCOPE}
        self.assertEqual(b.area(rows),out);self.assertEqual(b.area(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))
def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for fn,message in ((a.fractions,'masses must be exactint0<=solute<=solution<=1000000'),(b.area,'harvest must be exactint0..1000000 and area exactint1..1000000')):
    row=('a',1,1)
    for bad in ([],[row]*65,{},set(),iter([]),'x',None,L([row]),T((row,))):cases.append((fn,(bad,),'rows must be exactlist/tuple length1..64'))
    for bad in ([],row[:-1],row+(0,),'abc',None,L(row),T(row)):cases.append((fn,([bad],),'row must be exactlist/tuple triple'))
    for bad in ('','x'*41,'\n','\x00',S('a'),0,None):cases.append((fn,([(bad,)+row[1:]],),'label must be exactstr printable Unicode length1..40'))
    for slot in (1,2):
        for bad in (True,False,I(0),1.,None,'1',-1,1000001):
            altered=list(row);altered[slot]=bad;cases.append((fn,([altered],),message))
cases.append((a.fractions,([('a',0,1)],),'masses must be exactint0<=solute<=solution<=1000000'))
cases.append((b.area,([('a',0,0)],),'harvest must be exactint0..1000000 and area exactint1..1000000'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))
def charset(char):
    def test(self):a.fractions([(char,0,0)]);b.area([(char,0,1)])
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))


def disclaimer(self):
    self.assertEqual(a.__doc__,'Hydroponics.\n\nPARTIAL: caller solution/solute mass fraction ledger only, not hydroponics,\nnutrient suitability, plant health, solution chemistry or growing advice.\nCaller compatible masses are abstract, not verified nutrient measurements.\n')
    self.assertEqual(b.__doc__,'Urban Agriculture.\n\nPARTIAL: caller harvest/area ratio ledger only, not urban agriculture,\ncrop yield prediction, land suitability, food safety or growing recommendations.\nCaller compatible quantities are declarations, not verified farming data.\n')
Tests.test_disclaimer=disclaimer
