import random,itertools,copy
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc import polya_generate145 as m
class D(dict):pass
class L(list):pass
class I(int):pass

def data():return dict(prior=[1,1],observed=[1,2],length=4,quantile=[1,2])
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
 a,b=[sum(x) for x in zip(d['prior'],d['observed'])];masses=[F(0) for _ in range(d['length']+1)]
 # Sequential reinforced-urn probability of each ordered binary sequence.
 for bits in itertools.product([0,1],repeat=d['length']):
  successes,failures=a,b;weight=F(1)
  for bit in bits:
   weight*=F(successes if bit else failures,successes+failures)
   successes+=bit;failures+=1-bit
  masses[sum(bits)]+=weight
 q=F(*d['quantile']);draw=next(k for k in range(len(masses)) if sum(masses[:k+1])>q)
 return dict(parameters=[a,b],masses=[[x.numerator,x.denominator] for x in masses],draw=draw,claims=[False]*3)
def expect(d,msg):
 with pytest.raises(ValueError) as e:m.generate(d)
 assert str(e.value)==msg

def test_sequence_urn_oracle():
 rng=random.Random(145);qs=[[a,b] for b in range(1,13) for a in range(b)]
 for _ in range(180):
  d=dict(prior=[rng.randint(1,4) for _ in range(2)],observed=[rng.randint(0,4) for _ in range(2)],length=rng.randint(1,6),quantile=rng.choice(qs));exact(m.generate(d),oracle(d))
 for prior,observed,length,q in itertools.product([[1,1],[4,4],[1,4]],[[0,0],[4,4]],[1,6],[[0,1],[11,12]]):
  d=dict(prior=prior,observed=observed,length=length,quantile=q);exact(m.generate(d),oracle(d))
 for q in [[0,1],[1,3],[2,3]]:
  d=dict(prior=[1,1],observed=[0,0],length=2,quantile=q);exact(m.generate(d),oracle(d))
 d=data();saved=copy.deepcopy(d);expected=oracle(d);result=m.generate(d);assert d==saved;exact(result,expected);result['parameters'][0]=99;result['masses'][0][0]=99;exact(m.generate(d),expected)
 assert m.SCOPE=='PARTIAL: exact beta-Bernoulli predictive count and supplied-quantile draw only'
 assert m.NOT_CLAIMED==('general generative modeling','random sampling','empirical model validity')

def test_types_caps_order():
 for v in [None,[],{},D(data()),dict(data(),extra=1)]:expect(v,'exact dict with prior, observed, length, quantile required')
 for name,lower in [('prior',1),('observed',0)]:
  for v in [None,(),L([1,1]),[],[1],[1]*3]:
   d=data();d[name]=v;expect(d,name+' must be an exact two-value list')
  for v in [lower-1,5,True,1.0,I(1),None,'1']:
   d=data();d[name][0]=v;expect(d,name+' values must be exact integers '+str(lower)+'..4')
 for v in [0,7,True,1.0,I(1),None,'1']:
  d=data();d['length']=v;expect(d,'length must be an exact integer 1..6')
 for v in [None,(),L([0,1]),[],[1],[1]*3]:
  d=data();d['quantile']=v;expect(d,'quantile must be an exact two-value list')
 for v in [[-1,2],[0,0],[2,2],[0,13],[True,2],[0,True],[0.0,2],[0,2.0],[I(0),2],[0,I(2)],['0',2]]:
  d=data();d['quantile']=v;expect(d,'quantile requires integers 0 <= numerator < denominator <= 12')
 d=data();d['prior']=[True,1];d['observed']=None;expect(d,'prior values must be exact integers 1..4')
