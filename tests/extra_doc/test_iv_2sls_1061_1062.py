import copy,random
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc import centered_iv_fit as v
from sugarcode.extra_doc import two_instrument_2sls as t
class L(list):pass
class D(dict):pass
class I(int):pass

def vd():return {'rows':[[1,1,-1],[4,2,0],[8,4,2],[5,3,1]]}
def td():return {'rows':[[2,1,1,0],[5,2,0,1],[-1,-1,-1,0],[-4,-2,0,-1],[3,1,1,1]]}
def pair(x):return [x.numerator,x.denominator]
def solve(matrix,rhs):
    rows=[list(map(F,row))+[F(value)] for row,value in zip(matrix,rhs)];n=len(rows)
    for col in range(n):
        pivot=next(k for k in range(col,n) if rows[k][col]);rows[col],rows[pivot]=rows[pivot],rows[col];scale=rows[col][col];rows[col]=[x/scale for x in rows[col]]
        for k in range(n):
            if k!=col:
                scale=rows[k][col];rows[k]=[a-scale*b for a,b in zip(rows[k],rows[col])]
    return [row[-1] for row in rows]
def vo(x):
    rows=x['rows'];n=len(rows);y=[r[0] for r in rows];xx=[r[1] for r in rows];z=[r[2] for r in rows]
    intercept,slope=solve([[n,sum(xx)],[sum(z),sum(a*b for a,b in zip(z,xx))]],[sum(y),sum(a*b for a,b in zip(z,y))])
    fs_intercept,fs_slope=solve([[n,sum(z)],[sum(z),sum(a*a for a in z)]],[sum(xx),sum(a*b for a,b in zip(z,xx))]);xb=F(sum(xx),n);zb=F(sum(z),n);res=[F(a)-intercept-slope*b for a,b in zip(y,xx)];total=sum((F(a)-xb)**2 for a in xx);fitted=[fs_intercept+fs_slope*a for a in z];explained=sum((a-xb)**2 for a in fitted)
    return {'intercept':pair(intercept),'slope':pair(slope),'residuals':list(map(pair,res)),'first_stage_slope':pair(fs_slope),'first_stage_r_squared':pair(explained/total),'claims':[False]*4}
def to(x):
    rows=x['rows'];design=[[1,r[2],r[3]] for r in rows];gram=[[sum(r[i]*r[j] for r in design) for j in range(3)] for i in range(3)];rhs=[sum(r[i]*raw[1] for r,raw in zip(design,rows)) for i in range(3)];fs=solve(gram,rhs);fit=[sum(F(a)*b for a,b in zip(row,fs)) for row in design];n=len(rows);intercept,slope=solve([[F(n),sum(fit)],[sum(fit),sum(a*a for a in fit)]],[F(sum(r[0] for r in rows)),sum(a*raw[0] for a,raw in zip(fit,rows))]);xb=F(sum(r[1] for r in rows),n)
    return {'intercept':pair(intercept),'slope':pair(slope),'first_stage_intercept':pair(fs[0]),'first_stage_coefficients':list(map(pair,fs[1:])),'fitted_x':list(map(pair,fit)),'residuals':[pair(F(r[0])-intercept-slope*r[1]) for r in rows],'first_stage_r_squared':pair(sum((a-xb)**2 for a in fit)/sum((F(r[1])-xb)**2 for r in rows)),'claims':[False]*4}
def expect(fn,x,msg):
    with pytest.raises(ValueError) as err:fn(x)
    assert str(err.value)==msg

def test_hand():
    x={'rows':[[1,0,-1],[3,1,0],[5,2,1]]};assert v.fit(x)==vo(x);assert v.fit(x)['slope']==[2,1];assert v.fit(x)['intercept']==[1,1];assert v.fit(x)['first_stage_r_squared']==[1,1]
    y={'rows':[[5,2,1,0],[7,3,0,1],[-3,-2,-1,0],[-5,-3,0,-1]]};assert t.fit(y)==to(y);assert t.fit(y)['slope']==[2,1];assert t.fit(y)['intercept']==[1,1];assert t.fit(y)['first_stage_coefficients']==[[2,1],[3,1]]

