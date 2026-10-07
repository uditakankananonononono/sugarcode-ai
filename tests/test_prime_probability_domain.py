"""Numerical/domain canaries only: surrogate probabilities are not assay fits."""
import math
import pytest
from sugarcode.modules.prime_design import (
    rt_processivity, flap_resolution, repair_competition, outcome_distribution,
    design_pegrna,
)
PEG = design_pegrna('ACGT'*5, 'ACGT'*5)
REPAIR = dict(intended=.4, reverted=.2, partial_edit=.1, indel=.3)


@pytest.mark.parametrize('function', [rt_processivity, flap_resolution, repair_competition])
@pytest.mark.parametrize('sequence', ['', 'ACGT!ACGT', 'ACGTNACGT'])
def test_templates_not_silently_cleaned(function, sequence):
    with pytest.raises(ValueError):
        function(sequence)


@pytest.mark.parametrize('function,kwargs', [
    (rt_processivity, {'base_processivity':True}),
    (flap_resolution, {'homology_length':True}),
    (flap_resolution, {'homology_length':1.5}),
    (flap_resolution, {'homology_length':float('nan')}),
    (flap_resolution, {'fen1_activity':True}),
    (repair_competition, {'nick_bias':True}),
])
def test_nonfinite_boolean_or_noninteger_conditions(function, kwargs):
    with pytest.raises(ValueError):
        function('ACGT'*3, **kwargs)


@pytest.mark.parametrize('repair', [{}, dict(REPAIR, intended=-.1),
    dict(REPAIR, intended=float('nan')), dict(REPAIR, intended=True),
    dict(REPAIR, intended=.9)])
def test_external_repair_must_be_probability_distribution(repair):
    with pytest.raises(ValueError):
        outcome_distribution(PEG, repair=repair)


@pytest.mark.parametrize('nick', [{'score':-100}, {'score':float('nan')},
    {'dsb_like_risk':-1}, {'dsb_like_risk':float('inf')}, {'score':True}])
def test_invalid_nick_never_yields_negative_or_nonfinite_outcomes(nick):
    with pytest.raises(ValueError):
        outcome_distribution(PEG, REPAIR, nick)


def test_invalid_tm_rejected():
    with pytest.raises(ValueError):
        outcome_distribution(dict(PEG, pbs_tm_c=float('nan')), REPAIR)


def test_zero_activities_explicit_surrogate_not_biological_assertion():
    r = repair_competition('ACGT'*3, mmr_activity=0, ber_activity=0, fen1_activity=0)
    assert r['intended'] == r['reverted'] == r['partial_edit'] == 0
    assert r['indel'] == 1  # Existing arbitrary residual channel, NOT observed biology.
    assert 'unfitted' in r['model_status']


def test_valid_outcomes_and_linear_homopolymer_scan():
    r = outcome_distribution(PEG, REPAIR, {'score':.5, 'dsb_like_risk':.2})
    assert sum(r.values()) == pytest.approx(1)
    assert all(math.isfinite(x) and 0 <= x <= 1 for x in r.values())
    assert rt_processivity('ACCCCGGTT')['homopolymer_max'] == 4


def test_valid_negative_nick_score_clamped_before_normalization():
    r = outcome_distribution(dict(PEG, pbs_tm_c=-1000),
                             dict(intended=0, partial_edit=0, indel=0, reverted=1),
                             {'score':-1})
    assert all(math.isfinite(x) and 0 <= x <= 1 for x in r.values())
    assert sum(r.values()) == pytest.approx(1)


def test_long_template_run_scan_completes_without_quadratic_substrings():
    r = rt_processivity('A'*10000)
    assert r['homopolymer_max'] == 10000
    assert 0 <= r['completion_probability'] < 1e-300
