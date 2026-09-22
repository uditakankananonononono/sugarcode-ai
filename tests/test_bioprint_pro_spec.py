import numpy as np
from sugarcode.modules.bioprint_pro import *
def test_carreau_shear_thinning(): assert carreau_yasuda(1)>carreau_yasuda(100)
def test_extrusion_real_dimensionless_and_viability():
 r=oldroyd_b_extrusion(100,.4); assert r["Weissenberg"]>0 and r["Reynolds"]>=0 and 0<r["mean_viability"]<=1
def test_crosslink_pde_builds_heterogeneous_stiffness():
 r=crosslink_reaction_diffusion("ionic",2,points=15); assert len(r["stiffness_kPa"])==15 and max(r["conversion"])>min(r["conversion"])
def test_mechanics_has_relaxation_and_safety():
 r=scaffold_mechanics(crosslink_reaction_diffusion("photo",2,points=15)); assert max(r["relaxed_strain"])<=max(r["instantaneous_strain"]) and r["safety_factor"]>=0
def test_full_simulation_50_computed_diagnostics_disclaimer_separate():
 r=simulate_bioprint((100,.4,2,.35,10)); assert len(r["diagnostics"])>=50 and "model_status" not in r["diagnostics"] and "not clinically validated" in r["model_status"]
def test_optimizer_is_seeded_and_bounded():
 r=optimize_print(seed=2); p=r["parameters"]; assert 20<=p["pressure_kPa"]<=200 and .2<=p["nozzle_mm"]<=.8 and r["solver"]=="differential evolution"
