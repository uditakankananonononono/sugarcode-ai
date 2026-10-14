import copy,random
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc import finite_liml_ratio as l
from sugarcode.extra_doc import linear_control_function as c
class L(list):pass
class D(dict):pass
class I(int):pass

def ld():return {'rows':[[2,1,1,0],[5,2,0,1],[-1,-1,-1,0],[-4,-2,0,-1],[3,1,1,1]],'slopes':[-5,0,10,25]}
def cd():return {'rows':[[4,1,-1],[3,1,0],[8,3,1],[7,3,2],[1,-1,-2]]}
def pair(v):return [v.numerator,v.denominator]
def solve(matrix,rhs):
    rows=[list(map(F,row))+[F(v)] for row,v in zip(matrix,rhs)];n=len(rows)
    for col in range(n):
        pivot=next(k for k in range(col,n) if rows[k][col]);rows[col],rows[pivot]=rows[pivot],rows[col];v=rows[col][col];rows[col]=[x/v for x in rows[col]]
        for k in range(n):
            if k!=col:
                v=rows[k][col];rows[k]=[a-v*b for a,b in zip(rows[k],rows[col])]
    return [r[-1] for r in rows]
def regression(design,outcome):
    k=len(design[0]);gram=[[sum(row[i]*row[j] for row in design) for j in range(k)] for i in range(k)];rhs=[sum(row[i]*value for row,value in zip(design,outcome)) for i in range(k)];return solve(gram,rhs)
def lo(x):
    rows=x['rows'];n=len(rows);design=[[1,r[2],r[3]] for r in rows];result=[]
    for tenth in x['slopes']:
        slope=F(tenth,10);u=[F(r[0])-slope*r[1] for r in rows];mean=sum(u)/n;centered=[v-mean for v in u];coef=regression(design,u);fitted=[sum(F(a)*b for a,b in zip(row,coef))-mean for row in design];total=sum(v*v for v in centered);projected=sum(v*v for v in fitted)
        if total==0 or total==projected:raise ZeroDivisionError
        result.append({'slope':pair(slope),'score':pair(projected/total),'total_ss':pair(total),'projected_ss':pair(projected)})
    best=min(range(len(result)),key=lambda j:F(*result[j]['score']));return {'best_tenth':x['slopes'][best],'candidates':result,'claims':[False]*4}
def co(x):
    rows=x['rows'];first=regression([[1,r[2]] for r in rows],[r[1] for r in rows]);res=[F(r[1])-first[0]-first[1]*r[2] for r in rows];second=regression([[1,r[1],v] for r,v in zip(rows,res)],[r[0] for r in rows]);structural=[F(r[0])-sum(F(a)*b for a,b in zip([1,r[1],v],second)) for r,v in zip(rows,res)]
    return {'first_stage_intercept':pair(first[0]),'first_stage_slope':pair(first[1]),'first_stage_residuals':list(map(pair,res)),'intercept':pair(second[0]),'slope':pair(second[1]),'control':pair(second[2]),'residuals':list(map(pair,structural)),'claims':[False]*4}
def expect(fn,x,msg):
    with pytest.raises(ValueError) as err:fn(x)
    assert str(err.value)==msg

def test_hand():
    assert l.rank(ld())==lo(ld());assert c.fit(cd())==co(cd())
    x={'rows':[[1,1,1,0],[2,0,0,1],[-1,-1,-1,0],[0,0,0,-1],[1,1,0,0]],'slopes':[0,10]};assert l.rank(x)==lo(x)
    y={'rows':[[1,1,-1],[3,1,0],[7,3,1],[7,3,2]]};assert c.fit(y)==co(y);assert c.fit(y)['slope']==[11,4];assert c.fit(y)['control']==[-5,4]

def test_random_oracles():
    r=random.Random(1064);counts=[0,0]
    for _ in range(250):
        rows=[[r.randint(-9,9) for _ in range(4)] for j in range(r.randint(5,20))];x={'rows':rows,'slopes':r.sample(range(-90,91),r.randint(2,12))}
        try:expected=lo(x)
        except (StopIteration,ZeroDivisionError):continue
        assert l.rank(x)==expected;counts[0]+=1
        y={'rows':[row[:3] for row in rows]}
        try:expected=co(y)
        except (StopIteration,ZeroDivisionError):continue
        assert c.fit(y)==expected;counts[1]+=1
    assert min(counts)>230

