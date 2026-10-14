import copy
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.bayes_search216 import suggest


def args():return [['a','b','c'],[dict(id='h1',prior=.25,values=[0,-2,3]),dict(id='h2',prior=.75,values=[2,1,-1])],[dict(candidate='a',value=0)],1,'min']


def test_hand_bayesian_update_expected_improvement_mean_variance_no_mutation():
    a=args();before=copy.deepcopy(a);r=suggest(*a)
    # weights 1/4 and3/20 normalize to5/8,3/8.
    assert r['posterior_fraction']=={'h1':'5/8','h2':'3/8'} and r['posterior_history_fraction']==[['5/8','3/8']]
    assert r['scores']==[dict(candidate='b',expected_improvement_fraction='5/4',posterior_mean_fraction='-7/8',posterior_variance_fraction='135/64'),dict(candidate='c',expected_improvement_fraction='3/8',posterior_mean_fraction='3/2',posterior_variance_fraction='15/4')]
    assert r['selected_candidate']=='b' and r['incumbent_observed_fraction']=='0' and r['direction']=='min'
    assert a==before and not r['objective_executed'] and not r['global_optimum_claimed'] and r['external_effects']==[]


def test_400_independent_exact_joint_likelihood_posterior_acquisition_oracles():
    from random import Random
    rng=Random(216)
    for _ in range(400):
        vals=[[rng.randrange(-5,6) for j in range(4)] for i in range(3)];priors=[F(1,4),F(1,4),F(1,2)];observed=[rng.randrange(-5,6),rng.randrange(-5,6)];direction=rng.choice(['min','max']);scale=rng.randrange(1,4)
        joint=[p/((scale**2+(observed[0]-row[0])**2)*(scale**2+(observed[1]-row[1])**2)) for p,row in zip(priors,vals)];posterior=[v/sum(joint) for v in joint]
        r=suggest(list('abcd'),[dict(id=str(i),prior=float(p),values=row) for i,(p,row) in enumerate(zip(priors,vals))],[dict(candidate='a',value=observed[0]),dict(candidate='b',value=observed[1])],scale,direction)
        assert list(map(F,r['posterior_fraction'].values()))==posterior
        baseline=min(observed) if direction=='min' else max(observed);scores=[]
        for j,got in zip((2,3),r['scores']):
            mean=sum(p*row[j] for p,row in zip(posterior,vals));variance=sum(p*(row[j]-mean)**2 for p,row in zip(posterior,vals));ei=sum(p*max(baseline-row[j] if direction=='min' else row[j]-baseline,0) for p,row in zip(posterior,vals));scores.append(ei)
            assert F(got['posterior_mean_fraction'])==mean and F(got['posterior_variance_fraction'])==variance and F(got['expected_improvement_fraction'])==ei
        assert r['selected_candidate']==('d' if scores[1]>scores[0] else 'c')


def test_max_min_ties_repeated_observations_zero_prior_and_caps():
    a=args();a[4]='max';assert suggest(*a)['selected_candidate']=='c'
    a=args();a[1][1]['prior']=0;a[1][0]['prior']=1;a[2]*=20;r=suggest(*a)
    assert r['posterior_fraction']=={'h1':'1','h2':'0'} and len(r['posterior_history_fraction'])==20
    for n in (2,19,20):
        menu=[str(i) for i in range(n)];hyp=[dict(id=str(i),prior=1 if i==0 else 0,values=[0]*n) for i in range(20)]
        r=suggest(menu,hyp,[dict(candidate='0',value=0)],.000001,'min');assert len(r['scores'])==n-1 and r['selected_candidate']=='1'
    for v in (-1000,1000,-1000.0,1000.0):suggest(['x'*80,'b'],[dict(id='y'*80,prior=1,values=[v,v])],[dict(candidate='b',value=v)],1000,'min')
    assert r['likelihood']=='Cauchy observation noise with supplied scale, independent observations' and r['selection']=='maximum expected latent improvement; supplied candidate order ties'


def test_all_staged_schema_numeric_types_caps_refusals():
    for direction in (True,None,'bad'):
        a=args();a[4]=direction
        with pytest.raises(ValueError,match='^direction min or max$'):suggest(*a)
    for candidates in (True,None,(),[],['a'],['a']*21):
        a=args();a[0]=candidates
        with pytest.raises(ValueError,match='^2..20 candidate ids before scan$'):suggest(*a)
    for candidates in (['a','a'],['','b'],['x'*81,'b'],[True,'b']):
        a=args();a[0]=candidates
        with pytest.raises(ValueError,match='^unique candidate ids 1..80$'):suggest(*a)
    for hypotheses in (True,None,(),[],[{}]*21):
        a=args();a[1]=hypotheses
        with pytest.raises(ValueError,match='^1..20 function hypotheses before scan$'):suggest(*a)
    for h in ({},None,[],dict(args()[1][0],extra=1)):
        a=args();a[1][0]=h
        with pytest.raises(ValueError,match='^exact hypothesis id/prior/values fields$'):suggest(*a)
    for ident in (True,None,'','x'*81,'h2'):
        a=args();a[1][0]['id']=ident
        with pytest.raises(ValueError,match='^unique hypothesis ids 1..80$'):suggest(*a)
    for values in (None,(),[],[0],[0]*4):
        a=args();a[1][0]['values']=values
        with pytest.raises(ValueError,match='^one hypothesis value per candidate$'):suggest(*a)
    for bad in (True,None,'1',-1000.01,1000.01,10**400,-10**400,float('nan'),float('inf')):
        for slot in ('scale','prior','value','observation'):
            a=args()
            if slot=='scale':a[3]=bad
            elif slot=='prior':a[1][0]['prior']=bad
            elif slot=='value':a[1][0]['values'][1]=bad
            else:a[2][0]['value']=bad
            with pytest.raises(ValueError,match='^strict finite bounded Bayesian number$'):suggest(*a)
    for scale in (0,.00000099):
        a=args();a[3]=scale
        with pytest.raises(ValueError,match='^strict finite bounded Bayesian number$'):suggest(*a)
    for prior in (-.01,1.01):
        a=args();a[1][0]['prior']=prior
        with pytest.raises(ValueError,match='^strict finite bounded Bayesian number$'):suggest(*a)
    for prior in (.24999999,.25000001):
        a=args();a[1][0]['prior']=prior
        with pytest.raises(ValueError,match='^hypothesis priors sum exactly one$'):suggest(*a)
    for observations in (True,None,(),[],[{}]*21):
        a=args();a[2]=observations
        with pytest.raises(ValueError,match='^1..20 observations before scan$'):suggest(*a)
    for obs in ({},None,[],dict(args()[2][0],extra=1)):
        a=args();a[2][0]=obs
        with pytest.raises(ValueError,match='^exact observation candidate/value fields$'):suggest(*a)
    for ident in (True,None,'unknown'):
        a=args();a[2][0]['candidate']=ident
        with pytest.raises(ValueError,match='^observation candidate in menu$'):suggest(*a)
    a=args();a[2]=[dict(candidate=c,value=0) for c in a[0]]
    with pytest.raises(ValueError,match='^at least one unobserved candidate required$'):suggest(*a)
