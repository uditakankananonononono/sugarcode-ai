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
a=load('indoor_turnover1665');b=load('soil_moisture1666')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand(self):
        for rows in ([['B',3,2],('A',2,1)],[('B',3,2),['A',2,1]]):
            self.assertEqual(a.turnover(rows,2),{'turnover':(('A',F(2)),('B',F(3,2))),'below':('B',),'minimum':F(3,2),'scope':'caller airflow-volume ratios only; no indoor air quality or safety claims'})
        self.assertEqual(a.turnover([('x',0,1)],0)['below'],())
        for rows in ([['B',3,2],('A',0,0),['B',1,1]],[('B',1,1),['A',0,0],('B',3,2)]):
            self.assertEqual(b.moisture(rows),{'moisture':(('A',0,0,0,None),('B',4,3,1,F(1,3))),'total_water':1,'dry_basis_fraction':F(1,3),'scope':'caller wet-dry mass moisture arithmetic only; no soil health or agronomic claims'})
        self.assertEqual(b.moisture([('x',1,0)])['dry_basis_fraction'],None)
    def test_caps(self):
        a.turnover([(str(i),1000000,1000000) for i in range(64)],1000000);a.turnover([('x'*40,0,1)],0)
        b.moisture([('x'*40,1000000,1000000)]*64)
    def test_precedence(self):
        with self.assertRaises(ValueError) as c:a.turnover([('x',1,1),('x',True,None)],0)
        self.assertEqual(str(c.exception),'labels must be unique')
        for fn,tail in ((a.turnover,(0,)),(b.moisture,())):
            with self.assertRaises(ValueError) as c:fn([('',True,None)],*tail)
            self.assertEqual(str(c.exception),'label must be exactstr printable Unicode length1..40')

def seeded(seed):
    def test(self):
        r=random.Random(seed);rows=[('Ω'+str(i),r.randrange(1000001),r.randrange(1,1000001)) for i in range(r.randrange(1,40))];r.shuffle(rows);threshold=r.randrange(1000001);result=tuple((name,F(v,q)) for name,v,q in sorted(rows));out={'turnover':result,'below':tuple(name for name,v,q in sorted(rows) if v<threshold*q),'minimum':sorted(v for name,v in result)[0],'scope':a.SCOPE}
        self.assertEqual(a.turnover(rows,threshold),out);self.assertEqual(a.turnover(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1])),threshold),out)
        rows=[]
        for i in range(r.randrange(1,40)):
            wet=r.randrange(1000001);rows.append(('É'+str(r.randrange(5)),wet,r.randrange(wet+1)))
        result=[]
        for name in sorted(set(row[0] for row in rows)):
            sub=[(w,d) for label,w,d in rows if label==name];wet=sum(w for w,d in sub);dry=sum(d for w,d in sub);water=sum(w-d for w,d in sub);result.append((name,wet,dry,water,F(water,dry) if dry else None))
        water=sum(w-d for name,w,d in rows);dry=sum(d for name,w,d in rows);out={'moisture':tuple(result),'total_water':water,'dry_basis_fraction':F(water,dry) if dry else None,'scope':b.SCOPE}
        self.assertEqual(b.moisture(rows),out);self.assertEqual(b.moisture(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))
def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for bad in (True,False,I(0),1.,None,'1',-1,1000001):cases.append((a.turnover,([],bad),'threshold must be exactint0..1000000'))
for fn,tail,quantity_message in ((a.turnover,(0,),'airflow must be exactint0..1000000 and volume exactint1..1000000'),(b.moisture,(),'masses must be exactint0<=dry<=wet<=1000000')):
    row=('a',1,1)
    for bad in ([],[row]*65,{},set(),iter([]),'x',None,L([row]),T((row,))):cases.append((fn,(bad,)+tail,'rows must be exactlist/tuple length1..64'))
    for bad in ([],row[:-1],row+(0,),'abc',None,L(row),T(row)):cases.append((fn,([bad],)+tail,'row must be exactlist/tuple triple'))
    for bad in ('','x'*41,'\n','\x00',S('a'),0,None):cases.append((fn,([(bad,)+row[1:]],)+tail,'label must be exactstr printable Unicode length1..40'))
    for slot in (1,2):
        for bad in (True,False,I(0),1.,None,'1',-1,1000001):
            altered=list(row);altered[slot]=bad;cases.append((fn,([altered],)+tail,quantity_message))
cases.append((a.turnover,([('a',0,1),('a',0,1)],0),'labels must be unique'))
cases.append((a.turnover,([('a',0,0)],0),'airflow must be exactint0..1000000 and volume exactint1..1000000'))
cases.append((b.moisture,([('a',0,1)],),'masses must be exactint0<=dry<=wet<=1000000'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))
def charset(char):
    def test(self):a.turnover([(char,0,1)],0);b.moisture([(char,0,0)])
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))

def disclaimer(self):
    self.assertEqual(a.__doc__,'Indoor Air Quality.\n\nPARTIAL: caller airflow/volume ratio arithmetic only, not indoor air quality,\nventilation adequacy, exposure assessment or health/safety recommendations.\nCaller compatible quantities are not verified room or ventilation measurements.\n')
    self.assertEqual(b.__doc__,'Soil Health.\n\nPARTIAL: caller wet/dry mass moisture arithmetic only, not soil health,\nsoil testing, crop suitability, fertility or agronomic recommendations.\nCaller masses are abstract compatible units, not verified soil measurements.\n')
Tests.test_disclaimer=disclaimer