def test_caps_and_freshness():
    for fn,make in [(l.rank,ld),(c.fit,cd)]:
        x=make();saved=copy.deepcopy(x);ans=fn(x);ans['claims'][0]=True;assert fn(x)['claims']==[False]*4;assert x==saved
        x=make();x['rows']=x['rows']*4;assert fn(x)==(lo(x) if fn==l.rank else co(x))
    x=ld();x['slopes']=[-90,90];assert l.rank(x)==lo(x)
    x=ld();x['slopes']=list(range(-6,6));assert l.rank(x)==lo(x)

@pytest.mark.parametrize('fn,make,width',[(l.rank,ld,4),(c.fit,cd,3)])
def test_types_shapes_messages(fn,make,width):
    msg='exact dict with rows and slopes required' if width==4 else 'exact dict with rows required'
    for val in [None,[],D(make()),{},dict(make(),extra=1)]:expect(fn,val,msg)
    for cls in [L,tuple]:
        x=make();x['rows']=cls(x['rows']);expect(fn,x,'rows must be an exact list of 4..20 observations')
    for count in [0,3,21]:
        x=make();x['rows']=[[1]*width]*count;expect(fn,x,'rows must be an exact list of 4..20 observations')
    rowmsg='row must be an exact list of y,x,z1,z2' if width==4 else 'row must be an exact list of y,x,z'
    for j in range(5):
        for cls in [L,tuple]:
            x=make();x['rows'][j]=cls(x['rows'][j]);expect(fn,x,rowmsg)
        for size in [width-1,width+1]:
            x=make();x['rows'][j]=[1]*size;expect(fn,x,rowmsg)
        for k in range(width):
            for val in [True,I(1),1.0,-10,10,None,'1']:
                x=make();x['rows'][j][k]=val;expect(fn,x,'row entries must be exact integers -9..9' if width==4 else 'entries must be exact integers -9..9')

def test_liml_slopes_messages():
    for cls in [L,tuple]:
        x=ld();x['slopes']=cls(x['slopes']);expect(l.rank,x,'slopes must be an exact list of 2..12 distinct tenths')
    for count in [0,1,13]:
        x=ld();x['slopes']=list(range(count));expect(l.rank,x,'slopes must be an exact list of 2..12 distinct tenths')
    for j in range(4):
        for val in [True,I(1),1.0,-91,91,None,'1']:
            x=ld();x['slopes'][j]=val;expect(l.rank,x,'slopes must contain exact integer tenths -90..90')
    x=ld();x['slopes']=[0,0];expect(l.rank,x,'slopes must be unique')
    x=ld();x['rows']=[r[:3]+[r[2]] for r in x['rows']];expect(l.rank,x,'centered instruments must be linearly independent')
    x={'rows':[[2,1,1,0],[4,2,0,1],[-2,-1,-1,0],[-4,-2,0,-1]],'slopes':[20,0]};expect(l.rank,x,'candidate has zero centered residual variance')
    x={'rows':[[1,0,1,0],[2,0,0,1],[-1,0,-1,0],[-2,0,0,-1]],'slopes':[0,10]};expect(l.rank,x,'candidate has zero instrument-residual variance')

def test_control_model_messages():
    expect(c.fit,{'rows':[[1,1,0],[2,2,0],[3,3,0],[4,4,0]]},'instrument must vary')
    expect(c.fit,{'rows':[[1,1,1],[2,-1,0],[3,1,-1],[4,-1,0]]},'first-stage fitted x must vary')
    expect(c.fit,{'rows':[[1,1,1],[2,2,2],[3,3,3],[4,4,4]]},'first-stage residual must vary')

def test_contract():
    assert l.SCOPE=='PARTIAL: finite-grid LIML least-variance ratio ranking only'
    assert c.SCOPE=='PARTIAL: exact linear first-stage residual inclusion only'
    assert l.NOT_CLAIMED==('continuous LIML optimization','instrument validity','statistical inference','production readiness')
    assert c.NOT_CLAIMED==('nonlinear control functions','instrument validity','standard errors','production readiness')

def test_liml_equal_score_first_grid_wins():
    x={'rows':[[1,1,1,0],[-1,-1,0,1],[1,1,-1,0],[-1,-1,0,-1]],'slopes':[20,0]}
    assert l.rank(x)==lo(x)
    assert l.rank(x)['best_tenth']==20
    assert [r['score'] for r in l.rank(x)['candidates']]==[[0,1],[0,1]]

def test_candidate_shapes_one_extra_isolated():
    x=ld();x['rows'][2].append(1);expect(l.rank,x,'row must be an exact list of y,x,z1,z2')
    x=cd();x['rows'][2].append(1);expect(c.fit,x,'row must be an exact list of y,x,z')
