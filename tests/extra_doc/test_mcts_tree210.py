import copy
import math
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.mcts_tree210 import search


def args():return [[dict(id='r',children=['a','b'],reward=None),dict(id='a',children=['c','d'],reward=None),dict(id='b',children=[],reward=2),dict(id='c',children=[],reward=-1),dict(id='d',children=[],reward=5)],'r',10,1,[.75]*80]


def test_hand_expansion_rollout_no_rollout_backprop_and_root_choice():
    a=args();a[2]=2;a[4]=[.75]*16;before=copy.deepcopy(a);r=search(*a)
    assert r['trace']==[dict(iteration=1,selected_path=['r','a'],rollout_path=['a','d'],reward_fraction='5'),dict(iteration=2,selected_path=['r','b'],rollout_path=['b'],reward_fraction='2')]
    assert r['visits']==dict(r=2,a=1,b=1,c=0,d=0) and r['reward_sum_fraction']==dict(r='7',a='5',b='2',c='0',d='0')
    assert r['selected_root_child']=='a' and r['uct_scores_FLOAT'] and r['external_effects']==[] and a==before
    assert r['selection']=='most visits, then highest mean, then supplied child order'


def test_250_independent_two_arm_uct_vote_oracles_and_exploration_effect():
    from random import Random
    rng=Random(210)
    for _ in range(250):
        rewards=[rng.randrange(-10,11),rng.randrange(-10,11)];coef=rng.choice([0,.5,1,2,10]);budget=rng.randrange(2,30);counts=[0,0];totals=[0,0];trace=[]
        for t in range(budget):
            if counts[0]==0:chosen=0
            elif counts[1]==0:chosen=1
            else:
                first=totals[0]/counts[0]+coef*math.sqrt(math.log(t)/counts[0]);second=totals[1]/counts[1]+coef*math.sqrt(math.log(t)/counts[1]);chosen=1 if second>first else 0
            counts[chosen]+=1;totals[chosen]+=rewards[chosen];trace.append(chosen)
        nodes=[dict(id='root',children=['left','right'],reward=None),dict(id='left',children=[],reward=rewards[0]),dict(id='right',children=[],reward=rewards[1])]
        r=search(nodes,'root',budget,coef,[0]*8*budget)
        assert [s['selected_path'][-1] for s in r['trace']]==[['left','right'][i] for i in trace]
        assert [r['visits'][i] for i in ('left','right')]==counts and [F(r['reward_sum_fraction'][i]) for i in ('left','right')]==totals
        chosen=sorted(range(2),key=lambda i:(-counts[i],-F(totals[i],counts[i]),i))[0]
        assert r['selected_root_child']==['left','right'][chosen]
    low=search(nodes,'root',30,0,[0]*240);high=search(nodes,'root',30,10,[0]*240)
    assert low['visits']!=high['visits']


def test_rollout_boundary_depth_terminal_root_and_child_order_ties():
    a=args();a[2]=1
    for draw,terminal,value in ((0,'c','-1'),(.499999,'c','-1'),(.5,'d','5'),(.999999,'d','5')):
        a[4]=[draw]*8;r=search(*a)
        assert r['trace'][0]['rollout_path']==['a',terminal] and r['trace'][0]['reward_fraction']==value
    r=search([dict(id='r',children=[],reward=.1)],'r',1,10,[0]*8)
    assert r['selected_root_child'] is None and r['visits']=={'r':1} and r['reward_sum_fraction']=={'r':'1/10'}
    chain=[dict(id=str(i),children=[str(i+1)] if i<8 else [],reward=None if i<8 else 0) for i in range(9)]
    assert search(chain,'0',1,0,[0]*8)['trace'][0]['rollout_path']==list(map(str,range(1,9)))
    for size in (2,8):
        menu=[str(i) for i in range(size)];nodes=[dict(id='r',children=menu,reward=None)]+[dict(id=i,children=[],reward=0) for i in menu]
        r=search(nodes,'r',100,10,[0]*800);assert sum(r['visits'][i] for i in menu)==100 and r['selected_root_child']=='0'


