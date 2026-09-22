import math
from sugarcode.modules.evofold_4d import *
C=[[i*3.8,0,0] for i in range(8)]
def test_legacy_modes_transition_and_perturbation():
 zig=[[i*3.8,(i%2)*2,0] for i in range(8)]; assert anm_modes(zig)['modes'] and transition_trace(zig,steps=5)['frames'] and perturbation_effect(zig,2)
def test_langevin_reproducible_and_time_resolved():
 a=langevin_dynamics(C,steps=5,seed=2); b=langevin_dynamics(C,steps=5,seed=2); assert a['frames']==b['frames'] and len(a['frames'])==6
def test_temperature_changes_motion():
 assert langevin_dynamics(C,steps=10,temperature=.5)['rmsd'][-1]>langevin_dynamics(C,steps=10,temperature=.01)['rmsd'][-1]
def test_state_assignment_and_msm_normalized():
 s=state_assignments([C,[[x+1,y,z] for x,y,z in C],[[x+2,y,z] for x,y,z in C]],2); m=markov_state_model(s['states']); assert all(abs(sum(row)-1)<1e-12 for row in m['transition_matrix'])
def test_landscape_has_probabilities_and_energy():
 r=free_energy_landscape([0,0,.1,.2,2,2.1]); assert abs(sum(r['probability'])-1)<1e-12 and min(r['free_energy_kcal_mol'])==0
def test_evolutionary_constraints_identify_fixed_site():
 r=evolutionary_constraints(['ACD','ACE','ACF']); assert 0 in r['constrained_positions'] and 1 in r['constrained_positions']
def test_mutation_effect_uses_conservation():
 a=mutation_dynamics(C,2,1,['AAAAAAAA','AAAAAAAA']); b=mutation_dynamics(C,2,1,['AACAAAAA','AAGAAAAA']); assert a['barrier_shift_relative']>b['barrier_shift_relative']
def test_multimodel_pdb_contains_frames():
 p=multi_model_pdb([C,C]); assert p.count('MODEL')==2 and p.endswith('END\n')
def test_report_complete_honest():
 r=dynamics_report(C,steps=5); assert r['msm'] and r['landscape'] and r['multi_model_pdb'] and 'no neural SDE' in r['model_status']
def test_diagnostics_honest_finite():
 d=evofold_diagnostics(C,steps=10); assert len(d)==12 and all(math.isfinite(x) for x in d.values())
