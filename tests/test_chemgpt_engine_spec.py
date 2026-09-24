import math
import pytest
from sugarcode.modules.chemgpt_engine import *
F=['benzene','amide','hydroxyl']

def test_legacy_scoring_and_lipinski():
 r=score_molecule(F); assert r['mw']>0 and math.isfinite(r['logP']) and 0<=r['lipinski_violations']<=4

def test_legacy_generation_pareto_front():
 r=generate(12,seed=2); assert r['generated']==12 and r['pareto_front'] and all('retrosynthesis' in c for c in r['pareto_front'])

def test_pareto_removes_dominated_candidate():
 a={'objectives':{'x':1,'y':1}}; b={'objectives':{'x':0,'y':1}}; assert pareto_front([a,b])==[a]

def test_graph_has_atoms_and_bonds():
 r=molecular_graph(F); assert len(r['nodes'])==sum(FRAGMENTS[x][1] for x in F) and r['edges']

def test_conformer_ensemble_seeded_and_weighted():
 a=conformer_ensemble(F,10,3); b=conformer_ensemble(F,10,3); assert a==b and sum(x['boltzmann_weight'] for x in a)==pytest.approx(1) and a[0]['energy_kcal_mol']<=a[-1]['energy_kcal_mol']

def test_quantum_gap_and_hardness_positive():
 r=quantum_descriptors(F); assert r['gap_ev']>0 and r['hardness_ev']>0 and r['electrophilicity_ev']>0

def test_admet_is_bounded_and_labeled():
 r=admet_profile(F); assert 0<=r['permeability']<=1 and 0<=r['hepatotoxicity']<=1 and set(r['uncertainty'])=={'logP','logS','permeability','cyp_risk','herg_risk','pgp_interaction','metabolic_stability','hepatotoxicity','potency_prior','synthetic_accessibility'} and all(v>0 for v in r['uncertainty'].values()) and r['model_status']=='fragment/physics surrogate'

def test_uncertainty_is_molecule_sensitive_across_layers():
 a=admet_profile(F); b=admet_profile(['piperazine','sulfonamide','fluorine'])
 assert a['uncertainty'] != b['uncertainty']
 assert set(quantum_descriptors(F)['uncertainty']) >= {'homo_ev','lumo_ev','gap_ev'}
 assert set(docking_score(F,{})['uncertainty']) >= {'binding_energy_kcal_mol','clash_penalty'}
 assert set(md_binding_stability(-5,2)['uncertainty']) == {'bound_fraction','off_rate_per_ns','expected_residence_ns'}


def test_docking_rewards_hydrogen_bonds():
 polar=docking_score(['amide','hydroxyl'],{'donors':5,'acceptors':5}); nonpolar=docking_score(['benzene','methyl'],{'donors':5,'acceptors':5}); assert polar['hydrogen_bonds']>nonpolar['hydrogen_bonds'] and 'solvent' in polar['limitation']

def test_md_stability_better_for_stronger_binding():
 assert md_binding_stability(-10,1)['bound_fraction']>md_binding_stability(-3,1)['bound_fraction']

def test_pareto_rank_returns_nondominated():
 c=[{'objectives':{'potency':1,'solubility':1,'safety':1,'feasibility':1}},{'objectives':{'potency':.5,'solubility':.5,'safety':.5,'feasibility':.5}}]; assert len(pareto_rank(c))==1

def test_retrosynthesis_route_has_conditions_yield_and_inventory():
 r=retrosynthesis_plan(F,['amide']); assert r['steps'] and 0<r['overall_yield']<=1 and r['inventory_coverage']>0 and r['estimated_route_cost_usd']>0 and r['cost_yield_objective']>r['estimated_route_cost_usd'] and r['optimization_objective'].startswith('minimize') and 'not an executable' in r['status']

def test_uncertainty_ensemble_seeded():
 a=uncertainty_ensemble(F,20,3); b=uncertainty_ensemble(F,20,3); assert a==b and a['metrics']['logP']['std']>0 and set(a['metrics']) >= {'cyp_risk','herg_risk','pgp_interaction','metabolic_stability','hepatotoxicity','homo_ev','lumo_ev','binding_energy_kcal_mol','bound_fraction'}

def test_active_learning_reduces_uncertainty():
 r=active_learning_update(0,.5,[.1,.2],.1); assert r['std']<.5 and 0<r['mean']<.2

def test_conditioned_generation_ranked():
 r=generate_conditioned(20,{'logP':2,'min_solubility':.2,'max_toxicity':.4},seed=2); assert r['candidates'] and r['candidates'][0]['reinforcement_score']>=r['candidates'][-1]['reinforcement_score'] and 'no trained diffusion' in r['model_status']

def test_diagnostics_honest_finite_metrics():
 d=molecule_diagnostics(F); assert len(d)==39 and all(math.isfinite(v) for v in d.values()) and not any(k.startswith('fragment_') and k.endswith('.present') for k in d)

def test_diagnostics_change_with_chemistry():
 a=molecule_diagnostics(F); b=molecule_diagnostics(['piperazine','sulfonamide','fluorine']); assert sum(a[k]!=b[k] for k in a)>=20

def test_discovery_package_complete_and_honest():
 r=discovery_package(F,{'donors':3,'acceptors':3}); assert r['graph'] and r['conformers'] and r['quantum'] and r['admet'] and r['docking'] and r['retrosynthesis'] and r['uncertainty'] and r['next_steps']
 assert 'no trained model and not clinically validated' in r['model_status']

def test_unknown_fragment_rejected():
 with pytest.raises(KeyError): molecule_diagnostics(['unobtainium'])


def test_generated_molecules_are_real_structures():
    import itertools
    from sugarcode.modules.chemgpt_engine import assemble_smiles, generate
    g = generate(n=12, seed=42)
    assert all(c['smiles'] for c in g['pareto_front'])
    # benzene is a closed 6-bond aromatic ring, not a chain
    b = molecular_graph(['benzene'])
    assert len(b['edges']) == 6 and all(e['bond_order'] == 1.5 for e in b['edges'])
    # heteroatoms land where the fragment SMILES puts them
    assert [n['element'] for n in molecular_graph(['carboxyl'])['nodes']] == ['C', 'O', 'O']
    # methyl benzoate C8H8O2 = 136.15 g/mol
    assert score_molecule(['benzene', 'carboxyl', 'methyl'])['mw'] == pytest.approx(136.15, abs=0.1)
    rdkit = pytest.importorskip('rdkit.Chem')
    from rdkit.Chem.Descriptors import MolWt
    for fr in itertools.product(sorted(FRAGMENTS), repeat=3):
        try:
            smi = assemble_smiles(list(fr))
        except ValueError:
            continue
        mol = rdkit.MolFromSmiles(smi)
        assert mol is not None, (fr, smi)
        assert MolWt(mol) == pytest.approx(score_molecule(list(fr))['mw'], abs=0.15)
        g = molecular_graph(list(fr))
        assert (len(g['nodes']), len(g['edges'])) == (mol.GetNumAtoms(), mol.GetNumBonds())
