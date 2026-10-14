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
from fractions import Fraction as F
a=load('satellite_paths1611');b=load('deep_retry1612')
class I(int):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand_scopes(self):
        for lengths in ([1,2],(1,2)):
            self.assertEqual(a.delay(lengths,2),{'segment_delays':(F(1,2),F(1)),'one_way':F(3,2),'doubled':F(3),'scope':'caller path-length propagation arithmetic only; no satellite visibility or link claims'})
        self.assertEqual(a.delay([0],1)['one_way'],0)
        self.assertEqual(b.retries(1,2,2,3),{'first_success':((1,F(1,2)),(2,F(1,4))),'exhausted':F(1,4),'expected_attempts':F(3,2),'expected_ticks':F(9,2),'scope':'caller independent retry arithmetic only; no space-channel or mission reliability claims'})
        self.assertEqual(b.retries(0,1,2,0)['expected_attempts'],2);self.assertEqual(b.retries(1,1,2,1)['expected_attempts'],1)
    def test_caps(self):
        a.delay([1000000000000]*64,1000000000)
        b.retries(1000000,1000000,64,1000000);b.retries(0,1,1,0)
    def test_precedence(self):
        with self.assertRaises(ValueError) as c:a.delay([],True)
        self.assertEqual(str(c.exception),'speed must be exactint1..1000000000')
        with self.assertRaises(ValueError) as c:b.retries(True,0,False,None)
        self.assertEqual(str(c.exception),'success components must be exactint0<=num<=den<=1000000 and den>0')

def seeded(seed):
    def test(self):
        rng=random.Random(seed);lengths=[rng.randrange(1000000000001) for _ in range(rng.randrange(1,40))];speed=rng.randrange(1,1000000001);total=F(sum(lengths),speed);out={'segment_delays':tuple(F(x,speed) for x in lengths),'one_way':total,'doubled':F(2*sum(lengths),speed),'scope':a.SCOPE};self.assertEqual(a.delay(lengths,speed),out);self.assertEqual(a.delay(tuple(lengths),speed),out)
        den=rng.randrange(1,1001);num=rng.randrange(den+1);attempts=rng.randrange(1,15);ticks=rng.randrange(1000001);p=F(num,den);q=1-p;first=tuple((i,p*q**(i-1)) for i in range(1,attempts+1));exhausted=q**attempts;expected=sum(i*prob for i,prob in first)+attempts*exhausted;out={'first_success':first,'exhausted':exhausted,'expected_attempts':expected,'expected_ticks':expected*ticks,'scope':b.SCOPE};self.assertEqual(b.retries(num,den,attempts,ticks),out);self.assertEqual(sum(prob for i,prob in first)+exhausted,1)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))

def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for bad in (False,True,I(1),1.,None,'1',0,1000000001):cases.append((a.delay,([0],bad),'speed must be exactint1..1000000000'))
for bad in (False,True,I(1),1.,None,'1',-1,1000000000001):cases.append((a.delay,([bad],1),'length must be exactint0..1000000000000'))
for bad in ([],[0]*65,{},set(),iter([]),'x',L([0]),T((0,))):cases.append((a.delay,(bad,1),'lengths must be exactlist/tuple length1..64'))
for position in (0,1):
    for bad in (False,True,I(1),1.,None,'1',-1,1000001):
        args=[0,1,1,0];args[position]=bad;cases.append((b.retries,tuple(args),'success components must be exactint0<=num<=den<=1000000 and den>0'))
for args in ((0,0,1,0),(2,1,1,0)):cases.append((b.retries,args,'success components must be exactint0<=num<=den<=1000000 and den>0'))
for position,low,cap in ((2,1,64),(3,0,1000000)):
    for bad in (False,True,I(1),1.,None,'1',low-1,cap+1):
        args=[0,1,1,0];args[position]=bad;cases.append((b.retries,tuple(args),('attempts must be exactint1..64' if position==2 else 'roundtrip_ticks must be exactint0..1000000')))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))

def exact_disclaimers(self):
    self.assertEqual(a.__doc__,'Satellite Communications.\n\nPARTIAL: caller path-length propagation arithmetic only, not satellite\ncommunications, ephemerides, visibility, link feasibility or actual latency.\nDistances/speed supplied by caller;processing,queuing and geometry omitted.\n')
    self.assertEqual(b.__doc__,'Deep Space Communications.\n\nPARTIAL: caller independent retry probability arithmetic only, not deep-space\ncommunications, mission reliability, measured channels or operational decisions.\nSuccess probability/delay/attempt cap are caller inputs; independence is a toy\nassumption, not a validated space-channel model.\n')
Tests.test_exact_disclaimers=exact_disclaimers
