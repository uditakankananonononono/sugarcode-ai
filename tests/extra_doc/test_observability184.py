import random,pytest
from fractions import Fraction as F
from copy import deepcopy
from sugarcode.extra_doc import observability184 as m
class D(dict):pass
class L(list):pass
class I(int):pass
class S(str):pass
class T(tuple):pass

def oracle(d):
 # Impulse-response columns, independently evolve each initial basis vector.
 columns=[]
 for initial in ([1,0],[0,1]):
  x=initial;col=[]
  for _ in range(d['horizon']):
   col.append(sum(a*b for a,b in zip(d['sensor'],x)));x=[sum(a*b for a,b in zip(row,x)) for row in d['matrix']]
  columns.append(col)
 rows=[list(row) for row in zip(*columns)];reduced=[[F(x) for x in row] for row in rows];pivots=[];p=0
 for j in range(2):
  candidate=next((i for i in range(p,len(rows)) if reduced[i][j]),None)
  if candidate is None:continue
  reduced[p],reduced[candidate]=reduced[candidate],reduced[p];scale=reduced[p][j];reduced[p]=[x/scale for x in reduced[p]]
  for i in range(len(rows)):
   if i!=p:
    factor=reduced[i][j];reduced[i]=[a-factor*b for a,b in zip(reduced[i],reduced[p])]
  pivots.append(j);p+=1
 basis=[]
 for j in range(2):
  if j not in pivots:
   v=[F(0),F(0)];v[j]=F(1)
   for i,k in enumerate(pivots):v[k]=-reduced[i][j]
   basis.append(v)
 def pair(v):return [v.numerator,v.denominator]
 return dict(observations=rows,gramian=[[sum(a*b for a,b in zip(x,y)) for y in columns] for x in columns],rank=len(pivots),unobservable_basis=[[pair(x) for x in row] for row in basis],claims=[False]*3)

def check(d):
 old=deepcopy(d);r=m.analyze(d);assert d==old;assert r==oracle(d);assert list(r)==['observations','gramian','rank','unobservable_basis','claims'];assert all(v is False for v in r['claims'])
 def typed(v):
  if isinstance(v,list):assert type(v) is list;[typed(x) for x in v]
  else:assert type(v) is int
 for k in list(r)[:-1]:typed(r[k])

def good():return dict(matrix=[[-2,2],[2,-2]],sensor=[-2,2],horizon=5)
def test_gauss_jordan():
 rng=random.Random(184)
 for _ in range(220):check(dict(matrix=[[rng.randint(-2,2) for _ in range(2)] for _ in range(2)],sensor=[rng.randint(-2,2) for _ in range(2)],horizon=rng.randint(1,5)))
 for sensor in ([0,0],[0,1],[1,0]):check(dict(matrix=[[1,0],[0,1]],sensor=sensor,horizon=5))
 assert m.SCOPE=='PARTIAL: exact supplied two-state finite-horizon observability matrix and nullspace only'
 assert m.NOT_CLAIMED==('identified real dynamics','noisy state estimation','production readiness')

def refuse(d,msg):
 old=deepcopy(d)
 with pytest.raises(ValueError) as e:m.analyze(d)
 assert str(e.value)==msg;assert d==old

def test_validation():
 for v in [None,[],{},D(good()),dict(good(),extra=1),S('x'),T(())]:refuse(v,'exact dict with matrix, sensor, horizon required')
 for v in [None,(),L([[0,0]]*2),[True],[True]*3]:
  d=good();d['matrix']=v;refuse(d,'matrix must be an exact two-row list')
 for i in range(2):
  for v in [None,(),T((0,0)),L([0,0]),[True],[True]*3]:
   d=good();d['matrix'][i]=v;refuse(d,'matrix row must be an exact two-item list')
  for j in range(2):
   for v in [-3,3,True,1.0,I(1),None,S('x'),'\x7f','\x1f']:
    d=good();d['matrix'][i][j]=v;refuse(d,'matrix entries must be exact integers -2..2')
 for v in [None,(),L([0,0]),[True],[True]*3]:
  d=good();d['sensor']=v;refuse(d,'sensor must be an exact two-item list')
 for i in range(2):
  for v in [-3,3,True,1.0,I(1),None]:
   d=good();d['sensor'][i]=v;refuse(d,'sensor entries must be exact integers -2..2')
 for v in [0,6,True,1.0,I(1),None]:
  d=good();d['horizon']=v;refuse(d,'horizon must be an exact integer 1..5')
 d=good();d.update(matrix=[[None,0],None],sensor=None,horizon=None);refuse(d,'matrix entries must be exact integers -2..2')
 d=good();d.update(sensor=[None,0],horizon=None);refuse(d,'sensor entries must be exact integers -2..2')
