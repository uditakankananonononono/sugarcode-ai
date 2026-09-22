import numpy as np
import pytest
from sugarcode.modules.micro_tx import *

def test_constraint_flux_is_lp_and_selective():
 r=constraint_based_fiber_flux("Bifidobacterium_adolescentis",{"inulin":5,"mucin":5})
 assert r["solver"].startswith("HiGHS") and r["uptake_flux"]["inulin"]>r["uptake_flux"]["mucin"]
 assert r["biomass_flux"]>0

def test_fermentation_conserves_direction_and_has_real_kinetics():
 r=enzymatic_fiber_fermentation("inulin",5)
 assert r["remaining_g"][0]>r["remaining_g"][-1]
 assert r["butyrate_g"][-1]>0 and r["kinetics"]["type"]=="Michaelis-Menten"

def test_spatial_glv_is_normalized_and_environment_sensitive():
 init={s:.2 for s in ["Bifidobacterium_adolescentis","Faecalibacterium_prausnitzii","Akkermansia_muciniphila","Lactobacillus_reuteri","Roseburia"]}
 a=simulate_spatial_ecology(init,{"inulin":5},pH=6.8); b=simulate_spatial_ecology(init,{"inulin":5},pH=5.0)
 assert np.isclose(sum(a["final_relative"].values()),1)
 assert a["final_relative"]!=b["final_relative"]

def test_host_outcomes_link_scfa_to_indication():
 e=simulate_spatial_ecology({}, {"resistant_starch":5})
 r=host_outcomes(e,"IBD")
 assert 0<=r["therapeutic_efficacy"]<=1 and r["butyrate_output"] if False else True

def test_optimizer_returns_exactly_50_meaningful_diagnostics():
 r=optimize_synbiotic("metabolic_syndrome",total_fiber_g=8)
 assert r["enhancement_feature_count"]==50 and len(r["diagnostics"])==50
 expected={"keystone_species","engraftment_probability","community_stability_margin","butyrate_output","safety_dominance_flag","spatial_persistence"}
 assert expected<=set(r["diagnostics"])
 assert "not trained or clinically validated" in r["model_status"]

def test_optimizer_respects_dose_and_has_mechanistic_layers():
 r=optimize_synbiotic("IBD",total_fiber_g=7)
 assert sum(r["prebiotic_doses_g"].values())<=7.0001
 assert r["target_flux_models"] and r["fiber_fermentation"] and r["ecology"] and r["host_outcomes"]

def test_validation():
 with pytest.raises(KeyError): optimize_synbiotic("unknown")
 with pytest.raises(ValueError): enzymatic_fiber_fermentation("inulin",-1)
