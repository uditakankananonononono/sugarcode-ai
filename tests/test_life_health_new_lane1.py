import random,pytest,copy
from fractions import Fraction as F
from sugarcode.extra_doc import life_table1186 as life,competing1184 as comp,lms1181 as lms

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

def test_life_independent_recursive_death_density():
 rng=random.Random(1186)
 for _ in range(150):
  rows=[(str(i),rng.randint(1,10),rng.randint(0,10),rng.randint(1,10),0,1) for i in range(rng.randint(1,12))]
  def build(i,l):
   if i==len(rows):return [],F(0),l
   label,n,r,d,a,b=rows[i];q=min(F(1),F(n*r,d+(n-F(a,b))*r));dead=l*q;L=n*l-(n-F(a,b))*dead;rest,t,s=build(i+1,l-dead);T=L+t
   return [(label,l,q,dead,L,T,T/l if l else None)]+rest,T,s
  out,T,s=build(0,F(1));exact(life.table(rows),dict(intervals=out,survivors=s,restricted_expectancy=T,population_validated=False))
 exact(life.table([('Z'*24,10,10,1,10,1)]),dict(intervals=[('Z'*24,F(1),F(1),F(1),F(10),F(10),F(10))],survivors=F(0),restricted_expectancy=F(10),population_validated=False))

def test_comp_independent_probability_tree():
 rng=random.Random(1184)
 for _ in range(150):
  risk=rng.randint(1,100);rows=[];mass=F(1);aa=bb=F(0);trace=[]
  for i in range(rng.randint(1,12)):
   a=rng.randint(0,risk);b=rng.randint(0,risk-a);c=rng.randint(0,risk-a-b);rows.append((str(i),risk,a,b,c))
   # Expand each risk-set member into equal branch probability, then pool.
   branches=[mass/risk]*risk;aa+=sum(branches[:a]);bb+=sum(branches[a:a+b]);mass=sum(branches[a+b:],F(0));trace.append((str(i),mass,aa,bb));risk-=a+b+c
   if not risk:break
  exact(comp.incidence(rows),dict(trace=trace,survival=mass,cause_a=aa,cause_b=bb,clinical_validated=False))

def test_lms_independent_geometric_series():
 rng=random.Random(1181)
 for _ in range(150):
  rows=[];expected=[]
  for i in range(rng.randint(1,12)):
   x,m,l,a,b=rng.randint(1,100),rng.randint(1,100),rng.randint(1,3),rng.randint(1,10),rng.randint(1,10);rows.append((str(i),x,m,l,a,b));ratio=F(x,m);z=(ratio-1)*sum(ratio**j for j in range(l))*F(b,l*a);expected.append((str(i),z))
  exact(lms.scores(rows),dict(scores=expected,reference_validated=False))

class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass
@pytest.mark.parametrize('module,fn,row',[(life,life.table,('x',1,0,1,0,1)),(comp,comp.incidence,('x',100,0,0,0)),(lms,lms.scores,('x',1,1,1,1,1))])
def test_common_caps_types_labels_order(module,fn,row):
 for v in (None,(),L([row]),[],[row]*13):
  with pytest.raises(ValueError,match='rows must be exact list1..12'):fn(v)
 for v in (None,list(row),T(row),row[:-1],row+(0,)):
  with pytest.raises(ValueError,match='row must be exact tuple'):fn([v])
 for name in ('','x'*25,'\x00','a\n','\u200b',S('x')):
  with pytest.raises(ValueError,match='labels must be unique printable'):fn([(name,*row[1:])])
 with pytest.raises(ValueError,match='labels must be unique printable'):fn([row,row])
 for name in ('x'*24,'Z'*24):assert fn([(name,*row[1:])])
 rows=[(str(i),*row[1:]) for i in range(12)];saved=copy.deepcopy(rows);out=fn(rows);assert rows==saved;exact(fn(rows),out)
 for pos in range(1,len(row)):
  for value in (True,1.0,I(1),'1',None,-1,101):
   bad=list(row);bad[pos]=value
   with pytest.raises(ValueError):fn([tuple(bad)])
 with pytest.raises(ValueError,match='labels must be unique printable'):fn([('',*row[1:]),None])
 assert 'PARTIAL' in module.SCOPE and module.NOT_CLAIMED

