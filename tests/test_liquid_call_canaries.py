import math
import pytest
from sugarcode.modules.liquid_biopsy.core import detect_ctdna

def test_variant_filter_is_exact_binomial_not_fake_beta_binomial_confidence():
    from scipy.stats import binom
    result=detect_ctdna([0,0,0,.02,0,0,0,0],depth=1000,error_rate=.001)
    hit=result['candidates'][0]
    assert hit['alt_count']==20
    assert hit['p_value']==pytest.approx(binom.sf(19,1000,.001))
    assert hit['q_value']==pytest.approx(min(1,8*hit['p_value']))
    assert hit['method']=='one-sided exact binomial error-null test with BH FDR'
    assert 'confidence' not in hit

def test_detection_is_not_disease_stage_or_sensitivity():
    result=detect_ctdna([0,0,0,.02,0,0,0,0],depth=1000)
    assert result['estimated_sensitivity'] is None
    assert result['stage_hint'] is None
    assert result['ctdna_detected'] is None
    assert result['variant_signal_detected'] is True

@pytest.mark.parametrize('signal,depth', [([0]*7+[math.nan],1000),([0]*7+[-.01],1000),([0]*7+[1.01],1000),([0]*8,0),([0]*8,True),([0]*8,1.5)])
def test_variant_filter_requires_valid_fractions_and_integer_depth(signal,depth):
    with pytest.raises(ValueError):
        detect_ctdna(signal,depth=depth)

def test_fraction_without_integer_read_count_is_not_silently_rounded():
    with pytest.raises(ValueError):
        detect_ctdna([0]*7+[.01234],depth=1000)
