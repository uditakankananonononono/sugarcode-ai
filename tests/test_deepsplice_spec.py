import math
from sugarcode.modules.deepsplice import *
D='CAGGTAAGT'
def test_legacy_scores_and_variant_effect():
 assert score_donor(D)>0 and variant_effect(D,D[:3]+'A'+D[4:],'donor')['delta']!=0
def test_regulatory_features_use_rbp_and_chromatin():
 a=regulatory_features('GAAGAAGAAGAA',chromatin={'H3K36me3':1}); b=regulatory_features('AAAAAAAAAAAA',chromatin={'H3K36me3':0}); assert a['exon_definition_support']>b['exon_definition_support']
def test_inclusion_is_strength_sensitive_and_uncertain():
 a=exon_inclusion(.8,.8,regulatory_features(D)); b=exon_inclusion(.8,.1,regulatory_features(D)); assert a['psi']>b['psi'] and b['interval95'][0]<=b['psi']<=b['interval95'][1]
def test_isoforms_normalized_and_frame_aware():
 r=isoform_distribution(.4,False,.2,.1); assert abs(sum(r['isoforms'].values())-1)<1e-12 and 'frameshift' in r['protein_outcomes']['exon_skipped']
def test_regulatory_graph_tracks_effect_direction():
 r=splice_regulatory_graph(['E1'],['I1'],[('SRSF1','E1','enhance'),('PTBP1','E1','silence')]); assert r['activation_balance']==0 and len(r['edges'])==2
def test_interventions_rank_restoration_and_risk():
 r=intervention_simulation(.8,.2,[{'name':'a','psi_shift':.5,'offtarget_risk':.1},{'name':'b','psi_shift':.1,'offtarget_risk':.1}]); assert r[0]['name']=='a' and 'non-procedural' in r[0]['status']
def test_active_learning_prefers_uncertain_high_impact():
 r=active_learning([{'id':'a','probability':.5,'impact':1},{'id':'b','probability':.99,'impact':1}]); assert r[0]['id']=='a'
def test_report_complete_honest():
 alt=D[:3]+'A'+D[4:]; r=splicing_report(D,alt,context_sequence='GAAGAA'+D); assert r['isoforms'] and r['regulatory'] and 'no transformer/GNN' in r['model_status']
def test_diagnostics_finite_and_honest():
 d=splice_diagnostics(splicing_report(D,D[:3]+'A'+D[4:])); assert len(d)==13 and all(math.isfinite(x) for x in d.values())
