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
 d=str_diagnostics(str_report(SEQ,'CAG',['CAG'*20])); assert len(d)==12 and all(math.isfinite(x) for x in d.values())
