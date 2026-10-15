import random,itertools,copy
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc import interpolation_gap137 as m
class D(dict):pass
class L(list):pass
class I(int):pass

def data():return dict(points=[[-2,1],[0,-1],[3,2]],threshold=2)
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
 # Fit held-out polynomials by Vandermonde Gauss-Jordan elimination.
 predictions=[]
 for excluded,(x,y) in enumerate(d['points']):
  train=[r for i,r in enumerate(d['points']) if i!=excluded];n=len(train);a=[[F(t**j) for j in range(n)]+[F(v)] for t,v in train]
  for col in range(n):
   pivot=next(i for i in range(col,n) if a[i][col]);a[col],a[pivot]=a[pivot],a[col];div=a[col][col];a[col]=[v/div for v in a[col]]
   for row in range(n):
    if row==col:continue
    factor=a[row][col];a[row]=[u-factor*v for u,v in zip(a[row],a[col])]
  predictions.append(sum(a[j][-1]*x**j for j in range(n)))
 mse=sum((p-y)**2 for p,(x,y) in zip(predictions,d['points']))/len(predictions)
 return dict(predictions=[[p.numerator,p.denominator] for p in predictions],loo_mse=[mse.numerator,mse.denominator],training_mse=[0,1],exceeds=mse>d['threshold'],claims=[False]*3)
def expect(d,msg):
 with pytest.raises(ValueError) as e:m.diagnose(d)
 assert str(e.value)==msg

def test_vandermonde_oracle():
 rng=random.Random(137)
 for _ in range(150):
  n=rng.randint(2,6);d=dict(points=[[x,rng.randint(-3,3)] for x in rng.sample(range(-3,4),n)],threshold=rng.randint(0,9));exact(m.diagnose(d),oracle(d))
 for n,threshold in itertools.product([2,6],[0,9]):
  for y in [-3,0,3]:
   d=dict(points=[[x,y] for x in range(-3,-3+n)],threshold=threshold);exact(m.diagnose(d),oracle(d))
 for threshold,exceeds in [(0,True),(1,False),(2,False)]:
  d=dict(points=[[0,0],[1,1]],threshold=threshold);exact(m.diagnose(d),oracle(d));assert m.diagnose(d)['exceeds'] is exceeds
 d=data();saved=copy.deepcopy(d);expected=oracle(d);result=m.diagnose(d);assert d==saved;exact(result,expected);result['predictions'][0][0]=99;exact(m.diagnose(d),expected)
 assert m.SCOPE=='PARTIAL: exact supplied polynomial interpolation leave-one-out gap only'
 assert m.NOT_CLAIMED==('actual overfitting detection','prevention','generalization guarantee')

def test_types_caps_order():
 for v in [None,[],{},D(data()),dict(data(),extra=1)]:expect(v,'exact dict with points and threshold required')
 for v in [None,(),L([[0,0],[1,1]]),[],[[0,0]],[[0,0]]*7]:expect(dict(points=v,threshold=0),'points must be an exact list of 2..6 pairs')
 for position in [0,1,2]:
  for row in [None,(),L([1,1]),[],[1],[1]*3]:
   d=data();d['points'][position]=row;expect(d,'points must contain exact two-value lists')
  for index in [0,1]:
   for v in [-4,4,True,1.0,I(1),None,'1']:
    d=data();d['points'][position][index]=v;expect(d,'coordinates must be exact integers -3..3')
 d=data();d['points'][1][0]=-2;expect(d,'x coordinates must be distinct')
 for v in [-1,10,True,1.0,I(1),None,'1']:
  d=data();d['threshold']=v;expect(d,'threshold must be an exact integer 0..9')
 d=data();d['points'][0][0]=True;d['points'][1]=None;expect(d,'coordinates must be exact integers -3..3')
