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
a=load('comm_frames1607');b=load('wireless_shares1608')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand_scopes_mix(self):
        for payloads in ([0,2,3],(0,2,3)):
            self.assertEqual(a.frames(payloads,2,1),{'frames':((0,0,0),(2,1,3),(3,2,5)),'payload_total':5,'wire_total':8,'frame_count':3,'useful_fraction':F(5,8),'scope':'caller frame overhead arithmetic only; no communication performance claims'})
        self.assertIsNone(a.frames([0],1,0)['useful_fraction']);self.assertEqual(a.frames([1],1,0)['useful_fraction'],1)
        for rows in ([['B',2],('A',1)],[('A',1),['B',2]]):
            self.assertEqual(b.shares(rows,10),{'shares':(('A',F(1,3),F(10,3)),('B',F(2,3),F(20,3))),'capacity':10,'scope':'caller weighted resource shares only; no wireless scheduling or rate claims'})
        self.assertEqual(b.shares([('a',1)],0)['shares'],(('a',1,0),))
    def test_caps(self):
        a.frames([1000000]*64,1000000,1000000);a.frames([0],1,0)
        b.shares([(str(i),1000000) for i in range(64)],1000000);b.shares([('a'*40,1)],0)
    def test_precedence(self):
        with self.assertRaises(ValueError) as c:a.frames([],True,True)
        self.assertEqual(str(c.exception),'capacity must be exactint1..1000000')
        with self.assertRaises(ValueError) as c:b.shares([('a',1),('a',False)],0)
        self.assertEqual(str(c.exception),'labels must be unique')

def seeded(seed):
    def test(self):
        rng=random.Random(seed);payloads=[rng.randrange(1000001) for _ in range(rng.randrange(1,40))];cap=rng.randrange(1,1000001);over=rng.randrange(1000001);result=[]
        for payload in payloads:
            q,r=divmod(payload,cap);count=q+(1 if r else 0);result.append((payload,count,payload+count*over))
        total=sum(payloads);wire=sum(x[2] for x in result);out={'frames':tuple(result),'payload_total':total,'wire_total':wire,'frame_count':sum(x[1] for x in result),'useful_fraction':F(total,wire) if wire else None,'scope':a.SCOPE};self.assertEqual(a.frames(payloads,cap,over),out);self.assertEqual(a.frames(tuple(payloads),cap,over),out)
        rows=[('Ω'+str(i),rng.randrange(1,1000001)) for i in range(rng.randrange(1,40))];cap=rng.randrange(1000001);weights=sum(w for _,w in rows);result=tuple(sorted((name,F(w,weights),F(w,weights)*cap) for name,w in rows));out={'shares':result,'capacity':cap,'scope':b.SCOPE};self.assertEqual(b.shares(rows,cap),out);self.assertEqual(b.shares(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1])),cap),out);self.assertEqual(sum(x[2] for x in result),cap)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))

def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for position,low in ((0,0),(1,1),(2,0)):
    for bad in (False,True,I(1),1.,None,'1',low-1,1000001):
        args=[[0],1,0]
        if position==0:args[0]=[bad]
        else:args[position]=bad
        name=('payload','capacity','overhead')[position];cases.append((a.frames,tuple(args),name+' must be exactint'+str(low)+'..1000000'))
for bad in ([],[0]*65,{},set(),iter([]),'x',L([0]),T((0,))):cases.append((a.frames,(bad,1,0),'payloads must be exactlist/tuple length1..64'))
for bad in (False,True,I(1),1.,None,'1',-1,1000001):cases.append((b.shares,([('a',1)],bad),'capacity must be exactint0..1000000'))
for bad in ([],[('a',1)]*65,{},set(),iter([]),'x',L([('a',1)]),T((('a',1),))):cases.append((b.shares,(bad,0),'rows must be exactlist/tuple length1..64'))
for bad in ([],[1],(1,2,3),'ab',L(['a',1]),T(('a',1))):cases.append((b.shares,([bad],0),'row must be exactlist/tuple pair'))
for bad in ('','a'*41,'\n','\x00',S('a'),0,None):cases.append((b.shares,([(bad,1)],0),'label must be exactstr printable Unicode length1..40'))
for bad in (False,True,I(1),1.,None,'1',0,1000001):cases.append((b.shares,([('a',bad)],0),'weight must be exactint1..1000000'))
cases.append((b.shares,([('a',1),('a',1)],0),'labels must be unique'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))

def charset(char):
    def test(self):b.shares([(char,1)],0)
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))

def exact_disclaimers(self):
    self.assertEqual(a.__doc__,'Communications Systems.\n\nPARTIAL: caller payload/frame overhead arithmetic only, not communications\nsystems, transmission simulation, throughput prediction or protocol compliance.\nFrame capacity/overhead supplied by caller; no headers or real network inferred.\n')
    self.assertEqual(b.__doc__,'Wireless Communications.\n\nPARTIAL: caller weighted resource-share arithmetic only, not wireless\ncommunications, airtime scheduling, interference modeling or achievable rates.\nWeights/capacity are caller abstractions; no actual radio resources allocated.\n')
Tests.test_exact_disclaimers=exact_disclaimers
