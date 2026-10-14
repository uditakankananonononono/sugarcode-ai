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
a=load('brownfield_cost1669');b=load('phyto_uptake1670')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand(self):
        for rows in ([['B',2,2,3],('A',1,2,2)],[('B',2,2,3),['A',1,2,2]]):
            self.assertEqual(a.budgets(rows),{'budgets':(('A',2,0),('B',4,-1)),'over_budget':('B',),'total_cost':6,'scope':'caller area-unit-cost-budget arithmetic only; no brownfield redevelopment advice'})
        self.assertEqual(a.budgets([('x',0,0,1)])['over_budget'],())
        for rows in ([['B',3,2],('A',0,1),['B',1,4]],[('B',1,4),['A',0,1],('B',3,2)]):
            self.assertEqual(b.uptake(rows),{'uptake':(('A',0,0),('B',4,10)),'total_product':10,'positive':('B',),'scope':'caller biomass-concentration product ledger only; no phytoremediation claims'})
        self.assertEqual(b.uptake([('x',1,1)])['positive'],('x',))
        self.assertEqual(b.uptake([('x',1,0)])['positive'],())
    def test_caps(self):
        a.budgets([(str(i),1000000,1000000,1000000) for i in range(64)]);a.budgets([('x'*40,0,0,0)])
        b.uptake([('x'*40,1000000,1000000)]*64)
    def test_precedence(self):
        with self.assertRaises(ValueError) as c:a.budgets([('x',1,1,1),('x',True,None,None)])
        self.assertEqual(str(c.exception),'labels must be unique')
        for fn,row in ((a.budgets,('',True,None,None)),(b.uptake,('',True,None))):
            with self.assertRaises(ValueError) as c:fn([row])
            self.assertEqual(str(c.exception),'label must be exactstr printable Unicode length1..40')

def seeded(seed):
    def test(self):
        r=random.Random(seed);rows=[('Ω'+str(i),r.randrange(1000001),r.randrange(1000001),r.randrange(1000001)) for i in range(r.randrange(1,40))];r.shuffle(rows);result=tuple((name,x*y,z-x*y) for name,x,y,z in sorted(rows));out={'budgets':result,'over_budget':tuple(name for name,x,y,z in sorted(rows) if x*y>z),'total_cost':sum(x*y for name,x,y,z in rows),'scope':a.SCOPE}
        self.assertEqual(a.budgets(rows),out);self.assertEqual(a.budgets(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
        rows=[('É'+str(r.randrange(5)),r.randrange(1000001),r.randrange(1000001)) for i in range(r.randrange(1,40))];result=[]
        for name in sorted(set(row[0] for row in rows)):
            sub=[(q,c) for label,q,c in rows if label==name];result.append((name,sum(q for q,c in sub),sum(q*c for q,c in sub)))
        out={'uptake':tuple(result),'total_product':sum(q*c for name,q,c in rows),'positive':tuple(name for name,q,c in result if c!=0),'scope':b.SCOPE}
        self.assertEqual(b.uptake(rows),out);self.assertEqual(b.uptake(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))
def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for fn,row in ((a.budgets,('a',1,1,1)),(b.uptake,('a',1,1))):
    for bad in ([],[row]*65,{},set(),iter([]),'x',None,L([row]),T((row,))):cases.append((fn,(bad,),'rows must be exactlist/tuple length1..64'))
    for bad in ([],row[:-1],row+(0,),'abcd',None,L(row),T(row)):cases.append((fn,([bad],),'row must be exactlist/tuple '+('quadruple' if fn==a.budgets else 'triple')))
    for bad in ('','x'*41,'\n','\x00',S('a'),0,None):cases.append((fn,([(bad,)+row[1:]],),'label must be exactstr printable Unicode length1..40'))
    for slot in range(1,len(row)):
        for bad in (True,False,I(0),1.,None,'1',-1,1000001):
            altered=list(row);altered[slot]=bad;cases.append((fn,([altered],),'quantities must be exactint0..1000000'))
cases.append((a.budgets,([('a',0,0,0),('a',0,0,0)],),'labels must be unique'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))
def charset(char):
    def test(self):a.budgets([(char,0,0,0)]);b.uptake([(char,0,0)])
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))

def disclaimer(self):
    self.assertEqual(a.__doc__,'Brownfield Redevelopment.\n\nPARTIAL: caller area/unit-cost/budget arithmetic only, not brownfield\nredevelopment, land valuation, remediation planning or investment advice.\nCaller quantities are declarations, not verified site conditions or quotes.\n')
    self.assertEqual(b.__doc__,'Phytoremediation.\n\nPARTIAL: caller biomass/concentration product ledger only, not phytoremediation,\nplant uptake prediction, species selection, cleanup effectiveness or safety.\nCaller compatible units are abstract, not measured contaminant uptake data.\n')
Tests.test_disclaimer=disclaimer
