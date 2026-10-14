import copy
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.mixed_linear222 import solve


def args():return [[[0,2]],[0,3],[2,-1],[dict(coefficients=[1,1],relation='<=',rhs=3),dict(coefficients=[-1,1],relation='>=',rhs=1)],'min']


def test_hand_continuous_not_rounded_intervals_and_integer_branch_optimum():
    a=args();before=copy.deepcopy(a);r=solve(*a)
    assert r['point_fraction']==['0','3'] and r['objective_fraction']=='-3' and r['integer_assignments_checked']==3 and r['feasible_integer_assignments']==2
    assert r['status']=='optimal_in_declared_mixed_box' and a==before and r['external_effects']==[] and not r['global_unbounded_optimum_claimed'] and r['continuous_axes']==1
    r=solve([[0,1]],[0,2],[0,1],[dict(coefficients=[1,-2],relation='<=',rhs=-1)],'min')
    assert r['point_fraction']==['0','1/2'] and r['objective_fraction']=='1/2'
    assert r['tie_break']=='lexicographically smallest full point'


def test_500_independent_line_intersection_endpoint_oracles():
    from random import Random
    rng=Random(222)
    for _ in range(500):
        obj=[rng.randrange(-3,4),rng.randrange(-3,4)];rows=[dict(coefficients=[rng.randrange(-3,4),rng.randrange(-3,4)],relation=rng.choice(['<=','>=','==']),rhs=rng.randrange(-5,6)) for k in range(rng.randrange(4))];direction=rng.choice(['min','max']);points=[];feasible=0
        for x in range(-2,3):
            candidates={F(-3),F(3)}
            for row in rows:
                a,b=row['coefficients']
                if b:candidates.add(F(row['rhs']-a*x,b))
            valid=[]
            for y in candidates:
                if not -3<=y<=3:continue
                allowed=True
                for row in rows:
                    value=row['coefficients'][0]*x+row['coefficients'][1]*y;rhs=row['rhs'];relation=row['relation']
                    if not {'<=':value<=rhs,'>=':value>=rhs,'==':value==rhs}[relation]:allowed=False
                if allowed:valid.append((obj[0]*x+obj[1]*y,(F(x),y)))
            if valid:feasible+=1;points+=valid
        r=solve([[-2,2]],[-3,3],obj,rows,direction)
        assert r['feasible_integer_assignments']==feasible
        if not points:assert r['point_fraction'] is None and r['status']=='infeasible_in_declared_mixed_box'
        else:
            expected=sorted(points,key=lambda p:(p[0] if direction=='min' else -p[0],p[1]))[0]
            assert tuple(map(F,r['point_fraction']))==expected[1] and F(r['objective_fraction'])==expected[0]


def test_all_caps_boundary_values_constraint_menu_and_infeasible_zero_coefficients():
    for d in (1,2,3):assert solve([[0,0]]*d,[0,0],[0]*(d+1),[],'max')['point_fraction']==['0']*(d+1)
    assert solve([[0,9]]*3,[0,0],[0]*4,[],'min')['integer_assignments_checked']==1000
    for v in (-1000,1000,-1000.0,1000.0):solve([[-50,50]],[v,v],[v,v],[],'min')
    for n in (0,19,20):solve([[0,0]],[0,1],[0,0],[dict(coefficients=[0,0],relation='==',rhs=0)]*n,'min')
    for relation,rhs in [('<=',-1),('>=',1),('==',1)]:assert solve([[0,0]],[0,1],[0,0],[dict(coefficients=[0,0],relation=relation,rhs=rhs)],'min')['point_fraction'] is None


def test_all_staged_caps_types_shapes_hugeints_and_relations():
    for direction in (None,True,'bad'):
        a=args();a[4]=direction
        with pytest.raises(ValueError,match='^mixed direction min or max$'):solve(*a)
    for bounds in (None,(),[],True,[[0,0]]*4):
        a=args();a[0]=bounds
        with pytest.raises(ValueError,match='^1..3 integer dimensions before scan$'):solve(*a)
    for pair in (None,(),[],[0],[0]*3,[True,1],[0,1.0],[-51,0],[0,51]):
        a=args();a[0]=[pair]
        with pytest.raises(ValueError,match='^strict integer bound pairs within -50..50$'):solve(*a)
    with pytest.raises(ValueError,match='^ordered inclusive integer bounds$'):solve([[1,0]],[0,1],[0,0],[],'min')
    with pytest.raises(ValueError,match='^at most 1000 integer assignments before scan$'):solve([[0,10],[0,9],[0,9]],[0,1],[0]*4,[],'min')
    for pair in (None,(),[],[0],[0]*3):
        a=args();a[1]=pair
        with pytest.raises(ValueError,match='^one continuous bound pair$'):solve(*a)
    a=args();a[1]=[1,0]
    with pytest.raises(ValueError,match='^ordered inclusive continuous bounds$'):solve(*a)
    for vector in (None,(),[],[0],[0]*3):
        a=args();a[2]=vector
        with pytest.raises(ValueError,match='^one coefficient per integer and continuous axis$'):solve(*a)
    for rows in (None,(),True,[{}]*21):
        a=args();a[3]=rows
        with pytest.raises(ValueError,match='^0..20 mixed constraints before scan$'):solve(*a)
    for row in (None,[],{},dict(args()[3][0],extra=1)):
        a=args();a[3]=[row]
        with pytest.raises(ValueError,match='^exact mixed coefficients/relation/rhs fields$'):solve(*a)
    for relation in (True,None,'bad'):
        a=args();a[3][0]['relation']=relation
        with pytest.raises(ValueError,match='^mixed constraint relation <=, >= or ==$'):solve(*a)
    for bad in (True,None,'1',-1000.01,1000.01,10**400,-10**400,float('nan'),float('inf')):
        for slot in ('bound','objective','coefficient','rhs'):
            a=args()
            if slot=='bound':a[1][1]=bad
            elif slot=='objective':a[2][1]=bad
            elif slot=='coefficient':a[3][0]['coefficients'][1]=bad
            else:a[3][0]['rhs']=bad
            with pytest.raises(ValueError,match='^strict finite mixed value within -1000..1000$'):solve(*a)


def test_signed_asymmetric_integer_box_count_first_overcap_and_decimal_curvature():
    r=solve([[-3,-1],[2,4]],[0,1],[0,0,0],[],'min')
    assert r['integer_assignments_checked']==9 and r['feasible_integer_assignments']==9 and r['point_fraction']==['-3','2','0']
    with pytest.raises(ValueError,match='^at most 1000 integer assignments before scan$'):solve([[0,6],[0,10],[0,12]],[0,1],[0]*4,[],'min')
    assert solve([[0,0]],[0,2],[0,1],[dict(coefficients=[0,.5],relation='>=',rhs=.5)],'min')['point_fraction']==['0','1']
