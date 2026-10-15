import random,pytest
from fractions import Fraction as F
from itertools import combinations
from sugarcode.extra_doc import embryo1176 as m

def exact(a,b):
 assert type(a) is type(b)
 if type(b) is dict:
  assert list(a)==list(b)
  for k in b:exact(a[k],b[k])
 elif type(b) in (list,tuple):
  assert len(a)==len(b)
  for x,y in zip(a,b):exact(x,y)
 elif type(b) is bool:assert a is b
 else:assert a==b

def test_independent_index_subsets_and_depletion_recursion():
 rng=random.Random(1176)
 for _ in range(150):
  n=rng.randint(1,9);v=rng.randint(0,n);d=rng.randint(0,n);tally=[0]*(d+1);den=0
  for chosen in combinations(range(n),d):tally[sum(i<v for i in chosen)]+=1;den+=1
  p=[F(c,den) for c in tally];exact(m.distribution((n,v,d)),{'pmf':p,'mean':sum((i*x for i,x in enumerate(p)),F(0)),'at_least_one':sum(p[1:],F(0)),'clinical_validated':False})
 for n,v,d in [(30,0,30),(30,30,30),(30,15,12),(30,15,0),(1,1,1)]:
  states={(v,n-v,0):F(1)}
  for _ in range(d):
   nxt={}
   for (good,bad,k),mass in states.items():
    if good:nxt[(good-1,bad,k+1)]=nxt.get((good-1,bad,k+1),F(0))+mass*F(good,good+bad)
    if bad:nxt[(good,bad-1,k)]=nxt.get((good,bad-1,k),F(0))+mass*F(bad,good+bad)
   states=nxt
  p=[sum((mass for (g,b,k),mass in states.items() if k==j),F(0)) for j in range(d+1)];exact(m.distribution((n,v,d)),{'pmf':p,'mean':sum((i*x for i,x in enumerate(p)),F(0)),'at_least_one':1-p[0],'clinical_validated':False})
class T(tuple):pass
class I(int):pass

def test_validation_caps_and_scope():
 for x in (None,[],T((1,1,1)),(),(1,1),(1,1,1,1)):
  with pytest.raises(ValueError,match='population must be exact tuple3'):m.distribution(x)
 for pos in range(3):
  for x in (True,1.0,I(1),None,-1,31):
   p=[2,1,1];p[pos]=x
   with pytest.raises(ValueError,match='bounded exact population counts'):m.distribution(tuple(p))
 for p in ((0,0,0),(1,2,0),(1,0,2)):
  with pytest.raises(ValueError):m.distribution(p)
 for p in ((1,0,0),(30,0,0),(30,30,0),(30,0,30),(30,30,30)):assert m.distribution(p)
 assert m.SCOPE=='PARTIAL: exact supplied finite-population viable-draw distribution'
 assert m.NOT_CLAIMED==('clinical viability','transfer advice','pregnancy prediction','production readiness')
