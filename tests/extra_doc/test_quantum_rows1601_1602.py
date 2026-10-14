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
a=load('power_quality1601');b=load('emc_margin1602')
class I(int):pass
class R(float):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand_scopes_mix(self):
        for values in ([.2,.1],(.2,.1)):
            self.assertEqual(a.harmonics(values),{'fundamental_squared':F(1,25),'harmonic_squared_sum':F(1,100),'thd_squared':F(1,4),'harmonic_energy_fraction':F(1,5),'scope':'caller harmonic squared-ratio arithmetic only; no electrical compliance or safety'})
        self.assertEqual(a.harmonics([1])['thd_squared'],0)
        for rows in ([['B',.3,.2],('A',-.1,-.1)],[('A',-.1,-.1),['B',.3,.2]]):
            self.assertEqual(b.margins(rows),{'margins':(('A',F(0),True),('B',F(-1,10),False)),'minimum_margin':F(-1,10),'all_within':False,'scope':'caller numerical limit margins only; no EMC testing certification or safety'})
        self.assertTrue(b.margins([('x',0,0)])['all_within'])
    def test_caps(self):
        a.harmonics([1000000]*64);a.harmonics([.000001,0])
        b.margins([(str(i),-1000000,1000000) for i in range(64)]);b.margins([('a'*40,1000000,-1000000)])
    def test_precedence(self):
        with self.assertRaises(ValueError) as c:a.harmonics([0,True])
        self.assertEqual(str(c.exception),'amplitude must be finite built-in real0..1000000')
        with self.assertRaises(ValueError) as c:b.margins([('a',0,0),('a',True,None)])
        self.assertEqual(str(c.exception),'labels must be unique')

def seeded(seed):
    def test(self):
        rng=random.Random(seed);values=[rng.randrange(1,10001)/10]+[rng.randrange(10001)/10 for _ in range(rng.randrange(30))];squares=[F(str(x))**2 for x in values];higher=sum(squares)-squares[0];expected={'fundamental_squared':squares[0],'harmonic_squared_sum':higher,'thd_squared':sum(square/squares[0] for square in squares[1:]),'harmonic_energy_fraction':higher/sum(squares),'scope':a.SCOPE}
        self.assertEqual(a.harmonics(values),expected);self.assertEqual(a.harmonics(tuple(values)),expected)
        rows=[('Ω'+str(i),rng.randrange(-10000,10001)/10,rng.randrange(-10000,10001)/10) for i in range(rng.randrange(1,40))];result=tuple(sorted((name,F(str(limit))-F(str(measured)),F(str(measured))<=F(str(limit))) for name,measured,limit in rows));expected={'margins':result,'minimum_margin':min(x[1] for x in result),'all_within':not any(measured>limit for _,measured,limit in rows),'scope':b.SCOPE}
        self.assertEqual(b.margins(rows),expected);self.assertEqual(b.margins(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),expected)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))

def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for bad in ([],[1]*65,{},set(),iter([]),'x',L([1]),T((1,))):cases.append((a.harmonics,(bad,),'values must be exactlist/tuple length1..64'))
for bad in (True,False,None,'1',I(1),R(1),-1,float('inf'),float('-inf'),float('nan'),1000000.5,1000001):
    cases.extend([(a.harmonics,([bad],),'amplitude must be finite built-in real0..1000000'),(a.harmonics,([1,bad],),'amplitude must be finite built-in real0..1000000')])
cases.append((a.harmonics,([0],),'fundamental must be positive'))
for bad in ([],[('a',0,0)]*65,{},set(),iter([]),'x',L([('a',0,0)]),T((('a',0,0),))):cases.append((b.margins,(bad,),'rows must be exactlist/tuple length1..64'))
for bad in ([],[1,2],(1,2,3,4),'abc',L(['a',0,0]),T(('a',0,0))):cases.append((b.margins,([bad],),'row must be exactlist/tuple triple'))
for bad in ('','a'*41,'\n','\x00',S('a'),0,None):cases.append((b.margins,([(bad,0,0)],),'label must be exactstr printable Unicode length1..40'))
for position in (1,2):
    for bad in (True,False,None,'1',I(1),R(1),float('inf'),float('-inf'),float('nan'),-1000001,1000001):
        row=['a',0,0];row[position]=bad;cases.append((b.margins,([row],),'number must be finite built-in real-1000000..1000000'))
cases.append((b.margins,([('a',0,0),('a',0,0)],),'labels must be unique'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))

def charset(char):
    def test(self):b.margins([(char,0,0)])
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))

def exact_disclaimers(self):
    self.assertEqual(a.__doc__,'Power Quality.\n\nPARTIAL: caller harmonic-amplitude ratio arithmetic only, not power-quality\nmeasurement, electrical compliance, transient analysis or equipment safety.\nAmplitudes supplied by caller; no waveform sampling, hardware or limits inferred.\n')
    self.assertEqual(b.__doc__,'Electromagnetic Compatibility.\n\nPARTIAL: caller numeric measurement/limit margin arithmetic only, not EMC\nassessment, testing, emissions prediction, certification or equipment safety.\nValues/limits must be caller inputs in matching units and test conditions.\n')
Tests.test_exact_disclaimers=exact_disclaimers