def test_special_boundaries():
 for r in (0,10):life.table([('a',10,r,10,10,10)])
 for x in (1,100):
  for m in (1,100):
   for l in (1,3):
    for a in (1,10):
     for b in (1,10):assert lms.scores([('a',x,m,l,a,b)])
 for r in (1,100):
  for a,b in ((0,0),(r,0),(0,r)):comp.incidence([('a',r,a,b,0)])
 with pytest.raises(ValueError,match='ax must not exceed'):life.table([('a',1,1,1,10,1)])
 with pytest.raises(ValueError,match='events exceed risk'):comp.incidence([('a',1,1,1,0)])
 with pytest.raises(ValueError,match='risk set mismatch'):comp.incidence([('a',2,0,0,0),('b',1,0,0,0)])

def test_each_numeric_boundary_and_firstbad():
 for fn,row,bounds in [(life.table,('a',1,0,1,0,1),[(1,10),(0,10),(1,10),(0,10),(1,10)]),(lms.scores,('a',1,1,1,1,1),[(1,100),(1,100),(1,3),(1,10),(1,10)]),(comp.incidence,('a',100,0,0,0),[(1,100),(0,100),(0,100),(0,100)])]:
  for pos,(lo,hi) in enumerate(bounds,1):
   for value in (lo,hi):
    r=list(row);r[pos]=value
    if fn is life.table:r[1]=10
    if fn is comp.incidence:r[1]=100
    assert fn([tuple(r)])
   for value in (lo-1,hi+1):
    r=list(row);r[pos]=value
    with pytest.raises(ValueError):fn([tuple(r)])
 # Explicit zero-survival remainder and censored competing events.
 assert life.table([('a',10,10,1,10,1),('b',1,0,1,0,1)])['intervals'][1][-1] is None
 exact(comp.incidence([('a',10,2,1,5),('b',2,1,0,0)]),{'trace':[('a',F(7,10),F(1,5),F(1,10)),('b',F(7,20),F(11,20),F(1,10))],'survival':F(7,20),'cause_a':F(11,20),'cause_b':F(1,10),'clinical_validated':False})


def test_scope_exact_and_return_key_order():
 assert life.SCOPE=='PARTIAL: closed-cohort supplied-rate restricted abridged life table'
 assert comp.SCOPE=='PARTIAL: exact supplied censored-cohort two-cause cumulative incidence'
 assert lms.SCOPE=='PARTIAL: exact supplied positive-integer-L LMS standard scores'
 for m in (life,comp,lms):
  assert 'NOT_CLAIMED:' in m.__doc__ and 'production readiness' in m.NOT_CLAIMED


@pytest.mark.parametrize('fn,row',[(life.table,(1,0,1,0,1)),(comp.incidence,(100,0,0,0)),(lms.scores,(1,1,1,1,1))])
def test_printable_ascii_guard_exact(fn,row):
 for label in ['\u200b','\x00','\n','\x7f','\x85','\ue000','\ud800','\u0378','Ω-1']:
  with pytest.raises(ValueError,match='labels must be unique printable ASCII strings1..24'):
   fn([(label,*row)])
 for label in [' ','   ','x'*24]:assert fn([(label,*row)])

def test_label24_and_competing12_are_accepted_exactly():
    label='A'*24
    exact(life.table([(label,1,0,1,0,1)]), {
        'intervals':[(label,F(1),F(0),F(0),F(1),F(1),F(1))],
        'survivors':F(1),'restricted_expectancy':F(1),'population_validated':False})
    exact(lms.scores([(label,1,1,1,1,1)]), {
        'scores':[(label,F(0))],'reference_validated':False})
    exact(comp.incidence([(label,1,0,0,0)]), {
        'trace':[(label,F(1),F(0),F(0))], 'survival':F(1),
        'cause_a':F(0),'cause_b':F(0),'clinical_validated':False})
    rows=[(str(i),1,0,0,0) for i in range(12)]
    exact(comp.incidence(rows), {
        'trace':[(str(i),F(1),F(0),F(0)) for i in range(12)],
        'survival':F(1),'cause_a':F(0),'cause_b':F(0),'clinical_validated':False})
