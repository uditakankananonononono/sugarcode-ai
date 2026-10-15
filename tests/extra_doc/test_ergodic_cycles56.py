import random,pytest,math
from fractions import Fraction as F
from copy import deepcopy
from sugarcode.extra_doc import ergodic_cycles56 as m
class D(dict):pass
class L(list):pass
class I(int):pass

def oracle(d):
 # After n steps all starts are recurrent. LCM(1..n) ticks is an exact whole
 # number of periods, so direct fixed-window average equals limiting time mean.
 n=len(d['next']);period=math.lcm(*range(1,n+1));means=[]
 for start in range(n):
  state=start
  for _ in range(n):state=d['next'][state]
  total=0
  for _ in range(period):total+=d['rewards'][state];state=d['next'][state]
  means.append(F(total,period))
 mass=sum(d['weights']);ensemble=sum((F(w,mass)*v for w,v in zip(d['weights'],means)),F(0));variance=sum((F(w,mass)*v*v for w,v in zip(d['weights'],means)),F(0))-ensemble*ensemble
 def pair(v):return [v.numerator,v.denominator]
 return dict(time_means=[pair(v) for v in means],ensemble=pair(ensemble),variance=pair(variance),same_mean=len({v for v,w in zip(means,d['weights']) if w})==1,claims=[False]*3)

def check(d):
 old=deepcopy(d);r=m.analyze(d);assert d==old;assert r==oracle(d);assert list(r)==['time_means','ensemble','variance','same_mean','claims'];assert type(r['same_mean']) is bool;assert all(v is False for v in r['claims']);assert all(type(v) is int for row in r['time_means']+[r['ensemble'],r['variance']] for v in row)

def test_whole_period_oracle():
 rng=random.Random(56)
 for _ in range(220):
  n=rng.randint(1,7);weights=[rng.randint(0,5) for _ in range(n)];weights[rng.randrange(n)]=1;check(dict(next=[rng.randrange(n) for _ in range(n)],rewards=[rng.randint(-5,5) for _ in range(n)],weights=weights))
 for weights in ([1,1],[1,0],[0,1]):check(dict(next=[0,1],rewards=[-5,5],weights=weights))
 check(dict(next=[1,2,3,4,5,6,0],rewards=[-5,0,1,2,3,4,5],weights=[1]*7))
 assert m.SCOPE=='PARTIAL: exact supplied deterministic finite-state cycle time-mean dispersion only'
 assert m.NOT_CLAIMED==('general ergodicity test','real process model','production readiness')

def good():return dict(next=[0,2,1],rewards=[-5,0,5],weights=[0,1,5])
def refuse(d,msg):
 old=deepcopy(d)
 with pytest.raises(ValueError) as e:m.analyze(d)
 assert str(e.value)==msg;assert d==old

def test_validation():
 for v in [None,[],{},D(good()),dict(good(),extra=1)]:refuse(v,'exact dict with next, rewards, weights required')
 for v in [None,(),L([0]),[],[0]*8]:
  d=good();d['next']=v;refuse(d,'next must be an exact list of 1..7 items')
 for i in range(3):
  for v in [-1,3,True,1.0,I(1),None,'1']:
   d=good();d['next'][i]=v;refuse(d,'next must contain exact valid state indices')
 for key,lo in [('rewards',-5),('weights',0)]:
  for v in [None,(),L([0]*3),[True]*2,[True]*4]:
   d=good();d[key]=v;refuse(d,key+' must be an exact state-length list')
  for i in range(3):
   for v in [lo-1,6,True,1.0,I(1),None,'1']:
    d=good();d[key][i]=v;refuse(d,key+' outside exact integer range')
 d=good();d['weights']=[0]*3;refuse(d,'weights must have positive total')
 d=good();d['rewards'][0]=None;d['weights']=None;refuse(d,'rewards outside exact integer range')
