import pytest
from sugarcode.modules.tissue_eng import *

def test_strategy_selects_cells_materials_layers_and_vascularization():
 r=design_tissue("cardiac_patch",(10,10,3)); assert r["cell_composition"]==["cardiomyocytes","endothelial","fibroblasts"] and r["bioink"]["name"] in BIOINKS and r["print_parameters"]["n_layers"]==15 and r["vascularization"]["required"]

def test_print_calibration_responds_to_material_and_nozzle():
 a=calibrate_printing("skin","gelma",250); b=calibrate_printing("skin","collagen",400); assert a["speed_mm_s"]!=b["speed_mm_s"] and a["predicted_fidelity"]>b["predicted_fidelity"] and "specific printer" in a["calibration_note"]

def test_mechanical_loading_reports_stress_fatigue_and_safety():
 r=simulate_physiological_stress("cardiac_patch",cycles=1000,strain=.05); assert r["peak_stress_kpa"]>0 and 0<r["modulus_retention"]<=1 and r["safety_factor"]>1 and "testing required" in r["model_status"]

def test_oxygen_model_detects_hypoxic_channel_spacing():
 wide=oxygen_profile("liver",channel_spacing_um=500); narrow=oxygen_profile("liver",channel_spacing_um=200); assert wide["hypoxic"] and not narrow["hypoxic"] and wide["minimum_oxygen_percent"]<narrow["minimum_oxygen_percent"]

def test_perfusion_improves_maturation_viability():
 a=viability_forecast("liver",perfused=True); b=viability_forecast("liver",perfused=False); assert a["endpoint_viability"]>b["endpoint_viability"] and len(a["viability_fraction"])==29

def test_drug_plan_has_controls_replicates_and_honest_limits():
 r=drug_testing_plan("skin",["drug_a","drug_b"],3); assert r["sample_count"]==9 and r["groups"][0]["compound"]=="vehicle_control" and r["include_blinded_analysis"] and "clinical efficacy" in r["limitations"][0]

def test_validation_errors_are_informative():
 with pytest.raises(KeyError,match="unknown tissue"): design_tissue("brain")
 with pytest.raises(ValueError,match="nozzle_um"): calibrate_printing("skin",nozzle_um=0)
 with pytest.raises(ValueError,match="points"): oxygen_profile("skin",points=2)
 with pytest.raises(ValueError,match="compounds"): drug_testing_plan("skin",[])
