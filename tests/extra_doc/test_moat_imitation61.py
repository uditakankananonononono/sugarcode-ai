import random,pytest
from copy import deepcopy
from sugarcode.extra_doc import moat_imitation61 as m
class D(dict):pass
class L(list):pass
class I(int):pass

def oracle(d):
 # Enumerate seed sets, expand prerequisite closure to fixed point, then cover.
 n=len(d['costs']);choices=set()
 for mask in range(1<<n):
  chosen={i for i in range(n) if mask&(1<<i)}
  while True:
   expanded=chosen|{u for u,v in d['prerequisites'] if v in chosen}
   if expanded==chosen:break
   chosen=expanded
  if all(any(cap in d['provides'][i] for i in chosen) for cap in d['required']):choices.add((sum(d['costs'][i] for i in chosen),len(chosen),tuple(sorted(chosen))))
 cost,_,subset=min(choices) if choices else (None,None,None)
 return dict(technologies=list(subset) if subset is not None else None,cost=cost,claims=[False]*3)

def check(d):
 original=deepcopy(d);r=m.assess(d);assert d==original;assert r==oracle(d);assert list(r)==['technologies','cost','claims'];assert r['cost'] is None or type(r['cost']) is int;assert all(type(v) is int for v in (r['technologies'] or []));assert all(v is False for v in r['claims'])

def test_closure_oracle():
 rng=random.Random(61)
 for _ in range(220):
  n=rng.randint(1,8);check(dict(costs=[rng.randint(1,8) for _ in range(n)],provides=[rng.sample(range(6),rng.randint(1,6)) for _ in range(n)],required=rng.sample(range(6),rng.randint(1,6)),prerequisites=[[i,j] for i in range(n) for j in range(i+1,n) if rng.randrange(3)==0]))
 check(dict(costs=[1]*8,provides=[[0]]*8,required=[5],prerequisites=[[i,j] for i in range(8) for j in range(i+1,8)]))
 assert m.SCOPE=='PARTIAL: exact supplied prerequisite-closed minimum imitation capability cover only'
 assert m.NOT_CLAIMED==('real moat','verified imitation costs','production readiness')

def good():return dict(costs=[1,8],provides=[[0,5],[1,4]],required=[0,5],prerequisites=[[0,1]])
def refuse(d,msg):
 original=deepcopy(d)
 with pytest.raises(ValueError) as e:m.assess(d)
 assert str(e.value)==msg;assert d==original

def test_validation():
 for v in [None,[],{},D(good()),dict(good(),extra=1)]:refuse(v,'exact dict with costs, provides, required, prerequisites required')
 for key,vals,msg in [('costs',[None,(),L([1]),[],[1]*9],'costs must be an exact list of 1..8 items'),('provides',[None,(),L([[0],[0]]),[[0]],[[0]]*3],'provides must be an exact technology-count list'),('prerequisites',[None,(),L([]),[[0,1]]*29],'prerequisites must be an exact list of at most 28 pairs')]:
  for v in vals:
   d=good();d[key]=v;refuse(d,msg)
 for i in range(2):
  for v in [0,9,True,1.0,I(1),None,'1']:
   d=good();d['costs'][i]=v;refuse(d,'costs must be exact integers 1..8')
 for location in ('required',0,1):
  for v in [None,(),L([0]),[],list(range(7))]:
   d=good()
   if location=='required':d['required']=v
   else:d['provides'][location]=v
   refuse(d,'capabilities must be exact lists of 1..6 items')
  for j in range(2):
   for v in [-1,6,True,1.0,I(1),None,'1']:
    d=good();row=d['required'] if location=='required' else d['provides'][location];row[j]=v;refuse(d,'capabilities must be exact integers 0..5')
  d=good()
  if location=='required':d['required']=[0,0]
  else:d['provides'][location]=[0,0]
  refuse(d,'capabilities must be unique per list')
 for v in [None,(),L([0,1]),[True],[True]*3]:
  d=good();d['prerequisites']=[v];refuse(d,'prerequisite must be an exact two-item list')
 for i in range(2):
  for v in [-1,2,True,1.0,I(1),None,'1']:
   d=good();d['prerequisites'][0][i]=v;refuse(d,'prerequisite indices must be exact valid indices')
 for edge in ([0,0],[1,0]):
  d=good();d['prerequisites']=[edge];refuse(d,'prerequisites must follow strict index order')
 d=good();d['prerequisites']*=2;refuse(d,'prerequisites must be unique')
