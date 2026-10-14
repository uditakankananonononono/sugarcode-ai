import copy
import pytest
from sugarcode.extra_doc.pso_exact212 import advance


def args():return [[[2],[4]],[[1],[-1]],[[1],[3]],[[-5,5]],[0],.5,1,1,[[.5],[.25]],[[.25],[.5]]]


def test_independent_synchronous_velocity_personal_and_global_reference():
    inputs=args();before=copy.deepcopy(inputs);r=advance(*inputs)
    # oldglobal1;vel0=.5-.5-.25=-.25,vel1=-.5-.25-1.5=-2.25.
    assert r['positions_fraction']==[['7/4'],['7/4']] and r['velocities_fraction']==[['-1/4'],['-9/4']]
    assert r['personal_best_fraction']==[['1'],['7/4']] and r['global_best_fraction']==['1']
    assert r['old_global_best_index']==0 and r['new_global_best_index']==0
    assert r['old_best_loss_fraction']=='1' and r['new_best_loss_fraction']=='1'
    assert inputs==before and not r['global_optimum_verified'] and not r['draw_randomness_verified'] and r['external_effects']==[]


def test_global_best_updates_and_two_axis_clipping_exact_boundary_keeps_velocity():
    r=advance([[2],[4]],[[0],[0]],[[2],[4]],[[-5,5]],[0],0,0,2,[[0],[0]],[[0],[1]])
    assert r['positions_fraction']==[['2'],['0']] and r['new_global_best_index']==1 and r['new_best_loss_fraction']=='0'
    r=advance([[1,-1]],[[2,-3]],[[1,-1]],[[-2,2],[-2,2]],[0,0],1,0,0,[[0,0]],[[0,0]])
    assert r['positions_fraction']==[['2','-2']] and r['velocities_fraction']==[['0','0']]
    r=advance([[1]],[[1]],[[1]],[[-2,2]],[0],1,0,0,[[0]],[[0]])
    assert r['positions_fraction']==[['2']] and r['velocities_fraction']==[['1']]


@pytest.mark.parametrize('n',[0,1,19,20,21])
def test_particle_caps(n):
    inputs=[[[0]]*n,[[0]]*n,[[0]]*n,[[-1,1]],[0],0,0,0,[[0]]*n,[[0]]*n]
    if 1<=n<=20:assert len(advance(*inputs)['positions_fraction'])==n
    else:
        with pytest.raises(ValueError,match='^1..20 particles before scan$'):advance(*inputs)
@pytest.mark.parametrize('d',[0,1,7,8,9])
def test_dimension_caps(d):
    inputs=[[[0]*d],[[0]*d],[[0]*d],[[-1,1]]*d,[0]*d,0,0,0,[[0]*d],[[0]*d]]
    if 1<=d<=8:assert len(advance(*inputs)['positions_fraction'][0])==d
    else:
        with pytest.raises(ValueError,match='^1..8 target dimensions before scan$'):advance(*inputs)


def test_all_numeric_edges_coefficients_draws_bounds_and_strict_refusals():
    for v in (-1000,1000,-1000.0,1000.0):
        advance([[v]],[[v]],[[v]],[[-1000,1000]],[v],0,0,0,[[0]],[[1]])
    for index in (5,6,7):
        for v in (0,2,2.0):inputs=args();inputs[index]=v;advance(*inputs)
    for index in (8,9):
        for v in (0,1,1.0):inputs=args();inputs[index]=[[v],[v]];advance(*inputs)
    for bad in (True,'1',None,-1001,1001,float('nan'),float('inf')):
        for index in (0,1,2,4):
            inputs=args()
            if index==4:inputs[index][0]=bad
            else:inputs[index][0][0]=bad
            with pytest.raises(ValueError,match='^strict finite bounded PSO number$'):advance(*inputs)
    for index in (5,6,7,8,9):
        for bad in (True,'1',None,-.1,3,float('nan')):
            inputs=args();inputs[index]=bad if index<8 else [[bad],[0]]
            with pytest.raises(ValueError,match='^strict finite bounded PSO number$'):advance(*inputs)


