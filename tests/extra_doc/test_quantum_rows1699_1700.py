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
a=load('rights_records1699');b=load('community_counts1700')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand(self):
        for rows in ([['B','disputed',1],('A','open',0)],[('B','disputed',1),['A','open',0]]):
            self.assertEqual(a.records(rows),{'records':(('A','open',0),('B','disputed',1)),'statuses':(('open',1,0),('recorded',0,0),('disputed',1,1)),'disputed':('B',),'scope':'caller-declared record-status ledger only; no Indigenous rights or consent verification'})
        for rows in ([['B',3,2],('A',0,0),['B',1,1]],[('B',1,1),['A',0,0],('B',3,2)]):
            self.assertEqual(b.participation(rows),{'participation':(('A',0,0,None),('B',4,3,F(3,4))),'invited':4,'participated':3,'fraction':F(3,4),'scope':'caller invited-participated count ledger only; no community engagement or consent claims'})
        self.assertEqual(b.participation([('x',0,0)])['fraction'],None)
    def test_caps(self):
        a.records([(str(i),'recorded',1000000) for i in range(64)]);a.records([('x'*40,'open',0)])
        b.participation([('x'*40,1000000,1000000)]*64)
    def test_precedence(self):
        with self.assertRaises(ValueError) as c:a.records([('x','open',1),('x',None,True)])
        self.assertEqual(str(c.exception),'labels must be unique')
def seeded(seed):
    def test(self):
        r=random.Random(seed);rows=[('Ω'+str(i),r.choice(('open','recorded','disputed')),r.randrange(1000001)) for i in range(r.randrange(1,40))];r.shuffle(rows);out={'records':tuple(sorted(rows)),'statuses':tuple((s,len([1 for name,status,n in rows if status==s]),sum(n for name,status,n in rows if status==s)) for s in ('open','recorded','disputed')),'disputed':tuple(name for name,status,n in sorted(rows) if status=='disputed'),'scope':a.SCOPE}
        self.assertEqual(a.records(rows),out);self.assertEqual(a.records(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
        rows=[]
        for i in range(r.randrange(1,40)):
            n=r.randrange(1000001);rows.append(('É'+str(r.randrange(5)),n,r.randrange(n+1)))
        result=[]
        for name in sorted(set(row[0] for row in rows)):
            sub=[(n,p) for label,n,p in rows if label==name];invited=sum(n for n,p in sub);participated=sum(p for n,p in sub);result.append((name,invited,participated,F(participated,invited) if invited else None))
        invited=sum(n for name,n,p in rows);participated=sum(p for name,n,p in rows);out={'participation':tuple(result),'invited':invited,'participated':participated,'fraction':F(participated,invited) if invited else None,'scope':b.SCOPE}
        self.assertEqual(b.participation(rows),out);self.assertEqual(b.participation(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))
def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for fn,row in ((a.records,('a','open',1)),(b.participation,('a',1,1))):
    for bad in ([],[row]*65,{},set(),iter([]),'x',None,L([row]),T((row,))):cases.append((fn,(bad,),'rows must be exactlist/tuple length1..64'))
    for bad in ([],row[:-1],row+(0,),'abc',None,L(row),T(row)):cases.append((fn,([bad],),'row must be exactlist/tuple triple'))
    for bad in ('','x'*41,'\n','\x00',S('a'),0,None):cases.append((fn,([(bad,)+row[1:]],),'label must be exactstr printable Unicode length1..40'))
    for slot in (2,) if fn==a.records else (1,2):
        for bad in (True,False,I(0),1.,None,'1',-1,1000001):
            altered=list(row);altered[slot]=bad;cases.append((fn,([altered],),'count must be exactint0..1000000' if fn==a.records else 'counts must be exactint0<=participated<=invited<=1000000'))
for bad in (S('open'),S('recorded'),S('disputed'),'OPEN','',None,1,True,[],{},'approved','Ω') :cases.append((a.records,([('a',bad,0)],),'status must be exactstr open/recorded/disputed'))
cases.append((a.records,([('a','open',0),('a','open',0)],),'labels must be unique'))
cases.append((b.participation,([('a',0,1)],),'counts must be exactint0<=participated<=invited<=1000000'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))
def charset(char):
    def test(self):a.records([(char,'open',0)]);b.participation([(char,0,0)])
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))

def disclaimer(self):
    self.assertEqual(a.__doc__,'Indigenous Rights.\n\nPARTIAL: caller-declared record-status ledger only, not Indigenous rights,\nconsent verification, consultation adequacy, legal status or cultural advice.\nA recorded status is not consent, authority, community agreement or permission.\n')
    self.assertEqual(b.__doc__,'Community Engagement.\n\nPARTIAL: caller invited/participated count ledger only, not community\nengagement, representativeness, consultation quality, consent or policy advice.\nCaller counts are declarations, not verified participants or community views.\n')
Tests.test_disclaimer=disclaimer
