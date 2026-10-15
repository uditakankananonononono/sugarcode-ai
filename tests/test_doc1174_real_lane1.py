import pytest,random
from fractions import Fraction as F
from sugarcode.extra_doc import decision_curve1174 as m
def exact(a,b):
 assert type(a) is type(b)
 if type(b) is dict:
  assert list(a)==list(b)
  for k in b:exact(a[k],b[k])
 elif type(b) in (list,tuple):
  assert len(a)==len(b)
  for x,y in zip(a,b):exact(x,y)
 elif type(b) is bool:assert a is b
 else:assert a==b


def test_independent_utility_units_oracle():
 rng=random.Random(1174)
 for _ in range(200):
  rows=[(str(i),rng.randint(0,10),10,rng.randrange(2)) for i in range(rng.randint(1,24))];ts=tuple(rng.sample(range(1,100),rng.randint(1,8)));expected=[]
  for t in ts:
   units=[];allunits=[];tp=fp=0
   for label,a,b,y in rows:
    score=F(a,b);unit=(100-t) if y else -t;allunits.append(unit)
    if score>=F(t,100):units.append(unit);tp+=y;fp+=1-y
   expected.append((t,tp,fp,F(sum(units),len(rows)*(100-t)),F(sum(allunits),len(rows)*(100-t)),F(0)))
  exact(m.curve(rows,ts),{'curve':expected,'clinical_validated':False})
 exact(m.curve([('Z'*24,1,2,1),('x'*24,0,10,0)],(50,99)),{'curve':[(50,1,0,F(1,2),F(0),F(0)),(99,0,0,F(0),F(-49),F(0))],'clinical_validated':False})

class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass

def test_types_caps_order_validation():
 row=('a',1,2,1)
 for rows in (None,(),L([row]),[],[row]*25):
  with pytest.raises(ValueError,match='rows must be exact list1..24'):m.curve(rows,(50,))
 for ts in (None,[],T((50,)),(),tuple(range(1,10))):
  with pytest.raises(ValueError,match='thresholds must be exact tuple1..8'):m.curve([row],ts)
 for ts in ((0,),(100,),(True,),(1.0,),(I(1),),(50,50)):
  with pytest.raises(ValueError,match='unique exact thresholds'):m.curve([row],ts)
 for r in (None,list(row),T(row),row[:-1],row+(1,)):
  with pytest.raises(ValueError,match='row must be exact tuple4'):m.curve([r],(50,))
 for label in ('','x'*25,'\x00','\u200b',S('a')):
  with pytest.raises(ValueError,match='labels must be unique'):m.curve([(label,1,2,1)],(50,))
 with pytest.raises(ValueError,match='labels must be unique'):m.curve([row,row],(50,))
 for pos in (1,2,3):
  for v in (True,1.0,I(1),None,-1,11):
   r=list(row);r[pos]=v
   with pytest.raises(ValueError):m.curve([tuple(r)],(50,))
 for a,b,y in ((0,1,0),(10,10,1),(1,1,0),(0,10,1)):
  assert m.curve([('a',a,b,y)],(1,99))
 with pytest.raises(ValueError):m.curve([('a',2,1,0)],(50,))
 with pytest.raises(ValueError):m.curve([('a',0,0,0)],(50,))
 with pytest.raises(ValueError):m.curve([('a',1,2,2)],(50,))
 assert len(m.curve([(str(i),1,2,1) for i in range(24)],tuple(range(1,9)))['curve'])==8
 assert m.SCOPE=='PARTIAL: exact supplied threshold decision-curve arithmetic only'
 assert m.NOT_CLAIMED==('calibration','clinical utility','screening advice','production readiness')


@pytest.mark.parametrize('label',['\u200b','\x00','\n','\x7f','\x85','\ue000','\ud800','\u0378','Ω-1'])
def test_printable_ascii_label_guard(label):
 with pytest.raises(ValueError,match='labels must be unique printable ASCII strings1..24'):
  m.curve([(label,1,2,1)],(50,))

@pytest.mark.parametrize('label',[' ','   ','x'*24])
def test_printable_ascii_spaces_and_cap_accepted(label):
 assert m.curve([(label,1,2,1)],(50,))['curve'][0][1]==1
