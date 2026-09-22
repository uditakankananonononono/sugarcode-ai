import math
import pytest
from sugarcode.modules.gene_analysis import *
SEQ=('GCGC'*60)+'ATG'+('GCT'*40)+'TAA'+('ATGC'*60)+'AGG'+('TTGC'*40)

def test_legacy_profile_full():
 p=gene_profile('DEMO1',SEQ,variants=[{'variant':'c.5A>G','consequence':'missense'}],publications=[2001,2003,2007]); assert p['symbol']=='DEMO1' and p['protein'] and p['crispr_targets'] and p['variants'][0]['classification'] and p['publication_trend']['total']==3

def test_molecular_graph_directionality():
 g=molecular_graph('G',[{'variant':'c.1A>G'}],['i1'],['P']); assert len(g['nodes'])==4 and {e['relation'] for e in g['edges']}=={'perturbs','transcribes','interacts'}

def test_splice_outcome_nmd_and_isoform():
 r=splice_outcome('splice donor and nonsense',20); assert r['splice_disruption']>.5 and r['nmd_probability']>.5 and r['isoform_switch_probability']>.5

def test_structure_context_increases_ddg():
 a=structure_perturbation(.2); b=structure_perturbation(.9,True,True,.9); assert b['ddg_kcal_mol']>a['ddg_kcal_mol'] and b['interface_loss_probability']>a['interface_loss_probability']

def test_variant_posterior_attributions_and_interval():
 r=variant_posterior(.8,regulatory=.7,splicing=.6); assert sum(r['attributions'].values())==pytest.approx(1) and r['conformal_interval'][0]<=r['pathogenic_probability']<=r['conformal_interval'][1]

def test_conformational_populations_normalized():
 r=conformational_ensemble(2); assert sum(r['populations'].values())==pytest.approx(1)

def test_pathway_is_dynamic_and_drug_sensitive():
 a=pathway_dynamics(drug_inhibition=0); b=pathway_dynamics(drug_inhibition=.8); assert len(a['time_h'])==121 and a['biomarker'][-1]>b['biomarker'][-1]

def test_counterfactual_propagates_to_phenotype():
 r=counterfactual_variant(.9,True,.7,.6,{'active_site':True}); assert r['posterior']['pathogenic_probability']>0 and r['structural']['ddg_kcal_mol']>0 and r['phenotype_delta']!=0

def test_crispr_outcome_ranking():
 r=outcome_aware_crispr(SEQ,chromatin=.8); assert r and r[0]['predicted_phenotype_score']>=r[-1]['predicted_phenotype_score']

def test_power_decreases_with_effect_size():
 assert power_estimate(.2)['replicates_per_group']>power_estimate(.8)['replicates_per_group']

def test_experimental_plan_is_nonprocedural():
 r=experimental_plan('TP53'); assert r['controls'] and r['readouts'] and 'not an executable' in r['status']

def test_feedback_updates_and_reduces_uncertainty():
 r=feedback_update(.5,8,10); assert r['mean']>.5 and r['std']>0

def test_diagnostics_honest_finite():
 d=gene_diagnostics('DEMO1',SEQ); assert len(d)==14 and all(math.isfinite(v) for v in d.values()) and not any(k.startswith('position_') for k in d)

def test_digital_twin_complete_and_honest():
 r=digital_twin('DEMO1',SEQ,condition={'drug_inhibition':.2}); assert r['profile'] and r['causal_graph'] and r['counterfactual'] and r['crispr'] and r['experimental_plan'] and r['diagnostics']
 assert 'no trained model and not clinically validated' in r['model_status']

def test_invalid_power_rejected():
 with pytest.raises(ValueError): power_estimate(0)

def test_digital_twin_variant_input_drives_mechanistic_cascade():
 synonymous=digital_twin('DEMO1',SEQ,[{'variant':'c.5A>G','consequence':'synonymous'}])
 severe=digital_twin('DEMO1',SEQ,[{'variant':'c.5A>T','consequence':'splice donor nonsense','conservation':.95,'active_site':True}])
 assert severe['counterfactual']['posterior']['pathogenic_probability']>synonymous['counterfactual']['posterior']['pathogenic_probability']
 assert severe['counterfactual']['structural']['ddg_kcal_mol']>synonymous['counterfactual']['structural']['ddg_kcal_mol']
 assert severe['counterfactual']['phenotype_delta']<synonymous['counterfactual']['phenotype_delta']
 assert severe['diagnostics']['variant_splice_disruption']>synonymous['diagnostics']['variant_splice_disruption']


def test_digital_twin_condition_interacts_with_variant_pathway():
 variant=[{'variant':'c.5A>T','consequence':'missense','conservation':.8}]
 untreated=digital_twin('EGFR',SEQ,variant,{'drug_inhibition':0})
 treated=digital_twin('EGFR',SEQ,variant,{'drug_inhibition':.8})
 assert untreated['counterfactual']['pathway']['biomarker_name']=='p_ERK'
 assert treated['counterfactual']['pathway']['biomarker'][-1] < untreated['counterfactual']['pathway']['biomarker'][-1]


def test_crispr_design_includes_advanced_modalities_and_validation():
 designs=outcome_aware_crispr(SEQ)
 assert designs and designs[0]['base_edit'] and designs[0]['prime_edit'] and designs[0]['silent_pam_disruption']
 assert designs[0]['validation_assays'] and 'nucleosome_score' in designs[0]


def test_diagnostics_no_literal_baseline_padding():
 d=gene_diagnostics('DEMO1',SEQ,[{'variant':'c.5A>G','consequence':'synonymous'}])
 assert len(d)==15 and not any(key.startswith('baseline.') or key=='pathway_count' for key in d)
 assert all(math.isfinite(v) for v in d.values())
