import math
import pytest
from sugarcode.modules.crispr_cargo import *

def test_legacy_recommendation_and_pk():
 r=recommend_vehicle('SpCas9+gRNA','liver'); p=pk_model('LNP'); assert r['ranked'] and p['concentration_ug_per_l'][0]>p['concentration_ug_per_l'][-1]
def test_payload_capacity_and_split_strategy():
 a=payload_architecture('SaCas9+gRNA'); b=payload_architecture('prime_editor+pegRNA'); assert a['aav_fit'] and b['split_required'] and b['split_strategy']
def test_receptor_atlas_drives_subtype_uptake():
 r=receptor_uptake('liver',{'high':1,'low':.1}); assert r['cell_subtypes']['high']['uptake_probability']>r['cell_subtypes']['low']['uptake_probability']
def test_lnp_biophysics_sensitive_to_size_and_peg():
 a=lnp_biophysics(90,peg_mol_pct=1); b=lnp_biophysics(250,peg_mol_pct=8); assert a['endosomal_escape_probability']>b['endosomal_escape_probability'] and b['relative_clearance']>a['relative_clearance']
def test_compartment_pk_conserves_mass_and_targets():
 r=compartment_pk('LNP',tissue='liver'); assert r['target_auc']>0 and r['mass_balance_error']<1e-6 and r['target_ug_l'][-1]>0
def test_tropism_changes_target_exposure():
 assert compartment_pk('AAV8',tissue='liver')['target_auc']>compartment_pk('AAV8',tissue='retina')['target_auc']
def test_immune_risk_respects_antibody_for_aav():
 assert immune_risk('AAV8',preexisting_antibody=.9)['adaptive_risk']>immune_risk('AAV8',preexisting_antibody=.01)['adaptive_risk']
def test_expression_is_transient_and_exposure_quantified():
 r=expression_kinetics('SpCas9+gRNA','LNP'); assert r['relative_activity'][0]==0 and r['relative_activity'][-1]<max(r['relative_activity']) and r['off_target_exposure_proxy']>0
def test_optimizer_balances_cell_uptake_and_risk():
 r=optimize_delivery('SpCas9+gRNA','liver',{'hepatocyte':.9}); assert r['ranked']==sorted(r['ranked'],key=lambda x:-x['benefit_risk']) and r['validation'] and 'no trained toxicity model' in r['model_status']
def test_diagnostics_honest_finite():
 d=cargo_diagnostics('SpCas9+gRNA','liver'); assert len(d)==14 and all(math.isfinite(v) for v in d.values())
def test_diagnostics_change_by_vehicle():
 a=cargo_diagnostics('SpCas9+gRNA','liver','LNP'); b=cargo_diagnostics('SpCas9+gRNA','liver','AAV8'); assert sum(a[k]!=b[k] for k in a)>=7
def test_invalid_particle_rejected():
 with pytest.raises(ValueError): lnp_biophysics(-1)
