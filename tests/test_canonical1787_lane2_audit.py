import itertools as it,copy,random,pytest
from sugarcode.extra_doc import canonical1787 as m
class I(int):pass
class T(tuple):pass
class L(list):pass
class S(str):pass

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

def oracle(a):
 n=len(a);outcomes=[]
 for bits in range(2**n):
  if bits&1:continue
  p=tuple((bits//2**i)%2 for i in range(n));bad=[]
  for i,j in it.combinations(range(n),2):
   if a[i][j]==1 and p[i]!=p[j] or a[i][j]==-1 and p[i]==p[j]:bad.append((i,j))
  outcomes.append((len(bad),p,bad))
 minimum=min(x[0] for x in outcomes);selected=sorted((p,bad) for s,p,bad in outcomes if s==minimum)
 return dict(frustration_index=minimum,optimal_partitions=[p for p,b in selected],violated_edges=[b for p,b in selected],balanced=minimum==0,trust_validated=False)

def mat(n,signs):
 a=[[0]*n for _ in range(n)]
 for (i,j),v in zip(it.combinations(range(n),2),signs):a[i][j]=a[j][i]=v
 return tuple(map(tuple,a))

def test_allcolourings():
 for n in range(2,5):
  for signs in it.product((-1,0,1),repeat=n*(n-1)//2):
   a=mat(n,signs);old=copy.deepcopy(a);exact(m.balance(a),oracle(a));assert a==old
 rng=random.Random(1787002)
 for _ in range(160):
  a=mat(5,[rng.randint(-1,1) for j in range(10)]);exact(m.balance(a),oracle(a))
 for sign in (-1,0,1):exact(m.balance(mat(5,[sign]*10)),oracle(mat(5,[sign]*10)))
 assert m.SCOPE=='PARTIAL: caller signed-network frustration index and optimal balance partitions'
 assert m.NOT_CLAIMED==('verified trust','relationship inference','social diagnosis')

def fail(a,msg):
 old=copy.deepcopy(a)
 with pytest.raises(ValueError) as e:m.balance(a)
 assert str(e.value)==msg;assert a==old

def test_validation():
 for a in (None,[],L(),T(((0,0),(0,0))),(),((0,),),((0,)*6,)*6):fail(a,'adjacency exact tuple2..5')
 for pos in range(5):
  for row in (None,[],T((0,)*5),(),(0,)*4,(0,)*6):
   a=[(0,)*5]*5;a[pos]=row;fail(tuple(a),'row exact tupleN')
  for col in range(5):
   for bad in (-2,2,True,I(0),0.0,None,S('0'),chr(31),chr(32),chr(126),chr(127)):
    a=[[0]*5 for _ in range(5)];a[pos][col]=bad;fail(tuple(map(tuple,a)),'edge exact int-1/0/1')
  a=[[0]*5 for _ in range(5)];a[pos][pos]=1;fail(tuple(map(tuple,a)),'diagonal must be zero')
 for i,j in it.combinations(range(5),2):
  a=[[0]*5 for _ in range(5)];a[i][j]=1;fail(tuple(map(tuple,a)),'adjacency must be symmetric')
 fail(((1,None),None),'edge exact int-1/0/1')
 fail(((1,0),None),'row exact tupleN')
 fail(((1,1),(0,0)),'diagonal must be zero')