def test_random_oracles():
    r=random.Random(1062);counts=[0,0]
    for fn,oracle,width in [(v.fit,vo,3),(t.fit,to,4)]:
        for _ in range(250):
            rows=[[r.randint(-9,9) for _ in range(width)] for _ in range(r.randint(width,20))];x={'rows':rows}
            try:expected=oracle(x)
            except (StopIteration,ZeroDivisionError):continue
            assert fn(x)==expected;counts[width-3]+=1
    assert min(counts)>230

def test_caps_shift_and_freshness():
    for fn,oracle,width in [(v.fit,vo,3),(t.fit,to,4)]:
        for size in [width,20]:
            rows=[[2*j+1,j,j] if width==3 else [2*j+1,j,j%3,(j*j)%5] for j in range(size)]
            # Keep values within integer caps while retaining exact y=2*x+1.
            rows=[[2*((j%5)-2)+1,(j%5)-2,(j%3)-1] if width==3 else [2*((j%5)-2)+1,(j%5)-2,(j%3)-1,(j*j)%5-2] for j in range(size)]
            x={'rows':rows}
            try:expected=oracle(x)
            except (StopIteration,ZeroDivisionError):continue
            assert fn(x)==expected
    for fn,make in [(v.fit,vd),(t.fit,td)]:
        x=make();saved=copy.deepcopy(x);out=fn(x);out['claims'][0]=True;assert fn(x)['claims']==[False]*4;assert x==saved
        shifted={'rows':[[row[0]+1,row[1]+1]+row[2:] for row in make()['rows']]};assert fn(shifted)['slope']==fn(make())['slope']

@pytest.mark.parametrize('fn,make,minimum,width',[(v.fit,vd,3,3),(t.fit,td,4,4)])
def test_every_type_slot_and_message(fn,make,minimum,width):
    for val in [None,[],D(make()),{},dict(make(),extra=1)]:expect(fn,val,'exact dict with rows required')
    rowmsg='row must be an exact list of y,x,z' if width==3 else 'row must be an exact list of y,x,z1,z2'
    outermsg=f'rows must be an exact list of {minimum}..20 observations'
    for cls in [L,tuple]:
        x=make();x['rows']=cls(x['rows']);expect(fn,x,outermsg)
    for count in [0,minimum-1,21]:expect(fn,{'rows':[[1]*width]*count},outermsg)
    for i in range(len(make()['rows'])):
        for cls in [L,tuple]:
            x=make();x['rows'][i]=cls(x['rows'][i]);expect(fn,x,rowmsg)
        for size in [width-1,width+1]:
            x=make();x['rows'][i]=[1]*size;expect(fn,x,rowmsg)
        for j in range(width):
            for val in [True,I(1),1.0,-10,10,None,'1']:
                x=make();x['rows'][i][j]=val;expect(fn,x,'entries must be exact integers -9..9')

def test_model_messages():
    expect(v.fit,{'rows':[[1,1,0],[2,2,0],[3,3,0]]},'instrument must vary')
    expect(v.fit,{'rows':[[1,1,-1],[2,1,0],[3,1,1]]},'centered instrument-times-x product must be nonzero')
    expect(t.fit,{'rows':[[1,1,-1,-2],[2,2,0,0],[3,3,1,2],[4,4,2,4]]},'centered instruments must be linearly independent')
    expect(t.fit,{'rows':[[1,1,1,0],[2,1,0,1],[3,1,-1,0],[4,1,0,-1]]},'x must vary')
    expect(t.fit,{'rows':[[1,1,1,0],[2,-1,0,1],[3,1,-1,0],[4,-1,0,-1]]},'first-stage fitted x must vary')

def test_numeric_boundary_valid():
    x={'rows':[[-9,-9,-9],[0,0,0],[9,9,9]]};assert v.fit(x)==vo(x)
    y={'rows':[[-9,-9,9,0],[9,9,0,9],[9,9,-9,0],[-9,-9,0,-9]]};assert t.fit(y)==to(y)

def test_contract():
    assert v.SCOPE=='PARTIAL: centered just-identified linear IV with supplied observations only'
    assert t.SCOPE=='PARTIAL: centered two-instrument two-stage least squares only'
    assert v.NOT_CLAIMED==t.NOT_CLAIMED==('instrument validity','causal identification','standard errors','production readiness')
