import random,itertools,pytest
from fractions import Fraction as F
from sugarcode.extra_doc import mixed_nash76 as m
class D(dict):pass
class L(list):pass
class I(int):pass

def oracle(d):
 # Finite candidate grid includes every possible indifference probability for
 # integer differences -10..10, then checks expected best response inequalities.
 a=d['row'];b=d['column'];grid={F(0),F(1)}
 for x in range(1,11):
  for y in range(1,11):grid.add(F(x,x+y))
 valid=[]
 def best_responses(p,q):
  r0=q*a[0][0]+(1-q)*a[0][1];r1=q*a[1][0]+(1-q)*a[1][1];c0=p*b[0][0]+(1-p)*b[1][0];c1=p*b[0][1]+(1-p)*b[1][1]
  return (p==0 or r0>=r1) and (p==1 or r1>=r0) and (q==0 or c0>=c1) and (q==1 or c1>=c0)
 ps={F(0),F(1)}|{p for p in grid if p*b[0][0]+(1-p)*b[1][0]==p*b[0][1]+(1-p)*b[1][1]}
 qs={F(0),F(1)}|{q for q in grid if q*a[0][0]+(1-q)*a[0][1]==q*a[1][0]+(1-q)*a[1][1]}
 for p in ps:
  for q in qs:
   if best_responses(p,q):valid.append((p,q))
 return dict(equilibria=[[[p.numerator,p.denominator],[q.numerator,q.denominator]] for p,q in sorted(valid)],claims=[False]*3)

def test_candidate_grid():
 rng=random.Random(76);fixtures=[]
 while len(fixtures)<110:
  a=[[rng.randint(-5,5) for _ in range(2)] for _ in range(2)];b=[[rng.randint(-5,5) for _ in range(2)] for _ in range(2)]
  if any(a[0][j]==a[1][j] for j in range(2)) or any(b[i][0]==b[i][1] for i in range(2)):continue
  fixtures.append(dict(row=a,column=b))
 for d in fixtures:
  r=m.solve(d);assert r==oracle(d);assert set(r)=={'equilibria','claims'};assert all(v is False for v in r['claims']);assert all(type(v) is int for e in r['equilibria'] for pair in e for v in pair)
 assert m.SCOPE=='PARTIAL: exact nondegenerate supplied 2x2 complete Nash equilibria only'
 assert m.NOT_CLAIMED==('real competitive stability','general game solver','production readiness')

def good():return dict(row=[[5,-5],[-5,5]],column=[[-5,5],[5,-5]])
def refuse(d,msg):
 with pytest.raises(ValueError) as e:m.solve(d)
 assert str(e.value)==msg

def test_validation_and_strict_domain():
 for v in [None,[],{},D(good()),dict(good(),extra=1)]:refuse(v,'exact dict with row and column required')
 for key in ('row','column'):
  for v in [None,(),L([[0,0]]*2),[[0,0]],[[0,0]]*3]:
   d=good();d[key]=v;refuse(d,'payoff matrix must be an exact two-row list')
  for i in range(2):
   for v in [None,(),L([0,0]),[True],[True]*3]:
    d=good();d[key][i]=v;refuse(d,'payoff row must be an exact two-item list')
   for j in range(2):
    for v in [-6,6,True,1.0,I(1),None,'1']:
     d=good();d[key][i][j]=v;refuse(d,'payoffs must be exact integers -5..5')
 for j in range(2):
  d=good();d['row'][1][j]=d['row'][0][j];refuse(d,'strict endpoint payoff differences required')
 for i in range(2):
  d=good();d['column'][i][1]=d['column'][i][0];refuse(d,'strict endpoint payoff differences required')
 d=good();d['row'][0][0]=None;d['column']=None;refuse(d,'payoffs must be exact integers -5..5')
 for d in [good(),dict(row=[[5,0],[0,5]],column=[[5,0],[0,5]]),dict(row=[[5,5],[0,0]],column=[[5,0],[5,0]])]:assert m.solve(d)==oracle(d)
