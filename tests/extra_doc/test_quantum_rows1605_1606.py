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
a=load('microwave_reflect1605');b=load('radar_delay1606')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand_scope_mix(self):
        for loads in ([25,50,100],(25,50,100)):
            self.assertEqual(a.reflection(loads,50),{'reflection':((F(-1,3),F(1,9),F(8,9)),(F(0),F(0),F(1)),(F(1,3),F(1,9),F(8,9))),'scope':'caller real-resistance reflection arithmetic only; no microwave hardware claims'})
        for rows in ([['B',1,3],('A',0,1)],[('A',0,1),['B',1,3]]):
            self.assertEqual(b.ranges(rows,10),{'ranges':(('A',F(0)),('B',F(5,3))),'minimum':F(0),'maximum':F(5,3),'scope':'caller round-trip delay distance arithmetic only; no radar detection or tracking'})
    def test_caps(self):
        a.reflection([1000000]*64,1000000);a.reflection([1],1)
        b.ranges([(str(i),1000000,1000000) for i in range(64)],1000000000);b.ranges([('a'*40,0,1)],1)
    def test_precedence(self):
        with self.assertRaises(ValueError) as c:a.reflection([],True)
        self.assertEqual(str(c.exception),'reference must be exactint1..1000000')
        with self.assertRaises(ValueError) as c:b.ranges([('a',0,1),('a',True,0)],1)
        self.assertEqual(str(c.exception),'labels must be unique')

def seeded(seed):
    def test(self):
        rng=random.Random(seed);loads=[rng.randrange(1,1000001) for _ in range(rng.randrange(1,40))];ref=rng.randrange(1,1000001);result=[]
        for load in loads:
            numerator=load-ref;denominator=load+ref;result.append((F(numerator,denominator),F(numerator**2,denominator**2),F(4*load*ref,denominator**2)))
        expected={'reflection':tuple(result),'scope':a.SCOPE};self.assertEqual(a.reflection(loads,ref),expected);self.assertEqual(a.reflection(tuple(loads),ref),expected)
        speed=rng.randrange(1,1000000001);rows=[('Ω'+str(i),rng.randrange(1000001),rng.randrange(1,1000001)) for i in range(rng.randrange(1,40))];result=tuple(sorted((name,F(num,den)*F(speed,2)) for name,num,den in rows));expected={'ranges':result,'minimum':min(x[1] for x in result),'maximum':max(x[1] for x in result),'scope':b.SCOPE};self.assertEqual(b.ranges(rows,speed),expected);self.assertEqual(b.ranges(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1])),speed),expected)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))

def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for bad in (False,True,I(1),1.,None,'1',0,1000001):
    cases.extend([(a.reflection,([bad],1),'load must be exactint1..1000000'),(a.reflection,([1],bad),'reference must be exactint1..1000000')])
for bad in ([],[1]*65,{},set(),iter([]),'x',L([1]),T((1,))):cases.append((a.reflection,(bad,1),'loads must be exactlist/tuple length1..64'))
for bad in (False,True,I(1),1.,None,'1',0,1000000001):cases.append((b.ranges,([('a',0,1)],bad),'speed must be exactint1..1000000000'))
for bad in ([],[('a',0,1)]*65,{},set(),iter([]),'x',L([('a',0,1)]),T((('a',0,1),))):cases.append((b.ranges,(bad,1),'rows must be exactlist/tuple length1..64'))
for bad in ([],[1,2],(1,2,3,4),'abc',L(['a',0,1]),T(('a',0,1))):cases.append((b.ranges,([bad],1),'row must be exactlist/tuple triple'))
for bad in ('','a'*41,'\n','\x00',S('a'),0,None):cases.append((b.ranges,([(bad,0,1)],1),'label must be exactstr printable Unicode length1..40'))
for position,low in ((1,0),(2,1)):
    for bad in (False,True,I(1),1.,None,'1',low-1,1000001):
        row=['a',0,1];row[position]=bad;cases.append((b.ranges,([row],1),('delay numerator must be exactint0..1000000' if position==1 else 'delay denominator must be exactint1..1000000')))
cases.append((b.ranges,([('a',0,1),('a',0,1)],1),'labels must be unique'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))

def charset(char):
    def test(self):b.ranges([(char,0,1)],1)
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))

def exact_disclaimers(self):
    self.assertEqual(a.__doc__,'Microwave Engineering.\n\nPARTIAL: caller real-resistance ideal reflection arithmetic only, not microwave\nengineering, complex impedance analysis, measurement or hardware performance.\nPositive resistances are caller inputs; frequency/material behavior not inferred.\n')
    self.assertEqual(b.__doc__,'Radar Systems.\n\nPARTIAL: caller round-trip delay distance arithmetic only, not radar systems,\nobject detection, tracking, propagation modeling or measurement validation.\nCaller speed and delay units must match; no physical constants or targets inferred.\n')
Tests.test_exact_disclaimers=exact_disclaimers
