import random,itertools,copy
import pytest
from sugarcode.extra_doc import backdoor113 as m
class D(dict):pass
class L(list):pass
class I(int):pass

def data():return dict(parents=[[],[0],[0,1]],treatment=1,outcome=2)
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
 parents=d['parents'];n=len(parents);t=d['treatment'];y=d['outcome'];arrows={(p,i) for i,row in enumerate(parents) for p in row}
 # Transitive closure for descendants, then direct active simple-path enumeration.
 reach=set(arrows)
 for k in range(n):
  reach|={(i,j) for i,j in itertools.product(range(n),repeat=2) if (i,k) in reach and (k,j) in reach}
 descendants=sorted(j for i,j in reach if i==t);arrows={e for e in arrows if e[0]!=t};reach2=set(arrows)
 for k in range(n):reach2|={(i,j) for i,j in itertools.product(range(n),repeat=2) if (i,k) in reach2 and (k,j) in reach2}
 paths=[]
 for length in range(n-1):
  for middle in itertools.permutations([i for i in range(n) if i not in [t,y]],length):
   path=[t,*middle,y]
   if all((a,b) in arrows or (b,a) in arrows for a,b in zip(path,path[1:])):paths.append(path)
 allowed=[i for i in range(n) if i not in [t,y] and i not in descendants];results=[]
 for mask in range(1<<len(allowed)):
  z={allowed[i] for i in range(len(allowed)) if mask>>i&1};active=False
  for path in paths:
   open_path=True
   for a,b,c in zip(path,path[1:],path[2:]):
    collider=(a,b) in arrows and (c,b) in arrows
    if collider:
     if b not in z and not any((b,k) in reach2 for k in z):open_path=False
    elif b in z:open_path=False
   if open_path:active=True
  if not active:results.append(sorted(z))
 return dict(adjustment_sets=sorted(results,key=lambda x:(len(x),x)),descendants=descendants,claims=[False]*3)
def expect(d,msg):
 with pytest.raises(ValueError) as e:m.identify(d)
 assert str(e.value)==msg

def test_active_paths_oracle():
 rng=random.Random(113)
 for _ in range(180):
  n=rng.randint(2,6);t,y=rng.sample(range(n),2);d=dict(parents=[[j for j in range(i) if rng.randrange(2)] for i in range(n)],treatment=t,outcome=y);exact(m.identify(d),oracle(d))
 # Common cause, mediated common cause, collider and collider descendant.
 for parents,t,y in [([[],[0],[0,1]],1,2),([[],[0],[0],[1,2]],1,2),([[],[],[0,1],[2]],0,1),([[],[0],[1],[0]],2,3),([[],[],[],[0,1],[1,2],[3]],0,2),([[],[0],[1],[2],[3],[4]],0,5),([[],[],[],[],[],[]],0,5)]:
  d=dict(parents=parents,treatment=t,outcome=y);exact(m.identify(d),oracle(d))
 for t,y in [(0,1),(1,0)]:exact(m.identify(dict(parents=[[],[0]],treatment=t,outcome=y)),oracle(dict(parents=[[],[0]],treatment=t,outcome=y)))
 d=data();saved=copy.deepcopy(d);expected=oracle(d);result=m.identify(d);assert d==saved;exact(result,expected);result['adjustment_sets'][0].append(99);exact(m.identify(d),expected)
 assert m.SCOPE=='PARTIAL: exact supplied ordered-DAG graphical backdoor sets only'
 assert m.NOT_CLAIMED==('graph truth','hidden-confounder detection','causal effect estimation')

def test_types_caps_order():
 for v in [None,[],{},D(data()),dict(data(),extra=1)]:expect(v,'exact dict with parents, treatment, outcome required')
 for v in [None,(),L([[],[]]),[],[[]],[[]]*7]:expect(dict(parents=v,treatment=0,outcome=1),'parents must be an exact list of 2..6 rows')
 for v in [None,(),L([]),[0]]:
  d=data();d['parents'][0]=v;expect(d,'parent rows must be exact lists of at most their index entries')
 for v in [-1,1,True,0.0,I(0),None,'0']:
  d=data();d['parents'][1]=[v];expect(d,'parents must be exact nonnegative integers preceding child')
 d=data();d['parents'][2]=[0,0];expect(d,'parent indices must be unique')
 for name in ['treatment','outcome']:
  for v in [-1,3,True,1.0,I(1),None,'1']:
   d=data();d[name]=v;expect(d,name+' must be an exact declared node index')
 d=data();d['outcome']=1;expect(d,'treatment and outcome must differ')
 d=data();d['parents'][1]=[True];d['parents'][2]=None;expect(d,'parents must be exact nonnegative integers preceding child')
