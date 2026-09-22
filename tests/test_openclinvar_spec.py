import math
from sugarcode.modules.openclinvar import *
def test_legacy_interpretation_and_plain_language():
 r=interpret_variant('BRCA1','x',consequence='nonsense'); assert r['classification'] and r['plain_language'] and r['evidence']
def test_bayesian_acmg_trace_is_monotonic_for_pathogenic_evidence():
 r=bayesian_acmg([{'strength':'strong','direction':'pathogenic'},{'strength':'moderate','direction':'pathogenic'}]); p=[x['cumulative_probability'] for x in r['reasoning_trace']]; assert p[1]>p[0]>.1
def test_benign_evidence_lowers_posterior():
 assert bayesian_acmg([{'strength':'strong','direction':'benign'}])['posterior_probability']<.1
def test_literature_consensus_preserves_conflicts_and_provenance():
 r=evidence_consensus([{'classification':'pathogenic','quality':.9,'year':2025,'sample_size':100,'id':'a'},{'classification':'benign','quality':.3,'year':2000,'id':'b'}]); assert r['consensus']=='pathogenic' and r['conflicts'][0]['id']=='b'
def test_reasoning_graph_connects_variant_to_phenotype():
 r=reasoning_graph('G','v','missense',['HPO:1'],['P']); assert r['causal_chain']==['v','missense','P','HPO:1'] and len(r['edges'])==4
def test_phenotype_semantics_partial_match():
 r=phenotype_match(['child'],['parent'],{'child':['parent']}); assert r['semantic_partial']==.5 and r['score']>0
def test_reverse_inference_ranks_patient_fit():
 r=reverse_inference(['H1'],[{'variant':'a','phenotypes':['H1'],'variant_probability':.5},{'variant':'b','phenotypes':['H2'],'variant_probability':.5}]); assert r[0]['variant']=='a'
def test_forward_trajectory_is_labeled_not_prognosis():
 r=forward_trajectory('pathogenic'); assert r['cumulative_risk']==sorted(r['cumulative_risk']) and 'not prognosis' in r['status']
def test_federated_update_uses_aggregates():
 r=federated_evidence([{'supporting':8,'total':10},{'supporting':2,'total':5}]); assert r['sites']==2 and r['shared_data']=='aggregate counts only'
def test_integrated_intelligence_complete_honest():
 r=variant_intelligence('G','v',acmg_evidence=[{'strength':'strong','direction':'pathogenic'}],literature=[{'classification':'pathogenic'}],phenotypes=['H1'],pathways=['P'],patient_hpo=['H1']); assert r['reasoning_graph'] and r['phenotype_match']['score']>0 and 'no trained transformer/GNN' in r['model_status']
def test_diagnostics_honest_finite():
 r=variant_intelligence('G','v',acmg_evidence=[{'strength':'strong','direction':'pathogenic'}],literature=[{'classification':'pathogenic'}]); d=clinvar_diagnostics(r); assert len(d)==12 and all(math.isfinite(x) for x in d.values())
