import math
from sugarcode.modules.docking_studio import *
def test_legacy_docking_and_screen():
 r=dock('HDEFWY','CC(=O)N'); s=virtual_screen('HDEFWY',['CC','CC(=O)N']); assert r['energy_terms'] and s['best']
def test_pose_energy_changes_with_distance():
 assert pose_energy([[0,0,0]],[[2,0,0]])['total']!=pose_energy([[0,0,0]],[[8,0,0]])['total']
def test_transform_preserves_internal_distance():
 a=transform_pose([[0,0,0],[1,0,0]],[2,3,4],[0,0,1],1); assert abs(math.dist(*a)-1)<1e-12
def test_mc_search_reproducible_and_traced():
 a=monte_carlo_dock([[0,0,0]],[[5,0,0]],steps=5,seed=4); b=monte_carlo_dock([[0,0,0]],[[5,0,0]],steps=5,seed=4); assert a['best_energy']==b['best_energy'] and len(a['trajectory'])==5
def test_ensemble_returns_weights():
 r=ensemble_docking(['AAAA','HDEFWY'],'CCN'); assert abs(sum(r['conformational_weights'])-1)<1e-12
def test_thermodynamic_identity():
 r=binding_thermodynamics(-7,3,2); assert abs(r['delta_h_kcal_mol']+r['minus_t_delta_s_kcal_mol']-r['delta_g_kcal_mol'])<1e-12
def test_competition_normalized():
 ds=[dock('HDEFWY','CC'),dock('HDEFWY','CCN')]; r=competitive_binding(ds,[1,1]); assert abs(sum(r['occupancies'])+r['unbound_fraction']-1)<1e-12
def test_fingerprint_and_relative_free_energy():
 assert interaction_fingerprint('HDEFWY','CCN')['key_residues'] and len(relative_free_energy('HDEFWY','CC',['CCC'])['analogs'])==1
def test_report_honest():
 r=docking_report('HDEFWY',['CCN'],['HDEFWY','AAADEF']); assert r['ensemble'] and 'no trained GNN' in r['model_status']
def test_diagnostics_finite_and_ligand_sensitive():
 a=docking_diagnostics('HDEFWY','CC'); b=docking_diagnostics('HDEFWY','CC(=O)N'); assert len(a)==14 and all(math.isfinite(x) for x in a.values()) and sum(a[k]!=b[k] for k in a)>=5
