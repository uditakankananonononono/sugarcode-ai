import copy
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.robust_box225 import choose


def args():return [[dict(id='a',point=[1,-2]),dict(id='b',point=[0,1]),dict(id='c',point=[-1,0])],[2,-1],[1,.5],[dict(nominal=[1,1],radius=[.5,.25],rhs=1)]]


def test_hand_signed_adversarial_cost_feasibility_and_minimax_nomutation():
    a=args();before=copy.deepcopy(a);r=choose(*a)
    assert r['selected_id']=='c' and r['status']=='minimax_in_supplied_robust_menu'
    assert [(s['worst_objective_fraction'],s['best_objective_fraction'],s['robust_slack_fraction'],s['robust_feasible_in_supplied_boxes']) for s in r['scores']]==[('6','2',['1'],True),('-1/2','-3/2',['-1/4'],False),('-1','-3',['3/2'],True)]
    assert r['scores'][0]['adversarial_objective_coefficients_fraction']==['3','-3/2'] and r['scores'][0]['worst_constraint_lhs_fraction']==['0']
    assert a==before and r['external_effects']==[] and r['uncertainty_set']=='independent closed coefficient boxes, separate objective and constraint boxes'


def test_400_independent_uncertainty_vertex_enumeration_oracles():
    from itertools import product
    from random import Random
    rng=Random(225)
    for _ in range(400):
        d=3;c=[rng.randrange(-3,4) for j in range(d)];rad=[rng.randrange(3) for j in range(d)];nom=[rng.randrange(-3,4) for j in range(d)];cr=[rng.randrange(3) for j in range(d)];rhs=rng.randrange(-5,6);points=[[rng.randrange(-3,4) for j in range(d)] for i in range(5)];r=choose([dict(id=str(i),point=p) for i,p in enumerate(points)],c,rad,[dict(nominal=nom,radius=cr,rhs=rhs)]);valid=[]
        for i,(p,s) in enumerate(zip(points,r['scores'])):
            objective=[sum((c[j]+sign[j]*rad[j])*p[j] for j in range(d)) for sign in product([-1,1],repeat=d)]
            constraints=[sum((nom[j]+sign[j]*cr[j])*p[j] for j in range(d)) for sign in product([-1,1],repeat=d)]
            assert F(s['worst_objective_fraction'])==max(objective) and F(s['best_objective_fraction'])==min(objective) and F(s['worst_constraint_lhs_fraction'][0])==max(constraints)
            assert s['robust_feasible_in_supplied_boxes']==(max(constraints)<=rhs)
            if max(constraints)<=rhs:valid.append((max(objective),str(i)))
        assert r['selected_id']==(min(valid)[1] if valid else None)


def test_caps_edges_zero_radius_slack_equality_ties_and_no_feasible():
    for n in (1,99,100):
        for d in (1,7,8):assert choose([dict(id=str(i),point=[0]*d) for i in range(n)],[0]*d,[0]*d,[])['selected_id']=='0'
    for n in (0,19,20):assert choose([dict(id='x'*120,point=[0])],[1000],[1000],[dict(nominal=[0],radius=[0],rhs=0)]*n)['selected_id']=='x'*120
    for v in (-1000,1000,-1000.0,1000.0):choose([dict(id='a',point=[v])],[v],[1000],[])
    assert choose([dict(id='a',point=[0])],[0],[0],[dict(nominal=[0],radius=[0],rhs=-1)])['status']=='no_robust_feasible_option'


def test_all_staged_caps_shapes_schema_numeric_nonbool_and_huge_values():
    for nominal in (None,(),[],True,[0]*9):
        a=args();a[1]=nominal
        with pytest.raises(ValueError,match='^1..8 robust dimensions before scan$'):choose(*a)
    for raw in (None,(),[],[0],[0]*3):
        a=args();a[2]=raw
        with pytest.raises(ValueError,match='^one robust value per dimension$'):choose(*a)
    for rows in (None,(),True,[{}]*21):
        a=args();a[3]=rows
        with pytest.raises(ValueError,match='^0..20 robust constraints before scan$'):choose(*a)
    for row in (None,[],{},dict(args()[3][0],extra=1)):
        a=args();a[3]=[row]
        with pytest.raises(ValueError,match='^exact robust nominal/radius/rhs fields$'):choose(*a)
    for options in (None,(),[],True,[{}]*101):
        a=args();a[0]=options
        with pytest.raises(ValueError,match='^1..100 robust options before scan$'):choose(*a)
    for row in (None,[],{},dict(args()[0][0],extra=1)):
        a=args();a[0]=[row]
        with pytest.raises(ValueError,match='^exact robust id/point fields$'):choose(*a)
    for ident in (True,None,'',' ','x'*121,'b'):
        a=args();a[0][0]['id']=ident
        with pytest.raises(ValueError,match='^unique nonblank robust ids 1..120$'):choose(*a)
    for raw in (None,(),[],[0],[0]*3):
        for slot in ('point','nominal','radius'):
            a=args()
            if slot=='point':a[0][0]['point']=raw
            else:a[3][0][slot]=raw
            with pytest.raises(ValueError,match='^one robust value per dimension$'):choose(*a)
    for bad in (True,None,'1',-1000.01,1000.01,10**400,-10**400,float('nan'),float('inf')):
        for slot in ('point','nominal','radius','constraint_nominal','constraint_radius','rhs'):
            a=args()
            if slot=='point':a[0][0]['point'][1]=bad
            elif slot=='nominal':a[1][1]=bad
            elif slot=='radius':a[2][1]=bad
            elif slot=='rhs':a[3][0]['rhs']=bad
            else:a[3][0][slot.split('_')[1]][1]=bad
            with pytest.raises(ValueError,match='^strict finite bounded robust number$'):choose(*a)
    for slot in ('radius','constraint_radius'):
        a=args()
        if slot=='radius':a[2][0]=-.01
        else:a[3][0]['radius'][0]=-.01
        with pytest.raises(ValueError,match='^strict finite bounded robust number$'):choose(*a)


def test_adversarial_coefficient_witness_positive_zero_negative_sign_and_fraction():
    r=choose([dict(id='a',point=[.5,0,-.5])],[2,3,4],[1,2,3],[])
    assert r['scores'][0]['adversarial_objective_coefficients_fraction']==['3','5','1']
    assert r['scores'][0]['worst_objective_fraction']=='1'
