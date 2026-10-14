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
a=load('material_transfers1711');b=load('industrial_balance1712')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand(self):
        for rows in ([['B','A',1],('A','B',2),['A','A',3]],[('B','A',1),['A','B',2],('A','A',3)]):
            self.assertEqual(a.transfers(rows),{'transfers':(('A',4,5,-1),('B',2,1,1)),'total_transferred':6,'positive':('B',),'scope':'caller directed material-quantity transfer ledger only; no verified material flow analysis'})
        self.assertEqual(a.transfers([('x','x',0)])['positive'],())
        for rows in ([['B',1,2,0],('A',1,0,0),['B',0,0,0]],[('B',0,0,0),['A',1,0,0],('B',1,2,0)]):
            self.assertEqual(b.balances(rows),{'balances':(('A',1,0,0,1),('B',1,2,0,-1)),'total_residual':0,'negative':('B',),'scope':'caller input-output-loss material ledger only; no industrial ecology claims'})
        self.assertEqual(b.balances([('x',0,0,0)])['negative'],())
    def test_caps(self):
        a.transfers([('x'*40,'y'*40,1000000)]*64);b.balances([('x'*40,1000000,1000000,1000000)]*64)
    def test_precedence(self):
        with self.assertRaises(ValueError) as c:a.transfers([('',None,True)])
        self.assertEqual(str(c.exception),'source must be exactstr printable Unicode length1..40')
def seeded(seed):
    def test(self):
        r=random.Random(seed);rows=[('Ω'+str(r.randrange(5)),'Ω'+str(r.randrange(5)),r.randrange(1000001)) for i in range(r.randrange(1,40))];result=[]
        for name in sorted(set(s for s,t,q in rows)|set(t for s,t,q in rows)):
            incoming=sum(q for s,t,q in rows if t==name);outgoing=sum(q for s,t,q in rows if s==name);result.append((name,incoming,outgoing,incoming-outgoing))
        out={'transfers':tuple(result),'total_transferred':sum(q for s,t,q in rows),'positive':tuple(name for name,i,o,n in result if i>o),'scope':a.SCOPE}
        self.assertEqual(a.transfers(rows),out);self.assertEqual(a.transfers(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
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
for fn,row in ((a.transfers,('a','b',1)),(b.balances,('a',1,1,1))):
    for bad in ([],[row]*65,{},set(),iter([]),'x',None,L([row]),T((row,))):cases.append((fn,(bad,),'rows must be exactlist/tuple length1..64'))
    for bad in ([],row[:-1],row+(0,),'abcd',None,L(row),T(row)):cases.append((fn,([bad],),'row must be exactlist/tuple '+('triple' if fn==a.transfers else 'quadruple')))
    for slot,name in ((0,'source'),(1,'target')) if fn==a.transfers else ((0,'label'),):
        for bad in ('','x'*41,'\n','\x00',S('a'),0,None):
            altered=list(row);altered[slot]=bad;cases.append((fn,([altered],),name+' must be exactstr printable Unicode length1..40'))
    for slot in (2,) if fn==a.transfers else (1,2,3):
        for bad in (True,False,I(0),1.,None,'1',-1,1000001):
            altered=list(row);altered[slot]=bad;cases.append((fn,([altered],),('quantity' if fn==a.transfers else 'quantities')+' must be exactint0..1000000'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))
def charset(char):
    def test(self):a.transfers([(char,'x',0)]);a.transfers([('x',char,0)]);b.balances([(char,0,0,0)])
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))

def disclaimer(self):
    self.assertEqual(a.__doc__,'Material Flow Analysis.\n\nPARTIAL: caller directed material-quantity transfer ledger only, not material\nflow analysis, inventory verification, process modeling or environmental advice.\nCaller compatible quantities are abstract, not verified physical material data.\n')
    self.assertEqual(b.__doc__,'Industrial Ecology.\n\nPARTIAL: caller input/output/loss material ledger only, not industrial\necology, industrial symbiosis, lifecycle analysis or environmental benefit.\nCaller compatible quantities are abstract, not verified industrial process data.\n')
Tests.test_disclaimer=disclaimer
