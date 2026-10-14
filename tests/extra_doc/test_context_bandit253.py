import copy
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.context_bandit253 import choose


def test_side_information_reverses_arm_choice_and_other_context_does_not_leak():
    arms=['a','b'];history=[dict(context='day',arm='a',reward=1),dict(context='day',arm='b',reward=0),dict(context='night',arm='a',reward=0),dict(context='night',arm='b',reward=1)];before=copy.deepcopy(history)
    day=choose(arms,history,'day');night=choose(arms,history,'night')
    assert day['selected_arm']=='a' and night['selected_arm']=='b'
    assert [s['posterior_mean_fraction'] for s in day['scores']]==['2/3','1/3'] and [s['posterior_mean_fraction'] for s in night['scores']]==['1/3','2/3']
    assert day['matched_observations']==2 and day['total_observations']==4 and day['scores'][0]['all_context_count']==2 and history==before and day['external_effects']==[]
    r=choose(arms,history,'new');assert r['selected_arm']=='a' and r['matched_observations']==0 and r['unseen_context_prior']=='independent Beta(1,1) per arm' and r['tie_break']=='input arm order'


def test_500_independent_context_subset_and_beta_pseudocount_oracles():
    from random import Random
    rng=Random(253)
    for _ in range(500):
        arms=[str(i) for i in range(rng.randrange(1,21))];history=[dict(context=str(rng.randrange(4)),arm=rng.choice(arms),reward=rng.randrange(2)) for i in range(rng.randrange(100))];ctx=str(rng.randrange(5));filtered=[r for r in history if r['context']==ctx];means=[]
        r=choose(arms,history,ctx)
        for a,s in zip(arms,r['scores']):
            subset=[row['reward'] for row in filtered if row['arm']==a];mean=F(sum(subset)+1,len(subset)+2);means.append(mean)
            assert s['context_successes']==sum(subset) and s['context_failures']==len(subset)-sum(subset) and F(s['posterior_mean_fraction'])==mean and s['all_context_count']==sum(row['arm']==a for row in history)
        assert r['selected_arm']==arms[max(range(len(arms)),key=lambda i:(means[i],-i))] and r['matched_observations']==len(filtered)


def test_caps_and_identifier_endpoints():
    for n in (1,19,20):
        arms=[str(i) for i in range(n)];r=choose(arms,[dict(context='x',arm=arms[0],reward=1)]*1000,'x');assert r['total_observations']==1000 and r['matched_observations']==1000
    assert choose(['x'*80],[],'y'*80)['selected_arm']=='x'*80


def test_precise_shapes_types_bool_hugeint_and_caps_refusals():
    for arms in (None,(),[],True,['a']*21):
        with pytest.raises(ValueError,match='^1..20 context arms before scan$'):choose(arms,[],'x')
    for bad in (True,None,1,'',' ','x'*81):
        for a in (([bad],[],'x'),(['a'],[],bad),(['a'],[dict(context=bad,arm='a',reward=0)],'x'),(['a'],[dict(context='x',arm=bad,reward=0)],'x')):
            with pytest.raises(ValueError,match='^nonblank context identifiers 1..80$'):choose(*a)
    with pytest.raises(ValueError,match='^unique context arms$'):choose(['a','a'],[],'x')
    for history in (None,(),True,[{}]*1001):
        with pytest.raises(ValueError,match='^0..1000 context observations before scan$'):choose(['a'],history,'x')
    for row in (None,[],{},dict(context='x',arm='a',reward=0,extra=1)):
        with pytest.raises(ValueError,match='^exact context arm reward fields$'):choose(['a'],[row],'x')
    with pytest.raises(ValueError,match='^known context arm$'):choose(['a'],[dict(context='x',arm='b',reward=0)],'x')
    for reward in (True,None,'1',1.,-1,2,10**400):
        with pytest.raises(ValueError,match='^strict Bernoulli context reward 0 or 1$'):choose(['a'],[dict(context='x',arm='a',reward=reward)],'x')
