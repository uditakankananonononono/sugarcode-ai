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
a=load('emission_changes1663');b=load('atmospheric_transfers1664')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand(self):
        for rows in ([['B',3],('A',2),['C',3]],[('B',3),['A',2],('C',3)]):
            self.assertEqual(a.changes(rows),{'changes':(('B',3,None),('A',2,-1),('C',3,1)),'increases':('C',),'total_change':0,'maximum':3,'scope':'caller ordered value-difference arithmetic only; no emissions monitoring claims'})
        self.assertEqual(a.changes([('x',0),('y',0)])['increases'],())
        for rows in ([['B','A',1],('A','B',2),['A','A',3]],[('B','A',1),['A','B',2],('A','A',3)]):
            self.assertEqual(b.transfers(rows),{'transfers':(('A',4,5,-1),('B',2,1,1)),'total_transferred':6,'positive':('B',),'scope':'caller directed transfer ledger only; no atmospheric chemistry modeling'})
        self.assertEqual(b.transfers([('x','x',0)])['positive'],())
    def test_caps(self):
        a.changes([(str(i),1000000) for i in range(64)]);a.changes([('x'*40,0)])
        b.transfers([('x'*40,'y'*40,1000000)]*64)
    def test_precedence(self):
        with self.assertRaises(ValueError) as c:a.changes([('x',1),('x',True)])
        self.assertEqual(str(c.exception),'labels must be unique')
        with self.assertRaises(ValueError) as c:b.transfers([('',None,True)])
        self.assertEqual(str(c.exception),'source must be exactstr printable Unicode length1..40')

def seeded(seed):
    def test(self):
        r=random.Random(seed);rows=[('Ω'+str(i),r.randrange(1000001)) for i in range(r.randrange(1,40))];r.shuffle(rows);values=[v for name,v in rows];deltas=[None]+[right-left for left,right in zip(values,values[1:])];out={'changes':tuple((name,v,d) for (name,v),d in zip(rows,deltas)),'increases':tuple(rows[i][0] for i in range(1,len(rows)) if values[i]>values[i-1]),'total_change':sum(d for d in deltas[1:]),'maximum':sorted(values)[-1],'scope':a.SCOPE}
        self.assertEqual(a.changes(rows),out);self.assertEqual(a.changes(tuple(list(row) if i%2 else row for i,row in enumerate(rows))),out)
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
for fn,row in ((a.changes,('a',1)),(b.transfers,('a','b',1))):
    for bad in ([],[row]*65,{},set(),iter([]),'x',None,L([row]),T((row,))):cases.append((fn,(bad,),'rows must be exactlist/tuple length1..64'))
    for bad in ([],row[:-1],row+(0,),'abc',None,L(row),T(row)):cases.append((fn,([bad],),'row must be exactlist/tuple '+('pair' if fn==a.changes else 'triple')))
    for slot,name in ((0,'label'),) if fn==a.changes else ((0,'source'),(1,'target')):
        for bad in ('','x'*41,'\n','\x00',S('a'),0,None):
            altered=list(row);altered[slot]=bad;cases.append((fn,([altered],),name+' must be exactstr printable Unicode length1..40'))
    for bad in (True,False,I(0),1.,None,'1',-1,1000001):
        altered=list(row);altered[-1]=bad;cases.append((fn,([altered],),('value' if fn==a.changes else 'quantity')+' must be exactint0..1000000'))
cases.append((a.changes,([('a',0),('a',0)],),'labels must be unique'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))
def charset(char):
    def test(self):a.changes([(char,0)]);b.transfers([(char,'x',0)]);b.transfers([('x',char,0)])
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))

def disclaimer(self):
    self.assertEqual(a.__doc__,'Emissions Monitoring.\n\nPARTIAL: caller ordered emission-value differences only, not emissions\nmonitoring, sensor validation, source attribution or regulatory compliance.\nCaller values are abstract, not verified pollutant measurements.\n')
    self.assertEqual(b.__doc__,'Atmospheric Chemistry.\n\nPARTIAL: caller directed quantity-transfer ledger only, not atmospheric\nchemistry, chemical reactions, kinetics, species identification or forecasting.\nCaller labels are abstract buckets, not inferred molecular species.\n')
Tests.test_disclaimer=disclaimer
