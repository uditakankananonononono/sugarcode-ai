import pytest
from sugarcode.modules.bio_switch import *

STATUS="computational predictions only; no wetlab validation; no sensor performance claim"

def test_hill_kinetics_and_tunable_thresholds_are_computational_and_deterministic():
 assert hill_response(1)==pytest.approx(.5) and hill_response(0)==0
 r=design_sensor_tunable("lactose"); assert len(r["response"])==41 and r["c10_uM"]==.199526 and r["c90_uM"]==6.309573 and r["threshold_ratio"]==31.6228 and r["sensitivity_class"]=="graded analog" and r["model_status"]==STATUS
 u=design_sensor_tunable("theophylline",cooperativity=3,vmax=2); assert u["sensitivity_class"]=="ultrasensitive" and u["response"][20]==1

def test_sensor_modalities_and_binding_redesign_cover_rna_and_protein_paths():
 assert select_sensor_modality("theophylline")["modality"]=="rna_riboswitch"
 assert select_sensor_modality("arabinose",prefer="rna_toehold")["modality"]=="rna_toehold"
 r=binding_pocket_redesign("lactose"); assert r["target_kd_uM"]==.1 and r["kd_shift_log10"]==-1 and r["action"].startswith("tighten") and not r["directed_evolution_recommended"]

def test_reaction_diffusion_chemistry_off_targets_and_decay_are_explicit():
 d=reaction_diffusion_profile("lactose"); assert len(d["positions_um"])==21 and d["intracellular_concentration_uM"][0]==1 and d["intracellular_concentration_uM"][-1]==.818731 and d["tip_to_base_ratio"]==.818731
 c=cheminformatics_descriptors("lactose"); assert c["molecular_weight"]==342.3 and c["bioavailability_class"] in {"moderate","low"} and c["uptake_prediction"]=="transport-mediated uptake expected"
 o=off_target_profile("lactose"); assert len(o["off_targets"])==9 and o["specificity_margin"]==1 and "cross-reactivity" in o["competing_interactions"]
 k=degradation_kinetics("lactose"); assert k["half_life_h"]==6.9315 and k["fraction_remaining"][-1]==.301194

def test_stochastic_noise_logic_temporal_filters_and_feedback_are_reproducible():
 n=gillespie_sensor_noise("lactose",trajectories=5,seed=7); assert n["mean_bound_fraction"]==.564 and n["noise_std"]==.047159 and n["deterministic_occupancy"]==.5 and n["low_copy_number_regime"] and n["model_status"].startswith("stochastic simulation")
 a=multi_input_gate({"lactose":1,"theophylline":.3},"AND"); b=multi_input_gate({"lactose":1,"theophylline":.3},"OR"); assert a["gate_output"]==.25 and b["gate_output"]==.75
 t=temporal_filter([[0,0],[10,1],[20,1],[30,1]]); assert t["filtered_response"]==[0,.33333,.66667,1] and t["verdict"]=="sustained signal accepted"
 p=feedback_loop(); q=feedback_loop("negative"); assert "bistable" in p["verdict"] and "homeostatic" in q["verdict"] and p["output_response"][2]==.5

def test_synthesis_output_has_curves_parts_and_honest_limits():
 r=synthesize_biosensor("lactose"); assert len(r["external_concentrations_uM"])==41 and set(r["predicted_curves"])=={"standard","low_permeability","ultrasensitive"} and all(len(x)==41 for x in r["predicted_curves"].values()) and r["limit_of_detection_uM_external"]==1 and r["required_parts"]==["LacI binding domain","regulated promoter","GFP reporter"] and "no wetlab assembly was performed" in r["assembly_notes"] and r["model_status"]==STATUS

def test_legacy_api_and_public_exports_remain_available():
 r=design_biosensor("lactose"); assert r["architecture"]=="LacI -> promoter control -> GFP" and r["limit_of_detection_uM"]==.1 and r["response_time_min"]==34
 ns={}; exec("from sugarcode.modules.bio_switch import *",ns); assert {"design_biosensor","synthesize_biosensor","gillespie_sensor_noise"}<=set(ns)

def test_validation_errors_are_informative():
 with pytest.raises(ValueError,match="non-negative"): hill_response(-1)
 with pytest.raises(KeyError,match="binding domain"): design_sensor_tunable("glucose")
 with pytest.raises(ValueError,match="unsupported modality"): select_sensor_modality("lactose",prefer="optical")
 with pytest.raises(ValueError,match="points"): reaction_diffusion_profile("lactose",points=1)
 with pytest.raises(ValueError,match="logic"): multi_input_gate({"lactose":1},"XOR")
 with pytest.raises(ValueError,match="strictly increasing"): temporal_filter([[1,1],[1,0]])


def test_sweep_lipinski_counts_and_classes():
    from sugarcode.modules.bio_switch import cheminformatics_descriptors
    lac = cheminformatics_descriptors("lactose")
    assert lac["lipinski_violations"] == 2 and lac["bioavailability_class"] == "low"
    tet = cheminformatics_descriptors("tetracycline")
    assert tet["lipinski_violations"] == 1 and tet["bioavailability_class"] == "moderate"
    ara = cheminformatics_descriptors("arabinose")
    assert ara["lipinski_violations"] == 0 and ara["bioavailability_class"] == "high"


def test_sweep_tetracycline_kd_matches_literature():
    # Takahashi 1991 (PMID 1812784): TetR-tetracycline Ka = 3 +/- 2 x 10^9 M-1
    # -> Kd in the 0.2-1 nM range; curated value must sit in that range.
    from sugarcode.modules.bio_switch import BINDING_DOMAINS
    kd = BINDING_DOMAINS["tetracycline"]["kd_uM"]
    assert 2e-4 <= kd <= 1e-3
