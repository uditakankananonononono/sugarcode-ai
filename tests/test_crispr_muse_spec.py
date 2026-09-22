import json, math
import pytest
from sugarcode.modules.crispr_muse import *
GUIDE='GAGTCCGAGCAGAAGAAGAA'

def test_pam_cross_nuclease_compatibility():
 assert pam_matches('AGG','NGG') and pam_matches('TTTA','TTTV') and pam_compatibility('AGG','SpCas9')['SpCas9']

def test_enumerate_configurations_respects_pam():
 target='A'*20+'AGG'+'C'*25
 configs=enumerate_configurations(target,['SpCas9'])
 assert configs and configs[0]['guide']=='A'*20 and configs[0]['pam']=='AGG'

def test_folding_penalizes_poly_t():
 assert rna_folding_score('A'*20)>rna_folding_score('AAAATTTTAAAATTTTAAAA')

def test_chromatin_prior_decays_with_distance():
 assert chromatin_prior(.8,0)>chromatin_prior(.8,1000)

def test_repair_distribution_normalized_and_contextual():
 a=repair_outcomes(GUIDE*2); b=repair_outcomes('AAAA'*10)
 assert sum(a[k] for k in ('NHEJ','MMEJ','HDR'))==pytest.approx(1) and b['MMEJ']>a['MMEJ']

def test_base_editing_window_reports_positions():
 assert base_editing_window('AAAACCCCAAAACCCCAAAA','CBE')['editable_positions']==[5,6,7,8]

def test_prime_design_models_processivity():
 a=prime_editing_design(GUIDE,'G'*25,13,10); b=prime_editing_design(GUIDE,'G'*45,13,30)
 assert a['rt_processivity']>b['rt_processivity'] and 0<a['predicted_precise_fraction']<1

def test_reward_has_causal_decomposition():
 r=reward_decomposition(GUIDE,chromatin=.8)
 assert set(r['components'])=={'on_target','specificity','chromatin','repair','folding','functional'} and sum(r['contributions'].values())==pytest.approx(r['total'])

def test_digital_lab_seeded_and_noisy():
 assert simulate_digital_lab(GUIDE,replicates=30,seed=2)==simulate_digital_lab(GUIDE,replicates=30,seed=2)

def test_delivery_distribution_seeded():
 assert delivery_efficiency(seed=4)==delivery_efficiency(seed=4)

def test_sequence_error_conserves_reads():
 a={'HDR':20,'NHEJ':80}; assert sum(sequence_error_model(a).values())==pytest.approx(100)

def test_clonal_expansion_favors_fitter_clone():
 r=clonal_expansion({'edit':.5,'wt':.5},5,{'edit':1.2,'wt':1}); assert r['edit']>.5 and sum(r.values())==pytest.approx(1)

def test_bayesian_feedback_updates_posterior():
 r=ingest_sequencing_feedback([{'guide':GUIDE,'edited_reads':80,'total_reads':100}]); assert r['posterior'][GUIDE]['mean']>.75

def test_agent_ingests_persistent_feedback():
 a=MuseAgent(); a.ingest_feedback([{'guide':GUIDE,'edited_reads':8,'total_reads':10}]); old=a.posterior[GUIDE]['mean']; a.ingest_feedback([{'guide':GUIDE,'edited_reads':1,'total_reads':10}]); assert a.posterior[GUIDE]['mean']<old

def test_multiplex_interference_detected():
 a=GUIDE; b=GUIDE[:-1]+'C'; assert not multiplex_compatibility([a,b],3)['compatible']

def test_ranked_strategy_traceability():
 configs=[{'nuclease':'SpCas9','guide':GUIDE,'pam':'AGG','start':0,'end':20,'cut_site':17}]; r=rank_strategies(configs); assert r[0]['reward_decomposition'] and r[0]['repair_outcomes']

def test_policy_entropy_declines_when_concentrated():
 a=MuseAgent(); before=policy_entropy(a.logits); a.logits[:,0]=5; assert policy_entropy(a.logits)<before

def test_policy_update_is_seeded_and_changes_state():
 a=MuseAgent(seed=4); b=MuseAgent(seed=4); assert train_round(a,n_samples=8)==train_round(b,n_samples=8) and a.rounds==1 and a.history

def test_legacy_train_round_shape():
 r=train_round(MuseAgent(seed=1),n_samples=4); assert len(r['current_best_guide'])==20 and 'pam_compatibility' in r

def test_diagnostics_have_honest_finite_values():
 d=guide_diagnostics(GUIDE); assert len(d)==32 and all(math.isfinite(x) for x in d.values()) and d['total_reward']>0
 assert not any(key.startswith('position_') for key in d)

def test_diagnostics_change_with_sequence():
 a=guide_diagnostics(GUIDE); b=guide_diagnostics('ACGTACGTACGTACGTACGT'); assert sum(a[k]!=b[k] for k in a)>=8

def test_design_strategy_model_honesty():
 target='A'*20+'AGG'+'C'*25; r=design_muse_strategy(target,nucleases=['SpCas9']); assert r['strategies'] and 'No trained CNN/transformer' in r['traceability']['model_status']

def test_export_is_stable_json():
 r={'guide':GUIDE,'score':.5}; assert json.loads(export_simulation(r))==r and export_simulation(r)==export_simulation(r)

def test_continual_learning_report_honest():
 a=MuseAgent(); train_round(a,n_samples=4); assert 'not clinically validated' in continual_learning_report(a)['model_status']

@pytest.mark.parametrize('bad',['',GUIDE[:-1],GUIDE[:-1]+'N'])
def test_guide_validation(bad):
 with pytest.raises(ValueError): guide_diagnostics(bad)

def test_invalid_probability_rejected():
 with pytest.raises(ValueError): chromatin_prior(1.2)

def test_edit_precision_and_functional_impact():
 r={'NHEJ':.6,'MMEJ':.2,'HDR':.2}; assert edit_precision(r,'HDR')==pytest.approx(.2) and functional_impact(.8,True,1)>.5
