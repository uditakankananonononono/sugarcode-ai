import copy
import pytest
from fractions import Fraction as F
from sugarcode.extra_doc.bellman_exact223 import plan


def args():return [['a','b'],[[dict(state='a',action='stay',next='a',cost=1),dict(state='a',action='switch',next='b',cost=2)], [dict(state='a',action='end',next='a',cost=3),dict(state='b',action='end',next='a',cost=-1)]],'a',dict(a=4,b=0)]


def test_hand_shared_subproblems_value_tables_plan_and_terminal_cost():
    a=args();before=copy.deepcopy(a);r=plan(*a)
    assert r['initial_cost_fraction']=='5' and r['value_tables_fraction']==[dict(a='5'),dict(a='7',b='3'),dict(a='4',b='0')]
    assert r['plan']==[dict(stage=0,state='a',action='switch',next='b'),dict(stage=1,state='b',action='end',next='a')] and r['terminal_state']=='a'
    assert a==before and r['external_effects']==[] and r['status']=='optimal_in_supplied_finite_model'
    assert r['tie_break']=='lowest action label then next-state label'
    assert r['recurrence']=='V_t(s)=min_a(cost_t(s,a)+V_(t+1)(next)); dead states omitted'


def test_400_independent_exhaustive_full_path_cost_oracles():
    from random import Random
    rng=Random(223)
    for _ in range(400):
        states=list('abc');stages=[]
        for t in range(4):
            stage=[]
            for state in states:
                for action in ('x','y'):
                    if rng.randrange(4):stage.append(dict(state=state,action=action,next=rng.choice(states),cost=rng.randrange(-4,5)/2))
            stages.append(stage)
        terminal={s:rng.randrange(-4,5)/2 for s in states};r=plan(states,stages,'a',terminal);paths=[]
        def enumerate_paths(state,t,cost,route):
            if t==4:paths.append((cost+F(str(terminal[state])),tuple(route),state));return
            for e in stages[t]:
                if e['state']==state:enumerate_paths(e['next'],t+1,cost+F(str(e['cost'])),route+[(e['action'],e['next'])])
        enumerate_paths('a',0,F(0),[])
        if not paths:assert r['initial_cost_fraction'] is None and r['plan']==[] and r['status']=='no_terminal_reaching_plan'
        else:
            expected=min(paths);assert F(r['initial_cost_fraction'])==expected[0] and tuple((e['action'],e['next']) for e in r['plan'])==expected[1] and r['terminal_state']==expected[2]


def test_full_caps_dead_states_ties_and_negative_numeric_boundaries():
    for n in (1,19,20):
        states=[str(i) for i in range(n)];stage=[dict(state=s,action='go',next=s,cost=-1000) for s in states]
        r=plan(states,[stage]*20,'0',{s:1000 for s in states});assert r['initial_cost_fraction']=='-19000' and len(r['plan'])==20
    stage=[dict(state='a',action=str(i),next='a',cost=0) for i in range(100)]
    assert plan(['a'],[stage],'a',dict(a=0))['plan'][0]['action']=='0'
    assert plan(['a'],[[]],'a',dict(a=0))['terminal_state'] is None
    for v in (-1000,1000,-1000.0,1000.0):plan(['a'],[[dict(state='a',action='x'*80,next='a',cost=v)]],'a',dict(a=v))


def test_all_staged_refusals_types_schema_caps_and_huge_costs():
    for states in (None,(),[],True,['a']*21):
        a=args();a[0]=states
        with pytest.raises(ValueError,match='^1..20 states before scan$'):plan(*a)
    a=args();a[0]=['a','a']
    with pytest.raises(ValueError,match='^unique Bellman states$'):plan(*a)
    for initial in (True,None,'missing'):
        a=args();a[2]=initial
        with pytest.raises(ValueError,match='^initial state in supplied menu$'):plan(*a)
    for stages in (None,(),[],[[]]*21):
        a=args();a[1]=stages
        with pytest.raises(ValueError,match='^1..20 stages before scan$'):plan(*a)
    for terminal in (None,[],{},dict(a=0,b=0,extra=0)):
        a=args();a[3]=terminal
        with pytest.raises(ValueError,match='^terminal cost for every supplied state$'):plan(*a)
    for stage in (None,(),True,[{}]*101):
        a=args();a[1][0]=stage
        with pytest.raises(ValueError,match='^0..100 transitions per stage before scan$'):plan(*a)
    for row in (None,[],{},dict(args()[1][0][0],extra=1)):
        a=args();a[1][0]=[row]
        with pytest.raises(ValueError,match='^exact state/action/next/cost fields$'):plan(*a)
    for key in ('state','next'):
        a=args();a[1][0][0][key]='missing'
        with pytest.raises(ValueError,match='^transition states in menu$'):plan(*a)
    a=args();a[1][0]=[a[1][0][0]]*2
    with pytest.raises(ValueError,match='^unique state/action per stage$'):plan(*a)
    for bad in (True,None,'','x'*81):
        for slot in ('menu','state','action','next'):
            a=args()
            if slot=='menu':a[0][0]=bad
            else:a[1][0][0][slot]=bad
            with pytest.raises(ValueError,match='^state/action label 1..80 chars$'):plan(*a)
    for bad in (True,None,'1',-1000.01,1000.01,10**400,-10**400,float('nan'),float('inf')):
        for slot in ('terminal','transition'):
            a=args()
            if slot=='terminal':a[3]['a']=bad
            else:a[1][0][0]['cost']=bad
            with pytest.raises(ValueError,match='^strict finite Bellman cost within -1000..1000$'):plan(*a)
