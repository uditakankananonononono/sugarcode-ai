from fractions import Fraction as F
import itertools
import pytest
from sugarcode.extra_doc.contextual_bandit import contextual_bandit


def oracle(arms,rows,context,ridge):
    # Independent Cramer's rule for <=2 dimensions, not elimination.
    out=[];d=len(context)
    for arm in range(arms):
        A=[[F(ridge if i==j else 0) for j in range(d)] for i in range(d)];b=[F(0)]*d
        for a,x,y in rows:
            if a==arm:
                for i in range(d):
                    b[i]+=x[i]*y
                    for j in range(d): A[i][j]+=x[i]*x[j]
        if d==1:w=[b[0]/A[0][0]];v=context[0]**2/A[0][0]
        else:
            det=A[0][0]*A[1][1]-A[0][1]*A[1][0]
            w=[(b[0]*A[1][1]-b[1]*A[0][1])/det,(b[1]*A[0][0]-b[0]*A[1][0])/det]
            v=(context[0]**2*A[1][1]-2*context[0]*context[1]*A[0][1]+context[1]**2*A[0][0])/det
        out.append((w,sum(x*y for x,y in zip(w,context)),v))
    return out


def test_independent_nonplanar_updates():
    rows=[(0,[2,-1],3),(1,[-1,3],-2),(0,[1,2],-1)]
    r=contextual_bandit(2,rows,[3,-2],ridge=2,alpha=0)
    want=oracle(2,rows,[3,-2],2)
    assert r['weights']==[x[0] for x in want]
    assert r['means']==[x[1] for x in want]
    assert r['bonus_squared']==[F(0)]*2
    assert r['counts']==[2,1]
    assert r['chosen_arm']==max(range(2),key=lambda i:(want[i][1],-i))


def test_exploration_and_exact_tie():
    assert contextual_bandit(2,[],[1],alpha=1)['chosen_arm']==0
    r=contextual_bandit(2,[(0,[1],0)],[1],alpha=2)
    assert r['means']==[0,0] and r['bonus_squared']==[2,4]
    assert r['chosen_arm']==1


def test_many_small_oracles():
    for x,y,c in itertools.product([-2,0,1],repeat=3):
        rows=[(0,[x],y)];r=contextual_bandit(2,rows,[c],ridge=1,alpha=0)
        want=oracle(2,rows,[c],1)
        assert r['weights']==[z[0] for z in want]
        assert r['means']==[z[1] for z in want]


@pytest.mark.parametrize('value',[True,None,1.,'1',-1,0,5])
def test_arms_refuse(value):
    with pytest.raises((TypeError,ValueError)):contextual_bandit(value,[],[1])


@pytest.mark.parametrize('context',[[],[1]*3,None,(1,),[True],[1.],[1001],[-1001]])
def test_context_refuse(context):
    with pytest.raises((TypeError,ValueError)):contextual_bandit(2,[],context)


@pytest.mark.parametrize('rows',[None,(),[(2,[1],1)],[(0,[1,2],1)],[(True,[1],1)],[(0,[1],True)],[(0,[1],1.)],[(0,[1],1001)],[(0,[1],1)]*101])
def test_rows_refuse(rows):
    with pytest.raises((TypeError,ValueError)):contextual_bandit(2,rows,[1])


@pytest.mark.parametrize('name,value',[('ridge',0),('ridge',101),('ridge',True),('ridge',1.),('alpha',-1),('alpha',11),('alpha',None),('alpha',1.)])
def test_params_refuse(name,value):
    with pytest.raises((TypeError,ValueError)):contextual_bandit(2,[],[1],**{name:value})


def test_caps_endpoints_and_preflight():
    class Rows(list):
        def __iter__(self):raise AssertionError('overbudget scanned')
    with pytest.raises(ValueError): contextual_bandit(2,Rows([None]*101),[1])
    r=contextual_bandit(4,[(0,[1000,-1000],1000)]*100,[1000,-1000],ridge=100,alpha=10)
    assert r['counts']==[100,0,0,0]
    assert contextual_bandit(1,[],[0],ridge=1,alpha=0)['chosen_arm']==0


def test_radical_comparison_exact_square_oracle():
    from sugarcode.extra_doc.contextual_bandit import _compare
    for m,n,a,b in itertools.product(range(-2,3),range(-2,3),range(4),range(4)):
        want=(m+a>n+b)-(m+a<n+b)
        assert _compare(F(m),F(a*a),F(n),F(b*b))==want
    assert _compare(F(2),F(2),F(0),F(12))==-1
    assert _compare(F(3),F(2),F(0),F(12))==1


def test_two_arm_alpha_changes_choice_and_inputs_untouched():
    import copy
    rows=[(0,[1],1)];before=copy.deepcopy(rows)
    assert contextual_bandit(2,rows,[1],alpha=0)['chosen_arm']==0
    assert contextual_bandit(2,rows,[1],alpha=2)['chosen_arm']==1
    assert rows==before


def test_exact_refusal_schema_and_scalar_boundaries():
    with pytest.raises(ValueError,match='integer budget exceeded'):
        contextual_bandit(2,[],[1],ridge=0)
    assert contextual_bandit(2,[],[1],ridge=1)['bonus_squared']==[1,1]
    for row in [None,'abc',{},(0,[1]),(0,[1],1,2)]:
        with pytest.raises(ValueError,match='feedback row requires arm/context/reward'):
            contextual_bandit(2,[row],[1])
    for row in [(0,[1001],0),(0,[-1001],0),(0,[1],1001),(0,[1],-1001)]:
        with pytest.raises(ValueError,match='integer budget exceeded'):
            contextual_bandit(2,[row],[1])
    for x,y in [(1000,1000),(-1000,-1000),(1000,-1000),(-1000,1000)]:
        r=contextual_bandit(2,[(0,[x],y)],[1],ridge=1,alpha=0)
        assert r['weights'][0]==[F(x*y,1+x*x)]


def test_keyword_defaults_are_literal_and_equal_explicit_call():
    import inspect
    sig=inspect.signature(contextual_bandit)
    assert sig.parameters['ridge'].default==1
    assert sig.parameters['alpha'].default==1
    assert contextual_bandit(2,[],[1])==contextual_bandit(2,[],[1],ridge=1,alpha=1)