def test_all_strict_refusal_stages_numeric_schema_tree_connectivity_and_depth():
    for iterations in (True,1.0,0,101,None):
        a=args();a[2]=iterations
        with pytest.raises(ValueError,match='^strict MCTS iterations 1..100$'):search(*a)
    for coef in (True,None,'1',-.01,10.01,10**400,-10**400,float('nan'),float('inf')):
        a=args();a[3]=coef
        with pytest.raises(ValueError,match='^strict finite exploration 0..10$'):search(*a)
    for nodes in (True,None,(),[],[{}]*101):
        a=args();a[0]=nodes
        with pytest.raises(ValueError,match='^1..100 tree nodes before scan$'):search(*a)
    for draws in (True,None,(),[],[0]*79,[0]*81):
        a=args();a[4]=draws
        with pytest.raises(ValueError,match='^exact iterations times 8 rollout draws before scan$'):search(*a)
    for draw in (True,None,'1',-.01,1,10**400,float('nan'),float('inf')):
        for index in (0,79):
            a=args();a[4][index]=draw
            with pytest.raises(ValueError,match=r'^strict finite rollout draws \[0,1\)$'):search(*a)
    for bad in (None,[],{},dict(args()[0][0],extra=1)):
        a=args();a[0][0]=bad
        with pytest.raises(ValueError,match='^exact tree id/children/reward fields$'):search(*a)
    for ident in (None,True,'','x'*81,'r'):
        a=args();a[0][1]['id']=ident
        with pytest.raises(ValueError,match='^unique tree id 1..80 chars$'):search(*a)
    for children in (None,(),[True],['a']*2,['a']*9):
        a=args();a[0][0]['children']=children
        with pytest.raises(ValueError,match='^0..8 distinct child ids$'):search(*a)
    a=args();a[0][0]['reward']=1
    with pytest.raises(ValueError,match='^internal reward must be None$'):search(*a)
    for reward in (None,True,'1',-1000.01,1000.01,10**400,-10**400,float('nan'),float('inf')):
        a=args();a[0][2]['reward']=reward
        with pytest.raises(ValueError,match='^strict finite terminal reward within -1000..1000$'):search(*a)
    a=args();a[0][1]['children']=['b']
    with pytest.raises(ValueError,match='^one parent per nonroot node$'):search(*a)
    for root in (None,True,'unknown','a'):
        a=args();a[1]=root
        with pytest.raises(ValueError,match='^existing parentless root required$'):search(*a)
    a=args();a[0].append(dict(id='isolated',children=[],reward=0))
    with pytest.raises(ValueError,match='^existing acyclic connected tree required$'):search(*a)
    a=args();a[0][1]['children']=['missing']
    with pytest.raises(ValueError,match='^existing acyclic connected tree required$'):search(*a)
    chain=[dict(id=str(i),children=[str(i+1)] if i<9 else [],reward=None if i<9 else 0) for i in range(10)]
    with pytest.raises(ValueError,match='^tree depth at most 8 edges$'):search(chain,'0',1,0,[0]*8)


def test_hundred_node_cap_rewards_and_id_length_boundary():
    nodes=[dict(id='root',children=[str(i) for i in range(8)],reward=None)]
    for i in range(8):
        kids=[f'{i}-{j}' for j in range(8)];nodes.append(dict(id=str(i),children=kids,reward=None));nodes += [dict(id=k,children=[],reward=1000 if j%2 else -1000) for j,k in enumerate(kids)]
    # 73-node complete tree, extend leaf chains until exactly100nodes.
    for j in range(27):
        leaf=next(n for n in nodes if n['children']==[] and '-' in n['id'] and len(n['id'])<10)
        label='x'*80 if j==26 else f'long{j}'
        leaf['children']=[label];leaf['reward']=None;nodes.append(dict(id=label,children=[],reward=1000.0))
    assert len(nodes)==100 and len(search(nodes,'root',1,0,[0]*8)['visits'])==100


def test_distinct_child_overcap_not_masked_by_duplicate_schema():
    a=args();a[0][0]['children']=[str(j) for j in range(9)]
    with pytest.raises(ValueError,match='^0..8 distinct child ids$'):search(*a)


def test_different_draws_each_rollout_depth_and_round():
    nodes=[dict(id='root',children=['a','b'],reward=None),dict(id='a',children=['c','d'],reward=None),dict(id='b',children=['e','f'],reward=None),dict(id='c',children=['g','h'],reward=None),dict(id='d',children=[],reward=4),dict(id='e',children=[],reward=2),dict(id='f',children=[],reward=3),dict(id='g',children=[],reward=0),dict(id='h',children=[],reward=1)]
    draws=[0]*16;draws[1]=.75;draws[8]=.75
    r=search(nodes,'root',2,0,draws)
    assert r['trace'][0]['rollout_path']==['a','c','h'] and r['trace'][0]['reward_fraction']=='1'
    assert r['trace'][1]['rollout_path']==['b','f'] and r['trace'][1]['reward_fraction']=='3'


def test_uct_deeper_parent_child_menu_literal_witness():
    nodes=[dict(id='r',children=['a'],reward=None),dict(id='a',children=['b','c'],reward=None),dict(id='b',children=[],reward=1),dict(id='c',children=[],reward=2)]
    r=search(nodes,'r',5,1,[.5]*40)
    assert [t['selected_path'] for t in r['trace']]==[['r','a'],['r','a','b'],['r','a','c'],['r','a','c'],['r','a','c']]
    assert r['visits']==dict(r=5,a=5,b=1,c=3) and r['reward_sum_fraction']==dict(r='9',a='9',b='1',c='6') and r['selected_root_child']=='a'


def test_asymmetric_depth_three_uct_literal_trace_backprop():
    nodes=[dict(id='r',children=['a'],reward=None),dict(id='a',children=['b','c'],reward=None),dict(id='b',children=['d','e'],reward=None),dict(id='c',children=[],reward=2),dict(id='d',children=[],reward=-1),dict(id='e',children=[],reward=4)]
    r=search(nodes,'r',8,1,[.75]*64)
    assert [t['selected_path'] for t in r['trace']]==[['r','a'],['r','a','b'],['r','a','c'],['r','a','b','d']]+[['r','a','c']]*4
    assert [t['reward_fraction'] for t in r['trace']]==['2','4','2','-1','2','2','2','2']
    assert r['visits']==dict(r=8,a=8,b=2,c=5,d=1,e=0) and r['reward_sum_fraction']==dict(r='15',a='15',b='3',c='10',d='-1',e='0')
    assert r['selected_root_child']=='a'
