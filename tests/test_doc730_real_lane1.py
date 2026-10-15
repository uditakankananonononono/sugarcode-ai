import random,pytest
from fractions import Fraction as F
from sugarcode.extra_doc import recurrence730 as m

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

def test_independent_offset_diagonal_segmentation():
 rng=random.Random(730)
 for _ in range(200):
  a=[rng.randint(-5,5) for i in range(rng.randint(1,8))];b=[rng.randint(-5,5) for i in range(rng.randint(1,8))];tol=rng.randint(0,10);minimum=rng.randint(1,8);cells={(i,j) for i,x in enumerate(a) for j,y in enumerate(b) if y-tol<=x<=y+tol};runs=[]
  for offset in range(-len(a)+1,len(b)):
   current=[]
   for i in range(len(a)+1):
    j=i+offset
    if i<len(a) and (i,j) in cells:current.append((i,j))
    elif current:runs.append((*current[0],len(current)));current=[]
  runs.sort();covered=sum(n for i,j,n in runs if n>=minimum);exact(m.diagnose(a,b,tol,minimum),dict(matrix=[[int((i,j) in cells) for j in range(len(b))] for i in range(len(a))],diagonals=runs,recurrence=F(len(cells),len(a)*len(b)),determinism=F(covered,len(cells)) if cells else None,rapport_validated=False))
 exact(m.diagnose([0,1],[0,1],0,2),dict(matrix=[[1,0],[0,1]],diagonals=[(0,0,2)],recurrence=F(1,2),determinism=F(1),rapport_validated=False))
 assert m.diagnose([-5],[5],0,1)['determinism'] is None
class L(list):pass
class I(int):pass

def error(args,msg):
 with pytest.raises(ValueError) as exc:m.diagnose(*args)
 assert str(exc.value)==msg

def test_validation_types_caps():
 for pos in (0,1):
  for value in (None,(),L([0]),[],[0]*9):
   args=[[0],[0],0,1];args[pos]=value;error(args,'sequence must be exact list1..8')
  for badpos in range(8):
   for value in (True,1.0,I(1),None,-6,6):
    args=[[0]*8,[0]*8,0,1];args[pos][badpos]=value;error(args,'values must be exact ints-5..5')
 for value in (True,1.0,I(1),None,-1,11):error([[0],[0],value,1],'tolerance must be exact int0..10')
 for value in (True,1.0,I(1),None,0,9):error([[0],[0],0,value],'minimum must be exact int1..8')
 for x in (-5,5):
  for tol in (0,10):
   for mini in (1,8):assert len(m.diagnose([x]*8,[x]*8,tol,mini)['matrix'])==8
 assert m.SCOPE=='PARTIAL: exact supplied cross-recurrence matrix and diagonal determinism'
 assert m.NOT_CLAIMED==('rapport inference','causal coordination','valid observations','production readiness')
