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
a=load('stakeholder_grid1701');b=load('policy_net1702')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand(self):
        for rows in ([['B',2,1],('A',1,1),['C',0,0],('D',0,1),['E',1,0]],[('B',2,1),['A',1,1],('C',0,0),['D',0,1],('E',1,0)]):
            self.assertEqual(a.grid(rows,1),{'grid':(('A',True,True),('B',True,True),('C',False,False),('D',False,True),('E',True,False)),'counts':((False,False,1),(False,True,1),(True,False,1),(True,True,2)),'both_high':('A','B'),'scope':'caller influence-interest threshold grid only; no stakeholder assessment or outreach'})
        for rows in ([['B',1,2],('A',0,0),['B',0,0]],[('B',0,0),['A',0,0],('B',1,2)]):
            self.assertEqual(b.net(rows),{'net':(('A',0,0,0),('B',1,2,1)),'total_net':1,'positive':('B',),'scope':'caller cost-benefit ledger arithmetic only; no environmental policy advice'})
        self.assertEqual(b.net([('x',1,0)])['positive'],())
    def test_caps(self):
        a.grid([(str(i),1000000,1000000) for i in range(64)],1000000);a.grid([('x'*40,0,0)],0)
        b.net([('x'*40,1000000,1000000)]*64)
    def test_precedence(self):
        with self.assertRaises(ValueError) as c:a.grid([('x',1,1),('x',True,None)],0)
        self.assertEqual(str(c.exception),'labels must be unique')
def seeded(seed):
    def test(self):
        r=random.Random(seed);rows=[('Ω'+str(i),r.randrange(1000001),r.randrange(1000001)) for i in range(r.randrange(1,40))];r.shuffle(rows);threshold=r.randrange(1000001);result=tuple((name,not x<threshold,not y<threshold) for name,x,y in sorted(rows));counts=tuple((x,y,len([1 for name,xx,yy in result if (xx,yy)==(x,y)])) for x,y in ((False,False),(False,True),(True,False),(True,True)));out={'grid':result,'counts':counts,'both_high':tuple(name for name,x,y in sorted(rows) if min(x,y)>=threshold),'scope':a.SCOPE}
        self.assertEqual(a.grid(rows,threshold),out);self.assertEqual(a.grid(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1])),threshold),out)
        rows=[('É'+str(r.randrange(5)),r.randrange(1000001),r.randrange(1000001)) for i in range(r.randrange(1,40))];result=[]
        for name in sorted(set(row[0] for row in rows)):
            sub=[(c,v) for label,c,v in rows if label==name];cost=sum(c for c,v in sub);benefit=sum(v for c,v in sub);result.append((name,cost,benefit,sum(v-c for c,v in sub)))
        out={'net':tuple(result),'total_net':sum(v-c for name,c,v in rows),'positive':tuple(name for name,c,v,n in result if v>c),'scope':b.SCOPE}
        self.assertEqual(b.net(rows),out);self.assertEqual(b.net(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))
def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for bad in (True,False,I(0),1.,None,'1',-1,1000001):cases.append((a.grid,([],bad),'threshold must be exactint0..1000000'))
for fn,tail,message in ((a.grid,(0,),'scores must be exactint0..1000000'),(b.net,(),'values must be exactint0..1000000')):
    row=('a',1,1)
    for bad in ([],[row]*65,{},set(),iter([]),'x',None,L([row]),T((row,))):cases.append((fn,(bad,)+tail,'rows must be exactlist/tuple length1..64'))
    for bad in ([],row[:-1],row+(0,),'abc',None,L(row),T(row)):cases.append((fn,([bad],)+tail,'row must be exactlist/tuple triple'))
    for bad in ('','x'*41,'\n','\x00',S('a'),0,None):cases.append((fn,([(bad,)+row[1:]],)+tail,'label must be exactstr printable Unicode length1..40'))
    for slot in (1,2):
        for bad in (True,False,I(0),1.,None,'1',-1,1000001):
            altered=list(row);altered[slot]=bad;cases.append((fn,([altered],)+tail,message))
cases.append((a.grid,([('a',0,0),('a',0,0)],0),'labels must be unique'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))
def charset(char):
    def test(self):a.grid([(char,0,0)],0);b.net([(char,0,0)])
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))

def disclaimer(self):
    self.assertEqual(a.__doc__,'Stakeholder Analysis.\n\nPARTIAL: caller influence/interest threshold grid only, not stakeholder\nanalysis, relationship assessment, consent, outreach or engagement advice.\nCaller scores and thresholds are abstract, not verified stakeholder attributes.\n')
    self.assertEqual(b.__doc__,'Environmental Policy.\n\nPARTIAL: caller cost/benefit ledger arithmetic only, not environmental policy,\npolicy effectiveness, environmental benefit valuation or legal advice.\nCaller compatible values are abstract, not verified public-policy outcomes.\n')
Tests.test_disclaimer=disclaimer
