import itertools as it,copy,math,random,pytest
from fractions import Fraction
from app.modules.instinct_doc import p235_concepts_batch390 as m
NAMES=('contingency_feasible_tables','contingency_frechet_cell_bounds','contingency_min_cost_tables','contingency_monge_violations','contingency_northwest_corner','contingency_support_components','contingency_markov_neighbors','contingency_transport_polytope_vertices','contingency_fisher_weight_profile','contingency_martingale_tables')
class T(tuple):pass
class I(int):pass

def exact(a,b):
 assert type(a) is type(b)
 if type(b) in (list,tuple):
  assert len(a)==len(b)
  for x,y in zip(a,b):exact(x,y)
 else:assert a==b

def all_tables(n,k,total):
 # Stars/bars positions,independent of margin backtracking.
 out=[]
 for bars in it.combinations(range(total+n*k-1),n*k-1):
  positions=(-1,)+bars+(total+n*k-1,);flat=[positions[i+1]-positions[i]-1 for i in range(n*k)]
  out.append(tuple(tuple(flat[i*k:(i+1)*k]) for i in range(n)))
 return sorted(out)
def margins(t):return tuple(map(sum,t)),tuple(map(sum,zip(*t)))
def support_components(t):
 n=len(t);k=len(t[0]);pairs=[(i,n+j) for i in range(n) for j in range(k) if t[i][j]];blocks=[{v} for v in range(n+k)]
 for a,b in pairs:
  i=next(i for i,s in enumerate(blocks) if a in s);j=next(i for i,s in enumerate(blocks) if b in s)
  if i!=j:joined=blocks[i]|blocks[j];blocks=[s for z,s in enumerate(blocks) if z not in (i,j)]+[joined]
 return sorted(tuple(sorted(s)) for s in blocks)
def vertex(t):
 n=len(t);k=len(t[0]);edges=sum(bool(x) for row in t for x in row)
 return edges==n+k-len(support_components(t))
def nw_oracle(rows,cols):
 # Match ordered unit mass packets,not the grid greedy control loop.
 left=[i for i,r in enumerate(rows) for _ in range(r)];right=[j for j,c in enumerate(cols) for _ in range(c)]
 return tuple(tuple(sum(a==i and b==j for a,b in zip(left,right)) for j in range(len(cols))) for i in range(len(rows)))

def family_check(rows,cols,tables):
 exact(m.contingency_feasible_tables(rows,cols),tables)
 exact(m.contingency_frechet_cell_bounds(rows,cols),tuple(tuple((min(t[i][j] for t in tables),max(t[i][j] for t in tables)) for j in range(len(cols))) for i in range(len(rows))))
 exact(m.contingency_northwest_corner(rows,cols),nw_oracle(rows,cols))
 exact(m.contingency_transport_polytope_vertices(rows,cols),[t for t in tables if vertex(t)])
 profile={}
 for t in tables:
  d=math.prod(math.factorial(x) for row in t for x in row);profile[d]=profile.get(d,0)+1
 exact(m.contingency_fisher_weight_profile(rows,cols),[(d,c,Fraction(c,d)) for d,c in sorted(profile.items())])
 cost=tuple(tuple(((i*3+j*2+sum(rows))%7)-3 for j in range(len(cols))) for i in range(len(rows)))
 values=[sum(t[i][j]*cost[i][j] for i in range(len(rows)) for j in range(len(cols))) for t in tables];best=min(values)
 exact(m.contingency_min_cost_tables(rows,cols,cost),(best,[t for t,v in zip(tables,values) if v==best]))
 src=tuple(i-1 for i in range(len(rows)));tgt=tuple(j-1 for j in range(len(cols)))
 exact(m.contingency_martingale_tables(rows,cols,src,tgt),[t for t in tables if all(sum(t[i][j]*tgt[j] for j in range(len(cols)))==rows[i]*src[i] for i in range(len(rows)))])
 for t in tables:
  exact(m.contingency_support_components(t),support_components(t))
  # Compare against same-margin tables with exactly four alternating
  # +/-1changes in one2x2rectangle,not mutate-and-filter production.
  neigh=[]
  for u in tables:
   diff=[(i,j,u[i][j]-t[i][j]) for i in range(len(rows)) for j in range(len(cols)) if u[i][j]!=t[i][j]]
   if len(diff)==4 and sorted(d for i,j,d in diff)==[-1,-1,1,1] and len({i for i,j,d in diff})==2 and len({j for i,j,d in diff})==2:neigh.append(u)
  exact(m.contingency_markov_neighbors(t),neigh)


