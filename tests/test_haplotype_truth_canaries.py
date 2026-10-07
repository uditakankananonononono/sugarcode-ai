import numpy as np
import pytest
from sugarcode.modules.liquid_biopsy.core import bayesian_haplotype_inference as infer

@pytest.mark.parametrize('data', [[[.3,1]], [[2,1]], [[-2,1]], [[np.inf,1]], [[0,1],[-np.inf,1]], [[]]])
def test_only_binary_or_explicit_missing_alleles_are_accepted(data):
    with pytest.raises(ValueError): infer(data)

@pytest.mark.parametrize('kwargs',[{'alpha':-1},{'alpha':np.nan},{'max_iter':0},{'max_iter':True},{'tol':-1},{'tol':np.nan}])
def test_inference_configuration_is_validated(kwargs):
    with pytest.raises(ValueError): infer([[0,1],[1,0]],**kwargs)

def test_long_fragments_use_log_likelihood_not_underflow_to_zero():
    # Every candidate differs at about 500 sites. Direct eps**mismatch underflows.
    rng=np.random.default_rng(9)
    data=rng.integers(0,2,(6,1500))
    result=infer(data,max_iter=30)
    assert sum(x['posterior_mean'] for x in result['haplotypes'])==pytest.approx(1,abs=1e-6)
    assert result['numerical_method']=='log-space responsibilities'

def test_fitted_em_weights_are_not_bayesian_credible_intervals():
    result=infer([[0,0],[0,1],[1,1]])
    assert all('credible_interval_95' not in x for x in result['haplotypes'])
    assert 'not posterior credible intervals' in result['uncertainty_status']
    assert 'converged' in result and 'log_likelihood' in result
