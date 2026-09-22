import json, math
import numpy as np
import pytest
from sugarcode.modules.living_computer import (
    parse_logic, build_circuit, compile_logic, boolean_truth_table,
    two_stage_simulate, stochastic_simulate, gate_delay, path_delay,
    output_probability, circuit_diagnostics, host_burden, ligand_sensor,
    ligand_response_curve, riboswitch, toehold_switch, implementation_plan,
    design_cellular_computer, sensitivity_analysis, monte_carlo_robustness,
    fanout_report, cascade_depth, design_rules_check, timing_analysis,
    mutation_tolerance, robustness_envelope, noise_analysis,
)


def circuit(expr='A AND B'):
    return build_circuit(parse_logic(expr)[0])


def test_parser_precedence_and_inputs():
    ast, names = parse_logic('a OR b AND NOT c')
    assert names == ['A','B','C'] and ast['op'] == 'or' and ast['children'][1]['op'] == 'and'

@pytest.mark.parametrize('bad', ['', 'A AND', '(A OR B', 'TRUE', 'A + B', None])
def test_parser_reports_invalid_expression(bad):
    with pytest.raises(ValueError): parse_logic(bad)

@pytest.mark.parametrize('expr', ['A','NOT A','A AND B','A OR B','A NAND B','A NOR B','A XOR B','A XNOR B','(A OR B) AND C'])
def test_compiler_truth_fidelity(expr):
    result=compile_logic(expr)
    assert result['logical_fidelity'] == 1.0 and len(result['truth_table']) == 2**len(parse_logic(expr)[1])


def test_compile_preserves_legacy_shape():
    r=compile_logic('A AND B')
    assert set(r)=={'expression','circuit','gates','truth_table','logical_fidelity','parts','signal_propagation'}
    assert r['parts']['reporter']=='GFP' and r['parts']['assembly'].startswith('Golden Gate')


def test_boolean_or_table_is_exact():
    rows=boolean_truth_table('A OR B')
    assert [x['output'] for x in rows] == [False,True,True,True]


def test_builds_regulatory_cascade():
    c=circuit('(A OR B) AND C')
    assert [g.name for g in c.gates] == ['~g1','~g2','GFP'] and c.gates[0].logic=='OR'


def test_two_stage_matches_engine_equilibrium():
    c=circuit('A OR B'); r=two_stage_simulate(c,external={'A':3,'B':3},n_points=50)
    from sugarcode.modules.synbio_studio.core import simulate
    expected=simulate(c,(0,150),external={'A':3,'B':3},n_points=50)['steady_state']
    assert r['steady_state']['GFP'] == pytest.approx(expected['GFP'],abs=.002)


def test_stochastic_is_seeded_and_nonnegative():
    c=circuit(); a=stochastic_simulate(c,t_end=2,dt=.1,external={'A':3,'B':3},seed=4); b=stochastic_simulate(c,t_end=2,dt=.1,external={'A':3,'B':3},seed=4)
    assert a==b and min(min(v) for v in a['series'].values()) >= 0


def test_gate_and_path_delays_are_physical():
    c=circuit('(A OR B) AND C'); p=path_delay(c)
    assert gate_delay(c.gates[0])>0 and p['depth']==3 and p['critical_path_minutes']>gate_delay(c.gates[0])


def test_output_probability_exact_and_latency_weighted():
    assert output_probability('A OR B',{'A':.25,'B':0})==.25
    assert output_probability('A OR B',{'A':.25,'B':0},True)==.4375


def test_diagnostics_have_50_finite_real_metrics():
    d=circuit_diagnostics(circuit('A OR B'))
    assert len(d)==77 and all(math.isfinite(v) for v in d.values())
    assert d['gate_count']==2 and d['edge_count']==3 and d['behavior.high_fraction']==pytest.approx(.75)


