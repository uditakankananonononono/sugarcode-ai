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
a=load('carbon_transfer1623');b=load('ocean_ratio1624')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand_scope_mix(self):
        for balances,moves in (([['B',0],('A',2)],[['A','B',2],('B','A',1)]),([('A',2),['B',0]],[('A','B',2),['B','A',1]])):
            self.assertEqual(a.transfer(balances,moves),{'balances':(('A',1),('B',1)),'total':2,'scope':'caller pool-transfer ledger only; no carbon flux or climate analysis claims'})
        for rows in ([['B',1,4],('A',1,1)],[('A',1,1),['B',1,4]]):
            self.assertEqual(b.ratios(rows,[1,2]),{'ratios':(('A',F(2),F(1)),('B',F(1,2),F(-1,2))),'scope':'caller positive concentration ratios only; no ocean chemistry or pH predictions'})
    def test_caps(self):
        a.transfer([(str(i),1000000) for i in range(32)],[(str(0),str(1),0)]*64);a.transfer([('a'*40,0)],[])
        b.ratios([(str(i),1000000,1000000) for i in range(64)],[1000000,1000000]);b.ratios([('a'*40,1,1)],(1,1))
    def test_precedence(self):
        with self.assertRaises(ValueError) as c:a.transfer([('a',0),('a',True)],[])
        self.assertEqual(str(c.exception),'pool labels must be unique')
        with self.assertRaises(ValueError) as c:a.transfer([('a',0),('b',0)],[('a','b',1),('missing','b',0)])
        self.assertEqual(str(c.exception),'move endpoints must be distinct known pools')
        with self.assertRaises(ValueError) as c:b.ratios([],True)
        self.assertEqual(str(c.exception),'reference must be exactlist/tuple pair')

def seeded(seed):
    def test(self):
        rng=random.Random(seed);balances=[('Ω'+str(i),rng.randrange(100)) for i in range(rng.randrange(2,15))];pools=dict(balances);moves=[]
        for _ in range(rng.randrange(30)):
            source,target=rng.sample(list(pools),2);value=rng.randrange(pools[source]+1);moves.append((source,target,value));pools[source]-=value;pools[target]+=value
        expected=[]
        for name,initial in balances:expected.append((name,initial+sum(value for source,target,value in moves if target==name)-sum(value for source,target,value in moves if source==name)))
        out={'balances':tuple(sorted(expected)),'total':sum(value for _,value in balances),'scope':a.SCOPE};self.assertEqual(a.transfer(balances,moves),out);self.assertEqual(a.transfer(tuple(list(row) if i%2 else row for i,row in enumerate(balances[::-1])),tuple(list(row) if i%2 else row for i,row in enumerate(moves))),out)
        ref=(rng.randrange(1,1000001),rng.randrange(1,1000001));rows=[('É'+str(i),rng.randrange(1,1000001),rng.randrange(1,1000001)) for i in range(rng.randrange(1,40))];result=tuple(sorted((name,F(num*ref[1],den*ref[0]),F(num*ref[1]-den*ref[0],den*ref[0])) for name,num,den in rows));out={'ratios':result,'scope':b.SCOPE};self.assertEqual(b.ratios(rows,ref),out);self.assertEqual(b.ratios(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1])),list(ref)),out)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))
def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for bad in ([],[('a',0)]*33,{},set(),iter([]),'x',L([('a',0)]),T((('a',0),))):cases.append((a.transfer,(bad,[]),'balances must be exactlist/tuple length1..32'))
for bad in ([],[1],(1,2,3),'ab',L(['a',0]),T(('a',0))):cases.append((a.transfer,([bad],[]),'balance row must be exactlist/tuple pair'))
for position in (0,1,2):
    for bad in ('','a'*41,'\n','\x00',S('a'),0,None):
        balances=[('a',0),('b',0)];moves=[]
        if position==0:balances=[(bad,0)]
        else:moves=[(bad,'b',0) if position==1 else ('a',bad,0)]
        cases.append((a.transfer,(balances,moves),'label must be exactstr printable Unicode length1..40'))
for bad in (False,True,I(1),1.,None,'1',-1,1000001):
    cases.extend([(a.transfer,([('a',bad)],[]),'amount must be exactint0..1000000'),(a.transfer,([('a',0),('b',0)],[('a','b',bad)]),'amount must be exactint0..1000000')])
for bad in ([('a','b',0)]*65,{},set(),iter([]),'x',L([]),T(())):cases.append((a.transfer,([('a',0),('b',0)],bad),'moves must be exactlist/tuple atmost64'))
for bad in ([],[1,2],(1,2,3,4),'abc',L(['a','b',0]),T(('a','b',0))):cases.append((a.transfer,([('a',0),('b',0)],[bad]),'move row must be exactlist/tuple triple'))
for move in (('a','a',0),('a','missing',0),('missing','b',0)):cases.append((a.transfer,([('a',0),('b',0)],[move]),'move endpoints must be distinct known pools'))
cases.extend([(a.transfer,([('a',0),('a',0)],[]),'pool labels must be unique'),(a.transfer,([('a',0),('b',0)],[('a','b',1)]),'move must not overdraw current source')])
for bad in ([],[('a',1,1)]*65,{},set(),iter([]),'x',L([('a',1,1)]),T((('a',1,1),))):cases.append((b.ratios,(bad,(1,1)),'rows must be exactlist/tuple length1..64'))
for bad in ([],[1,2],(1,2,3,4),'abc',L(['a',1,1]),T(('a',1,1))):cases.append((b.ratios,([bad],(1,1)),'row must be exactlist/tuple triple'))
for bad in ('','a'*41,'\n','\x00',S('a'),0,None):cases.append((b.ratios,([(bad,1,1)],(1,1)),'label must be exactstr printable Unicode length1..40'))
for bad in ([],[1],(1,2,3),'ab',L([1,1]),T((1,1))):cases.append((b.ratios,([('a',1,1)],bad),'reference must be exactlist/tuple pair'))
for position in (0,1,2,3):
    for bad in (False,True,I(1),1.,None,'1',0,1000001):
        row=['a',1,1];ref=[1,1]
        if position<2:row[position+1]=bad
        else:ref[position-2]=bad
        cases.append((b.ratios,([row],ref),'fraction components must be exactint1..1000000'))
cases.append((b.ratios,([('a',1,1),('a',1,1)],(1,1)),'labels must be unique'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))
def charset(char):
    def test(self):a.transfer([(char,1),('long_other',0)],[(char,'long_other',1),('long_other',char,1)]);b.ratios([(char,1,1)],(1,1))
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))

def exact_disclaimers(self):
    self.assertEqual(a.__doc__,'Carbon Cycle Analysis.\n\nPARTIAL: caller nonnegative pool-transfer ledger arithmetic only, not carbon\ncycle analysis,flux estimates,chemical dynamics or climate projections.\nPool balances/transfers are caller abstractions,not measured carbon reservoirs.\n')
    self.assertEqual(b.__doc__,'Ocean Acidification.\n\nPARTIAL: caller positive concentration-ratio arithmetic only, not ocean\nacidification,carbonate chemistry,pH calculation or ecological projections.\nObservations/reference are caller values without inferred units or chemistry.\n')
Tests.test_exact_disclaimers=exact_disclaimers
