import math
from sugarcode.modules.str_scope import *
SEQ='AAA'+('CAG'*25)+'TTT'
def test_legacy_detection_expansion_index():
 h=find_strs(SEQ); e=expansion_call(30,10,'CAG'); assert h[0]['repeats']==25 and e['delta']==20 and diagnostic_index([e])['diagnostic_potential_index']>0
def test_long_reads_reconstruct_interruptions_and_mosaicism():
 r=reconstruct_repeat_reads(['CAG'*10,'CAG'*5+'CAA'+'CAG'*6],'CAG'); assert r['molecule_count']==2 and r['reads'][1]['interruptions'] and r['mosaicism_std']>0
def test_architecture_preserves_flanks():
 r=locus_architecture(SEQ,'CAG',3); assert r['repeat_count']==25 and r['left_flank']=='AAA' and r['right_flank']=='TTT'
def test_instability_seeded_and_repair_sensitive():
 a=repeat_instability(50,20,mmr=.1,seed=2); b=repeat_instability(50,20,mmr=1,seed=2); assert a['variance_trajectory'][-1]>b['variance_trajectory'][-1]
def test_coding_repeat_aggregation_length_sensitive():
 assert molecular_consequence('CAG',80)['aggregation_risk']>molecular_consequence('CAG',25)['aggregation_risk']
def test_noncoding_repeat_has_rna_and_splice_effects():
 r=molecular_consequence('CGG',80,'noncoding'); assert r['rna_toxicity']>0 and r['splice_disruption']>0
def test_repair_network_responds_to_capacity():
 assert repair_network(80,mmr=.1)['genomic_instability_index']>repair_network(80,mmr=1)['genomic_instability_index']
def test_intervention_nonprocedural_and_risk_adjusted():
 a=intervention_assessment(80,'contraction_editing',.1); b=intervention_assessment(80,'contraction_editing',.5); assert a['net_benefit']>b['net_benefit'] and 'non-procedural' in a['status']
def test_report_complete_honest():
 r=str_report(SEQ,'CAG',['CAG'*20]); assert r['single_molecule'] and r['repair_network'] and r['interventions'] and 'no trained transformer/GNN' in r['model_status']
def test_diagnostics_honest_finite():
 d=str_diagnostics(str_report(SEQ,'CAG',['CAG'*20])); assert len(d)>=50 and all(math.isfinite(x) for x in d.values())

def test_find_strs_feeds_diagnostic_index():
 hits=find_strs('ACGT'*5+'CAG'*40+'TTGACCA'*3); r=diagnostic_index(hits)
 cag=[l for l in r['loci'] if l['unit']=='CAG'][0]
 assert cag['delta']==14 and cag['delta_source']=='derived_from_reference' and cag['contribution']>0 and r['diagnostic_potential_index']>0
 assert diagnostic_index(find_strs('CAG'*20))['diagnostic_potential_index']==0
def test_hot_motif_matches_rotation_and_revcomp():
 r=diagnostic_index([{'unit':'AGC','repeats':60},{'unit':'CTG','repeats':60}]); assert all(l['hot_motif'] for l in r['loci'])
def test_reference_override():
 h=[{'unit':'CAG','repeats':40}]; assert diagnostic_index(h,reference_repeats=39)['loci'][0]['delta']==1
def test_architecture_detects_interruptions():
 r=locus_architecture('TTT'+'CAG'*10+'CAA'+'CAG'*10+'TTT','CAG',3)
 assert r['repeat_count']==21 and len(r['interruptions'])==1 and r['interruptions'][0]['observed']=='CAA' and abs(r['purity']-20/21)<1e-9 and r['left_flank']=='TTT' and r['right_flank']=='TTT'
def test_architecture_trims_edge_mismatch():
 r=locus_architecture('GGG'+'CAG'*10+'CAT'+'GGG','CAG'); assert r['repeat_count']==10 and not r['interruptions']
def test_diagnostics_track_interruptions_and_reads():
 d=str_diagnostics(str_report('TTT'+'CAG'*30+'CAA'+'CAG'*30+'TTT','CAG',['CAG'*55,'CAG'*70]))
 assert d['interruption_count']==1 and d['repeat_count']==61 and d['reads_expanded_fraction']==1.0 and d['longest_pure_run']==30
