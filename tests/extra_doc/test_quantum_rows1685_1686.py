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
a=load('vertical_layers1685');b=load('aqua_balance1686')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand(self):
        for rows in ([['B',2,3,4],('A',0,1,2)],[('B',2,3,4),['A',0,1,2]]):
            self.assertEqual(a.layers(rows),{'layers':(('A',0,0),('B',6,24)),'total_area':6,'total_product':24,'scope':'caller footprint-layers-output-rate arithmetic only; no vertical farming claims'})
        for rows in ([['B',1,2,0],('A',1,0,0),['B',0,0,0]],[('B',0,0,0),['A',1,0,0],('B',1,2,0)]):
            self.assertEqual(b.balances(rows),{'balances':(('A',1,0,0,1),('B',1,2,0,-1)),'total_residual':0,'negative':('B',),'scope':'caller input-uptake-loss nutrient ledger only; no aquaponics advice'})
        self.assertEqual(b.balances([('x',0,0,0)])['negative'],())
    def test_caps(self):
        a.layers([(str(i),1000000,64,1000000) for i in range(64)]);a.layers([('x'*40,0,1,0)])
        b.balances([('x'*40,1000000,1000000,1000000)]*64)
    def test_precedence(self):
        with self.assertRaises(ValueError) as c:a.layers([('x',1,1,1),('x',True,None,None)])
        self.assertEqual(str(c.exception),'labels must be unique')
def seeded(seed):
    def test(self):
        r=random.Random(seed);rows=[('Ω'+str(i),r.randrange(1000001),r.randrange(1,65),r.randrange(1000001)) for i in range(r.randrange(1,40))];r.shuffle(rows);result=tuple((name,q*n,q*(n*v)) for name,q,n,v in sorted(rows));out={'layers':result,'total_area':sum(q*n for name,q,n,v in rows),'total_product':sum(q*n*v for name,q,n,v in rows),'scope':a.SCOPE}
        self.assertEqual(a.layers(rows),out);self.assertEqual(a.layers(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
        rows=[('É'+str(r.randrange(5)),r.randrange(1000001),r.randrange(1000001),r.randrange(1000001)) for i in range(r.randrange(1,40))];result=[]
        for name in sorted(set(row[0] for row in rows)):
            sub=[(q,u,l) for label,q,u,l in rows if label==name];q=sum(x for x,u,l in sub);u=sum(y for x,y,l in sub);l=sum(z for x,y,z in sub);result.append((name,q,u,l,sum(x-(y+z) for x,y,z in sub)))
        out={'balances':tuple(result),'total_residual':sum(q-(u+l) for name,q,u,l in rows),'negative':tuple(name for name,q,u,l,v in result if u+l>q),'scope':b.SCOPE}
        self.assertEqual(b.balances(rows),out);self.assertEqual(b.balances(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))
def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for fn in (a.layers,b.balances):
    row=('a',1,1,1);message='footprint and rate must be exactint0..1000000 and layers exactint1..64' if fn==a.layers else 'quantities must be exactint0..1000000'
    for bad in ([],[row]*65,{},set(),iter([]),'x',None,L([row]),T((row,))):cases.append((fn,(bad,),'rows must be exactlist/tuple length1..64'))
    for bad in ([],row[:-1],row+(0,),'abcd',None,L(row),T(row)):cases.append((fn,([bad],),'row must be exactlist/tuple quadruple'))
    for bad in ('','x'*41,'\n','\x00',S('a'),0,None):cases.append((fn,([(bad,)+row[1:]],),'label must be exactstr printable Unicode length1..40'))
    for slot in (1,2,3):
        for bad in (True,False,I(0),1.,None,'1',-1,1000001):
            altered=list(row);altered[slot]=bad;cases.append((fn,([altered],),message))
for value in (0,65):cases.append((a.layers,([('a',0,value,0)],),'footprint and rate must be exactint0..1000000 and layers exactint1..64'))
cases.append((a.layers,([('a',0,1,0),('a',0,1,0)],),'labels must be unique'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))
def charset(char):
    def test(self):a.layers([(char,0,1,0)]);b.balances([(char,0,0,0)])
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))

def disclaimer(self):
    self.assertEqual(a.__doc__,'Vertical Farming.\n\nPARTIAL: caller footprint/layers/output-rate arithmetic only, not vertical\nfarming, crop growth, lighting design, yield prediction or economic advice.\nCaller factors are abstract, not verified equipment or crop performance data.\n')
    self.assertEqual(b.__doc__,'Aquaponics.\n\nPARTIAL: caller input/uptake/loss nutrient ledger only, not aquaponics,\nfish or plant health, nutrient cycling, water safety or operational advice.\nCaller compatible quantities are abstract, not verified biological data.\n')
Tests.test_disclaimer=disclaimer
