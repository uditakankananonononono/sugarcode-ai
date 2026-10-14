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
a=load('organic_input1681');b=load('perma_transfers1682')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand(self):
        for rows in ([['B',3,2],('A',0,1),['B',1,4]],[('B',1,4),['A',0,1],('B',3,2)]):
            self.assertEqual(a.inputs(rows),{'inputs':(('A',0,0),('B',4,10)),'total_input':10,'positive':('B',),'scope':'caller area-input-rate product ledger only; no organic farming or certification claims'})
        self.assertEqual(a.inputs([('x',1,1)])['positive'],('x',));self.assertEqual(a.inputs([('x',1,0)])['positive'],())
        for rows in ([['B','A',1],('A','B',2),['A','A',3]],[('B','A',1),['A','B',2],('A','A',3)]):
            self.assertEqual(b.transfers(rows),{'transfers':(('A',4,5,-1),('B',2,1,1)),'total_transferred':6,'positive':('B',),'scope':'caller directed resource-transfer ledger only; no permaculture design claims'})
        self.assertEqual(b.transfers([('x','x',0)])['positive'],())
    def test_caps(self):
        a.inputs([('x'*40,1000000,1000000)]*64);b.transfers([('x'*40,'y'*40,1000000)]*64)
    def test_precedence(self):
        with self.assertRaises(ValueError) as c:b.transfers([('',None,True)])
        self.assertEqual(str(c.exception),'source must be exactstr printable Unicode length1..40')

def seeded(seed):
    def test(self):
        r=random.Random(seed);rows=[('Ω'+str(r.randrange(5)),r.randrange(1000001),r.randrange(1000001)) for i in range(r.randrange(1,40))];result=[]
        for name in sorted(set(row[0] for row in rows)):
            sub=[(q,v) for label,q,v in rows if label==name];result.append((name,sum(q for q,v in sub),sum(q*v for q,v in sub)))
        out={'inputs':tuple(result),'total_input':sum(q*v for name,q,v in rows),'positive':tuple(name for name,q,v in result if v!=0),'scope':a.SCOPE}
        self.assertEqual(a.inputs(rows),out);self.assertEqual(a.inputs(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
        rows=[('É'+str(r.randrange(5)),'É'+str(r.randrange(5)),r.randrange(1000001)) for i in range(r.randrange(1,40))];result=[]
        for name in sorted(set(s for s,t,q in rows)|set(t for s,t,q in rows)):
            incoming=sum(q for s,t,q in rows if t==name);outgoing=sum(q for s,t,q in rows if s==name);result.append((name,incoming,outgoing,incoming-outgoing))
        out={'transfers':tuple(result),'total_transferred':sum(q for s,t,q in rows),'positive':tuple(name for name,i,o,n in result if i>o),'scope':b.SCOPE}
        self.assertEqual(b.transfers(rows),out);self.assertEqual(b.transfers(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))
def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for fn,row in ((a.inputs,('a',1,1)),(b.transfers,('a','b',1))):
    for bad in ([],[row]*65,{},set(),iter([]),'x',None,L([row]),T((row,))):cases.append((fn,(bad,),'rows must be exactlist/tuple length1..64'))
    for bad in ([],row[:-1],row+(0,),'abc',None,L(row),T(row)):cases.append((fn,([bad],),'row must be exactlist/tuple triple'))
    for slot,name in ((0,'label'),) if fn==a.inputs else ((0,'source'),(1,'target')):
        for bad in ('','x'*41,'\n','\x00',S('a'),0,None):
            altered=list(row);altered[slot]=bad;cases.append((fn,([altered],),name+' must be exactstr printable Unicode length1..40'))
    for slot in (1,2) if fn==a.inputs else (2,):
        for bad in (True,False,I(0),1.,None,'1',-1,1000001):
            altered=list(row);altered[slot]=bad;cases.append((fn,([altered],),('quantities' if fn==a.inputs else 'quantity')+' must be exactint0..1000000'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))
def charset(char):
    def test(self):a.inputs([(char,0,0)]);b.transfers([(char,'x',0)]);b.transfers([('x',char,0)])
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))

def disclaimer(self):
    self.assertEqual(a.__doc__,'Organic Farming.\n\nPARTIAL: caller area/input-rate product ledger only, not organic farming,\norganic certification, input eligibility, crop yield or agronomic advice.\nCaller compatible quantities are declarations, not verified farming data.\n')
    self.assertEqual(b.__doc__,'Permaculture.\n\nPARTIAL: caller directed resource-transfer ledger only, not permaculture,\nsite design, ecological synergy, productivity or farming recommendations.\nCaller endpoint labels are abstract buckets, not verified physical systems.\n')
Tests.test_disclaimer=disclaimer
