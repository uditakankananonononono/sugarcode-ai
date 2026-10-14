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
a=load('water_components1709');b=load('ecological_area1710')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand(self):
        for rows in ([['B',1,2,3],('A',0,0,0),['B',4,5,6]],[('B',4,5,6),['A',0,0,0],('B',1,2,3)]):
            self.assertEqual(a.components(rows),{'components':(('A',0,0,0,0),('B',5,7,9,21)),'totals':(5,7,9),'total':21,'scope':'caller component water-quantity ledger only; no verified water footprint claims'})
        for rows in ([['B',3,2],('A',0,1)],[('B',3,2),['A',0,1]]):
            self.assertEqual(b.areas(rows),{'areas':(('A',F(0)),('B',F(3,2))),'total_area':F(3,2),'zero':('A',),'scope':'caller demand-yield equivalent-area arithmetic only; no ecological footprint claims'})
        self.assertEqual(b.areas([('x',1,1)])['zero'],())
    def test_caps(self):
        a.components([('x'*40,1000000,1000000,1000000)]*64)
        b.areas([(str(i),1000000,1000000) for i in range(64)]);b.areas([('x'*40,0,1)])
    def test_precedence(self):
        with self.assertRaises(ValueError) as c:b.areas([('x',1,1),('x',True,None)])
        self.assertEqual(str(c.exception),'labels must be unique')
def seeded(seed):
    def test(self):
        r=random.Random(seed);rows=[('Ω'+str(r.randrange(5)),r.randrange(1000001),r.randrange(1000001),r.randrange(1000001)) for i in range(r.randrange(1,40))];result=[]
        for name in sorted(set(row[0] for row in rows)):
            sub=[(x,y,z) for label,x,y,z in rows if label==name];result.append((name,sum(x for x,y,z in sub),sum(y for x,y,z in sub),sum(z for x,y,z in sub),sum(sum(row) for row in sub)))
        totals=tuple(sum(row[i] for row in rows) for i in (1,2,3));out={'components':tuple(result),'totals':totals,'total':sum(sum(row[1:]) for row in rows),'scope':a.SCOPE}
        self.assertEqual(a.components(rows),out);self.assertEqual(a.components(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
        rows=[('É'+str(i),r.randrange(1000001),r.randrange(1,1000001)) for i in range(r.randrange(1,40))];r.shuffle(rows);result=tuple((name,F(q,d)) for name,q,d in sorted(rows));out={'areas':result,'total_area':sum(F(q,d) for name,q,d in rows),'zero':tuple(name for name,q,d in sorted(rows) if not q),'scope':b.SCOPE}
        self.assertEqual(b.areas(rows),out);self.assertEqual(b.areas(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))
def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for fn,row,message in ((a.components,('a',1,1,1),'quantities must be exactint0..1000000'),(b.areas,('a',1,1),'demand must be exactint0..1000000 and yield exactint1..1000000')):
    for bad in ([],[row]*65,{},set(),iter([]),'x',None,L([row]),T((row,))):cases.append((fn,(bad,),'rows must be exactlist/tuple length1..64'))
    for bad in ([],row[:-1],row+(0,),'abcd',None,L(row),T(row)):cases.append((fn,([bad],),'row must be exactlist/tuple '+('quadruple' if fn==a.components else 'triple')))
    for bad in ('','x'*41,'\n','\x00',S('a'),0,None):cases.append((fn,([(bad,)+row[1:]],),'label must be exactstr printable Unicode length1..40'))
    for slot in range(1,len(row)):
        for bad in (True,False,I(0),1.,None,'1',-1,1000001):
            altered=list(row);altered[slot]=bad;cases.append((fn,([altered],),message))
cases.append((b.areas,([('a',0,0)],),'demand must be exactint0..1000000 and yield exactint1..1000000'))
cases.append((b.areas,([('a',0,1),('a',0,1)],),'labels must be unique'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))
def charset(char):
    def test(self):a.components([(char,0,0,0)]);b.areas([(char,0,1)])
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))

def disclaimer(self):
    self.assertEqual(a.__doc__,'Water Footprinting.\n\nPARTIAL: caller component water-quantity ledger only, not water footprinting,\nverified consumption, hydrology, scarcity assessment or environmental advice.\nCaller category quantities are abstract, not verified footprint inventories.\n')
    self.assertEqual(b.__doc__,'Ecological Footprinting.\n\nPARTIAL: caller demand/yield equivalent-area arithmetic only, not ecological\nfootprinting, biocapacity assessment, sustainability or environmental advice.\nCaller factors are abstract, not verified yields or ecological inventories.\n')
Tests.test_disclaimer=disclaimer