def test_exhaustive_mass_matrices_and_own_oracles():
 families=0;tablecount=0
 for n,k in ((2,2),(2,3),(3,2),(3,3)):
  for total in range(4):
   groups={}
   for t in all_tables(n,k,total):groups.setdefault(margins(t),[]).append(t);tablecount+=1
   for (rows,cols),tables in groups.items():family_check(rows,cols,tables);families+=1
 assert (families,tablecount)==(306,423)
 for rows,cols in (((3,3),(2,4)),((1,2,3),(3,1,2)),((0,6),(0,3,3)),((0,0,6),(6,0)),((2,2,2),(2,2,2))):
  tables=[t for t in all_tables(len(rows),len(cols),sum(rows)) if margins(t)==(rows,cols)];family_check(rows,cols,tables)
 for flat in it.product((-1,0,1),repeat=4):
  cost=(flat[:2],flat[2:]);d=flat[0]+flat[3]-flat[1]-flat[2];exact(m.contingency_monge_violations(cost),[(0,1,0,1,d)] if d>0 else [])
 rng=random.Random(390)
 for _ in range(20):
  cost=tuple(tuple(rng.randint(-3,3) for _ in range(3)) for _ in range(3));expected=[]
  for i,k in it.combinations(range(3),2):
   for j,l in it.combinations(range(3),2):
    a=cost[i][j]+cost[k][l];b=cost[i][l]+cost[k][j]
    if a>b:expected.append((i,k,j,l,a-b))
  exact(m.contingency_monge_violations(cost),expected)


