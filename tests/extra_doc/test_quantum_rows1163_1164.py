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

from fractions import Fraction as F
import random
import string
a=load('chemo_budget1163');b=load('radiation_overlap1164')
class I(int):pass
class R(float):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_scope_mix_adjacent(self):
        self.assertEqual(a.budget([.1,.2],.3),{'cumulative':(F(1,10),F(3,10)),'total':F(3,10),'remaining':0,'at_or_over':(False,True),'scope':'caller dose-budget arithmetic only; no prescribing or clinical safety'})
        expected={'pairs':(('A','C',1),('B','C',1)),'union_length':4,'peak':2,'scope':'caller discrete interval overlap only; no dosimetry or treatment planning'}
        for rows in ([['A',0,2],('B',2,4),['C',1,3]],[('C',1,3),['B',2,4],('A',0,2)]):self.assertEqual(b.overlap(rows),expected)
        self.assertEqual(a.budget([0],0)['at_or_over'],(True,))
        self.assertEqual(a.budget([2,3],1)['remaining'],-4)
    def test_caps(self):
        a.budget([1000000]*64,1000000);a.budget((0,),0)
        self.assertEqual(b.overlap([('a'*40,0,100000)])['union_length'],100000)
        self.assertEqual(b.overlap([(str(i),0,1) for i in range(64)])['peak'],64)
    def test_precedence(self):
        with self.assertRaises(ValueError) as c:a.budget([],True)
        self.assertEqual(str(c.exception),'amount must be finite built-in real0..1000000')
        with self.assertRaises(ValueError) as c:b.overlap([('a',0,1),('a',False,2)])
        self.assertEqual(str(c.exception),'labels must be unique')

def oracle(seed):
    def test(self):
        rng=random.Random(seed);values=[rng.randrange(100)/10 for _ in range(rng.randrange(1,30))];cap=rng.randrange(100)/10
        fractions=list(map(lambda x:F(str(x)),values));cum=tuple(sum(fractions[:i+1],F(0)) for i in range(len(values)))
        self.assertEqual(a.budget(values,cap),{'cumulative':cum,'total':sum(fractions,F(0)),'remaining':F(str(cap))-sum(fractions,F(0)),'at_or_over':tuple(v>=F(str(cap)) for v in cum),'scope':a.SCOPE})
        rows=[]
        for i in range(rng.randrange(1,15)):
            start=rng.randrange(20);rows.append(('Ω!'+str(i),start,rng.randrange(start+1,25)))
        pairs=[]
        for left,right in itertools.combinations(sorted(rows),2):
            cells=set(range(left[1],left[2]))&set(range(right[1],right[2]))
            if cells:pairs.append((left[0],right[0],len(cells)))
        coverage=[sum(start<=x<end for _,start,end in rows) for x in range(25)]
        expected={'pairs':tuple(pairs),'union_length':sum(v>0 for v in coverage),'peak':max(coverage),'scope':b.SCOPE}
        self.assertEqual(b.overlap(rows),expected);self.assertEqual(b.overlap(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),expected)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,oracle(seed))

def reject_a(amounts,cap,message):
    def test(self):
        with self.assertRaises(ValueError) as caught:a.budget(amounts,cap)
        self.assertEqual(str(caught.exception),message)
    return test
cases=[]
for bad in (True,False,None,'1',I(1),R(1),-1,-.1,float('inf'),float('-inf'),float('nan'),1000000.5,1000001):
    cases.extend([([bad],0,'amount must be finite built-in real0..1000000'),([0],bad,'amount must be finite built-in real0..1000000')])
for bad in ([],[0]*65,{},set(),iter([0]),'x',L([0]),T((0,))):cases.append((bad,0,'amounts must be exactlist/tuple length1..64'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_a_%03d'%i,reject_a(*case))

def reject_b(rows,message):
    def test(self):
        with self.assertRaises(ValueError) as caught:b.overlap(rows)
        self.assertEqual(str(caught.exception),message)
    return test
cases=[]
for bad in ([],[('a',0,1)]*65,{},set(),iter([]),'x',L([('a',0,1)]),T((('a',0,1),))):cases.append((bad,'rows must be exactlist/tuple length1..64'))
for bad in ([],[1,2],(1,2,3,4),'abc',L(['a',0,1]),T(('a',0,1))):cases.append(([bad],'row must be exactlist/tuple triple'))
for bad in ('','a'*41,'\n','\x00',S('a'),0,None):cases.append(([(bad,0,1)],'label must be exactstr printable Unicode length1..40'))
for bad in (False,True,I(1),1.,R(1),None,'1',-1,100001):
    cases.extend([([('a',bad,2)],'endpoints must be exactint0..100000 with start<end'),([('a',0,bad)],'endpoints must be exactint0..100000 with start<end')])
cases.extend([([('a',1,1)],'endpoints must be exactint0..100000 with start<end'),([('a',2,1)],'endpoints must be exactint0..100000 with start<end'),([('a',0,1),('a',1,2)],'labels must be unique')])
for i,case in enumerate(cases):setattr(Tests,'test_refuse_b_%03d'%i,reject_b(*case))

def charset(char):
    def test(self):self.assertEqual(b.overlap([(char,0,1)])['peak'],1)
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))

def exact_disclaimers(self):
    self.assertEqual(a.__doc__,'Chemotherapy Planning.\n\nPARTIAL: caller-supplied dose-budget arithmetic only, not chemotherapy planning,\nprescribing, dose selection, eligibility or clinical safety assessment. No medical\nlimits inferred. Amounts and limits must be supplied by the caller in one unit.\n')
    self.assertEqual(b.__doc__,'Radiation Therapy Planning.\n\nPARTIAL: caller-declared discrete interval overlap arithmetic only, not radiation\ntherapy planning, dosimetry, beam geometry, treatment selection or clinical safety.\nNo patient data, dose or medical constraints inferred.\n')
Tests.test_exact_disclaimers=exact_disclaimers

def peak_initialization_proof_witness(self):
    intervals=list(itertools.combinations(range(5),2))
    for count in (1,2,3):
        for chosen in itertools.combinations_with_replacement(intervals,count):
            rows=[(str(i),start,end) for i,(start,end) in enumerate(chosen)]
            self.assertEqual(b.overlap(rows)['peak'],max(sum(start<=x<end for start,end in chosen) for x in range(5)))
Tests.test_peak_initialization_proof_witness=peak_initialization_proof_witness
