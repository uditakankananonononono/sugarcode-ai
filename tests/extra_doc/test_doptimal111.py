import random,itertools,copy
import pytest
from sugarcode.extra_doc import doptimal111 as m
class D(dict):pass
class L(list):pass
class I(int):pass

def data():return dict(rows=[[1,0],[0,1],[2,1]],choose=2)
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
 candidates=[];n=len(d['rows'])
 # Bit masks and Cauchy-Binet squared 2x2 minors, not moment determinant.
 for mask in range(1<<n):
  indices=[i for i in range(n) if mask>>i&1]
  if len(indices)!=d['choose']:continue
  score=0
  for i,j in itertools.combinations(indices,2):
   x,y=d['rows'][i];u,v=d['rows'][j];score+=(x*v-y*u)**2
  candidates.append((-score,indices))
 neg,indices=min(candidates);matrix=[[0,0],[0,0]]
 for i in indices:
  for a,b in itertools.product(range(2),repeat=2):matrix[a][b]+=d['rows'][i][a]*d['rows'][i][b]
 return dict(indices=indices,determinant=-neg,information=matrix,claims=[False]*3)
def expect(d,msg):
 with pytest.raises(ValueError) as e:m.select(d)
 assert str(e.value)==msg

def test_squared_minors_oracle():
 rng=random.Random(111)
 for _ in range(200):
  n=rng.randint(2,8);d=dict(rows=[[rng.randint(-3,3),rng.randint(-3,3)] for i in range(n)],choose=rng.randint(2,n));exact(m.select(d),oracle(d))
 for n,value in itertools.product([2,8],[-3,0,3]):
  for choose in [2,n]:
   d=dict(rows=[[value,value]]*n,choose=choose);exact(m.select(d),oracle(d))
 for rows in [[[1,0],[0,1],[1,0],[0,1]],[[-3,1],[2,-2],[0,3]]]:
  d=dict(rows=rows,choose=2);exact(m.select(d),oracle(d))
 d=data();expected=oracle(d);saved=copy.deepcopy(d);result=m.select(d);assert d==saved;exact(result,expected);result['information'][0][0]=99;result['indices'][0]=99;exact(m.select(d),expected)
 assert m.SCOPE=='PARTIAL: exact finite two-parameter D-optimal subset selection only'
 assert m.NOT_CLAIMED==('actual experiment efficiency','hypothesis validity','production readiness')

def test_types_caps_order():
 for v in [None,[],{},D(data()),dict(data(),extra=1)]:expect(v,'exact dict with rows and choose required')
 for rows in [None,(),L([[0,0]]*2),[],[[0,0]],[[0,0]]*9]:expect(dict(rows=rows,choose=2),'rows must be an exact list of 2..8 vectors')
 for row in [None,(),L([0,0]),[],[0],[0]*3]:
  d=data();d['rows'][0]=row;expect(d,'vectors must be exact two-value lists')
 for v in [-4,4,True,1.0,I(1),None,'1']:
  d=data();d['rows'][0][0]=v;expect(d,'values must be exact integers -3..3')
 for v in [1,4,True,2.0,I(2),None,'2']:
  d=data();d['choose']=v;expect(d,'choose must be an exact integer 2..row count')
 d=data();d['rows'][0][0]=True;d['rows'][1]=None;expect(d,'values must be exact integers -3..3')
