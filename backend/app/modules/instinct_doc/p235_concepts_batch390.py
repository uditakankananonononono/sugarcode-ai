"""P235 b390 bounded integer contingency/transport matrices.
Margins exact tuples length2..3 of exact int0..6,row margin then column
margin;all types before ranges within each;equal totals<=6. Table exact
tuple2..3 rows,each exact tuple of same length2..3,entries exact int0..6,
all per-row types before ranges,total<=6. Matrix cost exact same shape
as margins,exact ints-3..3. Bounds output per-cell(low,high),tables tuples.
Min-cost returns(cost,list all minimizing tables). Northwest returns one
table. Support components tuples of node ints(rows first,then columns),
isolated vertices included. Vertices:transport feasible tables whose
positive-support bipartite graph is acyclic,not all integer feasible.
Fisher profile tuples(factorial-product denominator,count,Fraction total
unnormalized mass count/denominator). Martingale source/target coordinates
exact tuple integers-3..3,matching margin lengths;rows must satisfy
sum(table[i][j]*target[j])==row_margin[i]*source[i].
No economic plan,Fisher significance or continuous LP guarantee.
"""
import itertools as it,math
from fractions import Fraction
from importlib.util import find_spec
try:
 from app.modules.instinct_doc.p235_concepts_registry import make_fail
except ModuleNotFoundError as exc:
 if exc.name!='app.modules.instinct_doc.p235_concepts_registry' or find_spec('app.modules.instinct_doc.p235_concepts_registry') is not None:raise
 def make_fail(name):
  def fail(code):raise ValueError('P235:%s:%s'%(name,code))
  return fail
SCOPE='PARTIAL: exact bounded integer contingency/transport fixtures,not Pearson chi-square or matrix rank'
NOT_CLAIMED=('economic plan','statistical significance','unbounded transport optimization','global novelty','production readiness')

CLAIMS = {'agi_like_intelligence': False, 'production_ready': False, 'real_world_validity': False}


def _vector(f,v,label,lo,hi,length=None):
 if type(v) is not tuple:f('bad_type:'+label)
 if (not 2<=len(v)<=3) if length is None else len(v)!=length:f('bad_value:'+label+'_length')
 if any(type(x) is not int for x in v):f('bad_type:'+label+'_entry')
 if any(not lo<=x<=hi for x in v):f('bad_value:'+label+'_entry')
def _margins(name,rows,cols):
 f=make_fail(name);_vector(f,rows,'rows',0,6);_vector(f,cols,'cols',0,6)
 if sum(rows)!=sum(cols):f('bad_value:total_equal')
 if sum(rows)>6:f('bad_value:total_cap')
 return f

def _matrix(f,t,label,rows=None,cols=None,lo=0,hi=6):
 if type(t) is not tuple:f('bad_type:'+label)
 if (not 2<=len(t)<=3) if rows is None else len(t)!=rows:f('bad_value:'+label+'_rows')
 width=None if cols is None else cols
 for row in t:
  if type(row) is not tuple:f('bad_type:'+label+'_row')
  if width is None:
   if not 2<=len(row)<=3:f('bad_value:'+label+'_cols')
   width=len(row)
  if len(row)!=width:f('bad_value:'+label+'_cols')
  if any(type(x) is not int for x in row):f('bad_type:'+label+'_entry')
  if any(not lo<=x<=hi for x in row):f('bad_value:'+label+'_entry')
 if label=='table' and sum(map(sum,t))>6:f('bad_value:total_cap')
def _compositions(total,bounds):
 if len(bounds)==1:
  if total<=bounds[0]:yield (total,)
  return
 for v in range(min(total,bounds[0])+1):
  for tail in _compositions(total-v,bounds[1:]):yield (v,)+tail

def contingency_feasible_tables(rows,cols):
 _margins('contingency_feasible_tables',rows,cols);result=[]
 def visit(index,left,prefix):
  if index==len(rows):
   if not any(left):result.append(prefix)
   return
  for row in _compositions(rows[index],left):visit(index+1,tuple(c-v for c,v in zip(left,row)),prefix+(row,))
 visit(0,cols,());return sorted(result)

def contingency_frechet_cell_bounds(rows,cols):
 _margins('contingency_frechet_cell_bounds',rows,cols);total=sum(rows)
 return tuple(tuple((max(0,r+c-total),min(r,c)) for c in cols) for r in rows)

def contingency_min_cost_tables(rows,cols,cost):
 f=_margins('contingency_min_cost_tables',rows,cols);_matrix(f,cost,'cost',len(rows),len(cols),-3,3);best=None;result=[];grid=[[0]*len(cols) for _ in rows]
 def search(pos,rr,cc,value):
  nonlocal best,result
  if best is not None and value+sum(rr)*min(x for row in cost for x in row)>best:return
  if pos==len(rows)*len(cols):
   if any(rr) or any(cc):return
   t=tuple(tuple(row) for row in grid)
   if best is None or value<best:best=value;result=[t]
   elif value==best:result.append(t)
   return
  i,j=divmod(pos,len(cols))
  for x in range(min(rr[i],cc[j])+1):
   if j==len(cols)-1 and x!=rr[i]:continue
   if i==len(rows)-1 and x!=cc[j]:continue
   grid[i][j]=x;r=list(rr);c=list(cc);r[i]-=x;c[j]-=x;search(pos+1,tuple(r),tuple(c),value+x*cost[i][j])
 search(0,rows,cols,0);return (best,sorted(result))

