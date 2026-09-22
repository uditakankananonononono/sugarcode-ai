import math
from sugarcode.modules.protein_painter import *
def test_legacy_design_is_seed_reproducible():
 a=design_protein('catalyze redox',seed=3); b=design_protein('catalyze redox',seed=3); assert a['best']['sequence']==b['best']['sequence'] and a['best']['active_site_positions']
def test_active_site_depends_on_residue_chemistry():
 assert active_site_geometry('HDEAAAA',[0,1,2],1)['net_charge'] != active_site_geometry('KKKAAAA',[0,1,2],1)['net_charge']
def test_kinetics_tracks_complementarity():
 a=enzyme_kinetics('HDEAAAA',[0,1,2],1); b=enzyme_kinetics('KKKAAAA',[0,1,2],-3); assert a['catalytic_efficiency_m_inv_s']!=b['catalytic_efficiency_m_inv_s']
def test_binding_interface_scores_packing_and_charge():
 a=binding_interface('LLLLDDD',[0,1,2,4,5,6],.5,1); b=binding_interface('GGGGGGG',range(7),.9,1); assert a['binding_score']!=b['binding_score']
def test_compartment_changes_disulfide_capacity():
 assert cellular_compatibility('MCCCCAAAA','ER')['disulfide_capacity']>cellular_compatibility('MCCCCAAAA','cytosol')['disulfide_capacity']
def test_immunogenicity_preserves_epitope_provenance():
 r=immunogenicity_scan('WWWWKKKKAAAA'); assert r['epitopes'] and r['epitopes'][0]['peptide']
def test_construct_is_host_specific_and_burdened():
 a=expression_construct('MALWMRLLPLL','ecoli'); b=expression_construct('MALWMRLLPLL','yeast'); assert a['coding_dna']!=b['coding_dna'] and a['expression_burden']>0
def test_mutational_scan_flags_active_site():
 r=mutational_scan('AAAAAAA',[3]); assert r['positions'][3]['functional_sensitivity']>r['positions'][0]['functional_sensitivity']
def test_blueprint_complete_and_honest():
 r=engineering_blueprint('catalyze redox',seed=2); assert r['kinetics'] and r['construct'] and r['mutational_scan'] and r['validation'] and 'no trained protein language model' in r['model_status']
def test_diagnostics_honest_finite_and_intent_sensitive():
 a=painter_diagnostics('catalyze redox'); b=painter_diagnostics('bind tumor antigen'); assert len(a)==14 and all(math.isfinite(v) for v in a.values()) and sum(a[k]!=b[k] for k in a)>=5
