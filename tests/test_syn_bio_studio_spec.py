import math
from sugarcode.modules.syn_bio_studio import *
def test_compiler_architecture():
 r=compile_circuit('toggle'); assert r['nodes'] and r['edges'] and 'non-procedural' in r['status']
def test_hill_logic_direction(): assert hill(.9)>.5 and hill(.9,repression=True)<.5
def test_toggle_state_separates(): assert simulate_toggle()['bistable_proxy']>0
def test_oscillator_dynamic():
 r=simulate_oscillator(); assert r['amplitude']>0 and len(r['time_h'])==481
def test_gillespie_seeded(): assert gillespie_expression(seed=4)==gillespie_expression(seed=4)
def test_sequence_context_penalizes_structure(): assert sequence_context(10.5,.5,0)['expression_factor']>sequence_context(3,.8,.8)['expression_factor']
def test_burden_reduces_growth(): assert host_burden(90,20)['growth_fraction']<host_burden(5,5)['growth_fraction']
def test_evolution_decay():
 r=evolution_stability(20,.01,.01); assert r['intact_fraction'][-1]<r['intact_fraction'][0]
def test_assembly_plan(): assert assembly_plan(['a','b','c'])['junction_count']==2
def test_report_honest(): assert 'no learned circuit model' in circuit_report()['model_status']
def test_diagnostics_finite():
 d=studio_diagnostics(circuit_report()); assert len(d)==12 and all(math.isfinite(x) for x in d.values())
