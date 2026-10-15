import random,pytest,itertools
from fractions import Fraction as F
from copy import deepcopy
from sugarcode.extra_doc import nonlinear_fit57 as m
class D(dict):pass
class L(list):pass
class I(int):pass

def oracle(d):
 x=d['x'];y=d['y'];n=len(x);models=[]
 for name,z in [('exponential',[2**v for v in x]),('logarithmic',[{1:0,2:1,4:2,8:3}[v] for v in x]),('square',[v**2 for v in x]),('cube',[v*v*v for v in x])]:
  # Pairwise slope identity, centered residuals, no raw normal equations.
  slope=F(sum((z[i]-z[j])*(y[i]-y[j]) for i in range(n) for j in range(i)),sum((z[i]-z[j])**2 for i in range(n) for j in range(i)))
  intercept=sum((F(b)-slope*a for a,b in zip(z,y)),F(0))/n;prediction=[intercept+slope*v for v in z];error=sum(((F(b)-p)**2 for b,p in zip(y,prediction)),F(0));models.append((name,intercept,slope,prediction,error))
 winner=next(row for row in models if row[4]==min(v[4] for v in models))
 def pair(v):return [v.numerator,v.denominator]
 name,a,b,p,_=winner
 return dict(family=name,coefficients=[pair(a),pair(b)],predictions=[pair(v) for v in p],errors=[[name,pair(error)] for name,a,b,p,error in models],claims=[False]*3)

def check(d):
 old=deepcopy(d);r=m.fit(d);assert d==old;assert r==oracle(d);assert list(r)==['family','coefficients','predictions','errors','claims'];assert all(v is False for v in r['claims']);assert all(type(v) is int for pair in r['coefficients']+r['predictions']+[pair for name,pair in r['errors']] for v in pair)

def test_pairwise_slope_oracle():
 rng=random.Random(57)
 for _ in range(220):
  x=rng.sample([1,2,4,8],rng.randint(3,4));check(dict(x=x,y=[rng.randint(-8,8) for _ in x]))
 for y in ([0]*4,[-8]*4,[0,1,2,3]):check(dict(x=[1,2,4,8],y=y))
 assert m.SCOPE=='PARTIAL: exact supplied four-family transformed-predictor OLS selection only'
 assert m.NOT_CLAIMED==('general nonlinear thinking','predictive validity','production readiness')

def good():return dict(x=[1,2,4,8],y=[-8,0,4,8])
def refuse(d,msg):
 old=deepcopy(d)
 with pytest.raises(ValueError) as e:m.fit(d)
 assert str(e.value)==msg;assert d==old

def test_validation():
 for v in [None,[],{},D(good()),dict(good(),extra=1)]:refuse(v,'exact dict with x and y required')
 for v in [None,(),L([1,2,4]),[],[1,2],[1,2,4,8,1]]:
  d=good();d['x']=v;refuse(d,'x must be an exact list of 3..4 items')
 for i in range(4):
  for v in [0,3,9,True,1.0,I(1),None,'1']:
   d=good();d['x'][i]=v;refuse(d,'x must contain exact integers from 1,2,4,8')
 d=good();d['x']=[1,2,4,1];refuse(d,'x must be unique')
 for v in [None,(),L([0]*4),[True]*3,[True]*5]:
  d=good();d['y']=v;refuse(d,'y must be an exact x-length list')
 for i in range(4):
  for v in [-9,9,True,1.0,I(1),None,'1']:
   d=good();d['y'][i]=v;refuse(d,'y must contain exact integers -8..8')
 d=good();d['x']=[1,2,4,1];d['y']=None;refuse(d,'x must be unique')
