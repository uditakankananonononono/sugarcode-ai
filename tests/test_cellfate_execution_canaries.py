import numpy as np
import pytest
from sugarcode.modules.cellfatenet.core import simulate_fate, optimal_reprogramming, grn_matrix

@pytest.mark.parametrize('kwargs',[{'hours':0},{'hours':-1},{'hours':np.nan},{'trajectories':0},{'trajectories':True},{'noise':-1},{'noise':np.nan}])
def test_simulation_rejects_invalid_domain_before_solving(kwargs):
    with pytest.raises(ValueError):
        simulate_fate({'OCT4':1},**kwargs)

@pytest.mark.parametrize('kwargs',[{'initial':{'TYPO':1}}, {'initial':{'OCT4':-1}}, {'initial':{'OCT4':np.nan}}, {'initial':{'OCT4':1},'controls':{'TYPO':1}}, {'initial':{'OCT4':1},'accessibility':{'OCT4':2}}, {'initial':{'OCT4':1},'methylation':{'OCT4':-1}}])
def test_simulation_rejects_unknown_nonphysical_or_nonfinite_state(kwargs):
    with pytest.raises(ValueError):
        simulate_fate(hours=1,**kwargs)

def test_repression_does_not_generate_negative_concentrations():
    result=simulate_fate({'OCT4':.05},hours=2,controls={'OCT4':-1})
    assert np.min(result['mean']) >= 0

def test_control_objective_describes_returned_sparse_controls():
    target={'TNNT2':2.,'MYH6':2.}
    result=optimal_reprogramming({},target,hours=2,max_factors=1)
    selected={x['factor']:x['control'] for x in result['interventions']}
    sim=simulate_fate({},hours=2,controls=selected)
    objective=sum((sim['final_state'][n]-v)**2 for n,v in target.items())+.08*sum(u*u for u in selected.values())+.04*sum(abs(u) for u in selected.values())
    assert result['objective']==pytest.approx(objective,rel=1e-5)
    assert result['execution_schedule']=='simultaneous constant controls'
    assert all(x['start_hour']==0 for x in result['recipe'])

def test_unknown_target_not_silently_optimized_as_empty_goal():
    with pytest.raises(ValueError):
        optimal_reprogramming({}, {'TYPO':1}, hours=2)

def test_stochastic_validation_is_simulation_frequency_not_biological_success():
    from sugarcode.modules.cellfatenet.core import stochastic_validate
    r=stochastic_validate({}, {'TNNT2':1}, [], replicates=2, noise=0)
    assert r['status']=='Simulated target-similarity threshold frequency, not biological success probability'
    assert r['horizon_hours']==72

def test_model_does_not_silently_validate_an_empty_or_unknown_target():
    from sugarcode.modules.cellfatenet.core import stochastic_validate
    with pytest.raises(ValueError):
        stochastic_validate({}, {'UNKNOWN':1}, [], replicates=2)
