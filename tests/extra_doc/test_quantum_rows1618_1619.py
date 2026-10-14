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
a=load('network_rules1618');b=load('cyber_inventory1619')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand_scope_mix(self):
        for rules in ([[1,3,'allow'],(2,4,'deny')],[(1,3,'allow'),[2,4,'deny']]):
            self.assertEqual(a.evaluate(rules,[0,1,3,4],'deny'),{'decisions':((0,'deny',None),(1,'allow',0),(3,'allow',0),(4,'deny',1)),'scope':'caller integer-port rule simulation only; no firewall enforcement or security claims'})
        for rows in ([['B',3,1],('A',0,2),['C',1,1]],[('C',1,1),['A',0,2],('B',3,1)]):
            self.assertEqual(b.inventory(rows),{'inventory':(('A',2,True),('B',-2,False),('C',0,False)),'below':('A',),'largest_gap':2,'scope':'caller integer version inventory comparison only; no vulnerability or security claims'})
        self.assertEqual(b.inventory([('x',1,0)])['largest_gap'],0)
    def test_caps(self):
        a.evaluate([(0,65535,'allow')]*64,[65535]*64,'deny');a.evaluate([], [0],'allow');a.evaluate([(0,0,'allow')],[0],'deny')
        b.inventory([(str(i),1000000,1000000) for i in range(64)]);b.inventory([('a'*40,0,0)]);b.inventory([('x',0,1000000)])
    def test_precedence(self):
        with self.assertRaises(ValueError) as c:a.evaluate({},[],S('deny'))
        self.assertEqual(str(c.exception),'action must be exactstr allow or deny')
        with self.assertRaises(ValueError) as c:b.inventory([('a',0,0),('a',True,None)])
        self.assertEqual(str(c.exception),'labels must be unique')

def seeded(seed):
    def test(self):
        rng=random.Random(seed);rules=[]
        for i in range(rng.randrange(30)):
            lo=rng.randrange(100);rules.append((lo,rng.randrange(lo,101),rng.choice(('allow','deny'))))
        ports=[rng.randrange(101) for _ in range(rng.randrange(1,40))];default=rng.choice(('allow','deny'));result=[]
        for port in ports:
            indices=[i for i,(lo,hi,_) in enumerate(rules) if port in range(lo,hi+1)];index=min(indices) if indices else None;result.append((port,default if index is None else rules[index][2],index))
        out={'decisions':tuple(result),'scope':a.SCOPE};self.assertEqual(a.evaluate(rules,ports,default),out);self.assertEqual(a.evaluate(tuple(list(row) if i%2 else row for i,row in enumerate(rules)),tuple(ports),default),out)
        rows=[('Ω'+str(i),rng.randrange(1000001),rng.randrange(1000001)) for i in range(rng.randrange(1,40))];result=tuple(sorted((name,required-current,required-current>0) for name,current,required in rows));out={'inventory':result,'below':tuple(sorted(name for name,current,required in rows if required>current)),'largest_gap':max([required-current for name,current,required in rows]+[0]),'scope':b.SCOPE};self.assertEqual(b.inventory(rows),out);self.assertEqual(b.inventory(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))
def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for bad in ('','ALLOW',' allow',S('allow'),0,None,[],{}):
    cases.extend([(a.evaluate,([],[0],bad),'action must be exactstr allow or deny'),(a.evaluate,([(0,1,bad)],[0],'deny'),'action must be exactstr allow or deny')])
for bad in ([(0,1,'allow')]*65,{},set(),iter([]),'x',L([]),T(())):cases.append((a.evaluate,(bad,[0],'deny'),'rules must be exactlist/tuple atmost64'))
for bad in ([],[1,2],(1,2,3,4),'abc',L([0,1,'allow']),T((0,1,'allow'))):cases.append((a.evaluate,([bad],[0],'deny'),'rule must be exactlist/tuple triple'))
for slot in (0,1):
    for bad in (False,True,I(1),1.,None,'1',-1,65536):
        row=[0,2,'allow'];row[slot]=bad;cases.append((a.evaluate,([row],[0],'deny'),'rule ports must be exactint0..65535 with lo<=hi'))
cases.append((a.evaluate,([(2,1,'allow')],[0],'deny'),'rule ports must be exactint0..65535 with lo<=hi'))
for bad in ([],[0]*65,{},set(),iter([]),'x',L([0]),T((0,))):cases.append((a.evaluate,([],bad,'deny'),'ports must be exactlist/tuple length1..64'))
for bad in (False,True,I(1),1.,None,'1',-1,65536):cases.append((a.evaluate,([],[bad],'deny'),'port must be exactint0..65535'))
for bad in ([],[('a',0,0)]*65,{},set(),iter([]),'x',L([('a',0,0)]),T((('a',0,0),))):cases.append((b.inventory,(bad,),'rows must be exactlist/tuple length1..64'))
for bad in ([],[1,2],(1,2,3,4),'abc',L(['a',0,0]),T(('a',0,0))):cases.append((b.inventory,([bad],),'row must be exactlist/tuple triple'))
for bad in ('','a'*41,'\n','\x00',S('a'),0,None):cases.append((b.inventory,([(bad,0,0)],),'label must be exactstr printable Unicode length1..40'))
for slot in (1,2):
    for bad in (False,True,I(1),1.,None,'1',-1,1000001):
        row=['a',0,0];row[slot]=bad;cases.append((b.inventory,([row],),'versions must be exactint0..1000000'))
cases.append((b.inventory,([('a',0,0),('a',0,0)],),'labels must be unique'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))
def charset(char):
    def test(self):b.inventory([(char,0,0)])
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))

def exact_disclaimers(self):
    self.assertEqual(a.__doc__,'Network Security.\n\nPARTIAL: caller integer-port first-match rule simulation only, not network\nsecurity, firewall enforcement, packet inspection or vulnerability assessment.\nNo network access or changes. Rules/default are caller declarations.\n')
    self.assertEqual(b.__doc__,'Cybersecurity.\n\nPARTIAL: caller patch-version inventory comparison only, not cybersecurity,\nvulnerability discovery, secure-version certification or remediation execution.\nRequired versions supplied by caller; version ordering is integer-only toy data.\n')
Tests.test_exact_disclaimers=exact_disclaimers
