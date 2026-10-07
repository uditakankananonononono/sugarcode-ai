import pytest
import numpy as np
from sugarcode.modules.liquid_biopsy import core as lb

def test_uncertainty_resamples_actual_fragments_and_reports_reproducibly():
    assert hasattr(lb,'bootstrap_haplotype_weights')
    fragments=[[0,0]]*16+[[1,1]]*4
    a=lb.bootstrap_haplotype_weights(fragments,replicates=40,seed=3)
    b=lb.bootstrap_haplotype_weights(fragments,replicates=40,seed=3)
    assert a==b
    assert a['replicates_requested']==40 and a['replicates_completed']==40
    assert a['sampling_unit']=='supplied fragment row'
    assert a['interval_method']=='empirical percentile fragment bootstrap; not Bayesian posterior'
    zero=next(x for x in a['haplotypes'] if x['haplotype']=='00')
    assert zero['interval_95'][0]<zero['fitted_weight']<zero['interval_95'][1]
    assert all(np.isfinite(x['bootstrap_std']) for x in a['haplotypes'])

def test_uncertainty_refits_not_fixed_score_perturbation():
    assert hasattr(lb,'bootstrap_haplotype_weights')
    homogeneous=lb.bootstrap_haplotype_weights([[0,0]]*20,replicates=30,seed=4)
    mixed=lb.bootstrap_haplotype_weights([[0,0]]*10+[[1,1]]*10,replicates=30,seed=4)
    assert max(x['bootstrap_std'] for x in homogeneous['haplotypes']) < 1e-10
    assert max(x['bootstrap_std'] for x in mixed['haplotypes']) > .04

@pytest.mark.parametrize('kwargs',[{'replicates':0},{'replicates':True},{'replicates':1.5}])
def test_uncertainty_config_validation(kwargs):
    assert hasattr(lb,'bootstrap_haplotype_weights')
    with pytest.raises(ValueError): lb.bootstrap_haplotype_weights([[0],[1]],**kwargs)

def test_long_locus_candidate_heuristic_not_given_false_bootstrap_coverage():
    assert hasattr(lb,'bootstrap_haplotype_weights')
    with pytest.raises(ValueError,match='12'):
        lb.bootstrap_haplotype_weights([[0]*13,[1]*13],replicates=20)
