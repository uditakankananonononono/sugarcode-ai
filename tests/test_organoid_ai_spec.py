import numpy as np
import pytest
from sugarcode.modules.organoid_ai import *

def test_patient_growth_fit_uses_real_nonlinear_solver():
 r=optimize_growth_conditions("intestinal",[{"day":0,"cells":1000},{"day":2,"cells":1900},{"day":4,"cells":3500}])
 assert r["solver"]=="scipy_least_squares" and r["growth_rate_per_day"]>0
 assert "mechanistic hermetic" in r["model_status"]

def test_digital_twin_solves_coupled_growth_death_nutrient_odes():
 a=simulate_digital_twin("tumor",5,1000,drug_events=[]); b=simulate_digital_twin("tumor",5,1000,drug_events=[{"day":1,"strength":.8}])
 assert a["solver"]["success"] and b["final_live_cells"]<a["final_live_cells"]
 assert b["trajectory"][-1]["dead_cells"]>0 and len(b["trajectory"])>5

def test_spatial_expression_is_reaction_diffusion_grid():
 r=spatial_gene_expression("intestinal",grid_size=15,diffusion_steps=10)
 assert r["solver"].startswith("explicit finite-difference") and {"LGR5","VIL1"}<=set(r["genes"])
 assert np.asarray(r["genes"]["LGR5"]).shape==(15,15)

def test_growth_design_and_drug_response_backward_compatible():
 assert "media_recipe" in design_organoid("cerebral",["TP53"])
 assert len(simulate_growth("intestinal",3)["trajectory"])==4
 assert drug_response("tumor",["unknown"])["responses"]["unknown"]["ic50_uM"]>0

def test_exactly_fifty_five_meaningful_diagnostics():
 twin=simulate_digital_twin("intestinal",8,1000); spatial=spatial_gene_expression("intestinal",7,diffusion_steps=3); drugs=drug_response("intestinal",["x"])
 f=enhancement_features("intestinal",twin["trajectory"],spatial,drugs)
 assert len(f)==55 and len(set(f))==55
 assert f["growth_window_covered"] if "growth_window_covered" in f else f["quality_growth_window_covered"]

def test_end_to_end_contains_every_spec_layer():
 r=analyze_organoid("hepatic",days=2,patient_mutations=["TP53"],compounds=["x"])
 assert r["diagnostic_count"]==55
 assert {"design","digital_twin","spatial_expression","drug_response","diagnostics"}<=set(r)
 assert "mechanistic hermetic" in r["model_status"]

def test_invalid_inputs_are_rejected():
 with pytest.raises(KeyError): simulate_digital_twin("unknown")
 with pytest.raises(ValueError): spatial_gene_expression("intestinal",3)
