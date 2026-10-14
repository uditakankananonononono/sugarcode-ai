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
a=load('information_collision1613');b=load('code_distance1614')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand_scope(self):
        self.assertEqual(a.collision([1,2,0]),{'collision':F(5,9),'inverse_collision':F(9,5),'positive_categories':2,'total':3,'scope':'caller discrete count collision arithmetic only; no source or coding performance claims'})
        for words in (['111','000'],('000','111')):
            self.assertEqual(b.distances(words),{'pairs':(('000','111',3),),'minimum_distance':3,'disjoint_ball_radius':1,'scope':'caller binary codebook distances only; no encoding decoding or channel reliability'})
        self.assertEqual(b.distances(['0','1'])['disjoint_ball_radius'],0)
    def test_caps(self):
        a.collision([1000000]*64);a.collision([1]);b.distances([format(i,'064b') for i in range(32)])
        self.assertEqual(b.distances(['0'*64,'1'*64])['minimum_distance'],64)
    def test_precedence(self):
        with self.assertRaises(ValueError) as c:a.collision([0,True])
        self.assertEqual(str(c.exception),'count must be exactint0..1000000')
        with self.assertRaises(ValueError) as c:b.distances(['0','0','11'])
        self.assertEqual(str(c.exception),'words must be unique')

def seeded(seed):
    def test(self):
        rng=random.Random(seed);counts=[rng.randrange(100) for _ in range(rng.randrange(1,40))];counts[0]+=1;total=sum(counts);p=sum((F(count,total)**2 for count in counts),F(0));expected={'collision':p,'inverse_collision':F(1)/p,'positive_categories':len([x for x in counts if x]),'total':total,'scope':a.SCOPE};self.assertEqual(a.collision(counts),expected);self.assertEqual(a.collision(tuple(counts[::-1])),expected)
        width=rng.randrange(1,15);numbers=rng.sample(range(1<<width),rng.randrange(2,min(20,1<<width)+1));words=[format(x,'0'+str(width)+'b') for x in numbers];pairs=[]
        for left,right in itertools.combinations(sorted(words),2):pairs.append((left,right,bin(int(left,2)^int(right,2)).count('1')))
        minimum=min(x[2] for x in pairs);radius=max(r for r in range(width+1) if 2*r<minimum);expected={'pairs':tuple(pairs),'minimum_distance':minimum,'disjoint_ball_radius':radius,'scope':b.SCOPE};self.assertEqual(b.distances(words),expected);self.assertEqual(b.distances(tuple(words[::-1])),expected)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))

def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for bad in ([],[0]*65,{},set(),iter([]),'x',L([1]),T((1,))):cases.append((a.collision,(bad,),'counts must be exactlist/tuple length1..64'))
for bad in (False,True,I(1),1.,None,'1',-1,1000001):cases.append((a.collision,([bad],),'count must be exactint0..1000000'))
cases.append((a.collision,([0],),'count total must be positive'))
for bad in ([],['0'],['0']*33,{},set(),iter([]),'x',L(['0','1']),T(('0','1'))):cases.append((b.distances,(bad,),'words must be exactlist/tuple length2..32'))
for bad in ('','0'*65,'2',' 0','\n',S('0'),0,None,True):
    for words in ([bad,'1'],['0',bad]):cases.append((b.distances,(words,),'word must be exactstr binary length1..64'))
cases.extend([(b.distances,(['0','0'],),'words must be unique'),(b.distances,(['0','11'],),'words must have equal width')])
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))

def exact_disclaimers(self):
    self.assertEqual(a.__doc__,'Information Theory.\n\nPARTIAL: caller discrete count collision arithmetic only, not information-theory\ncoverage,Shannon entropy,source modeling or coding performance. Counts supplied\nby caller; no statistical population or independence assumptions validated.\n')
    self.assertEqual(b.__doc__,'Coding Theory.\n\nPARTIAL: caller binary codebook Hamming distances only, not coding-theory\ncoverage, encoder/decoder, channel reliability or error-correction execution.\nCodewords are caller declarations with no channel or protocol assumptions.\n')
Tests.test_exact_disclaimers=exact_disclaimers
