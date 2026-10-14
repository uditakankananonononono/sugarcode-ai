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
from math import prod
a=load('grid_slots1609');b=load('optical_loss1610')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand_scope_mix(self):
        for rows in ([[0,1,0,2],(0,2,1,2)],[(0,2,1,2),[0,1,0,2]]):
            self.assertEqual(a.occupancy(rows,2,2),{'occupied':((0,0),(0,1),(1,1)),'free_count':1,'occupied_fraction':F(3,4),'scope':'caller abstract resource-grid occupancy only; no 5G/6G radio or protocol claims'})
        self.assertEqual(a.occupancy([],1,1)['free_count'],1)
        for rows in ([['B',1,2],('A',1,3)],[('B',1,2),['A',1,3]]):
            self.assertEqual(b.transmission(rows),{'stages':(('B',F(1,2)),('A',F(1,6))),'transmission':F(1,6),'loss':F(5,6),'scope':'caller transmission-factor product only; no optical performance or rate claims'})
        self.assertEqual(b.transmission([])['loss'],0);self.assertEqual(b.transmission([('x',0,1)])['transmission'],0)
    def test_caps(self):
        self.assertEqual(len(a.occupancy([(0,32,0,32)]*64,32,32)['occupied']),1024)
        b.transmission([(str(i),1000000,1000000) for i in range(64)]);b.transmission([('a'*40,1,1)])
    def test_precedence(self):
        with self.assertRaises(ValueError) as c:a.occupancy({},True,1)
        self.assertEqual(str(c.exception),'grid dimensions must be exactint1..32')
        with self.assertRaises(ValueError) as c:b.transmission([('a',1,1),('a',True,0)])
        self.assertEqual(str(c.exception),'labels must be unique')

def seeded(seed):
    def test(self):
        rng=random.Random(seed);slots=rng.randrange(1,10);carriers=rng.randrange(1,10);rows=[]
        for _ in range(rng.randrange(30)):
            lo=rng.randrange(slots);left=rng.randrange(carriers);rows.append((lo,rng.randrange(lo+1,slots+1),left,rng.randrange(left+1,carriers+1)))
        cells=tuple((x,y) for x in range(slots) for y in range(carriers) if any(lo<=x<hi and left<=y<right for lo,hi,left,right in rows));out={'occupied':cells,'free_count':slots*carriers-len(cells),'occupied_fraction':F(len(cells),slots*carriers),'scope':a.SCOPE};self.assertEqual(a.occupancy(rows,slots,carriers),out);self.assertEqual(a.occupancy(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1])),slots,carriers),out)
        rows=[]
        for i in range(rng.randrange(40)):
            den=rng.randrange(1,1000001);rows.append(('Ω'+str(i),rng.randrange(den+1),den))
        stages=tuple((name,F(prod(n for _,n,d in rows[:i+1]),prod(d for _,n,d in rows[:i+1]))) for i,(name,num,den) in enumerate(rows));final=F(prod(n for _,n,d in rows),prod(d for _,n,d in rows));out={'stages':stages,'transmission':final,'loss':1-final,'scope':b.SCOPE};self.assertEqual(b.transmission(rows),out);self.assertEqual(b.transmission(tuple(list(row) if i%2 else row for i,row in enumerate(rows))),out)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))

def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for position in (1,2):
    for bad in (False,True,I(1),1.,None,'1',0,33):
        args=[[],1,1];args[position]=bad;cases.append((a.occupancy,tuple(args),'grid dimensions must be exactint1..32'))
for bad in ([(0,1,0,1)]*65,{},set(),iter([]),'x',L([]),T(())):cases.append((a.occupancy,(bad,1,1),'rows must be exactlist/tuple atmost64'))
for bad in ([],[1,2,3],(1,2,3,4,5),'abcd',L([0,1,0,1]),T((0,1,0,1))):cases.append((a.occupancy,([bad],1,1),'row must be exactlist/tuple four values'))
for position in range(4):
    for bad in (False,True,I(1),1.,None,'1',-1,3):
        row=[0,2,0,2];row[position]=bad;cases.append((a.occupancy,([row],2,2),'rectangle endpoints must be exactint positive spans inside grid'))
for row in ((0,0,0,1),(1,0,0,1),(0,1,1,1),(0,1,2,1)):cases.append((a.occupancy,([row],2,2),'rectangle endpoints must be exactint positive spans inside grid'))
for bad in ([('a',1,1)]*65,{},set(),iter([]),'x',L([]),T(())):cases.append((b.transmission,(bad,),'rows must be exactlist/tuple atmost64'))
for bad in ([],[1,2],(1,2,3,4),'abc',L(['a',1,1]),T(('a',1,1))):cases.append((b.transmission,([bad],),'row must be exactlist/tuple triple'))
for bad in ('','a'*41,'\n','\x00',S('a'),0,None):cases.append((b.transmission,([(bad,1,1)],),'label must be exactstr printable Unicode length1..40'))
for position in (1,2):
    for bad in (False,True,I(1),1.,None,'1',-1,1000001):
        row=['a',0,1];row[position]=bad;cases.append((b.transmission,([row],),'factor components must be exactint0<=num<=den<=1000000 and den>0'))
for row in (('a',0,0),('a',2,1)):cases.append((b.transmission,([row],),'factor components must be exactint0<=num<=den<=1000000 and den>0'))
cases.append((b.transmission,([('a',1,1),('a',1,1)],),'labels must be unique'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))

def charset(char):
    def test(self):b.transmission([(char,1,1)])
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))

def exact_disclaimers(self):
    self.assertEqual(a.__doc__,'5G/6G.\n\nPARTIAL: caller rectangular resource-grid occupancy only, not5G/6G protocol,\nradio simulation, throughput, interference or standards compliance. Abstract\nslot/subcarrier coordinates and reservations are caller declarations.\n')
    self.assertEqual(b.__doc__,'Optical Communications.\n\nPARTIAL: caller multiplicative transmission-factor arithmetic only, not optical\ncommunications, attenuation measurement, fiber modeling or achievable rates.\nFactors are caller declarations, no wavelengths/materials or physics inferred.\n')
Tests.test_exact_disclaimers=exact_disclaimers
