import math
import numpy as np
import pytest
from sugarcode.modules.dark_genome import *
SEQ='TGACTCA'+'A'*50+'GGGCGG'+'AT'*30+'CCAAT'+'AT'*30+'TGACTCA'+'GGGCGG'+'CCAAT'

def test_legacy_decode_finds_dark_enhancer():
 r=decode(SEQ); assert r['tf_motif_hits'] and r['enhancer_clusters'] and r['dark_matter_fraction']==1

def test_coordinate_field_cell_state_sensitive():
 a=coordinate_field(SEQ,{'atac':.9}); b=coordinate_field(SEQ,{'atac':.1}); assert np.mean([x['regulatory_potential'] for x in a['field']])>np.mean([x['regulatory_potential'] for x in b['field']])

def test_chromatin_graph_distance_edges():
 r=chromatin_graph(SEQ,bin_size=25); assert r['nodes'] and r['edges'] and max(e['contact'] for e in r['edges'])<=1

def test_graph_propagation_changes_perturbed_state():
 g=chromatin_graph(SEQ,bin_size=25); r=graph_propagate(g,{0:1}); assert r['propagated']!=r['initial'] and len(r['delta'])==len(g['nodes'])

def test_binding_energy_prefers_motif():
 motif=TF_MOTIFS['AP-1']; assert motif_binding_energy(motif,motif)['energy_kcal_mol']<motif_binding_energy('A'*len(motif),motif)['energy_kcal_mol']

def test_nucleosome_positions_bounded():
 r=nucleosome_positioning('ATGC'*100); assert r and all(0<=x['occupancy']<=1 for x in r)

def test_interventional_causality_labeled():
 x=[0,0,1,1]; y=[.1,.2,.8,.9]; r=enhancer_gene_causality(x,y,[False,False,True,True]); assert r['evidence']=='interventional' and r['interventional_effect']>0

def test_association_does_not_claim_causality():
 r=enhancer_gene_causality([0,1,2],[0,1,2]); assert r['interventional_effect'] is None and r['evidence']=='associational only'

def test_regulatory_logic_semantics():
 assert regulatory_logic([.5,.5],'AND')['activity']==.25 and regulatory_logic([.5,.5],'OR')['activity']==.75 and regulatory_logic([.2],'NOT')['activity']==.8

def test_cell_state_decode_keeps_conditions_separate():
 r=cell_state_decode(SEQ,{'a':{'atac':.9},'b':{'atac':.1}}); assert r['a']!=r['b']

def test_temporal_trajectory_conserves_probability():
 r=temporal_trajectory([1,0],[[.8,.2],[.1,.9]],5); assert all(sum(x)==pytest.approx(1) for x in r['trajectory']) and r['final_state'][1]>0

def test_counterfactual_seeded_and_uncertain():
 a=variant_counterfactual(SEQ,5,'T',samples=50,seed=2); b=variant_counterfactual(SEQ,5,'T',samples=50,seed=2); assert a==b and a['cell_states']['generic']['expression_delta_std']>0

def test_counterfactual_varies_by_cell_state():
 states={'open':{'atac':.9},'closed':{'atac':.1}}; r=variant_counterfactual(SEQ,5,'T',states,samples=20); assert set(r['cell_states'])==set(states)

def test_blueprint_ranks_minimal_edits():
 r=perturbation_blueprint(SEQ[:40],.05,top_n=3); assert len(r['strategies'])==3 and all(x['type']=='base_edit' and x['ref']!=x['alt'] for x in r['strategies']) and r['strategies'][0]['reward']>=r['strategies'][-1]['reward']

def test_feedback_reduces_uncertainty():
 r=perturbation_feedback({'mean':.2,'std':.3},.1,.1); assert r['std']<.1+.0001 and .1<=r['mean']<=.2

def test_regulatory_blueprint_complete_and_honest():
 r=regulatory_blueprint(SEQ); assert r['elements'] and r['causal_graph'] and r['prioritized_interventions'] and r['validation'] and 'no trained foundation model and not clinically validated' in r['model_status']

def test_diagnostics_are_honest_finite_metrics():
 d=dark_genome_diagnostics(SEQ); assert 25<=len(d)<45 and all(math.isfinite(v) for v in d.values()) and not any(k.startswith('position_') for k in d)

def test_diagnostics_change_with_sequence():
 a=dark_genome_diagnostics(SEQ); b=dark_genome_diagnostics('A'*len(SEQ)); assert sum(a[k]!=b[k] for k in a)>=10

def test_invalid_transition_rejected():
 with pytest.raises(ValueError): temporal_trajectory([1,0],[[1,1],[0,1]])
