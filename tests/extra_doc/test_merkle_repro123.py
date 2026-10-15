import random,itertools,hashlib,copy
import pytest
from sugarcode.extra_doc import merkle_repro123 as m
class D(dict):pass
class L(list):pass
class S(str):pass

def data():return dict(original=['a','b','c'],repeated=['a','z','c',''])
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
 # Recursive index lookup of each level, no iterative digest-list folding.
 def root(rows):
  widths=[len(rows)]
  while widths[-1]>1:widths.append((widths[-1]+1)//2)
  def digest(depth,index):
   if depth==0:return hashlib.sha256(('leaf:'+rows[index]).encode()).digest()
   left=2*index;right=min(left+1,widths[depth-1]-1)
   return hashlib.sha256(b'node:'+digest(depth-1,left)+digest(depth-1,right)).digest()
  return digest(len(widths)-1,0).hex()
 roots=[root(d['original']),root(d['repeated'])];changed=[i for i,(a,b) in enumerate(itertools.zip_longest(d['original'],d['repeated'],fillvalue=None)) if a!=b]
 return dict(roots=roots,equal=roots[0]==roots[1],changed=changed,claims=[False]*3)
def expect(d,msg):
 with pytest.raises(ValueError) as e:m.compare(d)
 assert str(e.value)==msg

def test_recursive_oracle():
 rng=random.Random(123)
 for _ in range(180):
  rows=[''.join(rng.choice('ab :~') for _ in range(rng.randrange(13))) for i in range(rng.randint(1,8))];other=list(rows)
  if rng.randrange(2):other=[''.join(rng.choice('ab :~') for _ in range(rng.randrange(13))) for i in range(rng.randint(1,8))]
  d=dict(original=rows,repeated=other);exact(m.compare(d),oracle(d))
 for n,k in itertools.product(range(1,9),repeat=2):
  d=dict(original=['']*n,repeated=['~'*12]*k);exact(m.compare(d),oracle(d))
 for code in range(32,127):
  d=dict(original=[chr(code)],repeated=[chr(code)]);exact(m.compare(d),oracle(d))
 # Odd-leaf duplication can produce equal roots for different lengths.
 d=dict(original=['a','b','c'],repeated=['a','b','c','c']);r=m.compare(d);exact(r,oracle(d));assert r['equal'] is True;assert r['changed']==[3]
 d=data();saved=copy.deepcopy(d);expected=oracle(d);result=m.compare(d);assert d==saved;exact(result,expected);result['roots'][0]='bad';exact(m.compare(d),expected)
 assert m.SCOPE=='PARTIAL: supplied ordered artifact Merkle-root comparison only'
 assert m.NOT_CLAIMED==('result recreation','provenance verification','equality of artifact lists from equal roots','production readiness')

def test_types_caps_order():
 for v in [None,[],{},D(data()),dict(data(),extra=1)]:expect(v,'exact dict with original and repeated required')
 for name in ['original','repeated']:
  for v in [None,(),L(['a']),[],['a']*9]:
   d=data();d[name]=v;expect(d,name+' must be an exact list of 1..8 artifacts')
  for v in [None,1,True,S('a'),'a'*13,'\x1f','\x7f','é','\ud800']:
   d=data();d[name][0]=v;expect(d,'artifacts must be exact printable ASCII strings of length 0..12')
 d=data();d['original'][0]='\n';d['repeated']=None;expect(d,'artifacts must be exact printable ASCII strings of length 0..12')

def test_nonfirst_artifact_validation():
 for name in ['original','repeated']:
  for bad in [None,1,S('a'),'a'*13,'\x1f','\x7f','é','\ud800']:
   for position in [1,2]:
    d=dict(original=['a']*3,repeated=['a']*3);d[name][position]=bad;expect(d,'artifacts must be exact printable ASCII strings of length 0..12')
