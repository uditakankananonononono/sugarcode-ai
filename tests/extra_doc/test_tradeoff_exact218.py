import copy
import pytest
from sugarcode.extra_doc.tradeoff_exact218 import choose


def args():return [[dict(id='a',values=[0,10]),dict(id='b',values=[5,20]),dict(id='c',values=[10,10])],['min','max'],[3,1]]


def test_mixed_direction_range_normalized_hand_reference_pareto_and_no_mutation():
    inputs=args();before=copy.deepcopy(inputs);r=choose(*inputs)
    assert r['selected_id']=='a' and r['frontier_ids']==['a','b'] and r['dominated_ids']==['c']
    assert r['weights_fraction']==['3/4','1/4']
    assert r['scores']==[dict(id='a',max_weighted_regret_fraction='1/4',normalized_regrets_fraction=['0','1']),dict(id='b',max_weighted_regret_fraction='3/8',normalized_regrets_fraction=['1/2','0'])]
    assert inputs==before and not r['global_optimum_verified'] and not r['preferences_truth_verified'] and r['external_effects']==[]
    changed=args();changed[2]=[1,3];assert choose(*changed)['selected_id']=='b'


def test_minmax_menu_constant_axis_zero_weight_equal_options_and_ties():
    r=choose([dict(id='z',values=[2,0]),dict(id='a',values=[0,2])],['min','min'],[1,1])
    assert r['selected_id']=='a' and r['frontier_ids']==['a','z']
    r=choose([dict(id='z',values=[0,5]),dict(id='a',values=[0,5])],['max','min'],[0,2])
    assert r['selected_id']=='a' and all(x['normalized_regrets_fraction']==['0','0'] for x in r['scores'])
    assert r['weights_fraction']==['0','1']


@pytest.mark.parametrize('n',[0,1,99,100,101])
def test_option_count_caps(n):
    rows=[dict(id=str(i),values=[i]) for i in range(n)]
    if 1<=n<=100:assert choose(rows,['min'],[1])['selected_id']=='0'
    else:
        with pytest.raises(ValueError,match='^1..100 supplied options before scan$'):choose(rows,['min'],[1])
@pytest.mark.parametrize('n',[0,1,7,8,9])
def test_objective_count_caps(n):
    if 1<=n<=8:assert choose([dict(id='a',values=[0]*n)],['min']*n,[1]*n)['selected_id']=='a'
    else:
        with pytest.raises(ValueError,match='^1..8 objective directions before scan$'):choose([dict(id='a',values=[0]*n)],['min']*n,[1]*n)
@pytest.mark.parametrize('v',[-1000000,1000000,-1000000.0,1000000.0,.1])
def test_value_boundaries(v):assert choose([dict(id='a',values=[v])],['min'],[1])['selected_id']=='a'
@pytest.mark.parametrize('v',[.1,999,1000,1000.0])
def test_weight_edges(v):assert choose([dict(id='a',values=[0])],['min'],[v])['weights_fraction']==['1']
@pytest.mark.parametrize('n',[1,119,120,121])
def test_id_cap(n):
    if n<=120:assert choose([dict(id='x'*n,values=[0])],['min'],[1])['selected_id']=='x'*n
    else:
        with pytest.raises(ValueError,match='^bounded nonblank option id$'):choose([dict(id='x'*n,values=[0])],['min'],[1])


