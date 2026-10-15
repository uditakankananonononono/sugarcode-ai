import random,pytest
from sugarcode.extra_doc import vcg_public77 as m
class D(dict):pass
class L(list):pass
class I(int):pass

def oracle(d):
 n=len(d['values']);k=len(d['costs'])
 def welfare(agents,j):return sum(d['values'][i][j] for i in agents)-d['costs'][j]
 chosen=sorted(range(k),key=lambda j:(-welfare(range(n),j),j))[0];payments=[]
 for i in range(n):
  others=[a for a in range(n) if a!=i];best=sorted(range(k),key=lambda j:(-welfare(others,j),j))[0];payments.append(welfare(others,best)-welfare(others,chosen))
 return dict(alternative=chosen,welfare=welfare(range(n),chosen),payments=payments,utilities=[d['values'][i][chosen]-payments[i] for i in range(n)],claims=[False]*3)

def check(d):
 r=m.mechanism(d);assert r==oracle(d);assert set(r)=={'alternative','welfare','payments','utilities','claims'};assert type(r['alternative']) is type(r['welfare']) is int;assert all(type(v) is int for v in r['payments']+r['utilities']);assert all(v is False for v in r['claims'])

def test_delete_agent_oracle():
 rng=random.Random(77)
 for _ in range(220):
  k=rng.randint(2,5);check(dict(values=[[rng.randint(0,8) for _ in range(k)] for _ in range(rng.randint(2,5))],costs=[rng.randint(0,10) for _ in range(k)]))
 for d in [dict(values=[[0]*5]*5,costs=[10]*5),dict(values=[[8,0],[0,8]],costs=[0,0]),dict(values=[[8,0],[0,0]],costs=[0,1])]:check(d)
 assert m.SCOPE=='PARTIAL: exact supplied finite public-alternative Clarke pivot transfers only'
 assert m.NOT_CLAIMED==('real incentive guarantee','truthful reports','production readiness')

def good():return dict(values=[[0,8],[8,0]],costs=[0,10])
def refuse(d,msg):
 with pytest.raises(ValueError) as e:m.mechanism(d)
 assert str(e.value)==msg

def test_validation():
 for v in [None,[],{},D(good()),dict(good(),extra=1)]:refuse(v,'exact dict with values and costs required')
 for v in [None,(),L([[0,0]]*2),[],[[0,0]],[[0,0]]*6]:
  d=good();d['values']=v;refuse(d,'values must be an exact list of 2..5 agent rows')
 for i in range(2):
  for v in [None,(),L([0,0]),[],[0],[0]*6]:
   d=good();d['values'][i]=v;refuse(d,'value rows must be exact equal-width lists of 2..5 items')
  for j in range(2):
   for v in [-1,9,True,1.0,I(1),None,'1']:
    d=good();d['values'][i][j]=v;refuse(d,'values must be exact integers 0..8')
 for width in (1,6):
  d=dict(values=[[0]*width]*2,costs=[0]*width);refuse(d,'value rows must be exact equal-width lists of 2..5 items')
 for rows in ([[0,0],[0,0,0]],[[0,0,0],[0,0]]):
  d=good();d['values']=rows;refuse(d,'value rows must be exact equal-width lists of 2..5 items')
 for v in [None,(),L([0,0]),[True],[True]*3]:
  d=good();d['costs']=v;refuse(d,'costs must be an exact alternative-width list')
 for i in range(2):
  for v in [-1,11,True,1.0,I(1),None,'1']:
   d=good();d['costs'][i]=v;refuse(d,'costs must be exact integers 0..10')
 d=good();d['values'][0][0]=None;d['values'][1]=None;d['costs']=None;refuse(d,'values must be exact integers 0..8')
