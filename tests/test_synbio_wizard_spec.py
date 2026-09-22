import math
import pytest
from sugarcode.modules.synbio_wizard import *

def test_goal_parser_catalog_and_natural_phrase():
 assert parse_goal('vanillin')['product']=='vanillin' and parse_goal('produce vanillin sustainably')['product']=='vanillin'

def test_unknown_goal_is_informative():
 with pytest.raises(KeyError): run_wizard('unobtanium_synthesis')

def test_chassis_scores_have_components():
 r=score_chassis('insulin'); assert r==sorted(r,key=lambda x:(-x['score'],x['chassis'])) and r[0]['components']

def test_codon_metrics_gc_and_cai():
 r=codon_metrics('ATGGCCGCCGCC','E_coli'); assert 0<=r['cai_proxy']<=1 and r['length_nt']==12 and r['gc_fraction']>.5

def test_rbs_thermodynamic_response():
 a=rbs_thermodynamics('AUAUAUAUAUAU'); b=rbs_thermodynamics('GCGCGCGCGCGC'); assert a['delta_g_kcal_mol']>b['delta_g_kcal_mol'] and 0<=b['accessibility']<=1

def test_promoter_activation_and_repression():
 assert promoter_kinetics(10)['transcription_rate_reu_h']>promoter_kinetics(.01)['transcription_rate_reu_h']
 assert promoter_kinetics(10,repressor=True)['transcription_rate_reu_h']<promoter_kinetics(.01,repressor=True)['transcription_rate_reu_h']

def test_competitive_binding_reduces_occupancy():
 assert binding_occupancy(1,1,10,1)<binding_occupancy(1,1)

def test_michaelis_menten_saturates_and_inhibition_reduces():
 assert michaelis_menten(10,1,1)>michaelis_menten(.1,1,1) and michaelis_menten(1,1,1,10,1)<michaelis_menten(1,1,1)

def test_enzyme_capacity_scales_with_kcat():
 assert enzyme_capacity(20,1,.5,1)>enzyme_capacity(10,1,.5,1)

def test_flux_balance_constraints_and_serial_flux():
 r=flux_balance(['a','b','c']); assert r['product_flux_mmol_gdw_h']>0 and r['atp_use']<=20 and r['redox_use']<=12

def test_resource_burden_scales():
 assert resource_burden(100,1,500)['fraction']>resource_burden(1,.1,50)['fraction']

def test_deterministic_expression_approaches_steady_state():
 r=deterministic_expression(hours=100); assert r['protein'][-1]==pytest.approx(r['steady_protein'],rel=.01)

def test_gillespie_is_seeded_and_nonnegative():
 a=gillespie_expression(hours=2,seed=3); b=gillespie_expression(hours=2,seed=3); assert a==b and min(a['final_mrna'],a['final_protein'])>=0

def test_logic_gate_semantics():
 assert logic_circuit('AND',[1,1])['output'] and logic_circuit('OR',[0,1])['output'] and logic_circuit('NOT',[0])['output']

def test_crispr_scan_pam_gc_and_seed():
 r=scan_guides('A'*10+'GCGCGCGCGCGCGCGCGCGC'+'AGG'+'T'*10); assert r and any(x['pam']=='AGG' for x in r) and all(0<=x['gc']<=1 for x in r)

def test_variant_effect_stop_gain():
 r=variant_effect('TGG','TGA',.9,True); assert r['class']=='stop_gain' and r['deleterious_probability']>.8

def test_mutation_propagates_to_phenotype():
 r=mutation_propagation('TGG','TGA',active_site=True); assert r['pathway_flux']<1 and r['growth_rate_h']<.5 and r['phenotype_change_fraction']>0

def test_evolution_burden_reduces_stability():
 assert evolutionary_stability(burden=.2)['functional_fraction']<evolutionary_stability(burden=.01,selection=.02)['functional_fraction']

def test_docking_score_has_limitation_label():
 r=docking_surrogate(20,3); assert r['delta_g_kcal_mol']<0 and 'solvent' in r['limitation']

def test_uncertainty_is_seeded_with_ci():
 a=uncertainty_distribution(1,seed=4); b=uncertainty_distribution(1,seed=4); assert a==b and a['ci90'][0]<a['mean']<a['ci90'][1]

def test_strategy_tradeoffs_rank():
 r=compare_strategies([{'name':'safe','efficiency':.6,'robustness':.9,'risk':.1},{'name':'weak','efficiency':.2,'robustness':.2,'risk':.8}]); assert r[0]['name']=='safe'

def test_experiments_target_highest_uncertainty():
 r=suggest_experiments([{'name':'a','domain':'flux','uncertainty':.9},{'name':'b','domain':'structure','uncertainty':.2}],1); assert r[0]['target']=='a' and 'flux' in r[0]['experiment'].lower()

def test_assembly_switches_with_part_count():
 assert assembly_recommendation(5)['method']=='Golden Gate' and assembly_recommendation(15)['method']=='Gibson'

def test_plasmid_architecture_is_nonprocedural():
 r=plasmid_architecture(['geneA','geneB']); assert len(r['modules'])==2 and 'institutional review' in r['assembly']['design_status']

def test_sbml_export_has_reactions():
 x=sbml_export(['step1','step2']); assert '<sbml' in x and 'R1' in x and 'level="3"' in x

def test_knowledge_graph_has_provenance():
 r=knowledge_graph('vanillin'); assert r['nodes'] and r['edges'] and not r['source_provenance']['live_sources']

def test_feedback_posterior_learns():
 r=ingest_experimental_feedback([{'design':'d','successes':8,'total':10}]); assert r['posterior']['d']['mean']>.7

def test_environment_response_changes_with_ph():
 assert environment_response(1,ph=7)['relative_rate']>environment_response(1,ph=5)['relative_rate']

def test_diagnostics_are_honest_finite_metrics():
 d=wizard_diagnostics('vanillin'); assert 20<=len(d)<40 and all(math.isfinite(v) for v in d.values())

def test_compiler_covers_multiscale_stack():
 r=compile_project('vanillin',seed=2); assert r['pathway']['solver'].startswith('scipy') and r['sbml'].startswith('<sbml') and r['knowledge_graph']['edges'] and r['suggested_experiments']
 assert 'no trained model and not clinically validated' in r['model_status']

def test_legacy_run_wizard_shape_and_ci():
 r=run_wizard('vanillin',seed=9); lo,hi=r['steps']['6_yield_simulation']['90pct_CI']; assert r['steps']['4_selected_chassis']['chassis'] in CHASSIS and lo<=r['steps']['6_yield_simulation']['mean_titer_fraction']<=hi and 0<=r['feasibility_score']<=1
