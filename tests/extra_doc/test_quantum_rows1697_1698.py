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

import random,string
from fractions import Fraction as F
a=load('epi_counts1697');b=load('justice_weights1698')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand(self):
        for rows in ([['B',2,3],('A',0,1)],[('B',2,3),['A',0,1]]):
            self.assertEqual(a.fractions(rows),{'fractions':(('A',F(0)),('B',F(2,3))),'cases':2,'population':4,'aggregate_fraction':F(1,2),'scope':'caller case-population count fractions only; no epidemiological or health claims'})
        for rows in ([['B',3,2],('A',0,1),['B',1,1]],[('B',1,1),['A',0,1],('B',3,2)]):
            self.assertEqual(b.weights(rows),{'weights':(('A',1,F(0)),('B',3,F(7,3))),'overall_mean':F(7,4),'range':F(7,3),'scope':'caller group-value-population weighted arithmetic only; no environmental justice assessment'})
    def test_caps(self):
        a.fractions([(str(i),1000000,1000000) for i in range(64)]);a.fractions([('x'*40,0,1)])
        b.weights([('x'*40,1000000,1000000)]*64)
    def test_precedence(self):
        with self.assertRaises(ValueError) as c:a.fractions([('x',1,1),('x',True,None)])
        self.assertEqual(str(c.exception),'labels must be unique')
def seeded(seed):
    def test(self):
        r=random.Random(seed);rows=[]
        for i in range(r.randrange(1,40)):
            p=r.randrange(1,1000001);rows.append(('Ω'+str(i),r.randrange(p+1),p))
        r.shuffle(rows);p=sum(p for name,c,p in rows);c=sum(c for name,c,p in rows);out={'fractions':tuple((name,F(c,p)) for name,c,p in sorted(rows)),'cases':c,'population':p,'aggregate_fraction':sum(F(c,p) for name,c,pop in rows),'scope':a.SCOPE}
        self.assertEqual(a.fractions(rows),out);self.assertEqual(a.fractions(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
        rows=[('É'+str(r.randrange(5)),r.randrange(1000001),r.randrange(1,1000001)) for i in range(r.randrange(1,40))];result=[]
        for name in sorted(set(row[0] for row in rows)):
            sub=[(v,p) for label,v,p in rows if label==name];population=sum(p for v,p in sub);result.append((name,population,sum(F(v*p,population) for v,p in sub)))
        population=sum(p for name,v,p in rows);means=sorted(v for name,p,v in result);out={'weights':tuple(result),'overall_mean':sum(F(v*p,population) for name,v,p in rows),'range':means[-1]-means[0],'scope':b.SCOPE}
        self.assertEqual(b.weights(rows),out);self.assertEqual(b.weights(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))
def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for fn,message in ((a.fractions,'counts must be exactint0<=cases<=population<=1000000 with population>0'),(b.weights,'value must be exactint0..1000000 and population exactint1..1000000')):
    row=('a',1,1)
    for bad in ([],[row]*65,{},set(),iter([]),'x',None,L([row]),T((row,))):cases.append((fn,(bad,),'rows must be exactlist/tuple length1..64'))
    for bad in ([],row[:-1],row+(0,),'abc',None,L(row),T(row)):cases.append((fn,([bad],),'row must be exactlist/tuple triple'))
    for bad in ('','x'*41,'\n','\x00',S('a'),0,None):cases.append((fn,([(bad,)+row[1:]],),'label must be exactstr printable Unicode length1..40'))
    for slot in (1,2):
        for bad in (True,False,I(0),1.,None,'1',-1,1000001):
            altered=list(row);altered[slot]=bad;cases.append((fn,([altered],),message))
    cases.append((fn,([('a',0,0)],),message))
cases.append((a.fractions,([('a',2,1)],),'counts must be exactint0<=cases<=population<=1000000 with population>0'))
cases.append((a.fractions,([('a',0,1),('a',0,1)],),'labels must be unique'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))
def charset(char):
    def test(self):a.fractions([(char,0,1)]);b.weights([(char,0,1)])
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))

def disclaimer(self):
    self.assertEqual(a.__doc__,'Epidemiology.\n\nPARTIAL: caller case/population count fractions only, not epidemiology,\nincidence prediction, causal inference, diagnosis or public-health advice.\nCaller counts are abstract, not verified cases, cohorts or surveillance data.\n')
    self.assertEqual(b.__doc__,'Environmental Justice.\n\nPARTIAL: caller group value/population weighted arithmetic only, not\n environmental justice, fairness, discrimination or policy assessment.\nCaller groups and values are abstract, not verified demographics or burdens.\n')
Tests.test_disclaimer=disclaimer