def test_diagnostics_distinguish_logic_functions():
    expressions = ['A AND B', 'A OR B', 'A NAND B', 'A NOR B', 'A XOR B']
    diagnostics = [circuit_diagnostics(circuit(expr)) for expr in expressions]
    assert all(len(item) == 77 for item in diagnostics)
    signatures = [item['behavior.weighted_truth_signature'] for item in diagnostics]
    assert len(set(signatures)) == len(expressions)
    for left, right in zip(diagnostics, diagnostics[1:]):
        changed = sum(left[key] != right[key] for key in left)
        assert changed >= 5


def test_diagnostics_deterministic():
    c=circuit('A OR B'); assert circuit_diagnostics(c)==circuit_diagnostics(c)


def test_host_burden_classification_and_validation():
    assert host_burden(circuit(),100)['class']=='low'
    with pytest.raises(ValueError): host_burden(circuit(),0)


def test_ligand_sensor_binding_and_decay():
    low=ligand_sensor('AHL',.1,kd=1); high=ligand_sensor('AHL',10,kd=1); degraded=ligand_sensor('AHL',10,kd=1,degradation_rate=.1,exposure_minutes=20)
    assert low['occupancy']<high['occupancy'] and degraded['occupancy']<high['occupancy']


def test_ligand_response_curve_monotone():
    y=ligand_response_curve('AHL',[0,.1,1,10],kd=1)['signal_reu']; assert y==sorted(y)


def test_rna_switches_are_monotone():
    assert riboswitch(10)>riboswitch(.1) and toehold_switch(10)>toehold_switch(.1)


def test_noise_analysis_seeded_summary():
    c=circuit('A'); a=noise_analysis(c,{'A':3},simulations=5,t_end=10); b=noise_analysis(c,{'A':3},simulations=5,t_end=10)
    assert a==b and a['simulations']==5 and 'GFP' in a['steady_state_noise']


def test_fanout_and_depth_reports():
    c=circuit('(A OR B) AND C'); assert fanout_report(c)['maximum']==1 and cascade_depth(c)['maximum']==3


def test_design_rules_are_actionable():
    r=design_rules_check(circuit('A OR B')); assert isinstance(r['passes'],bool) and set(r)>={'findings','fanout','depth','burden'}


def test_timing_quantiles_increase():
    t=timing_analysis(circuit()); assert t['t50_minutes']<t['t90_minutes']<t['t99_minutes']


def test_sensitivity_has_four_parameters_per_gate():
    c=circuit('A'); s=sensitivity_analysis(c,{'A':3},t_end=20)
    assert len(s['local_derivatives'])==4*len(c.gates) and all(math.isfinite(x) for x in s['local_derivatives'].values())


def test_monte_carlo_is_seeded_and_quantitative():
    c=circuit('A'); a=monte_carlo_robustness(c,{'A':3},simulations=5,seed=7); b=monte_carlo_robustness(c,{'A':3},simulations=5,seed=7)
    assert a==b and 0<=a['pass_fraction']<=1 and len(a['values'])==5


def test_mutation_screen_covers_each_gate():
    c=circuit('A OR B'); r=mutation_tolerance(c)
    assert set(r['per_gate'])=={g.name for g in c.gates} and 0<=r['minimum_retained_fraction']


def test_robustness_envelope_has_real_span():
    r=robustness_envelope(circuit('A'),{'A':3}); assert r['maximum']>r['minimum'] and r['span']>0


def test_implementation_plan_is_nonprocedural():
    text=json.dumps(implementation_plan(circuit())).lower()
    assert 'moclo' in text and 'sequence-verify' in text
    assert all(word not in text for word in ('incubate','pipette','thermocycler','antibiotic','transformation','autoclave'))


def test_design_package_is_honest_and_complete():
    r=design_cellular_computer('A NAND B')
    assert 'no trained model and not clinically validated' in r['model_status']
    assert r['compiled']['logical_fidelity']==1 and len(r['diagnostics'])>=50 and r['implementation']['design_units']


def test_output_name_validation():
    with pytest.raises(ValueError): build_circuit(parse_logic('A')[0],'')
