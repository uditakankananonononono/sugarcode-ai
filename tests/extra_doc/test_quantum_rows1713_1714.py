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
a=load('cleaner_intensity1713');b=load('green_mass1714')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand(self):
        for rows in ([['B',3,2],('A',0,1),['B',1,1]],[('B',1,1),['A',0,1],('B',3,2)]):
            self.assertEqual(a.intensity(rows),{'intensity':(('A',0,1,F(0)),('B',4,3,F(4,3))),'resource':4,'output':4,'aggregate_intensity':F(1),'scope':'caller resource-output intensity arithmetic only; no cleaner production claims'})
        for rows in ([['B',3,2],('A',1,1)],[('B',3,2),['A',1,1]]):
            self.assertEqual(b.masses(rows),{'masses':(('A',0,F(0)),('B',1,F(1,2))),'total_waste':1,'aggregate_ratio':F(1,3),'scope':'caller input-product-waste mass arithmetic only; no green chemistry or safety claims'})
    def test_caps(self):
        a.intensity([('x'*40,1000000,1000000)]*64)
        b.masses([(str(i),1000000,1000000) for i in range(64)]);b.masses([('x'*40,1,1)])
    def test_precedence(self):
        with self.assertRaises(ValueError) as c:b.masses([('x',1,1),('x',True,None)])
        self.assertEqual(str(c.exception),'labels must be unique')
def seeded(seed):
    def test(self):
        r=random.Random(seed);rows=[('Ω'+str(r.randrange(5)),r.randrange(1000001),r.randrange(1,1000001)) for i in range(r.randrange(1,40))];result=[]
        for name in sorted(set(row[0] for row in rows)):
            sub=[(q,v) for label,q,v in rows if label==name];resource=sum(q for q,v in sub);output=sum(v for q,v in sub);result.append((name,resource,output,F(resource,output)))
        resource=sum(q for name,q,v in rows);output=sum(v for name,q,v in rows);out={'intensity':tuple(result),'resource':resource,'output':output,'aggregate_intensity':F(resource,output),'scope':a.SCOPE}
        self.assertEqual(a.intensity(rows),out);self.assertEqual(a.intensity(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
        rows=[]
        for i in range(r.randrange(1,40)):
            q=r.randrange(1,1000001);rows.append(('É'+str(i),q,r.randrange(1,q+1)))
        r.shuffle(rows);waste=sum(q-p for name,q,p in rows);product=sum(p for name,q,p in rows);out={'masses':tuple((name,q-p,F(q,p)-1) for name,q,p in sorted(rows)),'total_waste':waste,'aggregate_ratio':F(waste,product),'scope':b.SCOPE}
        self.assertEqual(b.masses(rows),out);self.assertEqual(b.masses(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))
def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for fn,message in ((a.intensity,'resource must be exactint0..1000000 and output exactint1..1000000'),(b.masses,'masses must be exactint1<=product<=input<=1000000')):
    row=('a',1,1)
    for bad in ([],[row]*65,{},set(),iter([]),'x',None,L([row]),T((row,))):cases.append((fn,(bad,),'rows must be exactlist/tuple length1..64'))
    for bad in ([],row[:-1],row+(0,),'abc',None,L(row),T(row)):cases.append((fn,([bad],),'row must be exactlist/tuple triple'))
    for bad in ('','x'*41,'\n','\x00',S('a'),0,None):cases.append((fn,([(bad,)+row[1:]],),'label must be exactstr printable Unicode length1..40'))
    for slot in (1,2):
        for bad in (True,False,I(0),1.,None,'1',-1,1000001):
            altered=list(row);altered[slot]=bad;cases.append((fn,([altered],),message))
    cases.append((fn,([('a',0,0)],),message))
for row in (('a',1,2),('a',1,0)):cases.append((b.masses,([row],),'masses must be exactint1<=product<=input<=1000000'))
cases.append((b.masses,([('a',1,1),('a',1,1)],),'labels must be unique'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))
def charset(char):
    def test(self):a.intensity([(char,0,1)]);b.masses([(char,1,1)])
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))

def disclaimer(self):
    self.assertEqual(a.__doc__,'Cleaner Production.\n\nPARTIAL: caller resource/output intensity arithmetic only, not cleaner\nproduction, environmental improvement, process optimization or certification.\nCaller quantities are abstract, not verified production or resource-use data.\n')
    self.assertEqual(b.__doc__,'Green Chemistry.\n\nPARTIAL: caller input/product/waste mass arithmetic only, not green chemistry,\nreaction design, chemical safety, atom economy or environmental assessment.\nCaller masses are abstract compatible units, not verified reaction data.\n')
Tests.test_disclaimer=disclaimer
