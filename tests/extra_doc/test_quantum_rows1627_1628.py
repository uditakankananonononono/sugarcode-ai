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
a=load('attribution_ratios1627');b=load('mitigation_subsets1628')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand_scopes_mix(self):
        self.assertEqual(a.ratio([1,2],(1,4)),{'left_frequency':F(1,2),'right_frequency':F(1,4),'ratio':F(2),'relative_fraction':F(1,2),'scope':'caller event-frequency ratios only; no causal climate attribution claims'})
        self.assertEqual(a.ratio((1,4),[1,2])['relative_fraction'],-1)
        for rows in ([['B',1,2],('A',1,2)],[('A',1,2),['B',1,2]]):
            self.assertEqual(b.options(rows,1),{'feasible':(((),0,0),(('A',),1,2),(('B',),1,2)),'best_value':2,'ties':(('A',),('B',)),'scope':'caller option cost/value subsets only; no mitigation impacts or policy advice'})
        self.assertEqual(b.options([],0)['ties'],((),));self.assertEqual(b.options([('x',0,0)],0)['ties'],((),('x',)))
    def test_caps(self):
        a.ratio([1000000,1000000],(1,1));self.assertEqual(len(b.options([(str(i),1000000,1000000) for i in range(12)],12000000)['feasible']),4096);b.options([('a'*40,0,0)],0)
    def test_precedence(self):
        with self.assertRaises(ValueError) as c:a.ratio([], [True,0])
        self.assertEqual(str(c.exception),'count pair must be exactlist/tuple pair')
        with self.assertRaises(ValueError) as c:b.options({},True)
        self.assertEqual(str(c.exception),'budget must be exactint0..12000000')
        with self.assertRaises(ValueError) as c:b.options([('a',0,0),('a',True,None)],0)
        self.assertEqual(str(c.exception),'labels must be unique')

def seeded(seed):
    def test(self):
        rng=random.Random(seed);lt=rng.randrange(1,1000001);rt=rng.randrange(1,1000001);lc=rng.randrange(1,lt+1);rc=rng.randrange(1,rt+1);out={'left_frequency':F(lc,lt),'right_frequency':F(rc,rt),'ratio':F(lc*rt,lt*rc),'relative_fraction':F(lc*rt-rc*lt,lc*rt),'scope':a.SCOPE};self.assertEqual(a.ratio([lc,lt],(rc,rt)),out)
        rows=[('Ω'+str(i),rng.randrange(30),rng.randrange(30)) for i in range(rng.randrange(9))];budget=rng.randrange(100);feasible=[]
        for size in range(len(rows)+1):
            for selected in itertools.combinations(rows,size):
                cost=sum(c for _,c,v in selected)
                if cost<=budget:feasible.append((tuple(sorted(name for name,c,v in selected)),cost,sum(v for name,c,v in selected)))
        feasible.sort();best=max(v for names,c,v in feasible);out={'feasible':tuple(feasible),'best_value':best,'ties':tuple(names for names,c,v in feasible if v==best),'scope':b.SCOPE};self.assertEqual(b.options(rows,budget),out);self.assertEqual(b.options(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1])),budget),out)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))
def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for position in (0,1):
    for bad in ([],[1],(1,2,3),'ab',L([1,1]),T((1,1))):
        args=[[1,1],[1,1]];args[position]=bad;cases.append((a.ratio,tuple(args),'count pair must be exactlist/tuple pair'))
    for slot in (0,1):
        for bad in (False,True,I(1),1.,None,'1',0,1000001):
            args=[[1,2],[1,2]];args[position][slot]=bad;cases.append((a.ratio,tuple(args),'counts must be exactint1<=count<=total<=1000000'))
    args=[[1,1],[1,1]];args[position]=[2,1];cases.append((a.ratio,tuple(args),'counts must be exactint1<=count<=total<=1000000'))
for bad in (False,True,I(1),1.,None,'1',-1,12000001):cases.append((b.options,([],bad),'budget must be exactint0..12000000'))
for bad in ([('a',0,0)]*13,{},set(),iter([]),'x',L([]),T(())):cases.append((b.options,(bad,0),'rows must be exactlist/tuple atmost12'))
for bad in ([],[1,2],(1,2,3,4),'abc',L(['a',0,0]),T(('a',0,0))):cases.append((b.options,([bad],0),'row must be exactlist/tuple triple'))
for bad in ('','a'*41,'\n','\x00',S('a'),0,None):cases.append((b.options,([(bad,0,0)],0),'label must be exactstr printable Unicode length1..40'))
for slot in (1,2):
    for bad in (False,True,I(1),1.,None,'1',-1,1000001):
        row=['a',0,0];row[slot]=bad;cases.append((b.options,([row],0),'cost and value must be exactint0..1000000'))
cases.append((b.options,([('a',0,0),('a',0,0)],0),'labels must be unique'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))
def charset(char):
    def test(self):b.options([(char,0,0)],0)
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))

def exact_disclaimers(self):
    self.assertEqual(a.__doc__,'Climate Attribution.\n\nPARTIAL: caller event-frequency ratio arithmetic only, not climate attribution,\ncausal inference,observational estimates or scientific confidence statements.\nTwo count pairs are caller declarations,not validated factual/counterfactual data.\n')
    self.assertEqual(b.__doc__,'Mitigation Strategies.\n\nPARTIAL: caller option cost/value subset arithmetic only, not mitigation\nstrategies,emissions savings,financial evaluation or policy recommendations.\nCosts/values/budget are abstract caller units,not verified impacts or spending.\n')
Tests.test_exact_disclaimers=exact_disclaimers
