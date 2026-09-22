import json, math
import pytest
from sugarcode.modules.prime_design import *
SPACER='ACGTACGTACGTACGTACGT'; EDIT='TTGCAAGGCCTTGCAAGGCC'; REGION=('ACGT'*30)+'AGG'+('TTGCA'*20)

def peg(): return design_pegrna(SPACER,EDIT)

def test_legacy_pegrna_ranges_and_extension():
 d=peg(); assert 10<=d['pbs_length']<=17 and 10<=d['rtt_length']<=20 and d['full_pegrna'].endswith(d['pegrna_3p_extension'])

def test_legacy_edit_substitution():
 r=design_edit(REGION,{'type':'substitution','position':60,'ref':'A','alt':'G'},background=REGION); assert r['edited_region'][60]=='G' and r['pe_system'] in ('PE2','PE3')

def test_pbs_thermodynamics_probability_and_gc():
 r=pbs_thermodynamics(peg()['pbs']); assert 0<=r['annealing_probability']<=1 and 0<=r['gc_fraction']<=1 and math.isfinite(r['delta_g_kcal_mol'])

def test_structure_penalizes_complementarity():
 a=secondary_structure('A'*20); b=secondary_structure('GCGCGCGCGCGCGCGCGCGC'); assert b['longest_stem']>=a['longest_stem'] and 0<=b['structure_penalty']<=1

def test_rt_processivity_decreases_with_length():
 a=rt_processivity('ACGT'*3); b=rt_processivity('ACGT'*5); assert a['completion_probability']>b['completion_probability']

def test_flap_resolution_bounded():
 r=flap_resolution(EDIT); assert 0<=r['resolution_probability']<=1

def test_repair_competition_normalized():
 r=repair_competition(EDIT); assert sum(r[k] for k in ('intended','reverted','partial_edit','indel'))==pytest.approx(1)

def test_nicking_strategy_distance_and_dsb_tradeoff():
 c=[{'position':70,'strand':'-'},{'position':5,'strand':'-'}]; r=nicking_strategy(0,c,'+'); assert r[0]['position']==70 and r[0]['dsb_like_risk']<r[1]['dsb_like_risk']

def test_spacer_background_scan_has_hits():
 r=spacer_binding_risk(SPACER,SPACER*2); assert r['hit_count']>=1

def test_spacer_binding_risk_orders_exact_above_mismatch():
 exact = spacer_binding_risk(SPACER, SPACER)
 mismatch = spacer_binding_risk(SPACER, SPACER[:-1] + ('A' if SPACER[-1] != 'A' else 'C'))
 assert exact['top_hits'][0]['binding_risk'] > mismatch['top_hits'][0]['binding_risk']
 assert exact['aggregate_binding_risk'] > mismatch['aggregate_binding_risk']
 intended = spacer_binding_risk(SPACER, SPACER + SPACER, intended_position=0)
 assert intended['hit_count'] >= 1 and intended['top_hits'][0]['binding_risk'] == 1.0


def test_rt_background_rewrite_layer():
 r=rt_template_offtarget_risk(EDIT,EDIT*2); assert r['hit_count']>=2 and r['aggregate_rewrite_risk']>0

def test_edit_window_optimal_zone():
 assert edit_window_score(8,15)['inside_optimal_window'] and not edit_window_score(20,15)['inside_optimal_window']

def test_outcomes_normalized():
 r=outcome_distribution(peg()); assert sum(r.values())==pytest.approx(1) and all(0<=v<=1 for v in r.values())

def test_architecture_grid_ranked():
 r=architecture_variants(SPACER,EDIT); assert len(r)>10 and r[0]['score']>=r[-1]['score'] and r[0]['thermodynamics'] and r[0]['repair']

def test_diagnostics_honest_default_and_background():
 d=pegrna_diagnostics(peg()); b=pegrna_diagnostics(peg(),EDIT*3); assert len(d)==27 and len(b)==31 and all(math.isfinite(v) for v in b.values()) and not any('background' in k for k in d)

def test_diagnostics_change_with_architecture():
 a=design_pegrna(SPACER,EDIT,10,10); b=design_pegrna(SPACER,EDIT,17,20); da=pegrna_diagnostics(a); db=pegrna_diagnostics(b); assert sum(da[k]!=db[k] for k in da)>=10

def test_export_stable_json():
 r={'spacer':SPACER}; assert json.loads(export_design(r))==r and export_design(r)==export_design(r)

def test_validation_depth_adapts_to_efficiency():
 assert validation_strategy(1,{'intended_edit':.01})['minimum_read_depth']>validation_strategy(1,{'intended_edit':.5})['minimum_read_depth']

def test_compiler_complete_and_honest():
 r=compile_prime_edit(SPACER,EDIT,nicking_candidates=[{'position':70,'strand':'-'}]); assert r['recommended'] and r['alternatives'] and r['nicking_strategies'] and r['diagnostics'] and r['validation'] and json.loads(r['export'])
 assert 'no trained sequence model and not clinically validated' in r['model_status']

def test_invalid_probability_rejected():
 with pytest.raises(ValueError): repair_competition(EDIT,mmr_activity=2)
