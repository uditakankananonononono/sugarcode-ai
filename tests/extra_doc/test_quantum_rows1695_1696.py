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
a=load('risk_products1695');b=load('exposure_integral1696')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand(self):
        for rows in ([['B',1,2,3],('A',1,1,1)],[('B',1,2,3),['A',1,1,1]]):
            self.assertEqual(a.scores(rows,1),{'scores':(('A',F(1)),('B',F(3,2))),'above':('B',),'total_score':F(5,2),'scope':'caller probability-severity arithmetic only; no validated risk assessment claims'})
        self.assertEqual(a.scores([('x',0,1,1)],0)['above'],())
        for rows in ([['B',3,2],('A',0,1),['B',1,1]],[('B',1,1),['A',0,1],('B',3,2)]):
            self.assertEqual(b.integrals(rows),{'integrals':(('A',1,0,F(0)),('B',3,7,F(7,3))),'total_integral':7,'total_duration':4,'scope':'caller concentration-duration product ledger only; no exposure or health claims'})
    def test_caps(self):
        a.scores([(str(i),1000000,1000000,1000000) for i in range(64)],1000000);a.scores([('x'*40,0,1,0)],0)
        b.integrals([('x'*40,1000000,1000000)]*64)
    def test_precedence(self):
        with self.assertRaises(ValueError) as c:a.scores([('x',1,1,1),('x',True,None,None)],0)
        self.assertEqual(str(c.exception),'labels must be unique')
        for fn,row,tail in ((a.scores,('',True,None,None),(0,)),(b.integrals,('',True,None),())):
            with self.assertRaises(ValueError) as c:fn([row],*tail)
            self.assertEqual(str(c.exception),'label must be exactstr printable Unicode length1..40')
def seeded(seed):
    def test(self):
        r=random.Random(seed);rows=[]
        for i in range(r.randrange(1,40)):
            d=r.randrange(1,1000001);rows.append(('Ω'+str(i),r.randrange(d+1),d,r.randrange(1000001)))
        r.shuffle(rows);threshold=r.randrange(1000001);result=tuple((name,F(n*s,d)) for name,n,d,s in sorted(rows));out={'scores':result,'above':tuple(name for name,n,d,s in sorted(rows) if n*s>threshold*d),'total_score':sum(v for name,v in result),'scope':a.SCOPE}
        self.assertEqual(a.scores(rows,threshold),out);self.assertEqual(a.scores(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1])),threshold),out)
        rows=[('É'+str(r.randrange(5)),r.randrange(1000001),r.randrange(1,1000001)) for i in range(r.randrange(1,40))];result=[]
        for name in sorted(set(row[0] for row in rows)):
            sub=[(c,d) for label,c,d in rows if label==name];duration=sum(d for c,d in sub);integral=sum(c*d for c,d in sub);result.append((name,duration,integral,sum(F(c*d,duration) for c,d in sub)))
        out={'integrals':tuple(result),'total_integral':sum(c*d for name,c,d in rows),'total_duration':sum(d for name,c,d in rows),'scope':b.SCOPE}
        self.assertEqual(b.integrals(rows),out);self.assertEqual(b.integrals(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))
def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for bad in (True,False,I(0),1.,None,'1',-1,1000001):cases.append((a.scores,([],bad),'threshold must be exactint0..1000000'))
for fn,row,tail,message in ((a.scores,('a',1,1,1),(0,),'probability must be exactint0<=numerator<=denominator<=1000000 with denominator>0 and severity exactint0..1000000'),(b.integrals,('a',1,1),(),'concentration must be exactint0..1000000 and duration exactint1..1000000')):
    for bad in ([],[row]*65,{},set(),iter([]),'x',None,L([row]),T((row,))):cases.append((fn,(bad,)+tail,'rows must be exactlist/tuple length1..64'))
    for bad in ([],row[:-1],row+(0,),'abcd',None,L(row),T(row)):cases.append((fn,([bad],)+tail,'row must be exactlist/tuple '+('quadruple' if fn==a.scores else 'triple')))
    for bad in ('','x'*41,'\n','\x00',S('a'),0,None):cases.append((fn,([(bad,)+row[1:]],)+tail,'label must be exactstr printable Unicode length1..40'))
    for slot in range(1,len(row)):
        for bad in (True,False,I(0),1.,None,'1',-1,1000001):
            altered=list(row);altered[slot]=bad;cases.append((fn,([altered],)+tail,message))
for row in (('a',0,0,0),('a',2,1,0)):cases.append((a.scores,([row],0),'probability must be exactint0<=numerator<=denominator<=1000000 with denominator>0 and severity exactint0..1000000'))
cases.append((a.scores,([('a',0,1,0),('a',0,1,0)],0),'labels must be unique'))
cases.append((b.integrals,([('a',0,0)],),'concentration must be exactint0..1000000 and duration exactint1..1000000'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))
def charset(char):
    def test(self):a.scores([(char,0,1,0)],0);b.integrals([(char,0,1)])
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))

def disclaimer(self):
    self.assertEqual(a.__doc__,'Risk Assessment.\n\nPARTIAL: caller probability/severity arithmetic only, not risk assessment,\nvalidated likelihood, health/safety classification or management advice.\nCaller severities and probability fractions are abstract, not calibrated risks.\n')
    self.assertEqual(b.__doc__,'Exposure Science.\n\nPARTIAL: caller concentration/duration product ledger only, not exposure\nscience, absorbed dose, route modeling, health assessment or safety advice.\nCaller compatible quantities are abstract, not verified exposure measurements.\n')
Tests.test_disclaimer=disclaimer
