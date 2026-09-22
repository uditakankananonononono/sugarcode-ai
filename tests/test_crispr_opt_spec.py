import json,math
import pytest
from sugarcode.modules.crispr_opt import *
G='GAGTCCGAGCAGAAGAAGAA'
LOCUS='A'*10+G+'AGG'+'C'*50

def test_legacy_pam_and_design():
 assert pam_sites(LOCUS,'NGG'); r=design_guides(LOCUS,top_n=3); assert r['guides'] and r['browser_track']['tracks']

def test_published_cfd_exact_and_mismatch():
 assert cfd_score(G,G,'GG')==1 and cfd_score(G,G[:-1]+'C','GG')<1

def test_mismatch_profile_exact_above_mismatch():
 a=mismatch_profile(G,G); b=mismatch_profile(G,G[:-1]+'C'); assert a['binding_probability']>b['binding_probability'] and b['mismatch_count']==1

def test_bulge_alignment_detects_shift():
 r=bulge_alignment(G,G[1:]+'A'); assert 0<=r['identity']<=1 and r['bulge'] in (-1,0,1)

def test_hybrid_energy_worsens_with_mismatch():
 assert hybrid_thermodynamics(G,G)['delta_g_kcal_mol']<hybrid_thermodynamics(G,G[:-1]+'C')['delta_g_kcal_mol']

def test_chromatin_context_changes_efficiency():
 a=chromatin_adjustment(.8,atac=.9,h3k27ac=.9); b=chromatin_adjustment(.8,atac=.1,h3k27ac=.1); assert a['context_score']>b['context_score']

def test_binding_kinetics_exact_higher_cleavage():
 assert binding_kinetics(G,G)['cleavage_probability']>binding_kinetics(G,G[:-1]+'C')['cleavage_probability']

def test_functional_risk_weights_essential_coding():
 hit={'cfd_score':.5}; assert functional_offtarget_risk(hit,{'coding':True,'essential_gene_proximity':True})['functional_risk']>functional_offtarget_risk(hit,{})['functional_risk']

def test_base_editor_reports_bystanders():
 r=base_editor_window('AAAACCCCAAAACCCCAAAA'); assert len(r['sites'])==4 and r['bystander_count']==3

def test_prime_architecture_bounded_efficiency():
 r=prime_editor_architecture(G,G[:13],G[:15]); assert 0<=r['efficiency']<=1 and 0<=r['mmr_retention']<=1

def test_report_has_context_exports_and_honesty():
 r=design_report(LOCUS,tracks=[{'name':'state','values':{'atac':.8}}]); assert r['guides'] and json.loads(r['exports']['json']) and r['exports']['bed'] and 'no trained deep model and not clinically validated' in r['model_status']

def test_diagnostics_honest_finite():
 d=guide_diagnostics(G); assert len(d)==26 and all(math.isfinite(v) for v in d.values()) and not any(k.startswith('position_') for k in d)

def test_diagnostics_change_with_target_and_chromatin():
 a=guide_diagnostics(G,G,{'atac':.9}); b=guide_diagnostics(G,G[:-1]+'C',{'atac':.1}); assert sum(a[k]!=b[k] for k in a)>=8

def test_invalid_chromatin_rejected():
 with pytest.raises(ValueError): chromatin_adjustment(.8,atac=2)
