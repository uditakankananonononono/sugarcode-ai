import random,itertools,copy,math
import pytest
from sugarcode.extra_doc import polynomial_features134 as m
class D(dict):pass
class L(list):pass
class I(int):pass

def data():return {'rows':[[1,2],[-2,0]],'degree':2}
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
 width=len(d['rows'][0]);terms=[];features=[]
 # Multisets of coordinate factors, not Cartesian exponent filtering.
 for size in range(d['degree']+1):
  for factors in itertools.combinations_with_replacement(range(width),size):
   terms.append(([factors.count(i) for i in range(width)],factors))
 for row in d['rows']:features.append([math.prod(row[i] for i in factors) for e,factors in terms])
 return dict(exponents=[e for e,factors in terms],features=features,claims=[False]*3)
def expect(d,msg):
 with pytest.raises(ValueError) as e:m.expand(d)
 assert str(e.value)==msg

def test_factor_multiset_oracle():
 rng=random.Random(134)
 for _ in range(200):
  width=rng.randint(1,4);d={'rows':[[rng.randint(-3,3) for j in range(width)] for i in range(rng.randint(1,6))],'degree':rng.randint(1,3)};exact(m.expand(d),oracle(d))
 for n,width,degree,value in itertools.product([1,6],[1,4],[1,3],[-3,0,3]):
  d={'rows':[[value]*width]*n,'degree':degree};exact(m.expand(d),oracle(d))
 d=data();saved=copy.deepcopy(d);expected=oracle(saved);result=m.expand(d);assert d==saved;exact(result,expected);result['features'][0][0]=99;exact(m.expand(d),expected);assert d==saved
 assert m.SCOPE=='PARTIAL: exact supplied total-degree polynomial feature expansion only'
 assert m.NOT_CLAIMED==('informative features','model improvement','production readiness')

def test_types_caps_order():
 for v in [None,[],{},D(data()),dict(data(),extra=1)]:expect(v,'exact dict with rows and degree required')
 for v in [None,(),L([[0]]),[],[[0]]*7]:expect({'rows':v,'degree':1},'rows must be an exact list of 1..6 vectors')
 for row in [None,(),L([0]),[],[0]*5]:expect({'rows':[row],'degree':1},'vectors must be exact lists of 1..4 values')
 for v in [-4,4,True,1.0,I(1),None,'1']:
  d=data();d['rows'][0][0]=v;expect(d,'values must be exact integers -3..3')
 d=data();d['rows'][1]=[0];expect(d,'vector widths must match')
 for v in [0,4,True,1.0,I(1),None,'1']:
  d=data();d['degree']=v;expect(d,'degree must be an exact integer 1..3')
 d=data();d['rows'][0][0]=True;d['rows'][1]=None;expect(d,'values must be exact integers -3..3')
