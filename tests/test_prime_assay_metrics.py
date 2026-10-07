"""Synthetic metric arithmetic, not model validation."""
import pytest


def score():
    from sugarcode.modules.prime_design.assay_data import evaluate_outcome_predictions
    return evaluate_outcome_predictions


def labels():
    return {'records':[dict(seq_id='a',outcomes={'HEK':(.5,.5,0)}),
                       dict(seq_id='b',outcomes={'HEK':None}),
                       dict(seq_id='c',outcomes={'HEK':(1,0,0)})]}


def test_hand_calculated_metrics_and_missing_exclusion():
    r=score()(labels(),{'a':(.25,.5,.25),'c':(.5,.5,0)},'HEK',[0,1,2])
    assert r['n_scored']==2 and r['n_missing']==1
    assert r['intended_mae']==pytest.approx(.375)
    assert r['intended_rmse']==pytest.approx((.15625)**.5)
    assert r['mean_total_variation']==pytest.approx(.375)
    assert r['mean_squared_distribution_error']==pytest.approx(.3125)
    assert 'not clinical' in r['status']
    assert 'likelihood' not in r


@pytest.mark.parametrize('pred', [
    {'a':(.2,.2,.2),'c':(.5,.5,0)},
    {'a':(-.1,.6,.5),'c':(.5,.5,0)},
    {'a':(float('nan'),.5,.5),'c':(.5,.5,0)},
    {'a':(True,0,0),'c':(.5,.5,0)},
    {'a':(.5,.5,0)},
    {'a':(.5,.5,0),'c':(.5,.5,0),'wrong':(1,0,0)},
])
def test_bad_prediction_contract(pred):
    with pytest.raises(ValueError):score()(labels(),pred,'HEK',[0,1,2])


@pytest.mark.parametrize('indices',[[0,0],[True],[3],[-1]])
def test_indices_must_be_distinct_and_valid(indices):
    with pytest.raises(ValueError):score()(labels(),{},'HEK',indices)


def test_missing_prediction_must_not_be_scored():
    with pytest.raises(ValueError):score()(labels(),{'b':(1,0,0)},'HEK',[1])


def test_no_observed_labels_returns_explicit_no_metrics():
    r=score()(labels(),{},'HEK',[1])
    assert r['n_scored']==0 and r['intended_mae'] is None
