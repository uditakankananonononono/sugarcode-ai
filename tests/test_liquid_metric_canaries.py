import numpy as np
import pytest
from sugarcode.modules.liquid_biopsy.core import enhancement_features

def test_constant_prefix_nonconstant_signal_autocorrelation_not_nan():
    result=enhancement_features([0,0,0,1])
    assert np.isfinite(result['signal_autocorrelation_lag1'])
    assert result['signal_autocorrelation_lag1']==0

@pytest.mark.parametrize('kwargs',[{'signal':[0,np.nan]}, {'signal':[0,1],'fragment_lengths':[-1]}, {'signal':[0,1],'methylation':[2]}, {'signal':[0,1],'proteins':[np.inf]}])
def test_metric_arrays_reject_invalid_measurements(kwargs):
    with pytest.raises(ValueError): enhancement_features(**kwargs)

def test_high_evidence_score_not_called_confident_variant():
    result=enhancement_features([.1,.2],calls=[{'allele_fraction':.2,'evidence_score':.95}])
    assert 'high_confidence_variant_count' not in result
    assert result['high_evidence_score_count']==1
