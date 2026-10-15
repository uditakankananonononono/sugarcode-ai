import itertools
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc import axis_ticks129 as m
class D(dict):pass
class L(list):pass
class I(int):pass

def data():return dict(bounds=[-3,4],target=5)
def exact(a,b):
 assert type(a) is type(b)
 if type(b) is dict:
  assert list(a)==list(b)
  for k in b:exact(a[k],b[k])
 elif type(b) is list:
  assert len(a)==len(b)
  for x,y in zip(a,b):exact(x,y)
 elif type(b) is bool:assert a is b
 else:assert a==b

def oracle(d):
 # Search integer tenths grid endpoints instead of floor/ceil rational arithmetic.
 low,high=[10*x for x in d['bounds']];candidates=[]
 for step in [1,2,5,10,20,50,100,200,500]:
  start=next(x for x in range(low,low-step-1,-1) if x%step==0)
  end=next(x for x in range(high,high+step+1) if x%step==0)
  ticks=list(range(start,end+1,step))
  if not 2<=len(ticks)<=20:continue
  excess=end-start-(high-low);key=(abs(len(ticks)-d['target']),excess,step);candidates.append((key,ticks))
 (gap,excess,step),ticks=min(candidates)
 def pair(v):v=F(v,10);return [v.numerator,v.denominator]
 return dict(step=pair(step),ticks=[pair(t) for t in ticks],excess=pair(excess),claims=[False]*3)
def expect(d,msg):
 with pytest.raises(ValueError) as e:m.plan(d)
 assert str(e.value)==msg

def test_exhaustive_bounds_targets():
 for low,high in itertools.combinations(range(-9,10),2):
  for target in range(2,7):
   d=dict(bounds=[low,high],target=target);exact(m.plan(d),oracle(d))
 assert m.SCOPE=='PARTIAL: exact supplied-bound finite 1-2-5 axis tick planning only'
 assert m.NOT_CLAIMED==('figure rendering','publication quality','production readiness')

def test_types_caps_order():
 for v in [None,[],{},D(data()),dict(data(),extra=1)]:expect(v,'exact dict with bounds and target required')
 for v in [None,(),L([0,1]),[],[0],[0]*3]:expect(dict(bounds=v,target=2),'bounds must be an exact two-value list')
 for position in [0,1]:
  for v in [-10,10,True,1.0,I(1),None,'1']:
   d=data();d['bounds'][position]=v;expect(d,'bounds must be exact integers -9..9')
 for bounds in [[0,0],[1,0]]:expect(dict(bounds=bounds,target=2),'lower bound must be less than upper bound')
 for bounds,target in [([1,0],None),([0,0],9)]:expect(dict(bounds=bounds,target=target),'lower bound must be less than upper bound')
 for v in [1,7,True,2.0,I(2),None,'2']:
  d=data();d['target']=v;expect(d,'target must be an exact integer 2..6')
 d=data();d['bounds']=[True,0];d['target']=None;expect(d,'bounds must be exact integers -9..9')
