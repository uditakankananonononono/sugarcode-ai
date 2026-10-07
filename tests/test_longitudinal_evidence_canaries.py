import numpy as np
import pytest
from sugarcode.modules.liquid_biopsy.core import longitudinal_trajectory as track

@pytest.mark.parametrize('rows', [[{'time':0,'burden':1},{'time':0,'burden':2}], [{'time':np.nan,'burden':1}], [{'time':0,'burden':-1}], [{'time':0,'burden':np.inf}], [{'time':True,'burden':1}]])
def test_time_and_signal_are_valid_before_regression(rows):
    with pytest.raises(ValueError): track(rows)

def test_zero_baseline_percent_change_is_undefined_not_billion_percent():
    result=track([{'time':0,'burden':0},{'time':1,'burden':.1}])
    assert result['percent_change'] is None

def test_signal_trend_is_not_treatment_response_or_progression():
    result=track([{'time':0,'burden':.2},{'time':2,'burden':.1}])
    assert result['trend']=='decreasing'
    assert result['status']=='Supplied signal trend only; not treatment response, progression or clonal selection'
    assert result['slope_interval_95'] is None

def test_fit_reports_residual_based_uncertainty_for_three_or_more_samples():
    result=track([{'time':0,'burden':1.1},{'time':1,'burden':1.8},{'time':2,'burden':3.2},{'time':3,'burden':3.9}])
    assert result['slope']==pytest.approx(.98)
    assert result['intercept']==pytest.approx(1.03)
    assert result['sample_count']==4
    assert result['slope_interval_95'][0]<.98<result['slope_interval_95'][1]
    assert result['residual_sum_squares']==pytest.approx(.098)
    assert result['uncertainty_assumptions']=='IID homoscedastic normal residuals; assay error and independence unverified'

def test_single_observation_has_no_trend():
    assert track([{'time':0,'burden':.3}])['trend']=='insufficient_data'