def test_validation_whole_input_deep_nesting_four_registry_routes(monkeypatch):
 def reject(name,args,code):
  before=copy.deepcopy(args)
  with pytest.raises(ValueError) as e:getattr(m,name)(*args)
  assert str(e.value)=='P235:'+name+':'+code and before==args
 margin_names=('contingency_feasible_tables','contingency_frechet_cell_bounds','contingency_min_cost_tables','contingency_northwest_corner','contingency_transport_polytope_vertices','contingency_fisher_weight_profile','contingency_martingale_tables')
 for name in margin_names:
  def args(r,c):return (r,c,None) if name=='contingency_min_cost_tables' else ((r,c,None,None) if name=='contingency_martingale_tables' else (r,c))
  for r,code in ((None,'bad_type:rows'),([], 'bad_type:rows'),(T((0,0)),'bad_type:rows'),((),'bad_value:rows_length'),((0,),'bad_value:rows_length'),((0,)*4,'bad_value:rows_length'),((True,0),'bad_type:rows_entry'),((I(0),0),'bad_type:rows_entry'),((0.0,0),'bad_type:rows_entry'),(((0,),0),'bad_type:rows_entry'),((((0,),),0),'bad_type:rows_entry'),((9,True),'bad_type:rows_entry'),((-1,0),'bad_value:rows_entry'),((7,0),'bad_value:rows_entry')):reject(name,args(r,None),code)
  reject(name,args((0,0),None),'bad_type:cols');reject(name,args((0,0),(0,)),'bad_value:cols_length');reject(name,args((0,0),(True,0)),'bad_type:cols_entry');reject(name,args((0,0),(7,0)),'bad_value:cols_entry')
  reject(name,args((4,4),(3,4)),'bad_value:total_equal');reject(name,args((4,4),(4,4)),'bad_value:total_cap')
 for name in ('contingency_support_components','contingency_markov_neighbors','contingency_monge_violations'):
  label='cost' if name=='contingency_monge_violations' else 'table';lo=-3 if label=='cost' else 0;hi=3 if label=='cost' else 6
  for t,code in ((None,'bad_type:'+label),([], 'bad_type:'+label),(T(((0,0),(0,0))),'bad_type:'+label),((),'bad_value:'+label+'_rows'),(((0,0),),'bad_value:'+label+'_rows'),(((0,0),)*4,'bad_value:'+label+'_rows'),((None,(0,0)),'bad_type:'+label+'_row'),(([],(0,0)),'bad_type:'+label+'_row'),(((0,),(0,)),'bad_value:'+label+'_cols'),(((0,0),(0,)),'bad_value:'+label+'_cols'),(((True,0),(0,0)),'bad_type:'+label+'_entry'),(((I(0),0),(0,0)),'bad_type:'+label+'_entry'),((((0,),0),(0,0)),'bad_type:'+label+'_entry'),(((((0,),),0),(0,0)),'bad_type:'+label+'_entry'),(((hi+1,True),(0,0)),'bad_type:'+label+'_entry'),(((lo-1,0),(0,0)),'bad_value:'+label+'_entry'),(((hi+1,0),(0,0)),'bad_value:'+label+'_entry')):reject(name,(t,),code)
  if label=='table':reject(name,(((4,4),(0,0)),),'bad_value:total_cap')
 reject('contingency_min_cost_tables',((1,1),(1,1),None),'bad_type:cost');reject('contingency_min_cost_tables',((1,1),(1,1),((0,0),)),'bad_value:cost_rows');reject('contingency_min_cost_tables',((1,1),(1,1),((0,0,0),(0,0,0))),'bad_value:cost_cols');reject('contingency_min_cost_tables',((1,1),(1,1),((4,True),(0,0))),'bad_type:cost_entry')
 for label,pos in (('source',2),('target',3)):
  for v,code in ((None,'bad_type:'+label),([], 'bad_type:'+label),(T((0,0)),'bad_type:'+label),((),'bad_value:'+label+'_length'),((True,0),'bad_type:'+label+'_entry'),((I(0),0),'bad_type:'+label+'_entry'),(((0,),0),'bad_type:'+label+'_entry'),((4,True),'bad_type:'+label+'_entry'),((-4,0),'bad_value:'+label+'_entry'),((4,0),'bad_value:'+label+'_entry')):
   a=[(1,1),(1,1),(0,0),(0,0)];a[pos]=v;reject('contingency_martingale_tables',tuple(a),code)
 values=[((1,1),(1,1)),((1,1),(1,1)),((1,1),(1,1),((0,1),(1,0))),(((0,1),(1,0)),),((1,1),(1,1)),(((0,1),(1,0)),),(((0,1),(1,0)),),((1,1),(1,1)),((1,1),(1,1)),((1,1),(1,1),(0,1),(0,1))]
 for name,args in zip(NAMES,values):
  before=copy.deepcopy(args);out=getattr(m,name)(*args);saved=copy.deepcopy(out)
  if type(out) is list:out.clear();exact(getattr(m,name)(*args),saved)
  assert args==before
 assert m.SCOPE=='PARTIAL: exact bounded integer contingency/transport fixtures,not Pearson chi-square or matrix rank'
 assert m.NOT_CLAIMED==('economic plan','statistical significance','unbounded transport optimization','global novelty','production readiness')
 import pathlib,builtins,importlib.util,sys,types
 source=pathlib.Path(m.__file__).read_text();original=builtins.__import__
 def execute(missing):
  def custom(name,*args,**kwargs):
   if name=='app.modules.instinct_doc.p235_concepts_registry':raise ModuleNotFoundError('blocked',name=missing)
   return original(name,*args,**kwargs)
  ns={'__builtins__':dict(vars(builtins),__import__=custom)};exec(compile(source,'standalone','exec'),ns);return ns
 assert execute('app.modules.instinct_doc.p235_concepts_registry')['contingency_feasible_tables']((0,0),(0,0))==[((0,0),(0,0))]
 with pytest.raises(ModuleNotFoundError):execute('other_dependency')
 monkeypatch.setattr(importlib.util,'find_spec',lambda name:object())
 with pytest.raises(ModuleNotFoundError):execute('app.modules.instinct_doc.p235_concepts_registry')
 registry=types.ModuleType('app.modules.instinct_doc.p235_concepts_registry');seen=[]
 def make_fail(name):
  seen.append(name)
  def fail(code):raise ValueError('P235:'+name+':'+code)
  return fail
 registry.make_fail=make_fail;monkeypatch.setitem(sys.modules,registry.__name__,registry);ns={};exec(compile(source,'registry','exec'),ns)
 ns['contingency_feasible_tables']((0,0),(0,0));assert seen==['contingency_feasible_tables']

def test_boundary_total_cost_coordinate_and_precedence():
 for name in ('contingency_feasible_tables','contingency_frechet_cell_bounds','contingency_northwest_corner','contingency_transport_polytope_vertices','contingency_fisher_weight_profile'):
  with pytest.raises(ValueError) as e:getattr(m,name)((3,4),(4,3))
  assert str(e.value)=='P235:'+name+':bad_value:total_cap'
 for name in ('contingency_support_components','contingency_markov_neighbors'):
  with pytest.raises(ValueError) as e:getattr(m,name)(((3,4),(0,0)))
  assert str(e.value)=='P235:'+name+':bad_value:total_cap'
 for cost in (((4,0),(0,0)),((-4,0),(0,0))):
  with pytest.raises(ValueError) as e:m.contingency_min_cost_tables((1,1),(1,1),cost)
  assert str(e.value)=='P235:contingency_min_cost_tables:bad_value:cost_entry'
 exact(m.contingency_martingale_tables((1,1),(1,1),(3,-3),(3,-3)),[((1,0),(0,1))])
 exact(m.contingency_martingale_tables((1,1),(1,1),(-3,3),(3,-3)),[((0,1),(1,0))])
 for name in ('contingency_support_components','contingency_markov_neighbors'):
  with pytest.raises(ValueError) as e:getattr(m,name)(((9,0),(True,0)))
  assert str(e.value)=='P235:'+name+':bad_value:table_entry'
 # Independent least-cost check over all81 binary-shape cost matrices.
 tables=[((0,1),(1,0)),((1,0),(0,1))]
 for flat in it.product((-1,0,1),repeat=4):
  c=(flat[:2],flat[2:]);v=[sum(a*b for row,cr in zip(t,c) for a,b in zip(row,cr)) for t in tables]
  exact(m.contingency_min_cost_tables((1,1),(1,1),c),(min(v),[t for t,z in zip(tables,v) if z==min(v)]))

