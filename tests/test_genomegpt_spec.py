import math
import numpy as np
import pytest
from sugarcode.modules.genomegpt import *
CTCF='CCGCGAGGCGGCAG'
SEQ='AT'*100+CTCF+'GC'*1500+CTCF[::-1].translate(str.maketrans('ACGT','TGCA'))+'AT'*100

def test_legacy_analysis_shape_and_motifs():
 r=analyze_sequence(CTCF*3+'ATGC'*50); assert r['gc_content']>0 and 'kmer_anomalies' in r and 'long_range' in r

def test_legacy_convergent_loops():
 r=predict_loops(SEQ,min_span=1000); assert r and r[0]['orientation']=='convergent' and r[0]['span']>=1000

def test_legacy_variant_motif_reading():
 r=interpret_sequence_variant('GENE',CTCF,5,'T'); assert r['ref_base']==CTCF[5] and (r['motifs_broken'] or r['regulatory_impact'])

def test_embedding_normalized_and_sequence_sensitive():
 a=sequence_embedding('ATGC'*20); b=sequence_embedding('AAAA'*20); assert a.sum()==pytest.approx(1) and np.linalg.norm(a-b)>0

def test_epigenetic_fusion_cell_specific():
 h=epigenetic_fusion('ATGC'*50,cell_type='hepatocyte'); n=epigenetic_fusion('ATGC'*50,cell_type='neuron'); assert h['mean_activity']>n['mean_activity']

def test_contact_probability_distance_and_orientation():
 assert contact_probability(1000,True)>contact_probability(10000,True)>contact_probability(10000,False)

def test_contact_map_symmetric():
 m=np.asarray(reconstruct_contact_map('ATGC'*100,100)['matrix']); assert np.allclose(m,m.T) and np.allclose(np.diag(m),1)

def test_tad_boundaries_have_coordinates():
 r=tad_boundaries('ATGC'*1000,200); assert all('position' in x and 'insulation_score' in x for x in r)

def test_motif_energy_improves_with_match():
 assert motif_energy(CTCF,'CCGCGNGGNGGCAG')['binding_energy_kcal_mol']<motif_energy('A'*len(CTCF),'CCGCGNGGNGGCAG')['binding_energy_kcal_mol']

def test_nucleosome_occupancy_bounded():
 assert 0<=nucleosome_occupancy('ATGC'*20)<=1

def test_expression_cell_state_contrast():
 r=cell_state_contrast('ATGC'*50); assert r['range_log2']>0 and r['highest']=='hepatocyte'

def test_delta_embedding_zero_for_identity():
 assert delta_embedding('ATGC'*10,'ATGC'*10)['l2']==0

def test_variant_deltas_are_mechanistic_and_finite():
 r=variant_mechanistic_deltas('ATGC'*50,10,'A'); keys=['delta_tf_binding_kcal_mol','delta_atac','delta_nucleosome','delta_contact','delta_rna_expression','uncertainty_std']; assert all(math.isfinite(r[k]) for k in keys)

def test_edit_simulation_changes_length_for_indel():
 r=simulate_edit('ATGC'*20,5,8,'A'); assert r['length_delta']==-2 and len(r['edited_sequence'])==78

def test_masked_objective_seeded():
 a=masked_sequence_objective('ATGC'*100,seed=3); b=masked_sequence_objective('ATGC'*100,seed=3); assert a==b and a['masked_bases']>0 and a['perplexity']>1

def test_modality_alignment_perfect_match():
 r=modality_alignment([0,1,2],[0,1,2]); assert r['pearson']==pytest.approx(1) and r['contrastive_loss']==pytest.approx(0)

def test_perturbation_calibration_exact():
 r=perturbation_calibration([1,2],[1,2]); assert r['rmse']==0 and r['calibration_slope']==pytest.approx(1)

def test_cryptic_splice_risk_bounded():
 assert 0<=cryptic_splice_risk('GTAG'*20)<=1

def test_edit_design_is_minimal_and_ranked():
 r=propose_regulatory_edits('ATGC'*10,.1,max_edits=3); assert len(r['edits'])==3 and all(e['ref']!=e['alt'] for e in r['edits']) and r['edits'][0]['reward']>=r['edits'][-1]['reward']

def test_diagnostics_are_honest_finite_metrics():
 d=genomegpt_diagnostics('ATGC'*100); assert 25<=len(d)<50 and all(math.isfinite(v) for v in d.values()) and not any(k.startswith('position_') for k in d)

def test_diagnostics_change_with_sequence():
 a=genomegpt_diagnostics('ATGC'*100); b=genomegpt_diagnostics('AAAA'*100); assert sum(a[k]!=b[k] for k in a)>=10

def test_report_integrates_modalities_and_honesty():
 r=genomegpt_report('ATGC'*100,'hepatocyte'); assert r['contact_map']['matrix'] and r['diagnostics'] and r['next_steps'] and 'no trained foundation model and not clinically validated' in r['model_status']

def test_variant_validation():
 with pytest.raises(ValueError): variant_mechanistic_deltas('ATGC',99,'A')
