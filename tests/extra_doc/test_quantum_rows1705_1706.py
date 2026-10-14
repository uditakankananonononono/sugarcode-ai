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
a=load('impact_products1705');b=load('strategic_weights1706')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand(self):
        for rows in ([['B',2,3,4],('A',0,1,1)],[('B',2,3,4),['A',0,1,1]]):
            self.assertEqual(a.impacts(rows),{'impacts':(('A',0),('B',24)),'total':24,'zero':('A',),'scope':'caller magnitude-extent-duration products only; no environmental impact assessment'})
        for rows in ([['B','x',2,3],('A','x',0,1),['B','y',1,1]],[('B','y',1,1),['A','x',0,1],('B','x',2,3)]):
            self.assertEqual(b.scores(rows),{'terms':(('A','x',0),('B','x',6),('B','y',1)),'totals':(('A',0),('B',7)),'scope':'caller alternative-criterion weighted-score ledger only; no strategic environmental assessment'})
        self.assertEqual(a.impacts([('x',1,1,1)])['zero'],())
    def test_caps(self):
        a.impacts([(str(i),1000000,1000000,1000000) for i in range(64)]);a.impacts([('x'*40,0,0,0)])
        b.scores([('x'*40,str(i),1000000,1000000) for i in range(64)]);b.scores([('x','y'*40,0,0)])
    def test_precedence(self):
        with self.assertRaises(ValueError) as c:a.impacts([('x',1,1,1),('x',True,None,None)])
        self.assertEqual(str(c.exception),'labels must be unique')
        with self.assertRaises(ValueError) as c:b.scores([('x','y',1,1),('x','y',True,None)])
        self.assertEqual(str(c.exception),'alternative/criterion pairs must be unique')
def seeded(seed):
    def test(self):
        r=random.Random(seed);rows=[('Ω'+str(i),r.randrange(1000001),r.randrange(1000001),r.randrange(1000001)) for i in range(r.randrange(1,40))];r.shuffle(rows);result=tuple((name,x*(y*z)) for name,x,y,z in sorted(rows));out={'impacts':result,'total':sum(v for name,v in result),'zero':tuple(name for name,x,y,z in sorted(rows) if not x or not y or not z),'scope':a.SCOPE}
        self.assertEqual(a.impacts(rows),out);self.assertEqual(a.impacts(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
        rows=[('É'+str(r.randrange(5)),'中'+str(i),r.randrange(1000001),r.randrange(1000001)) for i in range(r.randrange(1,40))];r.shuffle(rows);out={'terms':tuple((name,c,w*v) for name,c,w,v in sorted(rows)),'totals':tuple((name,sum(w*v for label,c,w,v in rows if label==name)) for name in sorted(set(row[0] for row in rows))),'scope':b.SCOPE}
        self.assertEqual(b.scores(rows),out);self.assertEqual(b.scores(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))
def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for fn,row in ((a.impacts,('a',1,1,1)),(b.scores,('a','b',1,1))):
    for bad in ([],[row]*65,{},set(),iter([]),'x',None,L([row]),T((row,))):cases.append((fn,(bad,),'rows must be exactlist/tuple length1..64'))
    for bad in ([],row[:-1],row+(0,),'abcd',None,L(row),T(row)):cases.append((fn,([bad],),'row must be exactlist/tuple quadruple'))
    for slot,name in ((0,'label'),) if fn==a.impacts else ((0,'alternative'),(1,'criterion')):
        for bad in ('','x'*41,'\n','\x00',S('a'),0,None):
            altered=list(row);altered[slot]=bad;cases.append((fn,([altered],),name+' must be exactstr printable Unicode length1..40'))
    for slot in (1,2,3) if fn==a.impacts else (2,3):
        for bad in (True,False,I(0),1.,None,'1',-1,1000001):
            altered=list(row);altered[slot]=bad;cases.append((fn,([altered],),'scores must be exactint0..1000000' if fn==a.impacts else 'weights and scores must be exactint0..1000000'))
    cases.append((fn,([row,row],),'labels must be unique' if fn==a.impacts else 'alternative/criterion pairs must be unique'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))
def charset(char):
    def test(self):a.impacts([(char,0,0,0)]);b.scores([(char,'x',0,0)]);b.scores([('x',char,0,0)])
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))

def disclaimer(self):
    self.assertEqual(a.__doc__,'Environmental Impact Assessment.\n\nPARTIAL: caller magnitude/extent/duration score arithmetic only, not an\n environmental impact assessment, significance finding or regulatory review.\nCaller scores are abstract, not validated environmental effects or evidence.\n')
    self.assertEqual(b.__doc__,'Strategic Environmental Assessment.\n\nPARTIAL: caller alternative/criterion weighted-score ledger only, not a\nstrategic environmental assessment, policy evaluation or decision advice.\nCaller weights and scores are abstract, not validated environmental evidence.\n')
Tests.test_disclaimer=disclaimer
