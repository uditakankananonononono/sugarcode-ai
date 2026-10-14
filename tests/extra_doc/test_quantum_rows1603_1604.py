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
a=load('antenna_length1603');b=load('rf_budget1604')
class I(int):pass
class R(float):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand_scopes_mix(self):
        for values in ([3,2],(2,3)):
            self.assertEqual(a.lengths(values,10,1,2),{'lengths':((2,F(5),F(5,2)),(3,F(10,3),F(5,3))),'scope':'caller ideal wavelength-length arithmetic only; no antenna performance claims'})
        for rows in ([['B',-.2],('A',.1)],[('B',-.2),['A',.1]]):
            self.assertEqual(b.budget(rows,.3,.2),{'stages':(('B',F(1,10)),('A',F(1,5))),'final':F(1,5),'margin':F(0),'within':True,'scope':'caller signed additive link budget only; no RF propagation or compliance claims'})
        self.assertFalse(b.budget([],0,1)['within']);self.assertEqual(b.budget([],1,0)['stages'],())
    def test_caps(self):
        a.lengths(list(range(1,65)),1000000000,1000,1000);a.lengths([1000000000000],1,1,1)
        b.budget([(str(i),1000000) for i in range(64)],1000000,-1000000);b.budget([('a'*40,-1000000)],-1000000,1000000)
    def test_precedence(self):
        with self.assertRaises(ValueError) as c:a.lengths([],True,True,0)
        self.assertEqual(str(c.exception),'speed must be exactint1..1000000000')
        with self.assertRaises(ValueError) as c:b.budget([],True,0)
        self.assertEqual(str(c.exception),'number must be finite built-in real-1000000..1000000')
        with self.assertRaises(ValueError) as c:b.budget([('a',0),('a',True)],0,0)
        self.assertEqual(str(c.exception),'labels must be unique')

def seeded(seed):
    def test(self):
        rng=random.Random(seed);freqs=rng.sample(range(1,10000),rng.randrange(1,40));speed=rng.randrange(1,1000000001);num=rng.randrange(1,1001);den=rng.randrange(1,1001);result=tuple((f,F(speed,f),F(speed*num,f*den)) for f in sorted(freqs));out={'lengths':result,'scope':a.SCOPE};self.assertEqual(a.lengths(freqs,speed,num,den),out);self.assertEqual(a.lengths(tuple(freqs[::-1]),speed,num,den),out)
        rows=[('Ω'+str(i),rng.randrange(-10000,10001)/10) for i in range(rng.randrange(40))];initial=rng.randrange(-10000,10001)/10;threshold=rng.randrange(-10000,10001)/10;ref=F(str(initial));stages=tuple((name,ref+sum(F(str(value)) for _,value in rows[:i+1])) for i,(name,value) in enumerate(rows));final=ref+sum(F(str(value)) for _,value in rows);out={'stages':stages,'final':final,'margin':final-F(str(threshold)),'within':final-F(str(threshold))>=0,'scope':b.SCOPE};self.assertEqual(b.budget(rows,initial,threshold),out);self.assertEqual(b.budget(tuple(list(row) if i%2 else row for i,row in enumerate(rows)),initial,threshold),out)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))

def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for position,cap in ((0,1000000000000),(1,1000000000),(2,1000),(3,1000)):
    for bad in (False,True,I(1),1.,None,'1',0,cap+1):
        args=[[1],1,1,1]
        if position==0:args[0]=[bad]
        else:args[position]=bad
        message=('frequency must be exactint1..1000000000000' if position==0 else 'speed must be exactint1..1000000000' if position==1 else 'scale components must be exactint1..1000');cases.append((a.lengths,tuple(args),message))
for bad in ([],[1]*65,{},set(),iter([]),'x',L([1]),T((1,))):cases.append((a.lengths,(bad,1,1,1),'frequencies must be exactlist/tuple length1..64'))
cases.append((a.lengths,([1,1],1,1,1),'frequencies must be unique'))
for bad in ([('a',0)]*65,{},set(),iter([]),'x',L([]),T(())):cases.append((b.budget,(bad,0,0),'rows must be exactlist/tuple atmost64'))
for bad in ([],[1],(1,2,3),'ab',L(['a',0]),T(('a',0))):cases.append((b.budget,([bad],0,0),'row must be exactlist/tuple pair'))
for bad in ('','a'*41,'\n','\x00',S('a'),0,None):cases.append((b.budget,([(bad,0)],0,0),'label must be exactstr printable Unicode length1..40'))
for position in (0,1,2):
    for bad in (True,False,None,'1',I(1),R(1),float('inf'),float('-inf'),float('nan'),-1000001,1000001):
        args=[[('a',0)],0,0]
        if position==0:args[0]=[('a',bad)]
        else:args[position]=bad
        cases.append((b.budget,tuple(args),'number must be finite built-in real-1000000..1000000'))
cases.append((b.budget,([('a',0),('a',0)],0,0),'labels must be unique'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))

def charset(char):
    def test(self):b.budget([(char,0)],0,0)
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))

def exact_disclaimers(self):
    self.assertEqual(a.__doc__,'Antenna Design.\n\nPARTIAL: caller propagation-speed/frequency ideal length arithmetic only, not\nantenna design, resonance prediction, impedance matching, radiation efficiency\nor hardware validation. Speed/scale supplied by caller; no material constants.\n')
    self.assertEqual(b.__doc__,'RF Engineering.\n\nPARTIAL: caller declared signed additive link-budget arithmetic only, not RF\nengineering, measured propagation, range prediction, regulatory compliance or\nhardware safety. Units and gains/losses are caller declarations, not inferred.\n')
Tests.test_exact_disclaimers=exact_disclaimers
