import random,pytest,itertools
from copy import deepcopy
from sugarcode.extra_doc import var_forecast183 as m
class D(dict):pass
class L(list):pass
class I(int):pass
class S(str):pass
class T(tuple):pass

def oracle(d):
 a=d['matrix'];h=d['horizon']
 # Matrix powers via enumerated intermediate-index paths.
 def power(t,i,j):
  if t==0:return int(i==j)
  total=0
  for middle in itertools.product(range(2),repeat=t-1):
   path=(i,)+middle+(j,);product=1
   for x,y in zip(path,path[1:]):product*=a[x][y]
   total+=product
  return total
 means=[[sum(power(t,i,j)*d['state'][j] for j in range(2)) for i in range(2)] for t in range(h+1)];covs=[[[sum(power(k,i,j)*power(k,l,j)*d['variances'][j] for k in range(t) for j in range(2)) for l in range(2)] for i in range(2)] for t in range(h+1)]
 return dict(means=means,covariances=covs,claims=[False]*3)

def check(d):
 old=deepcopy(d);r=m.forecast(d);assert d==old;assert r==oracle(d);assert list(r)==['means','covariances','claims'];assert all(v is False for v in r['claims'])
 def typed(v):
  if isinstance(v,list):assert type(v) is list;[typed(x) for x in v]
  else:assert type(v) is int
 typed(r['means']);typed(r['covariances'])

def good():return dict(matrix=[[-2,2],[2,-2]],state=[-3,3],variances=[0,3],horizon=5)
def test_paths():
 rng=random.Random(183)
 for _ in range(220):check(dict(matrix=[[rng.randint(-2,2) for _ in range(2)] for _ in range(2)],state=[rng.randint(-3,3) for _ in range(2)],variances=[rng.randint(0,3) for _ in range(2)],horizon=rng.randint(1,5)))
 check(good())
 assert m.SCOPE=='PARTIAL: exact supplied bivariate VAR forecast means and covariance propagation only'
 assert m.NOT_CLAIMED==('fitted time series','stable dynamics','production readiness')

def refuse(d,msg):
 old=deepcopy(d)
 with pytest.raises(ValueError) as e:m.forecast(d)
 assert str(e.value)==msg;assert d==old

def test_validation():
 for v in [None,[],{},D(good()),dict(good(),extra=1),S('x'),T(())]:refuse(v,'exact dict with matrix, state, variances, horizon required')
 for v in [None,(),L([[0,0]]*2),[True],[True]*3]:
  d=good();d['matrix']=v;refuse(d,'matrix must be an exact two-row list')
 for i in range(2):
  for v in [None,(),T((0,0)),L([0,0]),[True],[True]*3]:
   d=good();d['matrix'][i]=v;refuse(d,'matrix row must be an exact two-item list')
  for j in range(2):
   for v in [-3,3,True,1.0,I(1),None,S('x'),'\x7f','\x1f']:
    d=good();d['matrix'][i][j]=v;refuse(d,'matrix entries must be exact integers -2..2')
 for key,vals in [('state',[-4,4]),('variances',[-1,4])]:
  for v in [None,(),L([0,0]),[True],[True]*3]:
   d=good();d[key]=v;refuse(d,key+' must be an exact two-item list')
  for i in range(2):
   for v in vals+[True,1.0,I(1),None]:
    d=good();d[key][i]=v;refuse(d,key+' has invalid exact integer value')
 for v in [0,6,True,1.0,I(1),None]:
  d=good();d['horizon']=v;refuse(d,'horizon must be an exact integer 1..5')
 d=good();d.update(matrix=[[None,0],None],state=None,variances=None,horizon=None);refuse(d,'matrix entries must be exact integers -2..2')
 d=good();d.update(state=[None,0],variances=None,horizon=None);refuse(d,'state has invalid exact integer value')
 d=good();d.update(variances=[None,0],horizon=None);refuse(d,'variances has invalid exact integer value')