def test_shapes_order_bounds_and_invalid_personal_best_refusals():
    for index in (0,1,2,8,9):
        for bad in ((),None,True,[[0,0]],[[0]]):
            inputs=args();inputs[index]=bad
            message='1..20 particles before scan' if index==0 and type(bad) is not list else 'aligned particle matrix dimensions'
            with pytest.raises(ValueError,match='^'+message+'$'):advance(*inputs)
    for bad in ([],(),None,[[0]],[[0,1,2]]):
        inputs=args();inputs[3]=bad
        with pytest.raises(ValueError,match='^one ordered bound pair per target dimension$'):advance(*inputs)
    inputs=args();inputs[3]=[[2,2]]
    with pytest.raises(ValueError,match='^strictly ordered PSO bounds$'):advance(*inputs)
    inputs=args();inputs[3]=[[-1,1]]
    with pytest.raises(ValueError,match='^current and personal points inside bounds$'):advance(*inputs)
    inputs=args();inputs[2][0][0]=3
    with pytest.raises(ValueError,match='^personal best no worse than current point$'):advance(*inputs)


def test_400_independent_decimal_synchronous_multiaxis_oracles():
    from decimal import Decimal as D
    from random import Random
    rng=Random(212)
    for _ in range(400):
        n=3;d=2;target=[rng.randrange(-2,3) for j in range(d)];pos=[[rng.randrange(-4,5) for j in range(d)] for i in range(n)];best=[p[:] for p in pos];vel=[[rng.randrange(-2,3) for j in range(d)] for i in range(n)];cd=[[rng.randrange(11)/10 for j in range(d)] for i in range(n)];sd=[[rng.randrange(11)/10 for j in range(d)] for i in range(n)];coeff=[rng.randrange(21)/10 for j in range(3)]
        def loss(p):return sum((D(str(v))-D(t))**2 for v,t in zip(p,target))
        gi=min(range(n),key=lambda i:(loss(best[i]),i));new=[];newvel=[];newbest=[]
        for i in range(n):
            point=[];velocity=[]
            for j in range(d):
                v=D(str(coeff[0]))*vel[i][j]+D(str(coeff[1]))*D(str(cd[i][j]))*(best[i][j]-pos[i][j])+D(str(coeff[2]))*D(str(sd[i][j]))*(best[gi][j]-pos[i][j]);raw=D(pos[i][j])+v;clipped=min(D(5),max(D(-5),raw));point.append(clipped);velocity.append(v if D(-5)<=raw<=D(5) else D(0))
            new.append(point);newvel.append(velocity);newbest.append(point if loss(point)<loss(best[i]) else list(map(D,best[i])))
        r=advance(pos,vel,best,[[-5,5]]*d,target,*coeff,cd,sd)
        def decode(rows):
            from fractions import Fraction as F
            return [[D(F(s).numerator)/D(F(s).denominator) for s in row] for row in rows]
        assert decode(r['positions_fraction'])==new and decode(r['velocities_fraction'])==newvel and decode(r['personal_best_fraction'])==newbest
        ng=min(range(n),key=lambda i:(loss(newbest[i]),i));assert r['new_global_best_index']==ng and r['old_global_best_index']==gi


def test_numeric_oversize_at_all_input_slots_before_conversion():
    for value in (10**400,-10**400):
        for index in range(10):
            inputs=args()
            if index in (5,6,7):inputs[index]=value
            elif index==4:inputs[index][0]=value
            elif index==3:inputs[index][0][0]=value
            else:inputs[index][0][0]=value
            with pytest.raises(ValueError,match='^strict finite bounded PSO number$'):advance(*inputs)


def test_draw_caps_bounds_endpoints_and_mixed_invalid_stages():
    for index in (8,9):
        for bad in (1.01,-.01):
            for particle in (0,1):
                inputs=args();inputs[index][particle][0]=bad
                with pytest.raises(ValueError,match='^strict finite bounded PSO number$'):advance(*inputs)
    for endpoint,value in ((0,-1001),(1,1001)):
        inputs=args();inputs[3][0][endpoint]=value
        with pytest.raises(ValueError,match='^strict finite bounded PSO number$'):advance(*inputs)
    for index in (0,2):
        inputs=args();inputs[index][0][0]=6
        with pytest.raises(ValueError,match='^current and personal points inside bounds$'):advance(*inputs)
    for index in (0,1,2,8,9):
        for row in (None,True,(),[0,0]):
            inputs=args();inputs[index][1]=row
            with pytest.raises(ValueError,match='^aligned particle matrix dimensions$'):advance(*inputs)


def test_cognitive_coefficient_not_social_coefficient_independent_nontrivial_memory():
    r=advance([[3],[4]],[[0],[0]],[[1],[2]],[[-5,5]],[0],0,2,0,[[.25],[.5]],[[0],[0]])
    assert r['positions_fraction']==[['2'],['2']] and r['velocities_fraction']==[['-1'],['-2']]
    assert r['personal_best_fraction']==[['1'],['2']]
