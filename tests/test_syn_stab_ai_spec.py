import math
from sugarcode.modules.syn_stab_ai import *
def test_legacy(): assert evaluate_circuit_stability({'n_gates':3})['forecast']
def test_sequence_repeats(): assert sequence_risk('ATATATATAT')['repeat_burden']>sequence_risk('ACGTGCTA')['repeat_burden']
def test_burden(): assert resource_burden(.9,.9,.9)['total']>resource_burden(.1,.1,.1)['total']
def test_population_seeded(): assert population_simulation(seed=3)==population_simulation(seed=3)
def test_selection_increases_failure(): assert population_simulation(selection_cost=.1,seed=2)['failure_probability']>population_simulation(selection_cost=0,seed=2)['failure_probability']
def test_stress(): assert chemical_stress(oxidative=.9)['damage_rate']>chemical_stress(oxidative=.1)['damage_rate']
def test_landscape(): assert fitness_landscape([{'id':'a','functional_loss':.1},{'id':'b','functional_loss':.9}])['favored'][0]['id']=='a'
def test_compare(): assert compare_stabilization({'expression_level':.9},[{'id':'low','expression_factor':.2},{'id':'same'}])[0]['id']=='low'
def test_report_honest(): assert 'no trained predictor' in stability_report({'n_gates':3},'ATGC'*20)['model_status']
def test_diagnostics():
 d=stability_diagnostics(stability_report({'n_gates':3},'ATGC'*20)); assert len(d)==12 and all(math.isfinite(x) for x in d.values())
