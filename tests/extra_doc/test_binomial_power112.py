import copy,itertools,random
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc import binomial_power112 as m
class D(dict):pass
class L(list):pass
class I(int):pass

def data():return dict(alpha=[1,4],alternative=[3,4],target=[1,2],maximum=8)
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
 powers=[];p=F(*d['alternative']);alpha=F(*d['alpha'])
 # Enumerate ordered Bernoulli outcomes, not binomial coefficients.
 for n in range(1,d['maximum']+1):
  outcomes=list(itertools.product([0,1],repeat=n));counts=[sum(x) for x in outcomes];reject={k for k in set(counts) if F(sum(c>=k for c in counts),len(counts))<=alpha}
  probability=F(0)
  for outcome in outcomes:
   if sum(outcome) in reject:
    weight=F(1)
    for bit in outcome:weight*=p if bit else 1-p
    probability+=weight
  powers.append([probability.numerator,probability.denominator])
 minimum=next((i+1 for i,power in enumerate(powers) if F(*power)>=F(*d['target'])),None)
 return dict(powers=powers,minimum=minimum,claims=[False]*3)
def expect(d,msg):
 with pytest.raises(ValueError) as e:m.search(d)
 assert str(e.value)==msg

def test_outcome_enumeration_oracle():
 rng=random.Random(112);fractions=[[a,b] for b in range(2,13) for a in range(1,b)];alts=[x for x in fractions if 2*x[0]>x[1]]
 for _ in range(120):
  d=dict(alpha=rng.choice(fractions),alternative=rng.choice(alts),target=rng.choice(fractions),maximum=rng.randint(1,8));exact(m.search(d),oracle(d))
 for alpha,target,maximum in itertools.product([[1,2],[1,12],[11,12]],[[1,12],[11,12]],[1,8]):
  d=dict(alpha=alpha,alternative=[11,12],target=target,maximum=maximum);exact(m.search(d),oracle(d))
 d=data();expected=oracle(d);saved=copy.deepcopy(d);result=m.search(d);assert d==saved;exact(result,expected);result['powers'][0][0]=99;exact(m.search(d),expected)
 assert m.search(dict(alpha=[1,2],alternative=[3,4],target=[3,4],maximum=8))['minimum']==1
 assert m.search(dict(alpha=[1,12],alternative=[3,4],target=[11,12],maximum=1))['minimum'] is None
 assert m.SCOPE=='PARTIAL: exact bounded one-sided fair-binomial sample-size search only'
 assert m.NOT_CLAIMED==('general power analysis','assumptions verification','production readiness')

def test_types_caps_order():
 for v in [None,[],{},D(data()),dict(data(),extra=1)]:expect(v,'exact dict with alpha, alternative, target, maximum required')
 for name in ['alpha','alternative','target']:
  for v in [None,(),L([3,4]),[],[1],[1,2,3]]:
   d=data();d[name]=v;expect(d,name+' must be an exact two-integer fraction list')
  for v in [[0,2],[1,1],[2,1],[1,13],[True,2],[1,True],[1.0,2],[1,2.0],[I(1),2],[1,I(2)],['1',2]]:
   d=data();d[name]=v;expect(d,name+' requires integers 1 <= numerator < denominator <= 12')
 for alternative in [[1,2],[1,3],[6,12]]:
  d=data();d['alternative']=alternative;expect(d,'alternative must exceed one half')
 for v in [0,9,True,1.0,I(1),None,'1']:
  d=data();d['maximum']=v;expect(d,'maximum must be an exact integer 1..8')
 d=data();d['alpha']=[0,2];d['alternative']=None;expect(d,'alpha requires integers 1 <= numerator < denominator <= 12')
 d=data();d['alternative']=[1,2];d['target']=None;expect(d,'target must be an exact two-integer fraction list')
