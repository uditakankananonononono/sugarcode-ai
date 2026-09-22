import math
from sugarcode.modules.mutdock import *
P='AILMDEFWY'; S='CC(=O)N'
def test_legacy_mutation_and_scan():
 assert mutation_effect(P,S,0,'S')['mutation'] and resistance_scan(P,{'d':S})['per_drug']
def test_local_repack_is_traced():
 r=local_repack([[0,0,0],[6,0,0],[12,0,0]],1,1,3); assert len(r['energy_trace'])==3 and r['converged']
def test_interaction_graph_changes_by_mutation():
 r=graph_perturbation(P,S,0,'S'); assert r['wild_type']['fingerprint']!=r['mutant']['fingerprint']
def test_ensemble_returns_uncertainty():
 r=ensemble_mutation_effect([P,'VILMDEFWY'],S,0,'S'); assert abs(sum(r['weights'])-1)<1e-12 and r['ddg_std']>=0
def test_epistasis_is_explicit():
 r=epistasis_effect(P,S,[(0,'S'),(1,'D')]); assert abs(r['combined_ddg']-r['additive_expectation']-r['epistasis'])<1e-12
def test_fitness_landscape_real_variants():
 r=mutational_fitness_landscape(P,S,[0]); assert len(r['variants'])==19 and r['resistance_hotspots'][0]['ddg_kcal_mol']>=r['resistance_hotspots'][-1]['ddg_kcal_mol']
def test_cross_drug_matrix_preserves_names():
 r=cross_drug_matrix(P,{'a':'CC','b':'CCN'},[(0,'S')]); assert set(r['rows'][0]['ddg'])=={'a','b'}
def test_forecast_monotonic_and_labeled():
 r=evolutionary_forecast(P,S,5); assert r['resistance_emergence_probability']==sorted(r['resistance_emergence_probability']) and 'not patient prognosis' in r['status']
def test_report_complete_honest():
 r=mutdock_report(P,{'a':'CC','b':'CCN'},[(0,'S'),(1,'D')]); assert r['epistasis'] and r['fitness'] and r['forecast'] and 'no trained GNN' in r['model_status']
def test_diagnostics_honest_finite():
 d=mutdock_diagnostics(P,S,0,'S'); assert len(d)==14 and all(math.isfinite(x) for x in d.values())

def test_hotspot_and_high_risk_are_reachable():
 hits=[mutation_effect(P,S,p,a) for p in range(len(P)) for a in 'ACDEFGHIKLMNPQRSTVWY' if a!=P[p]]
 assert any(x['hotspot'] for x in hits) and any(x['resistance_risk']=='high' for x in hits)
