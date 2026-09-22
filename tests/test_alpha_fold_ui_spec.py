import math
import numpy as np
from sugarcode.modules.alpha_fold_ui import *
SEQ='MALWMRLLPLLALLALWGPGPGAGK'
def test_legacy_prediction_exports_pdb_and_analogs():
 r=predict_structure(SEQ); assert r['pdb'].endswith('END\n') and len(r['pae'])==len(SEQ) and len(r['plddt_per_residue'])==len(SEQ)
def test_msa_coupling_detects_covariation():
 r=msa_couplings(['AAAA','ACCA','AGGA','ATTA']); assert r['depth']==4 and np.asarray(r['mutual_information'])[1,2]>0
def test_sequence_weights_change_effective_depth():
 assert msa_couplings(['AAAA','AAAT'],[.9,.1])['effective_depth']<msa_couplings(['AAAA','AAAT'])['effective_depth']
def test_graph_is_rigid_transform_invariant():
 c=np.array([[0,0,0],[3,0,0],[9,0,0]]); r=graph_invariance(c,[[0,-1,0],[1,0,0],[0,0,1]],[4,2,1]); assert r['edges_preserved'] and r['max_distance_error']<1e-9
def test_physical_energy_sensitive_to_geometry_and_charge():
 a=physical_energy([[0,0,0],[4,0,0],[8,0,0]],[1,0,-1]); b=physical_energy([[0,0,0],[4,0,0],[5,0,0]],[1,0,-1]); assert a['total']!=b['total']
def test_refinement_has_trajectory():
 r=refine_coordinates([[0,0,0],[4,0,0],[5,0,0]],steps=2); assert len(r['energy_trajectory'])==3 and r['converged']
def test_mutation_stability_uses_residue_properties():
 assert mutation_stability(SEQ,1,'D')['ddg_relative']!=mutation_stability(SEQ,1,'V')['ddg_relative']
def test_workspace_preserves_pair_representation():
 msa=[SEQ,SEQ[:-1]+'A',SEQ[:-1]+'V']; r=folding_workspace(SEQ,msa); assert r['msa']['depth']==3 and r['pair_representation'] and 'no AlphaFold neural weights' in r['model_status']
def test_diagnostics_honest_finite_and_sequence_sensitive():
 a=structure_diagnostics(SEQ); b=structure_diagnostics('GGGGGGGGGGGG'); assert len(a)==14 and all(math.isfinite(x) for x in a.values()) and sum(a[k]!=b[k] for k in a)>=8

def test_mutation_hydrophobic_term_is_live():
 hyd=mutation_stability('AAAA',0,'V'); polar=mutation_stability('AAAA',0,'D')
 assert hyd['terms']['hydrophobicity'] != polar['terms']['hydrophobicity'] and hyd['ddg_relative'] != polar['ddg_relative']