@pytest.fixture(autouse=True)
def finite_transport_guard(monkeypatch):
 import sys
 for name in ('contingency_northwest_corner',):
  original=getattr(m,name)
  def guarded(*args,original=original):
   counts={}
   def trace(frame,event,arg):
    if frame.f_code.co_filename!=m.__file__:return None
    if event=='call':counts[id(frame)]=0
    if event=='line':
     counts[id(frame)]=counts.get(id(frame),0)+1
     if counts[id(frame)]>25000:raise AssertionError('transport traversal did not terminate')
    return trace
   previous=sys.gettrace();sys.settrace(trace)
   try:return original(*args)
   finally:sys.settrace(previous)
  monkeypatch.setattr(m,name,guarded)

def test_matrix_width_and_negative_bound_first_bad():
 with pytest.raises(ValueError) as e:m.contingency_monge_violations(((0,0,0,0),(0,0,0,0)))
 assert str(e.value)=='P235:contingency_monge_violations:bad_value:cost_cols'
 with pytest.raises(ValueError) as e:m.contingency_feasible_tables((0,0),(-1,0))
 assert str(e.value)=='P235:contingency_feasible_tables:bad_value:cols_entry'
 # Vertices need not include every table of given integer margins.
 rows=cols=(1,1,1);tables=[t for t in all_tables(3,3,3) if margins(t)==(rows,cols)]
 for cflat in it.product((-3,3),repeat=4):
  cost=(cflat[:2],cflat[2:]);rows2=cols2=(3,3);t2=[t for t in all_tables(2,2,6) if margins(t)==(rows2,cols2)];values=[sum(a*b for row,cr in zip(t,cost) for a,b in zip(row,cr)) for t in t2]
  exact(m.contingency_min_cost_tables(rows2,cols2,cost),(min(values),[t for t,v in zip(t2,values) if v==min(values)]))


def test_false_claims_and_additional_exact_caps():
 assert m.CLAIMS == {'agi_like_intelligence': False, 'production_ready': False, 'real_world_validity': False}
 assert all(type(v) is bool and v is False for v in m.CLAIMS.values())
 for name in ('contingency_feasible_tables','contingency_frechet_cell_bounds','contingency_northwest_corner','contingency_transport_polytope_vertices','contingency_fisher_weight_profile'):
  getattr(m,name)((0,6),(0,6))
  with pytest.raises(ValueError,match='^P235:'+name+':bad_value:total_cap$'):getattr(m,name)((1,6),(1,6))
  with pytest.raises(ValueError,match='^P235:'+name+':bad_value:rows_entry$'):getattr(m,name)((-1,0),(True,0))
 for name in ('contingency_support_components','contingency_markov_neighbors'):
  getattr(m,name)(((6,0),(0,0)))
  with pytest.raises(ValueError,match='^P235:'+name+':bad_value:total_cap$'):getattr(m,name)(((6,1),(0,0)))
 for value in (-3,3):
  m.contingency_monge_violations(((value,value),(value,value)))
  assert m.contingency_min_cost_tables((0,6),(0,6),((value,value),(value,value)))[0]==6*value
 for value in (-4,4):
  with pytest.raises(ValueError,match='^P235:contingency_monge_violations:bad_value:cost_entry$'):m.contingency_monge_violations(((value,0),(0,0)))


def test_full_forest_edge_bound_vertex_witness():
 rows,cols=(2,2,2),(1,2,3)
 tables=[t for t in all_tables(3,3,6) if margins(t)==(rows,cols)]
 expected=[t for t in tables if vertex(t)]
 assert any(sum(x>0 for row in t for x in row)==5 for t in expected)
 exact(m.contingency_transport_polytope_vertices(rows,cols),expected)
