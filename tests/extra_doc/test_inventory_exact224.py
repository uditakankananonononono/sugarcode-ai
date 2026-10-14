import copy
import pytest
from fractions import Fraction
from sugarcode.extra_doc.inventory_exact224 import plan


def inputs():return [[0,2,4],[dict(id='a',demand=0,probability=.25),dict(id='b',demand=4,probability=.75)],1,3,.5]


def test_asymmetric_recourse_hand_reference_expected_cost_information_value_no_mutation():
    a=inputs();before=copy.deepcopy(a);r=plan(*a)
    assert r['selected_quantity']==4 and r['expected_cost_fraction']=='9/2'
    assert [c['expected_cost_fraction'] for c in r['choices']]==['9','27/4','9/2']
    assert r['choices'][1]['scenario_outcomes']==[dict(id='a',shortage=0,excess=2,cost_fraction='3'),dict(id='b',shortage=2,excess=0,cost_fraction='8')]
    assert r['perfect_information_expected_cost_fraction']=='3' and r['expected_value_of_perfect_information_fraction']=='3/2'
    assert a==before and not r['purchase_executed'] and not r['probabilities_verified'] and r['external_effects']==[]


def test_zero_probability_ties_and_sorting():
    r=plan([4,0,2],[dict(id='a',demand=4,probability=0),dict(id='b',demand=0,probability=1)],0,0,0)
    assert r['selected_quantity']==0 and [c['quantity'] for c in r['choices']]==[0,2,4]
    assert r['expected_cost_fraction']=='0' and r['expected_value_of_perfect_information_fraction']=='0'


def test_probability_changes_real_decision():
    a=inputs();a[1][0]['probability']=.9;a[1][1]['probability']=.1
    assert plan(*a)['selected_quantity']==0


def test_400_independent_decimal_menu_references():
    from random import Random
    from decimal import Decimal
    rng=Random(224)
    for _ in range(400):
        qs=rng.sample(range(12),rng.randrange(1,8));ds=[rng.randrange(12) for j in range(3)]
        k=rng.randrange(11);l=rng.randrange(11-k);ps=[k/10,l/10,(10-k-l)/10]
        costs=[rng.randrange(11)/10 for j in range(3)]
        rows=[dict(id=str(j),demand=d,probability=p) for j,(d,p) in enumerate(zip(ds,ps))]
        matrix={q:[Decimal(str(costs[0]))*q+Decimal(str(costs[1]))*(d-q if d>q else 0)+Decimal(str(costs[2]))*(q-d if q>d else 0) for d in ds] for q in qs}
        expected={q:sum(Decimal(str(p))*v for p,v in zip(ps,vs)) for q,vs in matrix.items()}
        best=min(qs,key=lambda q:(expected[q],q));oracle=sum(Decimal(str(ps[j]))*min(v[j] for v in matrix.values()) for j in range(3))
        r=plan(qs,rows,*costs)
        assert r['selected_quantity']==best
        def decimal(s):
            v=s.split('/');return Decimal(v[0])/(Decimal(v[1]) if len(v)==2 else 1)
        assert decimal(r['expected_cost_fraction'])==expected[best]
        assert decimal(r['perfect_information_expected_cost_fraction'])==oracle
        assert decimal(r['expected_value_of_perfect_information_fraction'])==expected[best]-oracle
        for choice in r['choices']:
            assert decimal(choice['expected_cost_fraction'])==expected[choice['quantity']]


def test_full_menu_caps_and_numeric_endpoints():
    for n in (1,99,100):
        a=inputs();a[0]=list(range(n));assert len(plan(*a)['choices'])==n
        a=inputs();a[1]=[dict(id=str(j),demand=0,probability=1 if j==0 else 0) for j in range(n)];assert len(plan(*a)['choices'][0]['scenario_outcomes'])==n
    for q in (0,10000):
        a=inputs();a[0]=[q];a[1]=[dict(id='x'*120,demand=q,probability=1)];assert plan(*a)['selected_quantity']==q
    for cost in (0,1000000,0.0,1000000.0):
        for index in (2,3,4):
            a=inputs();a[index]=cost;plan(*a)


def test_precise_caps_and_every_type_schema_refusal_stage():
    for index in (0,1):
        for value in (None,(),[],True,list(range(101))):
            a=inputs();a[index]=value
            with pytest.raises(ValueError,match='^1..100 '+('candidate quantities' if index==0 else 'demand scenarios')+' before scan$'):plan(*a)
    for value in (True,1.0,'1',-1,10001):
        for j in (0,1):
            a=inputs();a[0][j]=value
            with pytest.raises(ValueError,match='^strict quantity integers within 0..10000$'):plan(*a)
        a=inputs();a[1][0]['demand']=value
        with pytest.raises(ValueError,match='^strict demand integers within 0..10000$'):plan(*a)
    a=inputs();a[0]=[0,0]
    with pytest.raises(ValueError,match='^unique quantity choices$'):plan(*a)
    for cost in (True,None,'1',-.01,1000000.01,float('nan'),float('inf')):
        for index in (2,3,4):
            a=inputs();a[index]=cost
            with pytest.raises(ValueError,match='^strict finite nonnegative cost within 1000000$'):plan(*a)
    for p in (True,None,'1',-.01,1.01,float('nan'),float('inf')):
        a=inputs();a[1][0]['probability']=p
        with pytest.raises(ValueError,match='^strict finite probability within 0..1$'):plan(*a)
    for bad in ({},[],dict(id='x',demand=1,probability=1,extra=0)):
        a=inputs();a[1][0]=bad
        with pytest.raises(ValueError,match='^exact id/demand/probability fields$'):plan(*a)
    for ident in ('',True,None,'x'*121,'b'):
        a=inputs();a[1][0]['id']=ident
        with pytest.raises(ValueError,match='^unique nonempty scenario id up to 120 characters$'):plan(*a)
    for p in (.74999999,.75000001):
        a=inputs();a[1][1]['probability']=p
        with pytest.raises(ValueError,match='^scenario probabilities must sum exactly to one$'):plan(*a)


def test_invariance_permutation_and_demand_zero_endpoint_recourse():
    a=inputs();r=plan(*a);a[0].reverse();a[1].reverse();s=plan(*a)
    assert s['selected_quantity']==r['selected_quantity'] and s['expected_cost_fraction']==r['expected_cost_fraction'] and s['perfect_information_expected_cost_fraction']==r['perfect_information_expected_cost_fraction']
    r=plan([2],[dict(id='x',demand=2,probability=1)],2,3,5)
    assert r['choices'][0]['scenario_outcomes']==[dict(id='x',shortage=0,excess=0,cost_fraction='4')]
    assert r['expected_value_of_perfect_information_fraction']=='0'


@pytest.mark.parametrize('huge',[10**400,-10**400])
def test_huge_integers_refused_before_conversion_all_numeric_slots(huge):
    for index in (2,3,4):
        a=inputs();a[index]=huge
        with pytest.raises(ValueError,match='^strict finite nonnegative cost within 1000000$'):plan(*a)
    a=inputs();a[1][0]['probability']=huge
    with pytest.raises(ValueError,match='^strict finite probability within 0..1$'):plan(*a)
    a=inputs();a[1][0]['demand']=huge
    with pytest.raises(ValueError,match='^strict demand integers within 0..10000$'):plan(*a)
    a=inputs();a[0][0]=huge
    with pytest.raises(ValueError,match='^strict quantity integers within 0..10000$'):plan(*a)
