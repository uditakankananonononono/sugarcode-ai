import math
import pytest
from sugarcode.modules.synthetic_life import *
GENES=[{'name':'rep','category':'replication','size_bp':1000,'crispr_essentiality':.95},{'name':'tx','category':'transcription','size_bp':900,'transposon_essentiality':.9},{'name':'tl','category':'translation','size_bp':1100,'model_essentiality':.95},{'name':'stress','category':'stress_response','size_bp':500,'crispr_essentiality':.1},{'name':'stress_backup','category':'stress_response','size_bp':550,'crispr_essentiality':.05},{'name':'mot','category':'motility','size_bp':600,'crispr_essentiality':.05},{'name':'mot_backup','category':'motility','size_bp':650,'crispr_essentiality':.01}]

def test_legacy_essentiality_and_minimal_design():
 e=essentiality_scan(); g=design_minimal_genome(); assert e['essential_reactions'] and e['essential_fraction']>0 and 0<g['minimal_set_size']<g['input_genes'] and 0<g['reduction_fraction']<1

def test_gene_evidence_is_causal_and_bounded():
 r=gene_evidence_score(GENES[0]); assert 0<=r['posterior_essentiality']<=1 and set(r)>={'crispr','transposon','conservation','whole_cell','uncertainty'}

def test_optimizer_keeps_core_coverage():
 r=optimize_minimal_genome(GENES); assert {'rep','tx','tl'}<={g['name'] for g in r['kept']} and r['objective_bp']<sum(g['size_bp'] for g in GENES)
 assert len([g for g in r['kept'] if g['category']=='stress_response'])==1 and len([g for g in r['kept'] if g['category']=='motility'])==1
 assert {'stress_backup','mot_backup'}<={g['name'] for g in r['dropped']}

def test_genome_validation_detects_missing_core():
 r=validate_genome_design({'kept':[GENES[0]]}); assert not r['valid'] and set(r['missing_core_categories'])=={'transcription','translation'}

def test_flux_optimization_obeys_oxygen_limit():
 r=flux_optimize(oxygen_limit=2); assert r['status']=='optimal' and r['fluxes']['RESP']<=2

def test_monod_saturates_and_inhibition_reduces():
 assert monod_rate(10)>monod_rate(.1) and monod_rate(1,inhibition=20)<monod_rate(1)

def test_oxygen_transfer_flags_limitation():
 assert oxygen_transfer(1,.2,.21,biomass=10)['oxygen_limited']

def test_dynamic_fba_is_time_resolved():
 r=dynamic_fba(hours=2,dt=.25); assert len(r['trajectory'])>2 and r['final_biomass_gdw_l']>.1 and r['final_glucose_mM']<50

def test_cofactor_balance_reports_direction():
 r=cofactor_balance(10,5,2,4); assert r['NADH_balance']==5 and r['redox_imbalance']==7 and r['transhydrogenase_direction']=='NADH_to_NADPH'

def test_overflow_activates_above_respiration():
 assert overflow_metabolism(10,5)['acetate_flux']>0 and overflow_metabolism(3,5)['acetate_flux']==0

def test_fermentation_product_accumulates():
 r=fermentation_simulate(hours=8); assert r['final_product_mM']>0 and r['final_biomass_gdw_l']>.1 and len(r['time_h'])==193

def test_stress_compounds_reduce_viability():
 assert stress_response()['combined_viability']>stress_response(ph=5,temperature_c=45,osmolarity=1,product_mM=100)['combined_viability']

def test_resilience_targets_failed_dimensions():
 s=stress_response(temperature_c=50,osmolarity=1,product_mM=100); r=resilience_design(s); assert len(r['modules'])>=2 and r['architecture_only']

def test_promoter_copy_optimization_respects_burden():
 r=promoter_copy_optimize(2,burden_limit=.2); assert r['recommendation']['feasible'] and r['recommendation']['burden']<=.2

def test_integration_site_prefers_safe_context():
 a=integration_site_score(.9,5000,.01); b=integration_site_score(.2,10,.8,.5); assert a['score']>b['score']

def test_dynamic_control_switches_phase():
 assert dynamic_control(.1)['phase']=='growth' and dynamic_control(10)['phase']=='production'

def test_stochastic_control_is_seeded_nonnegative():
 a=stochastic_control(seed=3); b=stochastic_control(seed=3); assert a==b and min(a['protein'])>=0

def test_circuit_burden_scales_with_gates():
 assert circuit_burden(10)['fraction']>circuit_burden(1)['fraction']

def test_ale_is_seeded_and_non_decreasing():
 a=ale_trajectory(seed=4); b=ale_trajectory(seed=4); assert a==b and all(y>=x for x,y in zip(a['fitness'],a['fitness'][1:]))

def test_beneficial_mutations_rank_severity():
 r=beneficial_mutations({'heat':.9,'salt':.2}); assert r[0]['target']=='heat'

def test_genome_comparison_and_functional_gap():
 modern=GENES[:3]; ancient=GENES[:2]+[{'name':'cold','category':'cold_tolerance','size_bp':500}]; c=compare_genomes(ancient,modern); g=functional_gap_analysis(ancient,modern); assert 'cold' in c['ancient_only'] and g['gap_count']==1

def test_regulatory_compatibility_bounded():
 r=regulatory_compatibility(.4,.5,.8,.9); assert 0<=r['score']<=1

def test_modular_chassis_counts_genes():
 base=design_minimal_genome(GENES); module=production_module('x',['a','b']); r=modular_chassis(base,[module]); assert r['total_gene_count']==base['minimal_set_size']+2 and r['module_count']==1

def test_process_scale_flags_oxygen_risk():
 r=process_scale_risk(1000,10,1,100); assert r['oxygen_risk'] and r['overall_risk']>0

def test_diagnostics_are_honest_finite_metrics():
 d=genome_diagnostics(GENES); assert 20<=len(d)<40 and all(math.isfinite(v) for v in d.values())

def test_compiler_covers_genome_metabolism_process_control():
 r=compile_synthetic_life(GENES,seed=2); assert r['validation']['valid'] and r['metabolic_optimization']['status']=='optimal' and r['fermentation']['final_product_mM']>0 and r['control']['phase']=='production'
 assert 'no trained model and not clinically validated' in r['model_status'] and 'institutional review' in r['design_status']

@pytest.mark.parametrize('bad',[[],None])
def test_optimizer_rejects_empty_catalog(bad):
 with pytest.raises(ValueError): optimize_minimal_genome(bad)
