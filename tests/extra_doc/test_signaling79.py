import random,pytest
from fractions import Fraction as F
from sugarcode.extra_doc import signaling79 as m
class D(dict):pass
class L(list):pass
class I(int):pass

def oracle(d):
 result=[];k=len(d['offpath'])
 def pair(v):return [v.numerator,v.denominator]
 for low in range(k):
  for high in range(k):
   beliefs=[];wages=[]
   for s in range(k):
    if low==high==s:p=F(d['prior'][1],sum(d['prior']))
    elif high==s:p=F(1)
    elif low==s:p=F(0)
    else:p=F(d['offpath'][s],4)
    beliefs.append(p);wages.append(F(d['quality'][0])+p*(d['quality'][1]-d['quality'][0]))
   choices=[low,high];utilities=[wages[s]-d['costs'][t][s] for t,s in enumerate(choices)]
   # Translate all no-deviation inequalities into wage difference/cost difference.
   if any(wages[j]-wages[s]>d['costs'][t][j]-d['costs'][t][s] for t,s in enumerate(choices) for j in range(k)):continue
   result.append([choices,[pair(v) for v in beliefs],[pair(v) for v in wages],[pair(v) for v in utilities]])
 return dict(equilibria=result,claims=[False]*3)

def check(d):
 r=m.equilibria(d);assert r==oracle(d);assert set(r)=={'equilibria','claims'};assert all(v is False for v in r['claims']);assert all(type(v) is int for s,b,w,u in r['equilibria'] for row in b+w+u for v in row)

def test_bayes_cases_oracle():
 rng=random.Random(79)
 for _ in range(220):
  k=rng.randint(1,4);check(dict(quality=sorted(rng.sample(range(9),2)),prior=[rng.randint(1,4),rng.randint(1,4)],costs=[[rng.randint(0,8) for _ in range(k)] for _ in range(2)],offpath=[rng.randint(0,4) for _ in range(k)]))
 check(dict(quality=[0,8],prior=[1,4],costs=[[0]*4,[0]*4],offpath=[0,1,3,4]))
 assert m.SCOPE=='PARTIAL: exact supplied two-type finite costly-signal wage equilibria only'
 assert m.NOT_CLAIMED==('actual quality inference','real signaling equilibrium','production readiness')

def good():return dict(quality=[0,8],prior=[1,4],costs=[[0,8],[8,0]],offpath=[0,4])
def refuse(d,msg):
 with pytest.raises(ValueError) as e:m.equilibria(d)
 assert str(e.value)==msg

def test_validation():
 for v in [None,[],{},D(good()),dict(good(),extra=1)]:refuse(v,'exact dict with quality, prior, costs, offpath required')
 for key,lo,hi in [('quality',0,8),('prior',1,4)]:
  for v in [None,(),L([1,2]),[True],[True]*3]:
   d=good();d[key]=v;refuse(d,key+' must be an exact two-item list')
  for i in range(2):
   for v in [lo-1,hi+1,True,1.0,I(1),None,'1']:
    d=good();d[key][i]=v;refuse(d,key+' entries outside exact integer range')
 for q in ([0,0],[8,0]):
  d=good();d['quality']=q;refuse(d,'quality must be strictly increasing')
 for v in [None,(),L([[0],[0]]),[[0]],[[0]]*3]:
  d=good();d['costs']=v;refuse(d,'costs must be an exact two-row list')
 for i in range(2):
  for v in [None,(),L([0]),[],[0]*5]:
   d=good();d['costs'][i]=v;refuse(d,'cost rows must be exact equal-width lists of 1..4 items')
  for j in range(2):
   for v in [-1,9,True,1.0,I(1),None,'1']:
    d=good();d['costs'][i][j]=v;refuse(d,'costs must be exact integers 0..8')
 for rows in ([[0],[0,0]],[[0,0],[0]]):
  d=good();d['costs']=rows;refuse(d,'cost rows must be exact equal-width lists of 1..4 items')
 for v in [None,(),L([0,0]),[True],[True]*3]:
  d=good();d['offpath']=v;refuse(d,'offpath must be an exact signal-width list')
 for i in range(2):
  for v in [-1,5,True,1.0,I(1),None,'1']:
   d=good();d['offpath'][i]=v;refuse(d,'offpath must be exact integers 0..4')

def test_invalid_common_width_before_offpath():
 for width in (0,5):
  d=good();d['costs']=[[0]*width,[0]*width];d['offpath']=[0]*width
  refuse(d,'cost rows must be exact equal-width lists of 1..4 items')
