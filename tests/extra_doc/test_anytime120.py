import itertools,random,copy
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc import anytime120 as m
class D(dict):pass
class L(list):pass
class I(int):pass

def data():return dict(outcomes=[1,1,1,0],alternative=[3,4],alpha=[1,2])
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
 # Prefix binomial sequence probabilities divided by fair-null sequence mass.
 p=F(*d['alternative']);es=[F(1)];bounds=[]
 for time in range(1,len(d['outcomes'])+1):
  ones=sum(d['outcomes'][:time]);es.append(p**ones*(1-p)**(time-ones)*2**time);bounds.append(min(F(1),min(1/v for v in es)))
 crossing=next((i+1 for i,b in enumerate(bounds) if b<=F(*d['alpha'])),None)
 def pair(x):return [x.numerator,x.denominator]
 return dict(evalues=[pair(x) for x in es[1:]],bounds=[pair(x) for x in bounds],first_crossing=crossing,claims=[False]*3)
def expect(d,msg):
 with pytest.raises(ValueError) as e:m.analyze(d)
 assert str(e.value)==msg

def test_prefix_probability_oracle():
 for length in range(1,9):
  for bits in itertools.product([0,1],repeat=length):
   d=dict(outcomes=list(bits),alternative=[3,4],alpha=[1,2]);exact(m.analyze(d),oracle(d))
 rng=random.Random(120);fractions=[[a,b] for b in range(2,13) for a in range(1,b)];alts=[x for x in fractions if 2*x[0]>x[1]]
 for _ in range(120):
  d=dict(outcomes=[rng.randrange(2) for i in range(rng.randint(1,8))],alternative=rng.choice(alts),alpha=rng.choice(fractions));exact(m.analyze(d),oracle(d))
 d=dict(outcomes=[1,0,1],alternative=[3,4],alpha=[2,3]);assert m.analyze(d)['first_crossing']==1;exact(m.analyze(d),oracle(d))
 d=data();saved=copy.deepcopy(d);expected=oracle(d);result=m.analyze(d);assert d==saved;exact(result,expected);result['bounds'][0][0]=99;exact(m.analyze(d),expected)
 assert m.SCOPE=='PARTIAL: exact supplied-bit fixed-alternative running e-process only'
 assert m.NOT_CLAIMED==('manipulation prevention','assumptions verification','production readiness')

def test_types_caps_order():
 for v in [None,[],{},D(data()),dict(data(),extra=1)]:expect(v,'exact dict with outcomes, alternative, alpha required')
 for v in [None,(),L([1]),[],[1]*9]:expect(dict(outcomes=v,alternative=[3,4],alpha=[1,2]),'outcomes must be an exact list of 1..8 bits')
 for position in range(4):
  for v in [-1,2,True,1.0,I(1),None,'1']:
   d=data();d['outcomes'][position]=v;expect(d,'outcomes must be exact integer bits')
 for name in ['alternative','alpha']:
  for v in [None,(),L([3,4]),[],[1],[1]*3]:
   d=data();d[name]=v;expect(d,name+' must be an exact two-value fraction list')
  for v in [[0,2],[1,1],[2,1],[1,13],[True,2],[1,True],[1.0,2],[1,2.0],[I(1),2],[1,I(2)],['1',2]]:
   d=data();d[name]=v;expect(d,name+' requires integers 1 <= numerator < denominator <= 12')
 for v in [[1,2],[1,3],[6,12]]:
  d=data();d['alternative']=v;expect(d,'alternative must exceed one half')
 d=data();d['alternative']=[1,2];d['alpha']=None;expect(d,'alpha must be an exact two-value fraction list')