def contingency_monge_violations(cost):
 f=make_fail('contingency_monge_violations');_matrix(f,cost,'cost',lo=-3,hi=3);result=[]
 for i,k in it.combinations(range(len(cost)),2):
  for j,l in it.combinations(range(len(cost[0])),2):
   delta=cost[i][j]+cost[k][l]-cost[i][l]-cost[k][j]
   if delta>0:result.append((i,k,j,l,delta))
 return result

def contingency_northwest_corner(rows,cols):
 _margins('contingency_northwest_corner',rows,cols);r=list(rows);c=list(cols);out=[[0]*len(cols) for _ in rows];i=j=0
 while i<len(r) and j<len(c):
  x=min(r[i],c[j]);out[i][j]=x;r[i]-=x;c[j]-=x
  if r[i]==0:i+=1
  else:j+=1
 return tuple(tuple(row) for row in out)

def contingency_support_components(table):
 f=make_fail('contingency_support_components');_matrix(f,table,'table');n=len(table);m=len(table[0]);adj=[set() for _ in range(n+m)]
 for i in range(n):
  for j in range(m):
   if table[i][j]:adj[i].add(n+j);adj[n+j].add(i)
 unseen=set(range(n+m));out=[]
 while unseen:
  root=min(unseen);seen={root};todo=[root]
  for v in todo:
   for w in adj[v]-seen:seen.add(w);todo.append(w)
  unseen.difference_update(seen);out.append(tuple(sorted(seen)))
 return out

def contingency_markov_neighbors(table):
 f=make_fail('contingency_markov_neighbors');_matrix(f,table,'table');out=set()
 for i,k in it.combinations(range(len(table)),2):
  for j,l in it.combinations(range(len(table[0])),2):
   for sign in (-1,1):
    g=[list(r) for r in table];g[i][j]+=sign;g[k][l]+=sign;g[i][l]-=sign;g[k][j]-=sign
    if all(x>=0 for r in g for x in r):out.add(tuple(tuple(r) for r in g))
 return sorted(out)

def contingency_transport_polytope_vertices(rows,cols):
 _margins('contingency_transport_polytope_vertices',rows,cols);n=len(rows);m=len(cols);out=[]
 # Enumerate acyclic support sets,then solve leaf flow equations,not a
 # feasible-table predicate wrapper. Forest supports may include zero cells.
 cells=list(it.product(range(n),range(m)))
 for size in range(min(n+m-1,n*m)+1):
  for support in it.combinations(cells,size):
   edges=set(support);rem=list(rows)+list(cols);grid=[[0]*m for _ in rows];valid=True
   while edges:
    degree=[sum(i==v if v<n else n+j==v for i,j in edges) for v in range(n+m)]
    leaves=[v for v,d in enumerate(degree) if d==1]
    if not leaves:valid=False;break
    v=min(leaves);i,j=next((i,j) for i,j in edges if (i==v if v<n else n+j==v));a=i;b=n+j;x=rem[v]
    if x>rem[b if v==a else a]:valid=False;break
    grid[i][j]=x;rem[a]-=x;rem[b]-=x;edges.remove((i,j))
   if valid and not any(rem):out.append(tuple(tuple(r) for r in grid))
 return sorted(set(out))

def contingency_fisher_weight_profile(rows,cols):
 _margins('contingency_fisher_weight_profile',rows,cols);counts={};grid=[0]*(len(rows)*len(cols))
 def fill(index,rr,cc,denominator):
  if index==len(grid):
   if not any(rr) and not any(cc):counts[denominator]=counts.get(denominator,0)+1
   return
  i,j=divmod(index,len(cols))
  for value in range(min(rr[i],cc[j])+1):
   r=list(rr);c=list(cc);r[i]-=value;c[j]-=value;fill(index+1,tuple(r),tuple(c),denominator*math.factorial(value))
 fill(0,rows,cols,1)
 return [(d,counts[d],Fraction(counts[d],d)) for d in sorted(counts)]

def contingency_martingale_tables(rows,cols,source,target):
 f=_margins('contingency_martingale_tables',rows,cols);_vector(f,source,'source',-3,3,len(rows));_vector(f,target,'target',-3,3,len(cols));out=[]
 options=[]
 for r,x in zip(rows,source):options.append([row for row in it.product(range(r+1),repeat=len(cols)) if sum(row)==r and sum(v*y for v,y in zip(row,target))==r*x])
 for table in it.product(*options):
  if all(sum(row[j] for row in table)==cols[j] for j in range(len(cols))):out.append(table)
 return sorted(out)