def test_all_types_schema_caps_decimal_just_outside_and_duplicate_refusals():
    for bad in (True,'1',None,-1000000.01,1000000.01,float('nan'),float('inf')):
        with pytest.raises(ValueError,match='^strict finite bounded objective/weight value$'):choose([dict(id='a',values=[bad])],['min'],[1])
    for bad in (True,'1',None,-.01,1000.01,float('nan'),float('inf')):
        with pytest.raises(ValueError,match='^strict finite bounded objective/weight value$'):choose([dict(id='a',values=[0])],['min'],[bad])
    for bad in ('bad','',True,None):
        with pytest.raises(ValueError,match='^objective direction min or max$'):choose([dict(id='a',values=[0])],[bad],[1])
    for bad in ('',' ','\t\n',True,None):
        with pytest.raises(ValueError,match='^bounded nonblank option id$'):choose([dict(id=bad,values=[0])],['min'],[1])
    for bad in ([],(),None,True):
        with pytest.raises(ValueError,match='^1..8 objective directions before scan$'):choose([],bad,[])
        with pytest.raises(ValueError,match='^1..100 supplied options before scan$'):choose(bad,['min'],[1])
        with pytest.raises(ValueError,match='^one objective weight per direction$'):choose([],['min'],bad)
        with pytest.raises(ValueError,match='^one option value per direction$'):choose([dict(id='a',values=bad)],['min'],[1])
    with pytest.raises(ValueError,match='^positive total objective weight$'):choose([],['min'],[0])
    with pytest.raises(ValueError,match='^distinct option ids$'):choose([dict(id='a',values=[0])]*2,['min'],[1])
    for bad in ({'id':'a','wrong':[0]},[],None):
        with pytest.raises(ValueError,match='^exact id/values fields$'):choose([bad],['min'],[1])


def test_weak_component_dominance_with_equal_other_axis():
    r=choose([dict(id='a',values=[1,1]),dict(id='b',values=[1,2])],['min','min'],[1,1])
    assert r['frontier_ids']==['a'] and r['dominated_ids']==['b'] and r['selected_id']=='a'


@pytest.mark.parametrize('position',range(3))
@pytest.mark.parametrize('bad',['bad','',True,None])
def test_mixed_valid_invalid_direction_refuses_every_position(position,bad):
    directions=['min','max','min'];directions[position]=bad
    with pytest.raises(ValueError,match='^objective direction min or max$'):
        choose([dict(id='a',values=[0,1,2])],directions,[1,1,1])


def test_500_independent_decimal_mixed_direction_frontier_and_normalization():
    from random import Random
    from decimal import Decimal as D
    from fractions import Fraction as F
    rng=Random(218)
    for _ in range(500):
        d=rng.randrange(1,5);n=rng.randrange(1,9);directions=[rng.choice(['min','max']) for _ in range(d)];raw=[[rng.randrange(-10,11) for j in range(d)] for i in range(n)];weights=[rng.randrange(1,5) for j in range(d)];rows=[dict(id=str(i),values=v) for i,v in enumerate(raw)];signed=[[D(v) if directions[j]=='min' else -D(v) for j,v in enumerate(row)] for row in raw];front=[]
        for i in range(n):
            dominated=False
            for k in range(n):
                differences=[signed[k][j]-signed[i][j] for j in range(d)]
                if max(differences)<=0 and min(differences)<0:dominated=True;break
            if not dominated:front.append(i)
        ideal=[min(v[j] for v in signed) for j in range(d)];spans=[max(v[j] for v in signed)-ideal[j] for j in range(d)];scores=[]
        for i in front:
            regrets=[(signed[i][j]-ideal[j])/spans[j] if spans[j] else D(0) for j in range(d)];score=max(D(weights[j])/sum(weights)*regrets[j] for j in range(d));scores.append((score,str(i),regrets))
        # Decimal approximation can round mathematical ties differently; compare exact score order with cross multiplication.
        exact=[]
        for i in front:
            regrets=[F(int(signed[i][j]-ideal[j]),int(spans[j])) if spans[j] else F(0) for j in range(d)];exact.append((max(F(weights[j],sum(weights))*regrets[j] for j in range(d)),str(i),regrets))
        exact.sort();r=choose(rows,directions,weights)
        assert r['selected_id']==exact[0][1] and r['frontier_ids']==sorted(str(i) for i in front)
        assert r['dominated_ids']==sorted(str(i) for i in range(n) if i not in front)
        assert [(F(s['max_weighted_regret_fraction']),s['id'],list(map(F,s['normalized_regrets_fraction']))) for s in r['scores']]==exact


def test_huge_integer_bounds_refused_every_numeric_input():
    for huge in (10**400,-10**400):
        with pytest.raises(ValueError,match='^strict finite bounded objective/weight value$'):choose([dict(id='a',values=[huge])],['min'],[1])
        with pytest.raises(ValueError,match='^strict finite bounded objective/weight value$'):choose([dict(id='a',values=[0])],['min'],[huge])
