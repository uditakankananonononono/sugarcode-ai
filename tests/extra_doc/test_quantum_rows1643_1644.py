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
a=load('transport_load1643');b=load('ev_energy1644')
class I(int):pass
class S(str):pass
class L(list):pass
class T(tuple):pass
class Tests(unittest.TestCase):
    def test_hand_scope_mix(self):
        for rows in ([['B',2,3],('A',1,1)],[('A',1,1),['B',2,3]]):
            self.assertEqual(a.trips(rows),{'passenger_distances':(('A',1),('B',6)),'distance_total':3,'passenger_distance_total':7,'weighted_passengers':F(7,3),'scope':'caller trip passenger-distance totals only; no sustainability or routing claims'})
        for rows in ([[3,2],(0,3)],[(3,2),[0,3]]):
            self.assertEqual(b.ledger(rows,5,4),{'steps':((0,3,2),(1,0,0)),'final_charge':0,'use_total':5,'discarded_total':2,'scope':'caller battery-energy trip ledger only; no EV range or charging-control claims'})
        self.assertIsNone(a.trips([('x',0,0)])['weighted_passengers']);self.assertEqual(b.ledger([(0,0)],1,0)['final_charge'],0)
    def test_caps(self):
        a.trips([(str(i),1000000,1000) for i in range(64)]);a.trips([('a'*40,0,0)])
        b.ledger([(1000000,1000000)]*64,1000000,1000000)
    def test_precedence(self):
        with self.assertRaises(ValueError) as c:a.trips([('a',0,0),('a',True,None)])
        self.assertEqual(str(c.exception),'labels must be unique')
        with self.assertRaises(ValueError) as c:b.ledger([(0,1),(True,0)],1,0)
        self.assertEqual(str(c.exception),'charge and use must be exactint0..1000000')

def seeded(seed):
    def test(self):
        rng=random.Random(seed);rows=[('Ω'+str(i),rng.randrange(1000001),rng.randrange(1001)) for i in range(rng.randrange(1,40))];distance=sum(x[1] for x in rows);total=sum(d*p for _,d,p in rows);out={'passenger_distances':tuple(sorted((name,d*p) for name,d,p in rows)),'distance_total':distance,'passenger_distance_total':total,'weighted_passengers':sum(F(d,distance)*p for name,d,p in rows) if distance else None,'scope':a.SCOPE};self.assertEqual(a.trips(rows),out);self.assertEqual(a.trips(tuple(list(row) if i%2 else row for i,row in enumerate(rows[::-1]))),out)
        cap=rng.randrange(1,100);initial=rng.randrange(cap+1);current=initial;rows=[];expected=[]
        for i in range(rng.randrange(1,40)):
            charge=rng.randrange(100);incoming=current+charge
            if incoming>cap:discarded=incoming-cap;incoming=cap
            else:discarded=0
            use=rng.randrange(incoming+1);current=incoming-use;rows.append((charge,use));expected.append((i,current,discarded))
        out={'steps':tuple(expected),'final_charge':current,'use_total':sum(use for charge,use in rows),'discarded_total':initial+sum(charge-use for charge,use in rows)-current,'scope':b.SCOPE};self.assertEqual(b.ledger(rows,cap,initial),out);self.assertEqual(b.ledger(tuple(list(row) if i%2 else row for i,row in enumerate(rows)),cap,initial),out)
    return test
for seed in range(400):setattr(Tests,'test_seed_%03d'%seed,seeded(seed))
def refusal(fn,args,message):
    def test(self):
        with self.assertRaises(ValueError) as c:fn(*args)
        self.assertEqual(str(c.exception),message)
    return test
cases=[]
for fn,row,tail in ((a.trips,('a',0,0),()),(b.ledger,(0,0),(1,0))):
    for bad in ([],[row]*65,{},set(),iter([]),'x',L([row]),T((row,))):cases.append((fn,(bad,)+tail,'rows must be exactlist/tuple length1..64'))
    for bad in ([],list(row[:-1]),tuple(row)+(1,),'abc',L(row),T(row)):cases.append((fn,([bad],)+tail,'row must be exactlist/tuple '+('triple' if fn==a.trips else 'pair')))
for bad in ('','a'*41,'\n','\x00',S('a'),0,None):cases.append((a.trips,([(bad,0,0)],),'label must be exactstr printable Unicode length1..40'))
for slot,cap in ((1,1000000),(2,1000)):
    for bad in (False,True,I(1),1.,None,'1',-1,cap+1):
        row=['a',0,0];row[slot]=bad;cases.append((a.trips,([row],),('distance' if slot==1 else 'passengers')+' must be exactint0..'+str(cap)))
cases.append((a.trips,([('a',0,0),('a',0,0)],),'labels must be unique'))
for slot in (0,1):
    for bad in (False,True,I(1),1.,None,'1',-1,1000001):
        row=[0,0];row[slot]=bad;cases.append((b.ledger,([row],1,0),'charge and use must be exactint0..1000000'))
for bad in (False,True,I(1),1.,None,'1',0,1000001):cases.append((b.ledger,([(0,0)],bad,0),'capacity must be exactint1..1000000'))
for bad in (False,True,I(1),1.,None,'1',-1,2):cases.append((b.ledger,([(0,0)],1,bad),'initial must be exactint0..capacity'))
cases.append((b.ledger,([(0,1)],1,0),'use must not exceed current charge'))
for i,case in enumerate(cases):setattr(Tests,'test_refuse_%03d'%i,refusal(*case))
def charset(char):
    def test(self):a.trips([(char,0,0)])
    return test
for i,char in enumerate(string.printable+'ÉΩ中９！'):
    if char.isprintable():setattr(Tests,'test_charset_%03d'%i,charset(char))

def exact_disclaimers(self):
    self.assertEqual(a.__doc__,'Sustainable Transport.\n\nPARTIAL: caller trip passenger/distance totals only, not sustainable transport,\nemissions modeling,mode recommendations,routing or environmental evaluation.\nDistances/passengers caller declarations,no real trips or vehicle data inferred.\n')
    self.assertEqual(b.__doc__,'Electric Vehicles.\n\nPARTIAL: caller battery-energy trip ledger only, not electric vehicles,\nrange prediction,charging control,battery physics or route feasibility.\nCharges/uses/capacity caller inputs,no efficiencies or vehicle telemetry inferred.\n')
Tests.test_exact_disclaimers=exact_disclaimers
