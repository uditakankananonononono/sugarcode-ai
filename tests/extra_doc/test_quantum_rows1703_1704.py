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
a=load('regulation_register1703');b=load('permit_register1704')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand(self):
        for fn,statuses,scope in ((a.records,('pending','documented','disputed'),'caller-declared requirement-status register only; no regulatory compliance claims'),(b.records,('draft','submitted','returned'),'caller-declared permit-stage register only; no permitting or approval claims')):
            x,y,z=statuses
            for rows in ([['B',z,1],('A',x,0)],[('B',z,1),['A',x,0]]):
                self.assertEqual(fn(rows),{'records':(('A',x,0),('B',z,1)),'statuses':((x,1,0),(y,0,0),(z,1,1)),z:('B',),'scope':scope})
    def test_caps(self):
        for fn,status in ((a.records,'pending'),(b.records,'draft')):
            fn([(str(i),status,1000000) for i in range(64)]);fn([('x'*40,status,0)])
    def test_precedence(self):
        for fn,status in ((a.records,'pending'),(b.records,'draft')):
            with self.assertRaises(ValueError) as c:fn([('x',status,0),('x',True,None)])
            self.assertEqual(str(c.exception),'labels must be unique')
def seeded(seed):
    def test(self):
        r=random.Random(seed)
        for fn,statuses,scope in ((a.records,('pending','documented','disputed'),a.SCOPE),(b.records,('draft','submitted','returned'),b.SCOPE)):
            rows=[('Ω'+str(i),r.choice(statuses),r.randrange(1000001)) for i in range(r.randrange(1,40))];r.shuffle(rows);out={'records':tuple(sorted(rows)),'statuses':tuple((s,len([1 for name,status,n in rows if status==s]),sum(n for name,status,n in rows if status==s)) for s in statuses),statuses[-1]:tuple(name for name,status,n in sorted(rows) if status==statuses[-1]),'scope':scope}
            self.assertEqual(fn(rows),out);self.assertEqual(fn(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))
def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for fn,statuses in ((a.records,('pending','documented','disputed')),(b.records,('draft','submitted','returned'))):
    row=('a',statuses[0],0)
    for bad in ([],[row]*65,{},set(),iter([]),'x',None,L([row]),T((row,))):cases.append((fn,(bad,),'rows must be exactlist/tuple length1..64'))
    for bad in ([],row[:-1],row+(0,),'abc',None,L(row),T(row)):cases.append((fn,([bad],),'row must be exactlist/tuple triple'))
    for bad in ('','x'*41,'\n','\x00',S('a'),0,None):cases.append((fn,([(bad,)+row[1:]],),'label must be exactstr printable Unicode length1..40'))
    for bad in (True,False,I(0),1.,None,'1',-1,1000001):cases.append((fn,([('a',statuses[0],bad)],),'count must be exactint0..1000000'))
    for bad in tuple(S(x) for x in statuses)+(statuses[0].upper(),'',None,1,True,[],{},'approved','Ω'):cases.append((fn,([('a',bad,0)],),'status must be exactstr '+'/'.join(statuses)))
    cases.append((fn,([row,row],),'labels must be unique'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))
def charset(char):
    def test(self):a.records([(char,'pending',0)]);b.records([(char,'draft',0)])
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))

def disclaimer(self):
    self.assertEqual(a.__doc__,'Regulation.\n\nPARTIAL: caller-declared requirement-status register only, not regulation,\nlegal interpretation, regulatory applicability, compliance or legal advice.\nRecorded status does not prove compliance or authorize any action.\n')
    self.assertEqual(b.__doc__,'Permitting.\n\nPARTIAL: caller-declared permit-stage register only, not permitting,\napplication submission, legal eligibility, approval verification or legal advice.\nCaller stage labels are not verified permits or authority to proceed.\n')
Tests.test_disclaimer=disclaimer
